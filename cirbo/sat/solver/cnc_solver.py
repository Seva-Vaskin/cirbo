import copy
import enum
import logging
import sys
import time
import uuid
from dataclasses import dataclass
import collections
import typing as tp

from cirbo.core import Circuit
from cirbo.core.circuit import gate, Transformer
from cirbo.minimization.simplification import RemoveConstantGates
from cirbo.sat import PySatResult, is_satisfiable, PySATSolverNames, Cnf
from extensions.abc_wrapper.src.abc import abc_transform

sys.setrecursionlimit(int(1e5))

logger = logging.getLogger(__name__)


class GateAssignmentResult(enum.Enum):
    OK = "OK"
    CONFLICT = "CONFLICT"

    @classmethod
    def from_is_conflict(cls, is_conflict: bool) -> "GateAssignmentResult":
        if is_conflict:
            return cls.CONFLICT
        else:
            return cls.OK

    @classmethod
    def from_is_ok(cls, is_ok: bool) -> "GateAssignmentResult":
        if is_ok:
            return cls.OK
        else:
            return cls.CONFLICT


class CubeAndConquerSolver:
    @dataclass
    class Config:
        max_depth: int = 2
        scoring_candidates: int = 5
        sat_solver: PySATSolverNames = PySATSolverNames.CADICAL195

    @dataclass
    class Cube:
        ckt: Circuit
        depth: int = 0
        parent_size: tp.Optional[int] = None
        delta_size: tp.Optional[int] = None

    def __init__(
            self,
            config: Config = Config()
    ):
        self._config = config

    @property
    def config(self):
        return self._config

    def solve(self, circ: Circuit) -> PySatResult:
        cubes = self.cube(circ)
        result = self.conquer(cubes)
        return result

    def cube(self, ckt: Circuit) -> list[Cube]:

        result: list[CubeAndConquerSolver.Cube] = list()

        stack: collections.deque[CubeAndConquerSolver.Cube] = collections.deque()
        stack.append(CubeAndConquerSolver.Cube(ckt=ckt))
        states_visited = 0
        while stack:
            states_visited += 1
            _cube = stack.pop()
            _indent = '  ' * _cube.depth
            print(f"{_indent} Cube with {_cube.ckt.size} gates, outputs {_cube.ckt.output_size}, depth {_cube.depth}")
            _simplified = _simplify(_cube.ckt, indent=_indent)
            if _simplified is None:
                print(f"{_indent} Stopping cubing at depth {_cube.depth} with {_cube.ckt.size} gates (simplification found contradiction)")
                continue
            _cube.ckt = _simplified
            if _cube.parent_size is not None:
                _cube.delta_size = _cube.parent_size - _cube.ckt.size
            logger.info(f"{_indent} Simplified cube with {_cube.ckt.size} gates")
            if self._should_stop_cubing(_cube):
                # print(f"{_indent} Stopping cubing at depth {_cube.depth} with {_cube.ckt.size} gates (should stop cubing)")
                result.append(_cube)
                continue
            new_cubes = self._cube_once(_cube)
            stack.extend(new_cubes)
        print(f"States visited: {states_visited}")
        return result

    def conquer(self, cubes: list[Cube]) -> PySatResult:
        for i, cube in enumerate(cubes):
            cnf = Cnf.from_circuit(cube.ckt)
            result = is_satisfiable(
                cnf=cnf,
                solver_name=self.config.sat_solver,
            )
            if result.answer:
                return result
        return PySatResult(answer=False, model=None)

    def _should_stop_cubing(self, cube: Cube) -> bool:
        if cube.depth > self.config.max_depth:
            indent = '  ' * cube.depth
            print(f"{indent} Stopping cubing at depth {cube.depth} with {cube.ckt.size} gates (max depth reached)")
            return True

        # if cube.delta_size is not None and cube.delta_size <= 1:
        #     return True
        
        has_and_gates = any(g.gate_type == gate.AND for g in cube.ckt.gates.values())
        if not has_and_gates:
            indent = '  ' * cube.depth
            print(f"{indent} Stopping cubing at depth {cube.depth} with {cube.ckt.size} gates (no AND gates)")
            return True
        
        return False

    def _cube_once(self, _cube: Cube) -> list[Cube]:
        selected_gate, gate_score_res = self._select_cube_gate(_cube)
        result = []

        def cube_into_value(value: bool):
            new_ckt = copy.deepcopy(_cube.ckt)
            res, new_ckt = _assign_gate(new_ckt, selected_gate.label, value)
            result.append(
                self.Cube(
                    ckt=new_ckt,
                    depth=_cube.depth + 1,
                    parent_size=_cube.ckt.size,
                )
            )

        match gate_score_res.status:
            case GateScoreResult.Status.CONFLICT:
                return []
            case GateScoreResult.Status.FORCED_VALUE:
                cube_into_value(gate_score_res.forced_value)
            case GateScoreResult.Status.SCORED:
                cube_into_value(False)
                cube_into_value(True)

        return result

    def _select_cube_gate(self, _cube: Cube) -> tp.Tuple[gate.Gate, "GateScoreResult"]:
        fast_scored = [
            (_fast_gate_score(_cube.ckt, g), g)
            for g in _cube.ckt.gates.values()
            if g.gate_type == gate.AND
        ]
        fast_scored.sort(key=lambda x: x[0], reverse=True)

        best_gate: tp.Optional[gate.Gate] = None
        best_score: tp.Optional[GateScoreResult] = None
        for (_, g) in fast_scored[:self.config.scoring_candidates]:
            gate_scored = _slow_gate_score(_cube.ckt, g)
            match gate_scored.status:
                case gate_scored.Status.CONFLICT:
                    return g, gate_scored
                case gate_scored.Status.FORCED_VALUE:
                    best_gate = g
                    best_score = gate_scored
                case gate_scored.Status.SCORED:
                    assert gate_scored.score is not None

                    if best_score is None or (
                            best_score.status == GateScoreResult.Status.SCORED and
                            best_score.score < gate_scored.score
                    ):
                        best_score = gate_scored
                        best_gate = g
        return best_gate, best_score


