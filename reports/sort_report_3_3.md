# Sorting Circuit Verification Experiment Report

## Summary

- **Total comparisons:** 9
- **Results matching:** 9/9
- **Conquer faster than baseline:** 0/9 (0.0%)

## Detailed Results

| Circuit 1 | Circuit 2 | depth | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |
|-----------|-----------|-------|----------|-------------|---------|------|-------|-------|-------|
| BubbleSort_3_3 | PancakeSort_3_3 | 1 | 0.0130 | **0.0172** |  | 0.4846 | 0.5018 | 2 | ✓ |
| BubbleSort_3_3 | PancakeSort_3_3 | 2 | 0.0130 | **0.0284** |  | 1.0504 | 1.0788 | 4 | ✓ |
| BubbleSort_3_3 | PancakeSort_3_3 | 5 | 0.0130 | **0.1378** |  | 7.3581 | 7.4959 | 32 | ✓ |
| BubbleSort_3_3 | SelectionSort_3_3 | 1 | 0.0101 | **0.0197** |  | 0.5003 | 0.5201 | 2 | ✓ |
| BubbleSort_3_3 | SelectionSort_3_3 | 2 | 0.0101 | **0.0286** |  | 1.1324 | 1.1611 | 4 | ✓ |
| BubbleSort_3_3 | SelectionSort_3_3 | 5 | 0.0101 | **0.1393** |  | 8.4659 | 8.6052 | 32 | ✓ |
| PancakeSort_3_3 | SelectionSort_3_3 | 1 | 0.0177 | **0.0215** |  | 0.6720 | 0.6934 | 2 | ✓ |
| PancakeSort_3_3 | SelectionSort_3_3 | 2 | 0.0177 | **0.0389** |  | 1.5416 | 1.5805 | 4 | ✓ |
| PancakeSort_3_3 | SelectionSort_3_3 | 5 | 0.0177 | **0.4073** |  | 10.7115 | 11.1188 | 32 | ✓ |

## Best Configurations

No configurations where conquer was faster than baseline.

## Speedup Analysis

- **Average conquer speedup (baseline/conquer):** 0.40x
- **Max conquer speedup:** 0.82x
- **Average total speedup (baseline/total):** 0.01x
- **Max total speedup:** 0.03x

