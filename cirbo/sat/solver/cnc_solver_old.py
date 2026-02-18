import copy
import logging
from dataclasses import dataclass

from cirbo.core.circuit import Circuit, ALWAYS_TRUE, ALWAYS_FALSE, INPUT, AND, NOT
from cirbo.sat import PySatResult, is_satisfiable, PySATSolverNames
from cirbo.sat.solver.circuit_sat_instance import CircuitSatInstance, AssignmentStatus
from extensions.abc_wrapper.src.abc import abc_transform

logger = logging.getLogger(__name__)


@dataclass
class GateWeightResult:
    """Result of weighting a gate for cube selection."""
    weight: int | None = None
    forced_value: bool | None = None

    @property
    def is_forced(self) -> bool:
        """Returns True if one branch leads to conflict, forcing the other value."""
        return self.forced_value is not None


@dataclass
class CubeGateSelection:
    """Result of selecting a gate for cube splitting."""
    label: str
    forced_value: bool | None = None
    passed_soft_threshold: bool = True  # True if weight > soft_threshold

    @property
    def is_forced(self) -> bool:
        """Returns True if this gate must take a specific value."""
        return self.forced_value is not None


class CubeAndConquerSolver:

    def __init__(
        self,
        max_depth: int | None = None,
        min_circuit_size: int | None = None,
        solver_name: PySATSolverNames = PySATSolverNames.CADICAL195,
        candidates_limit: int | None = None,
        hard_threshold: float | None = None,
        soft_threshold: float | None = None,
        soft_threshold_limit: int | None = None,
    ):
        self.max_depth = max_depth
        self.min_circuit_size = min_circuit_size
        self.solver_name = solver_name
        self.candidates_limit = candidates_limit
        self.hard_threshold = hard_threshold
        self.soft_threshold = soft_threshold
        self.soft_threshold_limit = soft_threshold_limit

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

        return list(self._cube(circuit_sat_instance, depth=0, soft_threshold_counter=0))

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

    def try_simplify_instance(self, instance: CircuitSatInstance) -> CircuitSatInstance:
        simplified_instance = abc_transform(instance.circuit, "fraig")
        return simplified_instance

    def _cube(self, instance: CircuitSatInstance, depth: int = 0, soft_threshold_counter: int = 0) -> list[CircuitSatInstance]:
        logger.info(f"Try cube. Depth {depth}, Circuit: {instance.circuit.size}, Cnf: {len(instance.cnf.get_raw())}, soft_th_count: {soft_threshold_counter}")

        if self._check_stop_cube(instance, depth, soft_threshold_counter):
            logger.info(f"Stop! Depth {depth}, Circuit: {instance.circuit.size} gates, Cnf: {len(instance.cnf.get_raw())} clauses")
            return [instance]

        logger.info("Selecting cube gate...")
        cube_gate_selection = self._select_cube_gate(instance)

        # simplified_circuit = self.try_simplify_instance(instance)
        # logger.info(f"Simplified circuit: {simplified_circuit.size} gates, reduction rate: {100 * (instance.circuit.size - simplified_circuit.size) / instance.circuit.size:.1f}%")
        
        if cube_gate_selection is None:
            logger.info(f"No candidates meet hard threshold - stopping at depth {depth}")
            return [instance]
        
        # Update soft threshold counter if soft threshold was not passed
        new_soft_counter = soft_threshold_counter
        if not cube_gate_selection.passed_soft_threshold:
            new_soft_counter += 1
            logger.info(f"Soft threshold not passed, counter: {new_soft_counter}")
        else: 
            new_soft_counter = 0
            logger.info(f"Soft threshold passed, counter reset to 0")
        if cube_gate_selection.is_forced:
            logger.info(f"Hardcode {cube_gate_selection.label}={cube_gate_selection.forced_value} as other option leads to contradiction")
            instance.assign(cube_gate_selection.label, cube_gate_selection.forced_value)
            return self._cube(instance, depth + 1, new_soft_counter)

        result = []
        for value in (False, True):
            logger.info(f"Checking {cube_gate_selection.label}={value}")
            new_instance = copy.deepcopy(instance)
            new_instance.assign(cube_gate_selection.label, value)
            result.extend(self._cube(new_instance, depth + 1, new_soft_counter))
        return result

    def _weight_gate(self, instance: CircuitSatInstance, gate_label: str) -> GateWeightResult:
        start_size = instance.circuit.size
        weight = 1
        # logger.info(f"Weighting gate {gate_label} with start size {start_size}")
        for i in (False, True):
            new_instance = copy.deepcopy(instance)
            assign_status = new_instance.assign(gate_label, i)
            if assign_status != AssignmentStatus.OK:
                return GateWeightResult(forced_value=not i)
            updated_size = new_instance.circuit.size
            mu = start_size - updated_size
            # logger.info(f"Weighting gate {gate_label} with mu {mu} for value {i}")
            assert mu > 0
            weight *= mu
        return GateWeightResult(weight=weight)

    def _select_cube_gate(self, instance: CircuitSatInstance) -> CubeGateSelection | None:
        best_gate_label = None
        best_weight = 0
        
        candidates = self._get_candidates(instance)
        
        if not candidates:
            return None  # No candidates available
        
        for gate_label in candidates:
            gate = instance.circuit.get_gate(gate_label)
            assert gate is not None and gate not in (ALWAYS_TRUE, ALWAYS_FALSE, NOT), "Gate should not be constant or NOT"
                
            weight_result = self._weight_gate(instance, gate_label)
            if weight_result.is_forced:
                return CubeGateSelection(label=gate_label, forced_value=weight_result.forced_value)
            
            # Filter by hard threshold - skip candidates that don't meet it
            if self.hard_threshold is not None and weight_result.weight <= self.hard_threshold:
                continue
            
            if weight_result.weight > best_weight:
                best_gate_label, best_weight = gate_label, weight_result.weight
        
        if best_gate_label is None:
            logger.info(f"No candidates meet hard threshold {self.hard_threshold}")
            return None

        # Check if best candidate passes soft threshold
        passed_soft = True
        if self.soft_threshold is not None and best_weight <= self.soft_threshold:
            passed_soft = False

        logger.info(f"Selected {best_gate_label} with weight {best_weight}, passed_soft={passed_soft}")
        
        return CubeGateSelection(label=best_gate_label, passed_soft_threshold=passed_soft)

    def _get_candidates(self, instance: CircuitSatInstance) -> list[str]:
        circuit = instance.circuit
        all_gates = []
        for gate_label in circuit.gates:
            gate = circuit.get_gate(gate_label)
            if gate.gate_type in (ALWAYS_TRUE, ALWAYS_FALSE, NOT):
                continue
            assert gate.gate_type in (AND, INPUT), "Gate should be AND or INPUT"
            all_gates.append(gate_label)

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
        
        # Limit candidates by count (threshold filtering happens on real weights in _select_cube_gate)
        scores = scores[:self.candidates_limit]
        # logger.info(f"Selected {len(scores)} candidates")
        return [x[1] for x in scores]

    def _check_stop_cube(self, instance: CircuitSatInstance, depth: int, soft_threshold_counter: int = 0) -> bool:
        if instance.circuit.input_size == 0:
            return True
        if self.max_depth is not None and depth >= self.max_depth:  # reached max depth
            return True
        if self.min_circuit_size is not None and instance.circuit.size <= self.min_circuit_size:  # reached min circuit size
            return True
        if self.soft_threshold_limit is not None and soft_threshold_counter > self.soft_threshold_limit:  # soft threshold limit reached
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
