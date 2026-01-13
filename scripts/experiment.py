"""
Experiment script for comparing baseline SAT solver vs CubeAndConquerSolver
on circuit verification.

Supports both multiplier circuits (.bench) and sorting circuits (.aig).
"""

import argparse
import copy
import itertools
import re
import time
from dataclasses import dataclass
from pathlib import Path

from cirbo.core import Circuit
from cirbo.sat import PySATSolverNames, build_miter, is_circuit_satisfiable
from cirbo.sat.solver.cnc_solver import CubeAndConquerSolver


@dataclass
class ExperimentResult:
    circuit1_name: str
    circuit2_name: str
    baseline_result: bool
    baseline_time: float
    cnc_result: bool
    cnc_cube_time: float
    cnc_conquer_time: float
    cnc_total_time: float
    cnc_cubes: int
    max_depth: int | None
    solver_name: str
    match: bool
    conquer_faster: bool  # True if conquer time (without cube) < baseline time


def load_circuit(file_path: Path) -> Circuit:
    """Load a circuit from a file, auto-detecting format based on extension."""
    suffix = file_path.suffix.lower()
    if suffix == ".bench":
        return Circuit.from_bench_file(str(file_path))
    elif suffix in (".aig", ".aag"):
        return Circuit.from_aig_file(str(file_path))
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def parse_multiplier_name(filename: str) -> tuple[str, str]:
    """
    Parse multiplier filename like 'mul_alter_4' or 'mul_pow2_m1_4'.
    Returns (algorithm_name, group_key).
    Group key is the size (e.g., '4').
    """
    # Match: mul_{algorithm}_{size} where algorithm can have underscores (e.g., pow2_m1)
    match = re.match(r"^(mul_.+)_(\d+)$", filename)
    if match:
        algorithm = match.group(1)
        size = match.group(2)
        return algorithm, size
    raise ValueError(f"Cannot parse multiplier filename: {filename}")


def parse_sort_name(filename: str) -> tuple[str, str]:
    """
    Parse sorting circuit filename like 'BubbleSort_7_4'.
    Returns (algorithm_name, group_key).
    Group key is 'N_K' (e.g., '7_4').
    """
    # Match: {Algorithm}_{N}_{K}
    match = re.match(r"^([A-Za-z]+)_(\d+)_(\d+)$", filename)
    if match:
        algorithm = match.group(1)
        n = match.group(2)
        k = match.group(3)
        return algorithm, f"{n}_{k}"
    raise ValueError(f"Cannot parse sort filename: {filename}")


def detect_circuit_type(directory: Path) -> str:
    """Detect the type of circuits in a directory based on file patterns."""
    bench_files = list(directory.glob("mul_*.bench"))
    aig_files = list(directory.glob("*Sort_*.aig"))
    
    if bench_files and not aig_files:
        return "multiplier"
    elif aig_files and not bench_files:
        return "sort"
    elif bench_files and aig_files:
        raise ValueError("Directory contains both multiplier and sort circuits. Please specify --type.")
    else:
        # Try to detect from any files present
        all_bench = list(directory.glob("*.bench"))
        all_aig = list(directory.glob("*.aig")) + list(directory.glob("*.aag"))
        if all_bench:
            return "multiplier"
        elif all_aig:
            return "sort"
        raise ValueError("No circuit files found in directory.")


def get_circuit_files(
    directory: Path,
    circuit_type: str,
    group_filter: str | None = None,
    prefixes: list[str] | None = None,
) -> dict[str, list[Path]]:
    """
    Get circuit files grouped by their parameters.
    
    Returns a dict mapping group_key -> list of file paths.
    For multipliers: group_key is the bit size (e.g., "4", "8")
    For sort circuits: group_key is "N_K" (e.g., "7_4")
    
    Args:
        directory: Path to the directory containing circuit files.
        circuit_type: "multiplier" or "sort".
        group_filter: If provided, only include groups matching this key.
        prefixes: If provided, only include circuits with these algorithm prefixes.
    """
    groups: dict[str, list[Path]] = {}
    
    if circuit_type == "multiplier":
        pattern = "*.bench"
        parser = parse_multiplier_name
    else:  # sort
        pattern = "*.aig"
        parser = parse_sort_name
    
    for file_path in sorted(directory.glob(pattern)):
        try:
            algorithm, group_key = parser(file_path.stem)
        except ValueError:
            continue  # Skip files that don't match expected pattern
        
        # Apply group filter
        if group_filter is not None and group_key != group_filter:
            continue
        
        # Apply prefix filter
        if prefixes is not None and algorithm not in prefixes:
            continue
        
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(file_path)
    
    return groups


