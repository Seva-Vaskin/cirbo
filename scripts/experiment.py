"""
Experiment script for comparing baseline SAT solver vs CubeAndConquerSolver
on miter circuits.

Takes miter circuit files and compares solvers performance.
Supports .bench, .aig, and .aag formats.

Usage:
    python experiment.py -i miter1.bench -o report.md
    python experiment.py -i miter1.bench -i miter2.aig -o report.md --timeout 60
    python experiment.py -i miter1.bench -o report.md -d 1,2,5 -c 3,5,10
"""

import argparse
import copy
import itertools
import logging
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from cirbo.core import Circuit
from cirbo.core.circuit import Transformer
from cirbo.minimization import RemoveRedundantGates, MergeUnaryOperators
from cirbo.minimization.simplification import RemoveConstantGates, MergeDuplicateGates
from cirbo.sat import PySATSolverNames, is_circuit_satisfiable
from cirbo.sat.solver.cnc_solver import CubeAndConquerSolver


class SolverTimeout(Exception):
    pass


def timeout_handler(signum, frame):
    raise SolverTimeout("Solver timed out")


@dataclass
class ExperimentResult:
    miter_name: str
    baseline_result: bool | None
    baseline_time: float | None
    baseline_timed_out: bool
    cnc_result: bool | None
    cnc_cube_time: float | None
    cnc_conquer_time: float | None
    cnc_total_time: float | None
    cnc_cubes: int | None
    cnc_timed_out: bool
    max_depth: int
    scoring_candidates: int
    solver_name: str
    match: bool | None
    conquer_faster: bool | None


def load_circuit(file_path: Path) -> Circuit:
    suffix = file_path.suffix.lower()
    if suffix == ".bench":
        return Circuit.from_bench_file(str(file_path))
    elif suffix in (".aig", ".aag"):
        return Circuit.from_aig_file(str(file_path))
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def run_baseline(
    miter: Circuit,
    solver_name: PySATSolverNames,
    timeout: int | None = None,
) -> tuple[bool | None, float | None, bool]:
    if timeout is not None:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
    try:
        t0 = time.time()
        result = is_circuit_satisfiable(miter, solver_name=solver_name)
        elapsed = time.time() - t0
        return result.answer, elapsed, False
    except SolverTimeout:
        return None, None, True
    finally:
        if timeout is not None:
            signal.alarm(0)


def run_cnc(
    miter: Circuit,
    max_depth: int,
    scoring_candidates: int,
    solver_name: PySATSolverNames,
    timeout: int | None = None,
) -> tuple[bool | None, float | None, float | None, float | None, int | None, bool]:
    if timeout is not None:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
    try:
        miter_copy = copy.deepcopy(miter)
        solver = CubeAndConquerSolver(
            config=CubeAndConquerSolver.Config(
                max_depth=max_depth,
                scoring_candidates=scoring_candidates,
                sat_solver=solver_name,
            )
        )

        t0 = time.time()
        cubes = solver.cube(miter_copy)
        t1 = time.time()
        result = solver.conquer(cubes)
        t2 = time.time()

        return result.answer, t1 - t0, t2 - t1, t2 - t0, len(cubes), False
    except SolverTimeout:
        return None, None, None, None, None, True
    except Exception as e:
        import traceback
        print(f"    ERROR: CnC crashed: {e}")
        traceback.print_exc()
        return None, None, None, None, None, True
    finally:
        if timeout is not None:
            signal.alarm(0)