def _assign_gate(ckt: Circuit, label: str, value: bool) -> tuple[GateAssignmentResult, Circuit]:
    _gate = ckt.get_gate(label)

    if _gate.label in ckt.outputs and not value:
        # if output is False it is immediate conflict
        return GateAssignmentResult.from_is_conflict(True), ckt

    match _gate.gate_type:
        case gate.ALWAYS_TRUE | gate.ALWAYS_FALSE:
            return GateAssignmentResult.from_is_conflict(_gate.operator() != value), ckt
        case gate.INPUT:
            ckt = _assign_input_gate(ckt, _gate, value)
            return GateAssignmentResult.OK, ckt
        case gate.NOT:
            return _assign_not_gate(ckt, _gate, value)
        case gate.IFF:
            return _assign_iff_gate(ckt, _gate, value)
        case gate.AND:
            return _assign_and_gate(ckt, _gate, value)
        case _:
            raise Exception(f"Propagation error: Unsupported operator {_gate.gate_type}")


def _simplify(ckt: Circuit, indent: str = '') -> tp.Optional[Circuit]:
    """Simplify the circuit. Returns None if a contradiction (ALWAYS_FALSE output) is detected."""
    ckt = Transformer.apply_transformers(ckt, [
        RemoveConstantGates(keep_false_outputs=True),
    ])
    if any(ckt.get_gate(ckt.output_at_index(i)).gate_type == gate.ALWAYS_FALSE for i in range(ckt.output_size)):
        return None
    if ckt.output_size > 0:
        orig_size = ckt.size
        logger.info(f"{indent}Simplify: Applying Fraig to circuit with {orig_size} gates")
        time_start = time.time()
        ckt = abc_transform(ckt, "strash; &get; &fraig -x -L 40 -C 1000; &put")
        time_end = time.time()
        print(f"{indent}Simplify: Fraig applied to circuit with {ckt.size} gates, improvement {(ckt.size - orig_size)/orig_size*100:.2f}%, took {time_end - time_start:.2f} seconds")
    return ckt


def _simplify_light(ckt: Circuit) -> Circuit:
    ckt = Transformer.apply_transformers(ckt, [
        RemoveConstantGates(),
    ])
    return ckt


def _assign_input_gate(ckt: Circuit, _gate: gate.Gate, value: bool) -> Circuit:
    assert _gate.gate_type == gate.INPUT
    inputs_to_true, inputs_to_false = [], []
    (inputs_to_true if value else inputs_to_false).append(_gate.label)
    return ckt.replace_inputs(inputs_to_true, inputs_to_false)


def _replace_gate_to_const(ckt: Circuit, _gate: gate.Gate, value: bool) -> None:
    label = _gate.label

    # delete users
    for operand in _gate.operands:
        ckt._remove_user(gate_label=operand, user=label)

    # replace gate
    new_gate_type = gate.ALWAYS_TRUE if value else gate.ALWAYS_FALSE
    new_gate = gate.Gate(label=label, gate_type=new_gate_type, operands=())
    ckt._gates[label] = new_gate


def _replace_gate_in_users(
    ckt: Circuit,
    old_label: str,
    new_label: str,
) -> None:
    for user_label in list(dict.fromkeys(ckt.get_gate_users(old_label))):
        user_gate = ckt.get_gate(user_label)
        new_operands = []
        replaced = False
        for operand in user_gate.operands:
            if operand == old_label:
                ckt._remove_user(old_label, user_label)
                ckt._add_user(new_label, user_label)
                new_operands.append(new_label)
                replaced = True
            else:
                new_operands.append(operand)
        if replaced:
            ckt._gates[user_label] = gate.Gate(
                label=user_gate.label,
                gate_type=user_gate.gate_type,
                operands=tuple(new_operands),
            )


