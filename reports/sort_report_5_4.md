# Sorting Circuit Verification Experiment Report

## Summary

- **Total comparisons:** 9
- **Results matching:** 9/9
- **Conquer faster than baseline:** 0/9 (0.0%)

## Detailed Results

| Circuit 1 | Circuit 2 | depth | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |
|-----------|-----------|-------|----------|-------------|---------|------|-------|-------|-------|
| BubbleSort_5_4 | PancakeSort_5_4 | 1 | 1.2698 | **2.5382** |  | 8.1418 | 10.6800 | 2 | ✓ |
| BubbleSort_5_4 | PancakeSort_5_4 | 2 | 1.2698 | **3.1268** |  | 20.5106 | 23.6374 | 4 | ✓ |
| BubbleSort_5_4 | PancakeSort_5_4 | 5 | 1.2698 | **12.5396** |  | 181.4170 | 193.9566 | 32 | ✓ |
| BubbleSort_5_4 | SelectionSort_5_4 | 1 | 1.0013 | **1.3758** |  | 8.4110 | 9.7868 | 2 | ✓ |
| BubbleSort_5_4 | SelectionSort_5_4 | 2 | 1.0013 | **2.2871** |  | 20.6126 | 22.8997 | 4 | ✓ |
| BubbleSort_5_4 | SelectionSort_5_4 | 5 | 1.0013 | **11.2138** |  | 177.4140 | 188.6278 | 32 | ✓ |
| PancakeSort_5_4 | SelectionSort_5_4 | 1 | 1.7197 | **2.4347** |  | 11.9567 | 14.3914 | 2 | ✓ |
| PancakeSort_5_4 | SelectionSort_5_4 | 2 | 1.7197 | **3.9401** |  | 30.5147 | 34.4548 | 4 | ✓ |
| PancakeSort_5_4 | SelectionSort_5_4 | 5 | 1.7197 | **13.6464** |  | 262.4113 | 276.0578 | 32 | ✓ |

## Best Configurations

No configurations where conquer was faster than baseline.

## Speedup Analysis

- **Average conquer speedup (baseline/conquer):** 0.39x
- **Max conquer speedup:** 0.73x
- **Average total speedup (baseline/total):** 0.06x
- **Max total speedup:** 0.12x
