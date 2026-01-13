# Sorting Circuit Verification Experiment Report

## Summary

- **Total comparisons:** 9
- **Results matching:** 9/9
- **Conquer faster than baseline:** 0/9 (0.0%)

## Detailed Results

| Circuit 1 | Circuit 2 | depth | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |
|-----------|-----------|-------|----------|-------------|---------|------|-------|-------|-------|
| BubbleSort_4_4 | PancakeSort_4_4 | 1 | 0.2684 | **0.3776** |  | 3.1718 | 3.5494 | 2 | ✓ |
| BubbleSort_4_4 | PancakeSort_4_4 | 2 | 0.2684 | **0.7877** |  | 7.4774 | 8.2651 | 4 | ✓ |
| BubbleSort_4_4 | PancakeSort_4_4 | 5 | 0.2684 | **2.1011** |  | 65.5210 | 67.6221 | 32 | ✓ |
| BubbleSort_4_4 | SelectionSort_4_4 | 1 | 0.1999 | **0.3256** |  | 3.1952 | 3.5208 | 2 | ✓ |
| BubbleSort_4_4 | SelectionSort_4_4 | 2 | 0.1999 | **0.5596** |  | 8.1941 | 8.7536 | 4 | ✓ |
| BubbleSort_4_4 | SelectionSort_4_4 | 5 | 0.1999 | **1.5938** |  | 65.4098 | 67.0036 | 32 | ✓ |
| PancakeSort_4_4 | SelectionSort_4_4 | 1 | 0.2879 | **0.4491** |  | 4.1517 | 4.6008 | 2 | ✓ |
| PancakeSort_4_4 | SelectionSort_4_4 | 2 | 0.2879 | **0.7355** |  | 10.4028 | 11.1384 | 4 | ✓ |
| PancakeSort_4_4 | SelectionSort_4_4 | 5 | 0.2879 | **3.1254** |  | 94.7988 | 97.9243 | 32 | ✓ |

## Best Configurations

No configurations where conquer was faster than baseline.

## Speedup Analysis

- **Average conquer speedup (baseline/conquer):** 0.38x
- **Max conquer speedup:** 0.71x
- **Average total speedup (baseline/total):** 0.03x
- **Max total speedup:** 0.08x
