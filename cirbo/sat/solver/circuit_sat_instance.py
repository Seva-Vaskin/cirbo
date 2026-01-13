import collections
import copy
import enum
import typing as tp
from dataclasses import dataclass

from cirbo.core.circuit import Circuit, INPUT, Transformer
from cirbo.core.circuit.gate import NOT, AND, ALWAYS_FALSE, ALWAYS_TRUE, Gate
from cirbo.minimization import RemoveRedundantGates
from cirbo.minimization.simplification.remove_constant_gates import RemoveConstantGates
from cirbo.sat import PySatResult, tseytin_transformation, Cnf, is_satisfiable, PySATSolverNames


class AssignmentStatus(enum.Enum):
    OK = "OK"
    CONFLICT = "CONFLICT"


@dataclass
class AssignmentResult:
    status: AssignmentStatus
    instance: tp.Optional["CircuitSatInstance"]


@dataclass
class GateConfig:
    label: str
    idx: int
    is_input: bool
    value: tp.Optional[bool] = None


class CircuitSatInstance:
    def __init__(
            self,
            circuit: Circuit,
    ):
        self.circuit = circuit
        self._check_circuit()
        self.gates_config: tp.Dict[str, GateConfig] = {}
        self.cnf = tseytin_transformation(self.circuit)
        for gate_label in self.circuit.gates:
            gate_idx = self.cnf.get_var(gate_label)
            is_input = self.circuit.get_gate(gate_label).gate_type == INPUT
            self.gates_config[gate_label] = GateConfig(label=gate_label, idx=gate_idx, is_input=is_input)

    def _check_circuit(self):
        for gate in self.circuit.gates.values():
            if gate.gate_type == INPUT:
                continue
            if gate.gate_type == AND:
                if len(gate.operands) != 2:
                    raise ValueError(f"AND gate {gate.label} has {len(gate.operands)} operands, expected 2")
                continue
            if gate.gate_type == NOT:
                if len(gate.operands) != 1:
                    raise ValueError(f"NOT gate {gate.label} has {len(gate.operands)} operands, expected 1")
                continue
            raise ValueError(f"Gate {gate.label} has unsupported type {gate.gate_type.name}")

    @classmethod
    def from_circuit(cls, circuit: Circuit) -> tp.Optional["CircuitSatInstance"]:
        assert circuit.output_size == 1

        next_free_idx = 0

        def __register_new_gate() -> int:
            nonlocal next_free_idx
            next_free_idx += 1
            return next_free_idx

        saved_gates: dict[str, int] = collections.defaultdict(__register_new_gate)

        for input_label in circuit.inputs:
            _ = saved_gates[input_label]

        instance = cls(
            circuit,
        )
        assign_status = instance.assign(instance.circuit.outputs[0], True)
        if assign_status != AssignmentStatus.OK:
            return None
        return instance

    def simplify(self):
        self.circuit = Transformer.apply_transformers(self.circuit, [
            RemoveConstantGates(),
        ])

    def assign(self, label: str, value: bool) -> AssignmentStatus:
        assignment_status = self._assign_and_propagate(label, value)
        if assignment_status != AssignmentStatus.OK:
            return assignment_status
        self.simplify()
        return AssignmentStatus.OK

    def assign_many(self, assignment: dict[str, bool]) -> AssignmentStatus:
        for label, value in assignment.items():
            status = self._assign_and_propagate(label, value)
            if status != AssignmentStatus.OK:
                return status
        self.simplify()
        return AssignmentStatus.OK

    def _assign_and_propagate(self, label: str, value: bool) -> AssignmentStatus:
        gate = self.circuit.get_gate(label)

        if gate.gate_type == ALWAYS_TRUE or gate.gate_type == ALWAYS_FALSE:
            if gate.operator() != value:
                return AssignmentStatus.CONFLICT
            return AssignmentStatus.OK

        if gate.gate_type == INPUT:
            inputs_to_true, inputs_to_false = [], []
            (inputs_to_true if value else inputs_to_false).append(label)
            self.circuit = self.circuit.replace_inputs(inputs_to_true, inputs_to_false)
            self.gates_config[label].value = value
            # Add unit clause to fix the input value in the CNF
            lit = self.gates_config[label].idx
            self.cnf.add_clause([lit if value else -lit])
            return AssignmentStatus.OK

        # unattach users
        is_output = label in self.circuit.outputs
        for operand in gate.operands:
            self.circuit._remove_user(gate_label=operand, user=label)
            if (
                    True
                    and is_output
                    and len(self.circuit.get_gate_users(operand)) == 0
                    and operand not in self.circuit.outputs
            ):
                self.circuit._outputs.append(operand)

        # change gate to const
        if label in self.circuit.outputs:
            self.circuit.remove_gate(label)
        else:
            new_gate_type = ALWAYS_TRUE if value else ALWAYS_FALSE
            new_gate = Gate(label=label, gate_type=new_gate_type, operands=())
            self.circuit._gates[label] = new_gate

        if gate.gate_type == NOT:
            return self._assign_and_propagate(gate.operands[0], not value)

        if gate.gate_type == AND and value:
            for operand_label in gate.operands:
                assignment_status = self._assign_and_propagate(operand_label, True)
                if assignment_status != AssignmentStatus.OK:
                    return assignment_status
            return AssignmentStatus.OK

        if gate.gate_type == AND and not value:
            assert len(gate.operands) == 2
            lit0 = self.gates_config[gate.operands[0]].idx
            lit1 = self.gates_config[gate.operands[1]].idx
            self.cnf.add_clause([-lit0, -lit1])
            return AssignmentStatus.OK

        raise Exception(f"Propagation error: Unsupported operator {gate.gate_type}")

    def apply_trivial_assignments(self) -> AssignmentStatus:
        assignments: tp.Dict[str, bool] = {}
        for gate_label in self.circuit.gates:
            false_instance = copy.deepcopy(self)
            false_ok = false_instance.assign(gate_label, False) == AssignmentStatus.OK
            true_instance = copy.deepcopy(self)
            true_ok = true_instance.assign(gate_label, True) == AssignmentStatus.OK

            if not false_ok and not true_ok:
                return AssignmentStatus.CONFLICT
            elif not false_ok:
                assignments[gate_label] = True
            elif not true_ok:
                assignments[gate_label] = False

        return self.assign_many(assignments)
