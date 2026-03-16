"""Tests for CubeAndConquerSolver using AIG test instances.

Test instances originate from Circuit-SAT-solver subproject (bench format),
preprocessed to AIG via ABC (``strash``).  Expected results (SAT / UNSAT) are
hardcoded from the CNFReductionSolver benchmark report.

Tests are split along two axes:
- SAT vs UNSAT (by expected answer)
- Light vs Heavy (reference solve time threshold = 10 s)

Heavy tests are marked with ``@pytest.mark.heavy`` so they can be skipped::

    poetry run pytest -m "not heavy"
"""

import pathlib

import pytest

from cirbo.core.circuit import Circuit
from cirbo.sat.solver.cnc_solver import CubeAndConquerSolver

AIG_DIR = pathlib.Path(__file__).resolve().parents[4] / "data" / "sat" / "aig_test"

# ---------------------------------------------------------------------------
# Instance classification (from CNFReductionSolver benchmark report).
# Heavy threshold: reference solve time >= 10 s.
# Unknown (timeout) instances are excluded.
# ---------------------------------------------------------------------------

SAT_LIGHT = [
    "100_50.aig",             # 0.22s
    "96_4_sat.aig",           # 0.01s
    "miter_6.aig",            # 0.00s
    "miter_16.aig",           # 0.00s
    "miter_26.aig",           # 0.00s
    "miter_46.aig",           # 0.00s
    "miter_188.aig",          # 0.00s
]

SAT_HEAVY = [
    "MOD3_49_sat.aig",        # 7.33s
    "hamming10-2_sat.aig",    # 1.14s
    "3300_4.aig",             # 3.75s
    "4300_4.aig",             # 5.65s
    "6700_4.aig",             # 8.65s
    "9900_4.aig",                  # 16.81s
    "MOD3_1_hard_sat.aig",        # 119.09s
    "MOD3_77_sat.aig",            # 23.79s
    "MOD3_low_density_1_sat.aig", # 122.85s
    "p_hat300-2_sat.aig",         # 63.92s
]

UNSAT_LIGHT = [
    "5_6.aig",                          # 0.00s
    "16_4.aig",                         # 0.00s
    "72_4.aig",                         # 0.02s
    "BvP_4_3-aigmiter.aig",             # 0.15s
    "BvP_4_4-aigmiter.aig",             # 0.33s
    "BvS_3_3-aigmiter.aig",             # 0.02s
    "logVn_2.aig",                      # 0.00s
    "logVn_4.aig",                      # 0.01s
    "logVn_6.aig",                      # 0.27s
    "miter_3.aig",                      # 0.00s
    "miter_8.aig",                      # 0.00s
    "miter_33.aig",                     # 0.00s
    "miter_68.aig",                     # 0.00s
    "miter_85.aig",                     # 0.13s
    "miter_91.aig",                     # 0.08s
    "miter_123.aig",                    # 0.21s
    "miter_129.aig",                    # 0.14s
    "miter_174.aig",                    # 0.16s
    "miter_197.aig",                    # 0.07s
    "miter_identity_php_3_4.aig",       # 0.00s
    "miter_identity_php_6_19_3.aig",    # 0.58s
    "miter_identity_php_11_23_2.aig",   # 0.61s
    "miter_identity_php_12_13_1.aig",   # 0.17s
    "PvS_4_3-aigmiter.aig",            # 0.36s
    "thr2_500.aig",                     # 0.38s
    "trVlog_2.aig",                     # 0.00s
    "trVlog_4.aig",                     # 0.01s
    "trVlog_6.aig",                     # 0.48s
    "trVn_2.aig",                       # 0.00s
    "trVn_4.aig",                       # 0.01s
    "trVn_6.aig",                       # 0.25s
]

UNSAT_HEAVY = [
    "thr2_2000.aig",  # 6.11s
    "miter_identity_php_8_9.aig",       # 4.46s
    "miter_identity_php_10_31_3.aig",   # 0.99s
    "miter_identity_php_13_14_1.aig",   # 3.30s
    "miter_identity_php_14_15_1.aig",   # 2.29s
    "miter_identity_php_23_24_1.aig",   # 0.63s
    "miter_identity_php_24_25_1.aig",   # 3.83s
    "paley_13.aig",                     # 9.01s
    "trVn_8.aig",                       # 8.85s
    "reg_11_6.aig",                     # 4.44s
    "simple_reg_240_6.aig",             # 5.89s
    "BvP_7_4-aigmiter.aig",  # 128.57s
    "BvS_6_4-aigmiter.aig",  # 12.76s
    "logVn_8.aig",            # 15.17s
    "MOD3_54.aig",            # 179.51s
    "MOD3_NW_4.aig",          # 168.10s
    "thr2_4000.aig",          # 31.03s
    "thr2_5000.aig",          # 38.59s
    "thr2_6000.aig",          # 32.05s
    "thr2_8000.aig",          # 46.77s
    "thr2_10000.aig",         # 43.38s
    "trVlog_8.aig",           # 18.00s
]


def _load_aig_circuit(filename: str) -> Circuit:
    """Load an AIG file pre-converted by ABC."""
    return Circuit.from_aig_file(str(AIG_DIR / filename))


def _make_solver() -> CubeAndConquerSolver:
    return CubeAndConquerSolver(
        config=CubeAndConquerSolver.Config()
    )


# =============================================================================
# SAT Light Tests
# =============================================================================


class TestCnCSolverBenchSATLight:
    """SAT instances that solve quickly (< 10 s reference time)."""

    @pytest.mark.parametrize("aig_file", SAT_LIGHT, ids=SAT_LIGHT)
    def test_sat(self, aig_file: str):
        circuit = _load_aig_circuit(aig_file)
        result = _make_solver().solve(circuit)

        assert result.answer is True, f"{aig_file} expected SAT but got UNSAT"
        assert result.model is not None


# =============================================================================
# SAT Heavy Tests
# =============================================================================


class TestCnCSolverBenchSATHeavy:
    """SAT instances that take longer to solve (>= 10 s reference time)."""

    @pytest.mark.heavy
    @pytest.mark.parametrize("aig_file", SAT_HEAVY, ids=SAT_HEAVY)
    def test_sat(self, aig_file: str):
        circuit = _load_aig_circuit(aig_file)
        result = _make_solver().solve(circuit)

        assert result.answer is True, f"{aig_file} expected SAT but got UNSAT"
        assert result.model is not None


# =============================================================================
# UNSAT Light Tests
# =============================================================================


class TestCnCSolverBenchUNSATLight:
    """UNSAT instances that solve quickly (< 10 s reference time)."""

    @pytest.mark.parametrize("aig_file", UNSAT_LIGHT, ids=UNSAT_LIGHT)
    def test_unsat(self, aig_file: str):
        circuit = _load_aig_circuit(aig_file)
        result = _make_solver().solve(circuit)

        assert result.answer is False, f"{aig_file} expected UNSAT but got SAT"
        assert result.model is None


# =============================================================================
# UNSAT Heavy Tests
# =============================================================================


class TestCnCSolverBenchUNSATHeavy:
    """UNSAT instances that take longer to solve (>= 10 s reference time)."""

    @pytest.mark.heavy
    @pytest.mark.parametrize("aig_file", UNSAT_HEAVY, ids=UNSAT_HEAVY)
    def test_unsat(self, aig_file: str):
        circuit = _load_aig_circuit(aig_file)
        result = _make_solver().solve(circuit)

        assert result.answer is False, f"{aig_file} expected UNSAT but got SAT"
        assert result.model is None
