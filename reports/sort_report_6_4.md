# Sorting Circuit Verification Experiment Report

## Summary

- **Total comparisons:** 9
- **Results matching:** 9/9
- **Conquer faster than baseline:** 0/9 (0.0%)

## Detailed Results

| Circuit 1 | Circuit 2 | depth | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |
|-----------|-----------|-------|----------|-------------|---------|------|-------|-------|-------|
| BubbleSort_6_4 | PancakeSort_6_4 | 1 | 10.0013 | **16.6930** |  | 13.7171 | 30.4101 | 2 | ✓ |
| BubbleSort_6_4 | PancakeSort_6_4 | 2 | 10.0013 | **26.9498** |  | 41.8339 | 68.7838 | 4 | ✓ |
| BubbleSort_6_4 | PancakeSort_6_4 | 5 | 10.0013 | **46.9369** |  | 324.6913 | 371.6282 | 32 | ✓ |
| BubbleSort_6_4 | SelectionSort_6_4 | 1 | 6.7702 | **10.8562** |  | 14.1413 | 24.9975 | 2 | ✓ |
| BubbleSort_6_4 | SelectionSort_6_4 | 2 | 6.7702 | **17.3705** |  | 33.6398 | 51.0103 | 4 | ✓ |
| BubbleSort_6_4 | SelectionSort_6_4 | 5 | 6.7702 | **35.1071** |  | 294.8865 | 329.9936 | 32 | ✓ |
| PancakeSort_6_4 | SelectionSort_6_4 | 1 | 21.3713 | **32.1252** |  | 23.3163 | 55.4414 | 2 | ✓ |
| PancakeSort_6_4 | SelectionSort_6_4 | 2 | 21.3713 | **35.1800** |  | 54.5722 | 89.7522 | 4 | ✓ |
| PancakeSort_6_4 | SelectionSort_6_4 | 5 | 21.3713 | **65.6173** |  | 449.3793 | 514.9966 | 32 | ✓ |

## Best Configurations

No configurations where conquer was faster than baseline.

## Speedup Analysis

- **Average conquer speedup (baseline/conquer):** 0.44x
- **Max conquer speedup:** 0.67x
- **Average total speedup (baseline/total):** 0.18x
- **Max total speedup:** 0.39x
