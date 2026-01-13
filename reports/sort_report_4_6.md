# Sorting Circuit Verification Experiment Report

## Summary

- **Total comparisons:** 9
- **Results matching:** 9/9
- **Conquer faster than baseline:** 0/9 (0.0%)

## Detailed Results

| Circuit 1 | Circuit 2 | depth | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |
|-----------|-----------|-------|----------|-------------|---------|------|-------|-------|-------|
| BubbleSort_4_6 | PancakeSort_4_6 | 1 | 0.5928 | **0.8745** |  | 9.5909 | 10.4655 | 2 | ✓ |
| BubbleSort_4_6 | PancakeSort_4_6 | 2 | 0.5928 | **1.7355** |  | 26.5355 | 28.2710 | 4 | ✓ |
| BubbleSort_4_6 | PancakeSort_4_6 | 5 | 0.5928 | **9.4718** |  | 236.4366 | 245.9084 | 32 | ✓ |
| BubbleSort_4_6 | SelectionSort_4_6 | 1 | 0.4382 | **0.7417** |  | 9.9934 | 10.7351 | 2 | ✓ |
| BubbleSort_4_6 | SelectionSort_4_6 | 2 | 0.4382 | **1.6306** |  | 26.7128 | 28.3434 | 4 | ✓ |
| BubbleSort_4_6 | SelectionSort_4_6 | 5 | 0.4382 | **8.8282** |  | 245.2595 | 254.0877 | 32 | ✓ |
| PancakeSort_4_6 | SelectionSort_4_6 | 1 | 0.6303 | **1.0060** |  | 14.3241 | 15.3301 | 2 | ✓ |
| PancakeSort_4_6 | SelectionSort_4_6 | 2 | 0.6303 | **1.8312** |  | 37.1978 | 39.0290 | 4 | ✓ |
| PancakeSort_4_6 | SelectionSort_4_6 | 5 | 0.6303 | **11.9348** |  | 285.5333 | 297.4681 | 32 | ✓ |

## Best Configurations

No configurations where conquer was faster than baseline.

## Speedup Analysis

- **Average conquer speedup (baseline/conquer):** 0.33x
- **Max conquer speedup:** 0.68x
- **Average total speedup (baseline/total):** 0.02x
- **Max total speedup:** 0.06x
