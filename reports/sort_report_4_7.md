# Sorting Circuit Verification Experiment Report

## Summary

- **Total comparisons:** 9
- **Results matching:** 9/9
- **Conquer faster than baseline:** 0/9 (0.0%)

## Detailed Results

| Circuit 1 | Circuit 2 | depth | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |
|-----------|-----------|-------|----------|-------------|---------|------|-------|-------|-------|
| BubbleSort_4_7 | PancakeSort_4_7 | 1 | 0.7951 | **1.1707** |  | 13.3830 | 14.5537 | 2 | ✓ |
| BubbleSort_4_7 | PancakeSort_4_7 | 2 | 0.7951 | **2.1186** |  | 33.2438 | 35.3624 | 4 | ✓ |
| BubbleSort_4_7 | PancakeSort_4_7 | 5 | 0.7951 | **12.4647** |  | 305.6142 | 318.0789 | 32 | ✓ |
| BubbleSort_4_7 | SelectionSort_4_7 | 1 | 0.6073 | **0.9836** |  | 14.9708 | 15.9543 | 2 | ✓ |
| BubbleSort_4_7 | SelectionSort_4_7 | 2 | 0.6073 | **1.7689** |  | 37.8832 | 39.6521 | 4 | ✓ |
| BubbleSort_4_7 | SelectionSort_4_7 | 5 | 0.6073 | **11.3147** |  | 325.1016 | 336.4163 | 32 | ✓ |
| PancakeSort_4_7 | SelectionSort_4_7 | 1 | 0.9140 | **1.4985** |  | 19.6526 | 21.1511 | 2 | ✓ |
| PancakeSort_4_7 | SelectionSort_4_7 | 2 | 0.9140 | **2.6456** |  | 49.7503 | 52.3959 | 4 | ✓ |
| PancakeSort_4_7 | SelectionSort_4_7 | 5 | 0.9140 | **15.1269** |  | 449.2833 | 464.4102 | 32 | ✓ |

## Best Configurations

No configurations where conquer was faster than baseline.

## Speedup Analysis

- **Average conquer speedup (baseline/conquer):** 0.35x
- **Max conquer speedup:** 0.68x
- **Average total speedup (baseline/total):** 0.02x
- **Max total speedup:** 0.05x
