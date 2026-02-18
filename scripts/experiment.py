"""
Experiment script for comparing baseline SAT solver vs CubeAndConquerSolver
on miter circuits.

Takes miter circuit files and compares solvers performance.
Supports .bench, .aig, and .aag formats.

Usage:
    python experiment.py -i miter1.bench -o report.md
    python experiment.py -i miter1.bench -i miter2.aig -o report.md --timeout 60
    python experiment.py -i miter1.bench -o report.md -d 1,2,5,None -m 100,500,None
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
from cirbo.sat.solver.cnc_solver_old import CubeAndConquerSolver


class SolverTimeout(Exception):
    """Raised when a solver times out."""
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
    max_depth: int | None
    min_circuit_size: int | None
    candidates_limit: int | None
    hard_threshold: float | None
    soft_threshold: float | None
    soft_threshold_limit: int | None
    solver_name: str
    match: bool | None
    conquer_faster: bool | None


def load_circuit(file_path: Path) -> Circuit:
    """Load a circuit from a file, auto-detecting format based on extension."""
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
    """
    Run baseline SAT solver and return (result, time, timed_out).
    If timed out, result and time are None.
    """
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
    max_depth: int | None,
    min_circuit_size: int | None,
    candidates_limit: int | None,
    hard_threshold: float | None,
    soft_threshold: float | None,
    soft_threshold_limit: int | None,
    solver_name: PySATSolverNames,
    timeout: int | None = None,
) -> tuple[bool | None, float | None, float | None, float | None, int | None, bool]:
    """
    Run CubeAndConquerSolver and return (result, cube_time, conquer_time, total_time, num_cubes, timed_out).
    If timed out, all values except timed_out are None.
    """
    if timeout is not None:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
    
    try:
        miter_copy = copy.deepcopy(miter)
        solver = CubeAndConquerSolver(
            max_depth=max_depth,
            min_circuit_size=min_circuit_size,
            solver_name=solver_name,
            candidates_limit=candidates_limit,
            hard_threshold=hard_threshold,
            soft_threshold=soft_threshold,
            soft_threshold_limit=soft_threshold_limit,
        )
        
        t0 = time.time()
        cubes = solver.cube(miter_copy)
        t1 = time.time()
        result = solver.conquer(cubes)
        t2 = time.time()
        
        cube_time = t1 - t0
        conquer_time = t2 - t1
        total_time = t2 - t0
        
        return result.answer, cube_time, conquer_time, total_time, len(cubes), False
    except SolverTimeout:
        return None, None, None, None, None, True
    finally:
        if timeout is not None:
            signal.alarm(0)


def generate_report(results: list[ExperimentResult], output_path: str) -> None:
    """Generate markdown report from experiment results."""
    with open(output_path, "w") as f:
        f.write("# Miter Verification Experiment Report\n\n")
        
        # Summary statistics
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
            f.write("⚠️ **WARNING: Some results do not match!**\n\n")
        
        # Detailed results table
        f.write("## Detailed Results\n\n")
        f.write("| Miter | depth | min_size | candidates | hard_th | soft_th | soft_lim | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |\n")
        f.write("|-------|-------|----------|------------|---------|---------|----------|----------|-------------|---------|------|-------|-------|-------|\n")
        
        for r in results:
            depth_str = str(r.max_depth) if r.max_depth is not None else "None"
            min_size_str = str(r.min_circuit_size) if r.min_circuit_size is not None else "None"
            candidates_str = str(r.candidates_limit) if r.candidates_limit is not None else "None"
            hard_th_str = str(r.hard_threshold) if r.hard_threshold is not None else "None"
            soft_th_str = str(r.soft_threshold) if r.soft_threshold is not None else "None"
            soft_lim_str = str(r.soft_threshold_limit) if r.soft_threshold_limit is not None else "None"
            
            # Format baseline
            if r.baseline_timed_out:
                baseline_str = "TIMEOUT"
            else:
                baseline_str = f"{r.baseline_time:.4f}"
            
            # Format CnC
            if r.cnc_timed_out:
                cnc_str = "TIMEOUT"
                cube_str = "-"
                total_str = "-"
                cubes_str = "-"
            else:
                cnc_str = f"**{r.cnc_conquer_time:.4f}**"
                cube_str = f"{r.cnc_cube_time:.4f}"
                total_str = f"{r.cnc_total_time:.4f}"
                cubes_str = str(r.cnc_cubes)
            
            # Format comparison columns
            if r.baseline_timed_out or r.cnc_timed_out:
                faster_mark = "-"
                match_mark = "-"
            else:
                faster_mark = "**✓**" if r.conquer_faster else ""
                match_mark = "✓" if r.match else "❌"
            
            f.write(
                f"| {r.miter_name} | {depth_str} | {min_size_str} | {candidates_str} | {hard_th_str} | {soft_th_str} | {soft_lim_str} | "
                f"{baseline_str} | {cnc_str} | {faster_mark} | "
                f"{cube_str} | {total_str} | {cubes_str} | {match_mark} |\n"
            )
        
        # Speedup analysis
        if completed:
            f.write("\n## Speedup Analysis\n\n")
            conquer_speedups = [r.baseline_time / r.cnc_conquer_time if r.cnc_conquer_time > 0 else 0 for r in completed]
            avg_conquer_speedup = sum(conquer_speedups) / len(conquer_speedups)
            max_conquer_speedup = max(conquer_speedups)
            
            total_speedups = [r.baseline_time / r.cnc_total_time if r.cnc_total_time > 0 else 0 for r in completed]
            avg_total_speedup = sum(total_speedups) / len(total_speedups)
            max_total_speedup = max(total_speedups)
            
            f.write(f"- **Average conquer speedup (baseline/conquer):** {avg_conquer_speedup:.2f}x\n")
            f.write(f"- **Max conquer speedup:** {max_conquer_speedup:.2f}x\n")
            f.write(f"- **Average total speedup (baseline/total):** {avg_total_speedup:.2f}x\n")
            f.write(f"- **Max total speedup:** {max_total_speedup:.2f}x\n")


def run_single_miter_experiment(
    miter_path: Path,
    max_depths: list[int | None],
    min_circuit_sizes: list[int | None],
    candidates_limits: list[int | None],
    thresholds: list[tuple[float | None, float | None]],
    soft_threshold_limits: list[int | None],
    solver_names: list[PySATSolverNames],
    timeout: int | None = None,
) -> list[ExperimentResult]:
    """Run experiment for a single miter circuit. Returns results list."""
    name = miter_path.name
    
    print(f"Loading {name}...")
    miter = load_circuit(miter_path)
    print(f"Miter size: {miter.size} gates, {miter.input_size} inputs")
    miter = Transformer.apply_transformers(
        miter,
        [
            RemoveConstantGates(),
            # RemoveRedundantGates(),
            MergeUnaryOperators(),
            # MergeDuplicateGates(),
        ]
    )
    print(f"Miter size: {miter.size} gates, {miter.input_size} inputs (after trivial simplification)")

    results: list[ExperimentResult] = []
    
    for solver_name in solver_names:
        # Run baseline with timeout
        baseline_result, baseline_time, baseline_timed_out = run_baseline(miter, solver_name, timeout)
        
        if baseline_timed_out:
            print(f"Baseline ({solver_name.value}): TIMEOUT")
        else:
            print(f"Baseline ({solver_name.value}): {'SAT' if baseline_result else 'UNSAT'} in {baseline_time:.4f}s")

        param_combinations = itertools.product(
            max_depths, min_circuit_sizes, candidates_limits, thresholds, soft_threshold_limits
        )
        for max_depth, min_circuit_size, candidates_limit, (hard_threshold, soft_threshold), soft_threshold_limit in param_combinations:
            # Run CnC with timeout
            cnc_result, cube_time, conquer_time, total_time, cnc_cubes, cnc_timed_out = run_cnc(
                miter, max_depth, min_circuit_size, candidates_limit, hard_threshold, soft_threshold, soft_threshold_limit, solver_name, timeout
            )
            
            depth_str = str(max_depth) if max_depth is not None else "None"
            min_size_str = str(min_circuit_size) if min_circuit_size is not None else "None"
            candidates_str = str(candidates_limit) if candidates_limit is not None else "None"
            hard_th_str = str(hard_threshold) if hard_threshold is not None else "None"
            soft_th_str = str(soft_threshold) if soft_threshold is not None else "None"
            soft_lim_str = str(soft_threshold_limit) if soft_threshold_limit is not None else "None"
            
            if cnc_timed_out:
                print(f"  CnC (depth={depth_str}, min_size={min_size_str}, cand={candidates_str}, hard={hard_th_str}, soft={soft_th_str}, lim={soft_lim_str}): TIMEOUT")
                match = None
                conquer_faster = None
            else:
                if baseline_timed_out:
                    match = None
                    conquer_faster = None
                else:
                    match = baseline_result == cnc_result
                    conquer_faster = conquer_time < baseline_time
                
                status = "✓" if match else ("MISMATCH!" if match is False else "?")
                faster = " (conquer faster)" if conquer_faster else ""
                print(f"  CnC (depth={depth_str}, min_size={min_size_str}, cand={candidates_str}, hard={hard_th_str}, soft={soft_th_str}, lim={soft_lim_str}): {'SAT' if cnc_result else 'UNSAT'} cube={cube_time:.4f}s conquer={conquer_time:.4f}s total={total_time:.4f}s, {cnc_cubes} cubes {status}{faster}")

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
                min_circuit_size=min_circuit_size,
                candidates_limit=candidates_limit,
                hard_threshold=hard_threshold,
                soft_threshold=soft_threshold,
                soft_threshold_limit=soft_threshold_limit,
                solver_name=solver_name.value,
                match=match,
                conquer_faster=conquer_faster,
            ))

            if match is False:
                print(f"  ⚠️ WARNING: Results do not match!")
    
    return results


def run_experiment(
    miters: list[str],
    output: str,
    max_depths: list[int | None],
    min_circuit_sizes: list[int | None],
    candidates_limits: list[int | None],
    thresholds: list[tuple[float | None, float | None]],
    soft_threshold_limits: list[int | None],
    solver_names: list[PySATSolverNames],
    timeout: int | None = None,
) -> list[ExperimentResult]:
    """Run experiments for all miter circuits."""
    
    # Validate all paths first
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
        
        miter_results = run_single_miter_experiment(path, max_depths, min_circuit_sizes, candidates_limits, thresholds, soft_threshold_limits, solver_names, timeout)
        all_results.extend(miter_results)
    
    # Generate report
    if all_results:
        generate_report(all_results, output)
        print(f"\nReport written to {output}")
        
        completed = [r for r in all_results if not r.baseline_timed_out and not r.cnc_timed_out]
        if completed:
            total_matches = sum(1 for r in completed if r.match)
            total_faster = sum(1 for r in completed if r.conquer_faster)
            print(f"Final: {total_matches}/{len(completed)} matches, {total_faster}/{len(completed)} conquer faster than baseline")
    
    return all_results


def main():
    parser = argparse.ArgumentParser(
        description="Compare baseline SAT vs CubeAndConquerSolver on miter verification"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        action="append",
        metavar="MITER",
        required=True,
        help="A miter circuit file to check (.bench, .aig, or .aag). Can be specified multiple times."
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Output report path (example: experiment_report.md)"
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=None,
        help="Timeout in seconds per solver call (default: no timeout)"
    )
    parser.add_argument(
        "--depths", "-d", "--depth",
        type=str,
        default=None,
        help="Comma-separated list of max depths to test (use 'None' for unlimited). Example: '1,2,5' (default: None)"
    )
    parser.add_argument(
        "--min-sizes", "-m",
        type=str,
        default="1",
        help="Comma-separated list of min circuit sizes to test (use 'None' for no limit). Example: '100,500' (default: 1)"
    )

    parser.add_argument(
        "--candidates", "-c",
        type=str,
        default=None,
        help="Comma-separated list of candidate limits to test (use 'None' for all). Example: '10,50' (default: None)"
    )

    parser.add_argument(
        "--thresholds", "-th",
        type=str,
        default=None,
        help="Comma-separated list of hard:soft threshold pairs. hard filters out candidates, soft increments counter. Use 'None' for no threshold. Example: '10:30,20:40,None:None' (default: None:None)"
    )

    parser.add_argument(
        "--soft-threshold-limits", "-sl",
        type=str,
        default=None,
        help="Comma-separated list of soft threshold limits (use 'None' for no limit). Stop recursion after this many soft threshold violations. Example: '3,5' (default: None)"
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )

    args = parser.parse_args()

    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")
    
    # Parse depths
    max_depths: list[int | None] = []
    if args.depths is None:
        max_depths.append(None)
    else:
        for d in args.depths.split(","):
            d = d.strip()
            if d.lower() == "none":
                max_depths.append(None)
            else:
                max_depths.append(int(d))
    
    # Parse min circuit sizes
    min_circuit_sizes: list[int | None] = []
    for s in args.min_sizes.split(","):
        s = s.strip()
        if s.lower() == "none":
            min_circuit_sizes.append(None)
        else:
            min_circuit_sizes.append(int(s))
            
    # Parse candidates limits
    candidates_limits: list[int | None] = []
    if args.candidates is None:
        candidates_limits.append(None)
    else:
        for c in args.candidates.split(","):
            c = c.strip()
            if c.lower() == "none":
                candidates_limits.append(None)
            else:
                candidates_limits.append(int(c))
    
    # Parse thresholds (hard:soft pairs)
    thresholds: list[tuple[float | None, float | None]] = []
    if args.thresholds is None:
        thresholds.append((None, None))
    else:
        for pair in args.thresholds.split(","):
            pair = pair.strip()
            parts = pair.split(":")
            if len(parts) != 2:
                print(f"Error: Invalid threshold pair format '{pair}'. Expected 'hard:soft'.")
                sys.exit(1)
            hard_str, soft_str = parts[0].strip(), parts[1].strip()
            hard_val = None if hard_str.lower() == "none" else float(hard_str)
            soft_val = None if soft_str.lower() == "none" else float(soft_str)
            thresholds.append((hard_val, soft_val))
    
    # Parse soft threshold limits
    soft_threshold_limits: list[int | None] = []
    if args.soft_threshold_limits is None:
        soft_threshold_limits.append(None)
    else:
        for t in args.soft_threshold_limits.split(","):
            t = t.strip()
            if t.lower() == "none":
                soft_threshold_limits.append(None)
            else:
                soft_threshold_limits.append(int(t))
    
    # Get input miters list
    miters = args.input
    
    print(f"Running {len(miters)} miter(s):")
    for i, m in enumerate(miters):
        print(f"  {i+1}. {m}")
    print(f"Depths: {max_depths}")
    print(f"Min circuit sizes: {min_circuit_sizes}")
    print(f"Candidates limits: {candidates_limits}")
    print(f"Thresholds (hard:soft): {thresholds}")
    print(f"Soft threshold limits: {soft_threshold_limits}")
    
    # Configuration
    solver_names = [
        PySATSolverNames.CADICAL195,
    ]
    
    run_experiment(
        miters=miters,
        output=args.output,
        max_depths=max_depths,
        min_circuit_sizes=min_circuit_sizes,
        candidates_limits=candidates_limits,
        thresholds=thresholds,
        soft_threshold_limits=soft_threshold_limits,
        solver_names=solver_names,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    main()