def generate_report(results: list[ExperimentResult], output_path: str) -> None:
    with open(output_path, "w") as f:
        f.write("# CnC Solver Experiment Report\n\n")

        total = len(results)
        baseline_timeouts = sum(1 for r in results if r.baseline_timed_out)
        cnc_timeouts = sum(1 for r in results if r.cnc_timed_out)
        completed = [r for r in results if not r.baseline_timed_out and not r.cnc_timed_out]
        matches = sum(1 for r in completed if r.match)
        conquer_faster_count = sum(1 for r in completed if r.conquer_faster)

        f.write("## Summary\n\n")
        f.write(f"- **Total runs:** {total}\n")
        f.write(f"- **Baseline timeouts:** {baseline_timeouts}\n")
        f.write(f"- **CnC timeouts:** {cnc_timeouts}\n")
        if completed:
            f.write(f"- **Results matching:** {matches}/{len(completed)}\n")
            f.write(f"- **Conquer faster than baseline:** {conquer_faster_count}/{len(completed)} ({100*conquer_faster_count/len(completed):.1f}%)\n\n")

        if completed and matches != len(completed):
            f.write("**WARNING: Some results do not match!**\n\n")

        f.write("## Detailed Results\n\n")
        f.write("| Miter | depth | candidates | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |\n")
        f.write("|-------|-------|------------|----------|-------------|---------|------|-------|-------|-------|\n")

        for r in results:
            if r.baseline_timed_out:
                baseline_str = "TIMEOUT"
            else:
                baseline_str = f"{r.baseline_time:.4f}"

            if r.cnc_timed_out:
                cnc_str = "TIMEOUT"
                cube_str = total_str = cubes_str = "-"
            else:
                cnc_str = f"**{r.cnc_conquer_time:.4f}**"
                cube_str = f"{r.cnc_cube_time:.4f}"
                total_str = f"{r.cnc_total_time:.4f}"
                cubes_str = str(r.cnc_cubes)

            if r.baseline_timed_out or r.cnc_timed_out:
                faster_mark = match_mark = "-"
            else:
                faster_mark = "**Y**" if r.conquer_faster else ""
                match_mark = "Y" if r.match else "**MISMATCH**"

            f.write(
                f"| {r.miter_name} | {r.max_depth} | {r.scoring_candidates} | "
                f"{baseline_str} | {cnc_str} | {faster_mark} | "
                f"{cube_str} | {total_str} | {cubes_str} | {match_mark} |\n"
            )

        if completed:
            f.write("\n## Speedup Analysis\n\n")
            conquer_speedups = [r.baseline_time / r.cnc_conquer_time if r.cnc_conquer_time > 0 else 0 for r in completed]
            total_speedups = [r.baseline_time / r.cnc_total_time if r.cnc_total_time > 0 else 0 for r in completed]
            f.write(f"- **Avg conquer speedup:** {sum(conquer_speedups)/len(conquer_speedups):.2f}x\n")
            f.write(f"- **Max conquer speedup:** {max(conquer_speedups):.2f}x\n")
            f.write(f"- **Avg total speedup:** {sum(total_speedups)/len(total_speedups):.2f}x\n")
            f.write(f"- **Max total speedup:** {max(total_speedups):.2f}x\n")


def run_single_miter_experiment(
    miter_path: Path,
    max_depths: list[int],
    scoring_candidates_list: list[int],
    solver_names: list[PySATSolverNames],
    timeout: int | None = None,
) -> list[ExperimentResult]:
    name = miter_path.name

    print(f"Loading {name}...")
    miter = load_circuit(miter_path)
    print(f"  Size: {miter.size} gates, {miter.input_size} inputs")
    miter = Transformer.apply_transformers(
        miter,
        [
            RemoveConstantGates(),
            MergeUnaryOperators(),
        ]
    )
    print(f"  After simplification: {miter.size} gates, {miter.input_size} inputs")

    results: list[ExperimentResult] = []

    for solver_name in solver_names:
        baseline_result, baseline_time, baseline_timed_out = run_baseline(miter, solver_name, timeout)

        if baseline_timed_out:
            print(f"  Baseline ({solver_name.value}): TIMEOUT")
        else:
            print(f"  Baseline ({solver_name.value}): {'SAT' if baseline_result else 'UNSAT'} in {baseline_time:.4f}s")

        for max_depth, scoring_cands in itertools.product(max_depths, scoring_candidates_list):
            cnc_result, cube_time, conquer_time, total_time, cnc_cubes, cnc_timed_out = run_cnc(
                miter, max_depth, scoring_cands, solver_name, timeout
            )

            if cnc_timed_out:
                print(f"    CnC (depth={max_depth}, cands={scoring_cands}): TIMEOUT")
                match = conquer_faster = None
            else:
                if baseline_timed_out:
                    match = conquer_faster = None
                else:
                    match = baseline_result == cnc_result
                    conquer_faster = conquer_time < baseline_time

                status = "Y" if match else ("MISMATCH!" if match is False else "?")
                faster = " (conquer faster)" if conquer_faster else ""
                print(f"    CnC (depth={max_depth}, cands={scoring_cands}): "
                      f"{'SAT' if cnc_result else 'UNSAT'} cube={cube_time:.4f}s conquer={conquer_time:.4f}s "
                      f"total={total_time:.4f}s, {cnc_cubes} cubes {status}{faster}")

            results.append(ExperimentResult(
                miter_name=name,
                baseline_result=baseline_result,
                baseline_time=baseline_time,
                baseline_timed_out=baseline_timed_out,
                cnc_result=cnc_result,
                cnc_cube_time=cube_time,
                cnc_conquer_time=conquer_time,
                cnc_total_time=total_time,
                cnc_cubes=cnc_cubes,
                cnc_timed_out=cnc_timed_out,
                max_depth=max_depth,
                scoring_candidates=scoring_cands,
                solver_name=solver_name.value,
                match=match,
                conquer_faster=conquer_faster,
            ))

            if match is False:
                print(f"    WARNING: Results do not match!")

    return results


