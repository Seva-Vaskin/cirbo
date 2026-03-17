"""
Optuna-based hyperparameter optimization for CubeAndConquerSolver.

Finds optimal parameters to minimize conquer time on miter circuits.
Supports .bench, .aig, and .aag formats.

Usage:
    python optuna_experiment.py -i miter.aig -o results.md --n-trials 100
    python optuna_experiment.py -i miter.aig -o results.md --n-trials 50 --timeout 120
"""

import argparse
import copy
import logging
import signal
import sys
import time
from pathlib import Path

import optuna
from optuna.trial import Trial

from cirbo.core import Circuit
from cirbo.core.circuit import Transformer
from cirbo.minimization import MergeUnaryOperators
from cirbo.minimization.simplification import RemoveConstantGates
from cirbo.sat import PySATSolverNames, is_circuit_satisfiable
from cirbo.sat.solver.cnc_solver_old import CubeAndConquerSolver


class SolverTimeout(Exception):
    """Raised when a solver times out."""
    pass


def timeout_handler(signum, frame):
    raise SolverTimeout("Solver timed out")


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
    """Run baseline SAT solver and return (result, time, timed_out)."""
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
    """Run CubeAndConquerSolver and return (result, cube_time, conquer_time, total_time, num_cubes, timed_out)."""
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


def create_objective(
    miter: Circuit,
    baseline_result: bool | None,
    solver_name: PySATSolverNames,
    timeout: int | None,
    optimize_target: str,
):
    """Create an Optuna objective function for the given miter circuit."""
    
    def objective(trial: Trial) -> float:
        # Sample hyperparameters with restricted ranges
        max_depth = trial.suggest_int("max_depth", 4, 10)
        # min_circuit_size = trial.suggest_int("min_circuit_size", 1, 50)
        min_circuit_size = 1
        # candidates_limit = trial.suggest_int("candidates_limit", 5, 20)
        candidates_limit = 10
        
        # Thresholds: hard <= soft (hard filters out, soft increments counter)
        # Restricted to promising range based on experiments
        hard_threshold = trial.suggest_int("hard_threshold", 0, 600)
        soft_threshold = trial.suggest_int("soft_threshold", hard_threshold, 3000)
        
        # Soft threshold limit (how many times soft threshold can be violated)
        soft_threshold_limit = trial.suggest_int("soft_threshold_limit", 1, 3)
        
        # Run CnC solver
        cnc_result, cube_time, conquer_time, total_time, num_cubes, timed_out = run_cnc(
            miter=miter,
            max_depth=max_depth,
            min_circuit_size=min_circuit_size,
            candidates_limit=candidates_limit,
            hard_threshold=hard_threshold,
            soft_threshold=soft_threshold,
            soft_threshold_limit=soft_threshold_limit,
            solver_name=solver_name,
            timeout=timeout,
        )
        
        # Handle timeout - return a large penalty
        if timed_out:
            return float("inf")
        
        # Verify correctness - if result doesn't match baseline, penalize heavily
        if baseline_result is not None and cnc_result != baseline_result:
            return float("inf")
        
        # Store additional metrics for analysis
        trial.set_user_attr("cube_time", cube_time)
        trial.set_user_attr("conquer_time", conquer_time)
        trial.set_user_attr("total_time", total_time)
        trial.set_user_attr("num_cubes", num_cubes)
        trial.set_user_attr("cnc_result", cnc_result)
        
        # Return the optimization target
        if optimize_target == "conquer":
            return conquer_time
        elif optimize_target == "total":
            return total_time
        elif optimize_target == "cube":
            return cube_time
        else:
            return conquer_time
    
    return objective