def run_baseline(miter: Circuit, solver_name: PySATSolverNames) -> tuple[bool, float]:
    """Run baseline SAT solver and return (result, time)."""
    t0 = time.time()
    result = is_circuit_satisfiable(miter, solver_name=solver_name)
    elapsed = time.time() - t0
    return result.answer, elapsed


def run_cnc(
    miter: Circuit,
    max_depth: int | None,
    solver_name: PySATSolverNames,
) -> tuple[bool, float, float, float, int]:
    """Run CubeAndConquerSolver and return (result, cube_time, conquer_time, total_time, num_cubes)."""
    # Deep copy to prevent CnC from mutating the original circuit
    miter_copy = copy.deepcopy(miter)
    solver = CubeAndConquerSolver(max_depth=max_depth, solver_name=solver_name)
    
    t0 = time.time()
    cubes = solver.cube(miter_copy)
    t1 = time.time()
    result = solver.conquer(cubes)
    t2 = time.time()
    
    cube_time = t1 - t0
    conquer_time = t2 - t1
    total_time = t2 - t0
    
    return result.answer, cube_time, conquer_time, total_time, len(cubes)


def generate_report(results: list[ExperimentResult], output_path: str, circuit_type: str) -> None:
    """Generate markdown report from experiment results."""
    with open(output_path, "w") as f:
        title = "Multiplier" if circuit_type == "multiplier" else "Sorting Circuit"
        f.write(f"# {title} Verification Experiment Report\n\n")
        
        # Summary statistics
        total = len(results)
        matches = sum(1 for r in results if r.match)
        conquer_faster_count = sum(1 for r in results if r.conquer_faster)
        
        f.write("## Summary\n\n")
        f.write(f"- **Total comparisons:** {total}\n")
        f.write(f"- **Results matching:** {matches}/{total}\n")
        f.write(f"- **Conquer faster than baseline:** {conquer_faster_count}/{total} ({100*conquer_faster_count/total:.1f}%)\n\n")
        
        if matches != total:
            f.write("⚠️ **WARNING: Some results do not match!**\n\n")
        
        # Detailed results table
        f.write("## Detailed Results\n\n")
        f.write("| Circuit 1 | Circuit 2 | depth | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |\n")
        f.write("|-----------|-----------|-------|----------|-------------|---------|------|-------|-------|-------|\n")
        
        for r in results:
            depth_str = str(r.max_depth) if r.max_depth is not None else "None"
            faster_mark = "**✓**" if r.conquer_faster else ""
            match_mark = "✓" if r.match else "❌"
            
            f.write(
                f"| {r.circuit1_name} | {r.circuit2_name} | {depth_str} | "
                f"{r.baseline_time:.4f} | **{r.cnc_conquer_time:.4f}** | {faster_mark} | "
                f"{r.cnc_cube_time:.4f} | {r.cnc_total_time:.4f} | "
                f"{r.cnc_cubes} | {match_mark} |\n"
            )
        
        # Best configurations
        f.write("\n## Best Configurations\n\n")
        
        if conquer_faster_count > 0:
            # Group by (max_depth, solver_name) and count wins
            config_wins: dict[tuple[int | None, str], int] = {}
            for r in results:
                if r.conquer_faster:
                    key = (r.max_depth, r.solver_name)
                    config_wins[key] = config_wins.get(key, 0) + 1
            
            sorted_configs = sorted(config_wins.items(), key=lambda x: -x[1])
            f.write("| max_depth | solver | Wins |\n")
            f.write("|-----------|--------|------|\n")
            for (depth, solver), wins in sorted_configs[:5]:
                depth_str = str(depth) if depth is not None else "None"
                f.write(f"| {depth_str} | {solver} | {wins} |\n")
        else:
            f.write("No configurations where conquer was faster than baseline.\n")
        
        # Speedup analysis
        f.write("\n## Speedup Analysis\n\n")
        if results:
            # Speedup based on conquer time vs baseline
            conquer_speedups = [r.baseline_time / r.cnc_conquer_time if r.cnc_conquer_time > 0 else 0 for r in results]
            avg_conquer_speedup = sum(conquer_speedups) / len(conquer_speedups)
            max_conquer_speedup = max(conquer_speedups)
            
            # Speedup based on total time vs baseline
            total_speedups = [r.baseline_time / r.cnc_total_time if r.cnc_total_time > 0 else 0 for r in results]
            avg_total_speedup = sum(total_speedups) / len(total_speedups)
            max_total_speedup = max(total_speedups)
            
            f.write(f"- **Average conquer speedup (baseline/conquer):** {avg_conquer_speedup:.2f}x\n")
            f.write(f"- **Max conquer speedup:** {max_conquer_speedup:.2f}x\n")
            f.write(f"- **Average total speedup (baseline/total):** {avg_total_speedup:.2f}x\n")
            f.write(f"- **Max total speedup:** {max_total_speedup:.2f}x\n")