def run_experiment(
    miters: list[str],
    output: str,
    max_depths: list[int],
    scoring_candidates_list: list[int],
    solver_names: list[PySATSolverNames],
    timeout: int | None = None,
) -> list[ExperimentResult]:
    validated_miters: list[Path] = []
    for miter_path in miters:
        path = Path(miter_path)
        if not path.exists():
            print(f"Error: Miter file not found: {path}")
            sys.exit(1)
        validated_miters.append(path)

    if timeout is not None:
        print(f"Per-solver timeout: {timeout} seconds")

    all_results: list[ExperimentResult] = []

    for i, path in enumerate(validated_miters):
        print(f"\n{'='*60}")
        print(f"Miter {i+1}/{len(validated_miters)}: {path.name}")
        print(f"{'='*60}")

        miter_results = run_single_miter_experiment(
            path, max_depths, scoring_candidates_list, solver_names, timeout
        )
        all_results.extend(miter_results)

    if all_results:
        generate_report(all_results, output)
        print(f"\nReport written to {output}")

        completed = [r for r in all_results if not r.baseline_timed_out and not r.cnc_timed_out]
        if completed:
            total_matches = sum(1 for r in completed if r.match)
            total_faster = sum(1 for r in completed if r.conquer_faster)
            print(f"Final: {total_matches}/{len(completed)} matches, "
                  f"{total_faster}/{len(completed)} conquer faster than baseline")

    return all_results


def main():
    parser = argparse.ArgumentParser(
        description="Compare baseline SAT vs CubeAndConquerSolver on miter circuits"
    )
    parser.add_argument(
        "--input", "-i", type=str, action="append", metavar="MITER", required=True,
        help="Miter circuit file (.bench, .aig, .aag). Can be specified multiple times."
    )
    parser.add_argument(
        "--output", "-o", type=str, required=True,
        help="Output report path (e.g. report.md)"
    )
    parser.add_argument(
        "--timeout", "-t", type=int, default=None,
        help="Timeout in seconds per solver call (default: no timeout)"
    )
    parser.add_argument(
        "--depths", "-d", type=str, default="2",
        help="Comma-separated max depths. Example: '1,2,3' (default: 2)"
    )
    parser.add_argument(
        "--candidates", "-c", type=str, default="5",
        help="Comma-separated scoring candidates counts. Example: '3,5,10' (default: 5)"
    )
    parser.add_argument(
        "--log-level", default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )

    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper()), format="%(levelname)s: %(message)s")

    max_depths = [int(d.strip()) for d in args.depths.split(",")]
    scoring_candidates_list = [int(c.strip()) for c in args.candidates.split(",")]

    solver_names = [PySATSolverNames.CADICAL195]

    print(f"Running {len(args.input)} miter(s):")
    for i, m in enumerate(args.input):
        print(f"  {i+1}. {m}")
    print(f"Depths: {max_depths}")
    print(f"Scoring candidates: {scoring_candidates_list}")

    run_experiment(
        miters=args.input,
        output=args.output,
        max_depths=max_depths,
        scoring_candidates_list=scoring_candidates_list,
        solver_names=solver_names,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    main()