def generate_report(
    study: optuna.Study,
    miter_name: str,
    baseline_time: float | None,
    output_path: str,
    optimize_target: str,
) -> None:
    """Generate markdown report from Optuna study results."""
    with open(output_path, "w") as f:
        f.write("# Optuna Hyperparameter Optimization Report\n\n")
        
        f.write(f"## Configuration\n\n")
        f.write(f"- **Miter:** {miter_name}\n")
        f.write(f"- **Optimization target:** {optimize_target} time\n")
        f.write(f"- **Total trials:** {len(study.trials)}\n")
        if baseline_time is not None:
            f.write(f"- **Baseline time:** {baseline_time:.4f}s\n")
        f.write("\n")
        
        # Best trial
        f.write("## Best Trial\n\n")
        best_trial = study.best_trial
        f.write(f"- **Best {optimize_target} time:** {best_trial.value:.4f}s\n")
        if baseline_time is not None and best_trial.value < baseline_time:
            speedup = baseline_time / best_trial.value
            f.write(f"- **Speedup vs baseline:** {speedup:.2f}x\n")
        f.write("\n")
        
        f.write("### Best Parameters\n\n")
        f.write("| Parameter | Value |\n")
        f.write("|-----------|-------|\n")
        for param, value in best_trial.params.items():
            f.write(f"| {param} | {value} |\n")
        f.write("\n")
        
        f.write("### Best Trial Metrics\n\n")
        f.write(f"- **Cube time:** {best_trial.user_attrs.get('cube_time', 'N/A'):.4f}s\n")
        f.write(f"- **Conquer time:** {best_trial.user_attrs.get('conquer_time', 'N/A'):.4f}s\n")
        f.write(f"- **Total time:** {best_trial.user_attrs.get('total_time', 'N/A'):.4f}s\n")
        f.write(f"- **Number of cubes:** {best_trial.user_attrs.get('num_cubes', 'N/A')}\n")
        f.write("\n")
        
        # Top 10 trials
        f.write("## Top 10 Trials\n\n")
        f.write("| Rank | Conquer | Cube | Total | Cubes | max_depth | min_size | candidates | hard_th | soft_th | soft_lim |\n")
        f.write("|------|---------|------|-------|-------|-----------|----------|------------|---------|---------|----------|\n")
        
        # Sort trials by value (excluding failed ones)
        valid_trials = [t for t in study.trials if t.value is not None and t.value != float("inf")]
        sorted_trials = sorted(valid_trials, key=lambda t: t.value)[:10]
        
        for rank, trial in enumerate(sorted_trials, 1):
            conquer = trial.user_attrs.get("conquer_time", 0)
            cube = trial.user_attrs.get("cube_time", 0)
            total = trial.user_attrs.get("total_time", 0)
            cubes = trial.user_attrs.get("num_cubes", 0)
            
            params = trial.params
            max_depth = params.get("max_depth", "N/A")
            min_size = params.get("min_circuit_size", "N/A")
            candidates = params.get("candidates_limit", "N/A")
            hard_th = f"{params.get('hard_threshold', 0):.1f}"
            soft_th = f"{params.get('soft_threshold', 0):.1f}"
            soft_lim = params.get("soft_threshold_limit", "None")
            
            f.write(f"| {rank} | {conquer:.4f} | {cube:.4f} | {total:.4f} | {cubes} | {max_depth} | {min_size} | {candidates} | {hard_th} | {soft_th} | {soft_lim} |\n")
        
        f.write("\n")
        
        # Parameter importance (if available)
        try:
            importance = optuna.importance.get_param_importances(study)
            f.write("## Parameter Importance\n\n")
            f.write("| Parameter | Importance |\n")
            f.write("|-----------|------------|\n")
            for param, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
                f.write(f"| {param} | {imp:.4f} |\n")
            f.write("\n")
        except Exception:
            pass  # Skip if importance calculation fails
        
        # Study statistics
        f.write("## Study Statistics\n\n")
        completed = len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE])
        failed = len([t for t in study.trials if t.state == optuna.trial.TrialState.FAIL])
        pruned = len([t for t in study.trials if t.state == optuna.trial.TrialState.PRUNED])
        
        f.write(f"- **Completed trials:** {completed}\n")
        f.write(f"- **Failed trials:** {failed}\n")
        f.write(f"- **Pruned trials:** {pruned}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Optuna hyperparameter optimization for CubeAndConquerSolver"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Miter circuit file to optimize on (.bench, .aig, or .aag)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Output report path (example: optuna_results.md)"
    )
    parser.add_argument(
        "--n-trials", "-n",
        type=int,
        default=100,
        help="Number of Optuna trials to run (default: 100)"
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=None,
        help="Timeout in seconds per solver call (default: no timeout)"
    )
    parser.add_argument(
        "--optimize",
        choices=["conquer", "total", "cube"],
        default="conquer",
        help="Which time metric to optimize (default: conquer)"
    )
    parser.add_argument(
        "--study-name",
        type=str,
        default=None,
        help="Optuna study name (default: auto-generated from input file)"
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: WARNING)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level.upper(), logging.WARNING)
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    
    # Load miter circuit
    miter_path = Path(args.input)
    if not miter_path.exists():
        print(f"Error: Miter file not found: {miter_path}")
        sys.exit(1)
    
    print(f"Loading {miter_path.name}...")
    miter = load_circuit(miter_path)
    print(f"Miter size: {miter.size} gates, {miter.input_size} inputs")
    
    miter = Transformer.apply_transformers(
        miter,
        [
            RemoveConstantGates(),
            MergeUnaryOperators(),
        ]
    )
    print(f"Miter size: {miter.size} gates, {miter.input_size} inputs (after simplification)")
    
    # Run baseline
    solver_name = PySATSolverNames.CADICAL195
    print(f"\nRunning baseline ({solver_name.value})...")
    baseline_result, baseline_time, baseline_timed_out = run_baseline(miter, solver_name, args.timeout)
    
    if baseline_timed_out:
        print("Baseline: TIMEOUT")
        baseline_time = None
    else:
        print(f"Baseline: {'SAT' if baseline_result else 'UNSAT'} in {baseline_time:.4f}s")
    
    # Create Optuna study
    study_name = args.study_name or f"cnc_optimization_{miter_path.stem}"
    study = optuna.create_study(
        study_name=study_name,
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=42),
    )
    
    # Create objective function
    objective = create_objective(
        miter=miter,
        baseline_result=baseline_result,
        solver_name=solver_name,
        timeout=args.timeout,
        optimize_target=args.optimize,
    )
    
    # Run optimization
    print(f"\nStarting Optuna optimization ({args.n_trials} trials)...")
    print(f"Optimizing: {args.optimize} time")
    
    study.optimize(
        objective,
        n_trials=args.n_trials,
        show_progress_bar=True,
    )
    
    # Print best result
    print(f"\n{'='*60}")
    print("OPTIMIZATION COMPLETE")
    print(f"{'='*60}")
    print(f"Best {args.optimize} time: {study.best_value:.4f}s")
    if baseline_time is not None and study.best_value < baseline_time:
        speedup = baseline_time / study.best_value
        print(f"Speedup vs baseline: {speedup:.2f}x")
    print(f"\nBest parameters:")
    for param, value in study.best_params.items():
        print(f"  {param}: {value}")
    
    # Generate report
    generate_report(
        study=study,
        miter_name=miter_path.name,
        baseline_time=baseline_time,
        output_path=args.output,
        optimize_target=args.optimize,
    )
    print(f"\nReport written to {args.output}")


if __name__ == "__main__":
    main()