def run_experiment(
    directory: str,
    circuit_type: str | None,
    output: str,
    max_depths: list[int | None],
    solver_names: list[PySATSolverNames],
    group_filter: str | None = None,
    prefixes: list[str] | None = None,
) -> list[ExperimentResult]:
    """Run the full experiment."""
    
    dir_path = Path(directory)
    
    # Auto-detect circuit type if not specified
    if circuit_type is None:
        circuit_type = detect_circuit_type(dir_path)
        print(f"Auto-detected circuit type: {circuit_type}")
    
    # Get grouped circuit files
    groups = get_circuit_files(dir_path, circuit_type, group_filter, prefixes)
    
    if not groups:
        print(f"No circuit files found in {directory}")
        return []
    
    all_results: list[ExperimentResult] = []
    
    for group_key in sorted(groups.keys(), key=lambda x: (len(x), x)):
        files = groups[group_key]
        
        if len(files) < 2:
            print(f"Skipping group '{group_key}': need at least 2 circuits, found {len(files)}")
            continue
        
        print(f"\n{'='*60}")
        print(f"Running experiments for group: {group_key}")
        print(f"{'='*60}")
        
        print(f"Found {len(files)} circuits:")
        for f in files:
            print(f"  - {f.name}")
        
        # Load circuits
        circuits: dict[str, Circuit] = {}
        for file_path in files:
            name = file_path.stem
            print(f"Loading {name}...")
            circuits[name] = load_circuit(file_path)
        
        # Generate pairs
        pairs = list(itertools.combinations(circuits.keys(), 2))
        print(f"\nComparing {len(pairs)} circuit pairs")
        
        for i, (name1, name2) in enumerate(pairs):
            print(f"\n[{i+1}/{len(pairs)}] Comparing {name1} vs {name2}")
            
            c1 = circuits[name1]
            c2 = circuits[name2]
            
            # Build miter and convert to AIG
            miter = build_miter(c1, c2)
            miter.into_aig()

            print(f"  Miter size: {miter.size} gates, {miter.input_size} inputs")

            for solver_name in solver_names:
                # Run baseline once per solver
                baseline_result, baseline_time = run_baseline(miter, solver_name)
                print(f"  Baseline ({solver_name.value}): {'SAT' if baseline_result else 'UNSAT'} in {baseline_time:.4f}s")

                for max_depth in max_depths:
                    cnc_result, cube_time, conquer_time, total_time, cnc_cubes = run_cnc(miter, max_depth, solver_name)

                    match = baseline_result == cnc_result
                    conquer_faster = conquer_time < baseline_time

                    depth_str = str(max_depth) if max_depth is not None else "None"
                    status = "✓" if match else "MISMATCH!"
                    faster = " (conquer faster)" if conquer_faster else ""
                    print(f"    CnC (depth={depth_str}): {'SAT' if cnc_result else 'UNSAT'} cube={cube_time:.4f}s conquer={conquer_time:.4f}s total={total_time:.4f}s, {cnc_cubes} cubes {status}{faster}")

                    all_results.append(ExperimentResult(
                        circuit1_name=name1,
                        circuit2_name=name2,
                        baseline_result=baseline_result,
                        baseline_time=baseline_time,
                        cnc_result=cnc_result,
                        cnc_cube_time=cube_time,
                        cnc_conquer_time=conquer_time,
                        cnc_total_time=total_time,
                        cnc_cubes=cnc_cubes,
                        max_depth=max_depth,
                        solver_name=solver_name.value,
                        match=match,
                        conquer_faster=conquer_faster,
                    ))

                    if not match:
                        print(f"    ⚠️ WARNING: Results do not match!")
    
    # Generate report
    if all_results:
        generate_report(all_results, output, circuit_type)
        print(f"\nReport written to {output}")
        
        # Final summary
        total_matches = sum(1 for r in all_results if r.match)
        total_faster = sum(1 for r in all_results if r.conquer_faster)
        print(f"\nFinal: {total_matches}/{len(all_results)} matches, {total_faster}/{len(all_results)} conquer faster than baseline")
    
    return all_results


