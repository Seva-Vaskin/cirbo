"""
Script to apply FRAIG transformation to miter circuits between
(Karatsuba, Dadda, Wallace, Default) multiplier implementations.
"""

import itertools
import time
from dataclasses import dataclass
from pathlib import Path

from cirbo.core import Circuit
from cirbo.sat import build_miter
from extensions.abc_wrapper.src.abc import abc_transform


@dataclass
class FraigResult:
    name1: str
    name2: str
    size: int
    original_size: int
    updated_size: int
    operation_time: float


def run_fraig_experiment(
    directory: str,
    min_size: int,
    max_size: int,
    output: str,
    prefixes: list[str],
) -> list[FraigResult]:
    """Run FRAIG experiment on miter circuits."""
    
    all_results: list[FraigResult] = []
    
    for size in range(min_size, max_size + 1):
        print(f"\n{'='*60}")
        print(f"Processing size {size}")
        print(f"{'='*60}")
        
        # Load circuits for this size
        circuits: dict[str, Circuit] = {}
        for prefix in prefixes:
            filename = f"{prefix}_{size}.bench"
            filepath = Path(directory) / filename
            if filepath.exists():
                print(f"Loading {filename}...")
                circuits[prefix] = Circuit.from_bench_file(str(filepath))
            else:
                print(f"Warning: {filename} not found, skipping")
        
        if len(circuits) < 2:
            print(f"Not enough circuits found for size {size}, skipping")
            continue
        
        # Generate all pairs
        pairs = list(itertools.combinations(circuits.keys(), 2))
        print(f"\nProcessing {len(pairs)} circuit pairs")
        
        for i, (name1, name2) in enumerate(pairs):
            print(f"\n[{i+1}/{len(pairs)}] {name1} vs {name2}")
            
            c1 = circuits[name1]
            c2 = circuits[name2]
            
            # Build miter circuit
            miter = build_miter(c1, c2)
            miter.into_aig()
            
            original_size = miter.size
            print(f"  Original miter size: {original_size} gates")
            
            # Apply FRAIG transformation
            cmd = "fraig -C 1000 -D 32769"
            print(f"  Applying transformation: {cmd}")
            
            t0 = time.time()
            transformed = abc_transform(miter, cmd)
            operation_time = time.time() - t0
            
            updated_size = transformed.size
            print(f"  Updated size: {updated_size} gates")
            print(f"  Operation time: {operation_time:.4f}s")
            print(f"  Reduction: {original_size - updated_size} gates ({100*(original_size - updated_size)/original_size:.1f}%)")
            
            all_results.append(FraigResult(
                name1=name1,
                name2=name2,
                size=size,
                original_size=original_size,
                updated_size=updated_size,
                operation_time=operation_time,
            ))
    
    # Generate report
    generate_report(all_results, output)
    print(f"\nReport written to {output}")
    
    return all_results


def generate_report(results: list[FraigResult], output_path: str) -> None:
    """Generate markdown report from experiment results."""
    with open(output_path, "w") as f:
        f.write("# FRAIG Transformation Experiment Report\n\n")
        
        # Summary
        f.write("## Summary\n\n")
        f.write(f"- **Total miter circuits processed:** {len(results)}\n")
        
        if results:
            total_original = sum(r.original_size for r in results)
            total_updated = sum(r.updated_size for r in results)
            total_reduction = total_original - total_updated
            avg_reduction_pct = 100 * total_reduction / total_original if total_original > 0 else 0
            total_time = sum(r.operation_time for r in results)
            
            f.write(f"- **Total original gates:** {total_original}\n")
            f.write(f"- **Total updated gates:** {total_updated}\n")
            f.write(f"- **Total reduction:** {total_reduction} gates ({avg_reduction_pct:.1f}%)\n")
            f.write(f"- **Total operation time:** {total_time:.4f}s\n\n")
        
        # Detailed results table
        f.write("## Detailed Results\n\n")
        f.write("| Name 1 | Name 2 | Size | Original Size | Updated Size | Reduction | Reduction % | Time (s) |\n")
        f.write("|--------|--------|------|---------------|--------------|-----------|-------------|----------|\n")
        
        for r in results:
            reduction = r.original_size - r.updated_size
            reduction_pct = 100 * reduction / r.original_size if r.original_size > 0 else 0
            f.write(
                f"| {r.name1} | {r.name2} | {r.size} | "
                f"{r.original_size} | {r.updated_size} | {reduction} | "
                f"{reduction_pct:.1f}% | {r.operation_time:.4f} |\n"
            )
        
        # Results by size
        f.write("\n## Results by Size\n\n")
        sizes = sorted(set(r.size for r in results))
        for size in sizes:
            size_results = [r for r in results if r.size == size]
            total_orig = sum(r.original_size for r in size_results)
            total_upd = sum(r.updated_size for r in size_results)
            total_red = total_orig - total_upd
            avg_red_pct = 100 * total_red / total_orig if total_orig > 0 else 0
            total_t = sum(r.operation_time for r in size_results)
            
            f.write(f"### Size {size}\n\n")
            f.write(f"- Pairs processed: {len(size_results)}\n")
            f.write(f"- Average original size: {total_orig / len(size_results):.0f}\n")
            f.write(f"- Average updated size: {total_upd / len(size_results):.0f}\n")
            f.write(f"- Average reduction: {avg_red_pct:.1f}%\n")
            f.write(f"- Total time: {total_t:.4f}s\n\n")


def main():
    # Configuration
    directory = "aig_output"
    min_size = 8
    max_size = 10
    output = "fraig_report.md"
    
    # The 4 multiplier types to compare
    prefixes = [
        "mul_karatsuba",
        "mul_dadda", 
        "mul_wallace",
        "mul_default",
    ]
    
    print("FRAIG Experiment")
    print(f"Sizes: {min_size} to {max_size}")
    print(f"Multiplier types: {prefixes}")
    print(f"Total pairs per size: {len(list(itertools.combinations(prefixes, 2)))}")
    
    run_fraig_experiment(
        directory=directory,
        min_size=min_size,
        max_size=max_size,
        output=output,
        prefixes=prefixes,
    )


if __name__ == "__main__":
    main()

