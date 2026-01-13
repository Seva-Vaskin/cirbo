# Sorting Circuit Verification Experiment Report

## Summary

- **Total comparisons:** 9
- **Results matching:** 9/9
- **Conquer faster than baseline:** 0/9 (0.0%)

## Detailed Results

| Circuit 1 | Circuit 2 | depth | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |
|-----------|-----------|-------|----------|-------------|---------|------|-------|-------|-------|
| BubbleSort_4_5 | PancakeSort_4_5 | 1 | 0.4455 | **0.5021** |  | 6.4449 | 6.9470 | 2 | ✓ |
| BubbleSort_4_5 | PancakeSort_4_5 | 2 | 0.4455 | **1.1860** |  | 14.6819 | 15.8679 | 4 | ✓ |
| BubbleSort_4_5 | PancakeSort_4_5 | 5 | 0.4455 | **5.9756** |  | 123.3407 | 129.3162 | 32 | ✓ |
| BubbleSort_4_5 | SelectionSort_4_5 | 1 | 0.2807 | **0.4304** |  | 5.9372 | 6.3675 | 2 | ✓ |
| BubbleSort_4_5 | SelectionSort_4_5 | 2 | 0.2807 | **0.9298** |  | 16.6496 | 17.5794 | 4 | ✓ |
| BubbleSort_4_5 | SelectionSort_4_5 | 5 | 0.2807 | **4.7969** |  | 139.8714 | 144.6682 | 32 | ✓ |
| PancakeSort_4_5 | SelectionSort_4_5 | 1 | 0.5564 | **0.7904** |  | 9.6812 | 10.4716 | 2 | ✓ |
| PancakeSort_4_5 | SelectionSort_4_5 | 2 | 0.5564 | **1.4597** |  | 23.9350 | 25.3946 | 4 | ✓ |
| PancakeSort_4_5 | SelectionSort_4_5 | 5 | 0.5564 | **7.8061** |  | 190.4878 | 198.2939 | 32 | ✓ |

## Best Configurations

No configurations where conquer was faster than baseline.

## Speedup Analysis

- **Average conquer speedup (baseline/conquer):** 0.39x
- **Max conquer speedup:** 0.89x
- **Average total speedup (baseline/total):** 0.03x
- **Max total speedup:** 0.06x
