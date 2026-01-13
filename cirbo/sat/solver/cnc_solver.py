import collections
import copy
import typing as tp

from cirbo.core.circuit import Circuit, ALWAYS_TRUE, ALWAYS_FALSE
from cirbo.sat import PySatResult, Cnf, is_satisfiable, PySATSolverNames
from cirbo.sat.solver.circuit_sat_instance import CircuitSatInstance, AssignmentStatus


class CubeAndConquerSolver:

    def __init__(
        self,
        max_depth: int | None = None,
        solver_name: PySATSolverNames = PySATSolverNames.CADICAL195,
    ):
        self.max_depth = max_depth
        self.solver_name = solver_name

    def solve(self, circuit: Circuit) -> PySatResult:
        cubes = self.cube(circuit)
        result = self.conquer(cubes)
        return result

    def cube(self, circuit: Circuit) -> list[CircuitSatInstance]:
        circuit_sat_instance = CircuitSatInstance.from_circuit(circuit)

        if circuit_sat_instance is None:
            return []  # empty list for trivially non-satisfiable case

        return self._cube(circuit_sat_instance)

    def conquer(self, cubes: list[CircuitSatInstance]) -> PySatResult:
        for instance in cubes:
            sat_result = self._solve_instance(instance)
            if sat_result.answer:
                # Build model combining pre-assigned values and SAT solver's model
                model: list[int] = [0] * len(instance.gates_config)
                for gate_conf in instance.gates_config.values():
                    if not gate_conf.is_input:
                        continue
                    assert sat_result.model is not None
                    lit = gate_conf.idx
                    model[gate_conf.idx - 1] = lit if gate_conf.value else -lit
                return PySatResult(answer=True, model=model)
        return PySatResult(answer=False, model=None)

    def _cube(self, instance: CircuitSatInstance, depth: int = 0) -> list[CircuitSatInstance]:
        trivial_assignment_status = instance.apply_trivial_assignments()
        if trivial_assignment_status != AssignmentStatus.OK:
            return []

        if self._check_stop_cube(instance) or (self.max_depth is not None and depth >= self.max_depth):
            return [instance]

        cube_gate = self._select_cube_gate(instance)
        cubes: list[CircuitSatInstance] = []
        for value in (False, True):
            new_instance = copy.deepcopy(instance)
            new_instance.assign(cube_gate, value)
            new_cubes = self._cube(new_instance, depth + 1)
            cubes.extend(new_cubes)
        return cubes

    def _weight_gate(self, instance: CircuitSatInstance, gate_label: str) -> int:
        start_size = instance.circuit.size
        weight = 1
        for i in (False, True):
            new_instance = copy.deepcopy(instance)
            assign_status = new_instance.assign(gate_label, i)
            assert assign_status == AssignmentStatus.OK
            updated_size = new_instance.circuit.size
            mu = start_size - updated_size
            assert mu > 0
            weight *= mu
        return weight

    def _select_cube_gate(self, instance: CircuitSatInstance) -> str:
        best_gate_label = None
        best_weight = 0
        for gate_label in instance.circuit.gates:
            gate = instance.circuit.get_gate(gate_label)
            if gate.gate_type == ALWAYS_TRUE or gate.gate_type == ALWAYS_FALSE:
                continue
            weight = self._weight_gate(instance, gate_label)
            if weight > best_weight:
                best_gate_label, best_weight = gate_label, weight
        assert best_gate_label is not None
        return best_gate_label

    @staticmethod
    def _check_stop_cube(instance: CircuitSatInstance) -> bool:
        # TODO: Refine stop criteria
        return instance.circuit.input_size == 0

    def _solve_instance(self, instance: CircuitSatInstance) -> PySatResult:
        """Solve a cube instance and return the full SAT result."""
        return is_satisfiable(
            cnf=instance.cnf,
            solver_name=self.solver_name,
        )

    def is_sat(self, instance: CircuitSatInstance) -> bool:
        """Check if a cube instance is satisfiable."""
        return self._solve_instance(instance).answer
