# Sorting Circuit Verification Experiment Report

## Summary

- **Total comparisons:** 9
- **Results matching:** 9/9
- **Conquer faster than baseline:** 0/9 (0.0%)

## Detailed Results

| Circuit 1 | Circuit 2 | depth | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |
|-----------|-----------|-------|----------|-------------|---------|------|-------|-------|-------|
| BubbleSort_7_4 | PancakeSort_7_4 | 1 | 98.8600 | **157.1828** |  | 25.9804 | 183.1632 | 2 | ✓ |
| BubbleSort_7_4 | PancakeSort_7_4 | 2 | 98.8600 | **247.9378** |  | 66.7480 | 314.6859 | 4 | ✓ |
| BubbleSort_7_4 | PancakeSort_7_4 | 5 | 98.8600 | **527.3984** |  | 568.6773 | 1096.0757 | 32 | ✓ |
| BubbleSort_7_4 | SelectionSort_7_4 | 1 | 68.0550 | **117.5910** |  | 24.9093 | 142.5003 | 2 | ✓ |
| BubbleSort_7_4 | SelectionSort_7_4 | 2 | 68.0550 | **143.6348** |  | 68.2425 | 211.8772 | 4 | ✓ |
| BubbleSort_7_4 | SelectionSort_7_4 | 5 | 68.0550 | **266.0983** |  | 584.4013 | 850.4996 | 32 | ✓ |
| PancakeSort_7_4 | SelectionSort_7_4 | 1 | 542.4785 | **716.3329** |  | 38.6924 | 755.0253 | 2 | ✓ |
| PancakeSort_7_4 | SelectionSort_7_4 | 2 | 542.4785 | **857.5059** |  | 105.1855 | 962.6914 | 4 | ✓ |
| PancakeSort_7_4 | SelectionSort_7_4 | 5 | 542.4785 | **1071.5428** |  | 822.4257 | 1893.9685 | 32 | ✓ |

## Best Configurations

No configurations where conquer was faster than baseline.

## Speedup Analysis

- **Average conquer speedup (baseline/conquer):** 0.49x
- **Max conquer speedup:** 0.76x
- **Average total speedup (baseline/total):** 0.38x
- **Max total speedup:** 0.72x
