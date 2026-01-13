# Sorting Circuit Verification Experiment Report

## Summary

- **Total comparisons:** 9
- **Results matching:** 9/9
- **Conquer faster than baseline:** 2/9 (22.2%)

## Detailed Results

| Circuit 1 | Circuit 2 | depth | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |
|-----------|-----------|-------|----------|-------------|---------|------|-------|-------|-------|
| BubbleSort_4_3 | PancakeSort_4_3 | 1 | 0.1891 | **0.1807** | **✓** | 2.0272 | 2.2079 | 2 | ✓ |
| BubbleSort_4_3 | PancakeSort_4_3 | 2 | 0.1891 | **0.1902** |  | 4.4221 | 4.6122 | 4 | ✓ |
| BubbleSort_4_3 | PancakeSort_4_3 | 5 | 0.1891 | **0.5138** |  | 29.7527 | 30.2665 | 32 | ✓ |
| BubbleSort_4_3 | SelectionSort_4_3 | 1 | 0.1671 | **0.1410** | **✓** | 1.6320 | 1.7730 | 2 | ✓ |
| BubbleSort_4_3 | SelectionSort_4_3 | 2 | 0.1671 | **0.2380** |  | 3.8082 | 4.0462 | 4 | ✓ |
| BubbleSort_4_3 | SelectionSort_4_3 | 5 | 0.1671 | **0.5374** |  | 31.6272 | 32.1646 | 32 | ✓ |
| PancakeSort_4_3 | SelectionSort_4_3 | 1 | 0.1551 | **0.1909** |  | 2.0857 | 2.2766 | 2 | ✓ |
| PancakeSort_4_3 | SelectionSort_4_3 | 2 | 0.1551 | **0.2569** |  | 5.0010 | 5.2580 | 4 | ✓ |
| PancakeSort_4_3 | SelectionSort_4_3 | 5 | 0.1551 | **0.9311** |  | 42.0483 | 42.9794 | 32 | ✓ |

## Best Configurations

| max_depth | solver | Wins |
|-----------|--------|------|
| 1 | cadical195 | 2 |

## Speedup Analysis

- **Average conquer speedup (baseline/conquer):** 0.69x
- **Max conquer speedup:** 1.18x
- **Average total speedup (baseline/total):** 0.04x
- **Max total speedup:** 0.09x
