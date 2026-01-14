import collections
import copy
import logging
import typing as tp

from cirbo.core.circuit import Circuit, ALWAYS_TRUE, ALWAYS_FALSE, INPUT, AND, NOT
from cirbo.sat import PySatResult, Cnf, is_satisfiable, PySATSolverNames
from cirbo.sat.solver.circuit_sat_instance import CircuitSatInstance, AssignmentStatus

logger = logging.getLogger(__name__)


class CubeAndConquerSolver:

    def __init__(
        self,
        max_depth: int | None = None,
        min_circuit_size: int | None = None,
        solver_name: PySATSolverNames = PySATSolverNames.CADICAL195,
        candidates_limit: int | None = None,
    ):
        self.max_depth = max_depth
        self.min_circuit_size = min_circuit_size
        self.solver_name = solver_name
        self.candidates_limit = candidates_limit

    def solve(self, circuit: Circuit) -> PySatResult:
        cubes = self.cube(circuit)
        result = self.conquer(cubes)
        return result

    def cube(self, circuit: Circuit) -> list[CircuitSatInstance]:

        logger.info("=" * 20)
        logger.info(f"Cube for circuit with {circuit.size} gates")
        logger.info("=" * 20)
        circuit_sat_instance = CircuitSatInstance.from_circuit(circuit)
        logger.info(f"Build an instance with {circuit_sat_instance.circuit.size} gates, {len(circuit_sat_instance.cnf.get_raw())} clauses")

        if circuit_sat_instance is None:
            return []  # empty list for trivially non-satisfiable case

        return list(self._cube(circuit_sat_instance))

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

    def _cube(self, instance: CircuitSatInstance, depth: int = 0) -> tp.List[CircuitSatInstance]:
        # trivial_assignment_status = instance.apply_trivial_assignments()
        # if trivial_assignment_status != AssignmentStatus.OK:
        #     return []
        logger.info(f"Try cube. Depth {depth}, Circuit: {instance.circuit.size}, Cnf: {len(instance.cnf.get_raw())}")

        if self._check_stop_cube(instance, depth):
            logger.info(f"Stop! Depth {depth}, Circuit: {instance.circuit.size} gates, Cnf: {len(instance.cnf.get_raw())} clauses")
            return [instance]

        logger.info("Selecting cube gate...")
        cube_gate_dict = self._select_cube_gate(instance)
        cube_gate = cube_gate_dict["label"]
        if "value" in cube_gate_dict:
            logger.info(f"Hardcode {cube_gate}={cube_gate_dict['value']} as other option leads to contradiction")
            instance.assign(cube_gate, cube_gate_dict["value"])
            return self._cube(instance, depth + 1)

        result = []
        for value in (False, True):
            logger.info(f"Checking {cube_gate}={value}")
            new_instance = copy.deepcopy(instance)
            new_instance.assign(cube_gate, value)
            result.extend(self._cube(new_instance, depth + 1))
        return result

    def _weight_gate(self, instance: CircuitSatInstance, gate_label: str) -> dict:
        start_size = instance.circuit.size
        weight = 1
        for i in (False, True):
            new_instance = copy.deepcopy(instance)
            assign_status = new_instance.assign(gate_label, i)
            # assert assign_status == AssignmentStatus.OK
            if assign_status != AssignmentStatus.OK:
                return {
                    "value": not i
                }
            updated_size = new_instance.circuit.size
            mu = start_size - updated_size
            assert mu > 0
            weight *= mu
        return {
            "weight": weight
        }

    def _select_cube_gate(self, instance: CircuitSatInstance) -> dict:
        best_gate_label = None
        best_weight = 0
        
        candidates = self._get_candidates(instance)
        
        for gate_label in candidates:
            gate = instance.circuit.get_gate(gate_label)
            assert gate is not None and gate not in (ALWAYS_TRUE, ALWAYS_FALSE, NOT), "Gate should not be constant or NOT"
                
            weight_dict = self._weight_gate(instance, gate_label)
            if "value" in weight_dict:
                return {
                    "label": gate_label,
                    "value": weight_dict["value"]
                }
            weight = weight_dict["weight"]
            if weight > best_weight:
                best_gate_label, best_weight = gate_label, weight
        
        assert best_gate_label is not None, "Could not select a branching variable"
        return {
            "label": best_gate_label
        }

    def _get_candidates(self, instance: CircuitSatInstance) -> list[str]:
        circuit = instance.circuit
        all_gates = []
        for gate_label in circuit.gates:
            gate = circuit.get_gate(gate_label)
            if gate.gate_type in (ALWAYS_TRUE, ALWAYS_FALSE, NOT):
                continue
            assert gate.gate_type in (AND, INPUT), "Gate should be AND or INPUT"
            all_gates.append(gate_label)

        if self.candidates_limit is None:
            return all_gates

        # Score candidates
        scores: list[tuple[int, str]] = []
        for gate_label in all_gates:
            gate = circuit.get_gate(gate_label)
            indegree = len(gate.operands)

            # Calculate outdegree ignoring NOTs, but only look at neighbors and their neighbors
            outdegree = 0
            for user_label in circuit.get_gate_users(gate_label):
                if circuit.get_gate(user_label).gate_type == NOT:
                    outdegree += len(circuit.get_gate_users(user_label))
                else:
                    outdegree += 1
            
            score = (indegree + 1) * (outdegree + 1)
            scores.append((score, gate_label))
            
        scores.sort(key=lambda x: x[0], reverse=True)
        return [x[1] for x in scores[:self.candidates_limit]]

    def _check_stop_cube(self, instance: CircuitSatInstance, depth: int) -> bool:
        # TODO: when to stop?
        if instance.circuit.input_size == 0:
            return True
        if self.max_depth is not None and depth >= self.max_depth: # reached max depth
            return True
        if self.min_circuit_size is not None and instance.circuit.size <= self.min_circuit_size: # reached min circuit size
            return True
        return False

    def _solve_instance(self, instance: CircuitSatInstance) -> PySatResult:
        """Solve a cube instance and return the full SAT result."""
        return is_satisfiable(
            cnf=instance.cnf,
            solver_name=self.solver_name,
        )

    # def is_sat(self, instance: CircuitSatInstance) -> bool:
    #     """Check if a cube instance is satisfiable."""
    #     return self._solve_instance(instance).answer
