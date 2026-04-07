import dataclasses
import enum
import logging
import subprocess
import tempfile
import typing as tp

import pysat.formula
import pysat.solvers

from cirbo.core.circuit import Circuit
from cirbo.sat.cnf import Cnf

logger = logging.getLogger(__name__)

__all__ = [
    'is_satisfiable',
    'is_circuit_satisfiable',
    'PySatResult',
    'PySATSolverNames',
    'ExternalSolver',
    'SolverSpec',
]


class PySATSolverNames(enum.Enum):
    """Enum version of pysat.solvers.SolverNames."""

    CADICAL103 = 'cadical103'
    CADICAL153 = 'cadical153'
    CADICAL195 = 'cadical195'
    CRYPTOSAT = 'crypto'
    GLUECARD3 = 'gluecard3'
    GLUECARD4 = 'gluecard4'
    GLUCOSE3 = 'glucose3'
    GLUCOSE4 = 'glucose4'
    GLUCOSE42 = 'glucose42'
    LINGELING = 'lingeling'
    MAPLECHRONO = 'maplechrono'
    MAPLECM = 'maplecm'
    MAPLESAT = 'maplesat'
    MERGESAT3 = 'mergesat3'
    MINICARD = 'minicard'
    MINISAT22 = 'minisat22'
    MINISATGH = 'minisat-gh'


@dataclasses.dataclass(frozen=True)
class ExternalSolver:
    """An external SAT solver executable following the SAT competition interface."""
    path: str


SolverSpec = tp.Union[PySATSolverNames, ExternalSolver, str]


@dataclasses.dataclass(frozen=True)
class PySatResult:
    """
    Class for is_satisfiable result.

    answer is bool, model shows var values, like [1, -2, 3, -4, ...].
    Model is None if answer is False.

    """

    answer: bool
    model: tp.Optional[list[int]]


def is_satisfiable(
    cnf: Cnf,
    *,
    solver_name: SolverSpec = PySATSolverNames.CADICAL195,
) -> PySatResult:
    """
    Checks if provided ``Cnf`` is satisfiable using specified solver.

    :param cnf: Cnf formula to be checked for satisfiability.
    :param solver_name: PySAT solver name/enum or an ``ExternalSolver`` instance.
    :return: PySatResult.

    """
    if isinstance(solver_name, ExternalSolver):
        return _run_external_solver(cnf, solver_name)

    solver_name = PySATSolverNames(solver_name)
    _pysat_cnf = pysat.formula.CNF(from_clauses=cnf.get_raw())
    with pysat.solvers.Solver(name=solver_name.value) as _solver:
        _solver.append_formula(_pysat_cnf)
        return PySatResult(_solver.solve(), _solver.get_model())


def _run_external_solver(cnf: Cnf, solver: ExternalSolver) -> PySatResult:
    dimacs = cnf.to_dimacs()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cnf', delete=False) as f:
        f.write(dimacs)
        tmp_path = f.name

    logger.info(f"Running external solver {solver.path} on {tmp_path}")
    proc = subprocess.run(
        [solver.path, tmp_path],
        capture_output=True,
        text=True,
    )

    answer: tp.Optional[bool] = None
    model: list[int] = []

    for line in proc.stdout.splitlines():
        if line.startswith("s SATISFIABLE"):
            answer = True
        elif line.startswith("s UNSATISFIABLE"):
            answer = False
        elif line.startswith("v "):
            model.extend(int(x) for x in line[2:].split() if x != "0")

    if answer is None:
        if proc.returncode == 10:
            answer = True
        elif proc.returncode == 20:
            answer = False
        else:
            raise RuntimeError(
                f"External solver {solver.path} returned unexpected exit code "
                f"{proc.returncode}.\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
            )

    return PySatResult(answer=answer, model=model if answer else None)


def is_circuit_satisfiable(
    circuit: Circuit,
    *,
    solver_name: SolverSpec = PySATSolverNames.CADICAL195,
) -> PySatResult:
    """
    Checks if circuit is satisfiable using specified solver. Uses Tseytin transformation
    to construct SAT instance based on the provided ``Circuit`` (Circuit SAT) instance.

    :param circuit: Circuit representing a Circuit SAT instance.
    :param solver_name: PySAT solver name/enum or an ``ExternalSolver`` instance.
    :return: PySatResult.

    """
    return is_satisfiable(
        cnf=Cnf.from_circuit(circuit),
        solver_name=solver_name,
    )
