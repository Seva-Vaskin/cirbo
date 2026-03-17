"""
Script to load an AIG file, apply FRAIG simplification, and report gate counts.
"""

from cirbo.core import Circuit
from extensions.abc_wrapper.src.abc import abc_transform


def main():
    # Load the AIG file
    aig_path = "/home/vsevolod/Work/cirbo/data/sat/miters/mul/mul_6_dadda_vs_karatsuba.aig"
    circuit = Circuit.from_aig_file(aig_path)
    
    gates_before = circuit.size
    print(f"Gates before FRAIG: {gates_before}")
    
    # Apply FRAIG simplification
    simplified = abc_transform(circuit, "fraig")
    
    gates_after = simplified.size
    print(f"Gates after FRAIG: {gates_after}")
    
    reduction = gates_before - gates_after
    reduction_pct = 100 * reduction / gates_before if gates_before > 0 else 0
    print(f"Reduction: {reduction} gates ({reduction_pct:.1f}%)")


if __name__ == "__main__":
    main()