def _assign_not_gate(ckt: Circuit, _gate: gate.Gate, value: bool) -> tuple[GateAssignmentResult, Circuit]:
    assert _gate.gate_type == gate.NOT
    assert len(_gate.operands) == 1
    _replace_gate_to_const(ckt, _gate, value)
    return _assign_gate(ckt, _gate.operands[0], not value)


def _assign_iff_gate(ckt: Circuit, _gate: gate.Gate, value: bool) -> tuple[GateAssignmentResult, Circuit]:
    assert _gate.gate_type == gate.IFF
    assert len(_gate.operands) == 1
    _replace_gate_to_const(ckt, _gate, value)
    return _assign_gate(ckt, _gate.operands[0], value)


def _assign_and_gate(ckt: Circuit, _gate: gate.Gate, value: bool) -> tuple[GateAssignmentResult, Circuit]:
    assert _gate.gate_type == gate.AND
    assert len(_gate.operands) == 2

    if value:
        _replace_gate_to_const(ckt, _gate, True)
        for operand in _gate.operands:
            assignment_res, ckt = _assign_gate(ckt, operand, True)
            if assignment_res != GateAssignmentResult.OK:
                return assignment_res, ckt
            ckt.mark_as_output(operand)
        return GateAssignmentResult.OK, ckt
    else:
        user_labels = ckt.get_gate_users(_gate.label)
        if user_labels:
            false_label = f"false_{_gate.label}_{uuid.uuid4().hex[:12]}"
            ckt.emplace_gate(false_label, gate.ALWAYS_FALSE)
            _replace_gate_in_users(ckt, _gate.label, false_label)

        # No replacement to const, just add a constraint that this gate is always false
        label = f"not_{_gate.label}_{uuid.uuid4().hex[:12]}"
        ckt.emplace_gate(label, gate.NOT, (_gate.label,))
        ckt.mark_as_output(label)
        return GateAssignmentResult.OK, ckt


def _fast_gate_score(ckt: Circuit, _gate: gate.Gate) -> int:
    indegree = len(_gate.operands)
    outdegree = 0
    for user_label in ckt.get_gate_users(_gate.label):
        user_gate = ckt.get_gate(user_label)
        match user_gate.gate_type:
            case gate.NOT | gate.IFF:
                outdegree += len(ckt.get_gate_users(user_label))
            case gate.AND:
                outdegree += 1
            case _:
                raise Exception(f"_fast_gate_score: Not supported case: {user_gate.gate_type}")

    score = (indegree + 1) * (outdegree + 1)
    return score


@dataclass
class GateScoreResult:
    class Status(enum.Enum):
        FORCED_VALUE = enum.auto()
        CONFLICT = enum.auto()
        SCORED = enum.auto()

    status: Status
    forced_value: tp.Optional[bool] = None
    score: tp.Optional[int] = None

    @classmethod
    def from_score(cls, score: int) -> "GateScoreResult":
        return GateScoreResult(
            status=cls.Status.SCORED,
            score=score
        )

    @classmethod
    def from_forced(cls, value: bool) -> "GateScoreResult":
        return GateScoreResult(
            status=cls.Status.FORCED_VALUE,
            forced_value=value
        )

    @classmethod
    def from_conflict(cls) -> "GateScoreResult":
        return GateScoreResult(status=cls.Status.CONFLICT)


def _count_and_gates(ckt: Circuit) -> int:
    return sum(map(lambda g: g.gate_type == gate.AND, ckt.gates.values()))


def _slow_gate_score(ckt: Circuit, _gate: gate.Gate) -> GateScoreResult:
    ckt_0 = copy.deepcopy(ckt)
    res_0, ckt_0 = _assign_gate(ckt_0, _gate.label, value=False)
    ckt_0 = _simplify_light(ckt_0)

    ckt_1 = copy.deepcopy(ckt)
    res_1, ckt_1 = _assign_gate(ckt_1, _gate.label, value=True)
    ckt_1 = _simplify_light(ckt_1)

    match (res_0, res_1):
        case (GateAssignmentResult.CONFLICT, GateAssignmentResult.CONFLICT):
            return GateScoreResult.from_conflict()
        case (GateAssignmentResult.CONFLICT, GateAssignmentResult.OK):
            return GateScoreResult.from_forced(value=True)
        case (GateAssignmentResult.OK, GateAssignmentResult.CONFLICT):
            return GateScoreResult.from_forced(value=False)
        case (GateAssignmentResult.OK, GateAssignmentResult.OK):
            size_orig = _count_and_gates(ckt)
            size_0 = _count_and_gates(ckt_0)
            size_1 = _count_and_gates(ckt_1)
            diff_0 = size_orig - size_0
            diff_1 = size_orig - size_1
            assert diff_0 >= 0
            assert diff_1 >= 0
            score = (diff_0 + 1) * (diff_1 + 1)
            return GateScoreResult.from_score(score=score)
        case _:
            raise Exception("This line is unreachable")