def main():
    parser = argparse.ArgumentParser(
        description="Compare baseline SAT vs CubeAndConquerSolver on circuit verification"
    )
    parser.add_argument(
        "--directory", "-d",
        type=str,
        default="aig_output",
        help="Directory containing circuit files (default: aig_output)"
    )
    parser.add_argument(
        "--type", "-t",
        type=str,
        choices=["multiplier", "sort"],
        default=None,
        help="Circuit type: 'multiplier' for .bench files, 'sort' for .aig files (auto-detected if not specified)"
    )
    parser.add_argument(
        "--group", "-g",
        type=str,
        default=None,
        help="Filter to specific group (e.g., '4' for 4-bit multipliers, '7_4' for 7-element 4-bit sort)"
    )
    parser.add_argument(
        "--pair", "-p",
        type=str,
        nargs=2,
        metavar=("PREFIX1", "PREFIX2"),
        help="Circuit pair prefixes to compare (e.g., --pair mul_alter mul_dadda or --pair BubbleSort PancakeSort)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="experiment_report.md",
        help="Output report path (default: experiment_report.md)"
    )
    # Legacy arguments for backwards compatibility
    parser.add_argument(
        "--min-size",
        type=int,
        default=None,
        help="[Deprecated] Use --group instead. Minimum multiplier bit size."
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=None,
        help="[Deprecated] Use --group instead. Maximum multiplier bit size."
    )
    
    args = parser.parse_args()
    
    # Handle legacy min/max-size arguments
    group_filter = args.group
    if args.min_size is not None or args.max_size is not None:
        print("Warning: --min-size and --max-size are deprecated. Use --group instead.")
        # If using legacy args without --group, we need to run for multiple groups
        # For now, just ignore them if --group is set
        if group_filter is None and args.min_size is not None:
            group_filter = str(args.min_size)
    
    # Configuration
    max_depths: list[int | None] = [1, 2, 5]
    solver_names = [
        PySATSolverNames.CADICAL195,
        # PySATSolverNames.GLUCOSE4,
        # PySATSolverNames.MINISAT22,
    ]
    
    # Get prefixes from pair argument if provided
    prefixes = list(args.pair) if args.pair else None
    
    run_experiment(
        directory=args.directory,
        circuit_type=args.type,
        output=args.output,
        max_depths=max_depths,
        solver_names=solver_names,
        group_filter=group_filter,
        prefixes=prefixes,
    )


if __name__ == "__main__":
    main()
