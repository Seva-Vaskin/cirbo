# Circuit Verification Experiment Report

## Summary

- **Total runs:** 6
- **Baseline timeouts:** 0
- **CnC timeouts:** 2
- **Results matching:** 4/4
- **Conquer faster than baseline:** 3/4 (75.0%)

## Detailed Results

| Circuit 1 | Circuit 2 | depth | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |
|-----------|-----------|-------|----------|-------------|---------|------|-------|-------|-------|
| mul_dadda_8 | mul_karatsuba_8 | 1 | 5.2556 | **5.5462** |  | 4.1467 | 9.6929 | 2 | ✓ |
| mul_dadda_8 | mul_karatsuba_8 | 2 | 5.2556 | **4.7839** | **✓** | 11.0656 | 15.8495 | 4 | ✓ |
| mul_dadda_8 | mul_karatsuba_8 | 5 | 5.2556 | TIMEOUT | - | - | - | - | - |
| mul_dadda_9 | mul_karatsuba_9 | 1 | 34.7077 | **30.2305** | **✓** | 6.9878 | 37.2183 | 2 | ✓ |
| mul_dadda_9 | mul_karatsuba_9 | 2 | 34.7077 | **29.8481** | **✓** | 17.5881 | 47.4362 | 4 | ✓ |
| mul_dadda_9 | mul_karatsuba_9 | 5 | 34.7077 | TIMEOUT | - | - | - | - | - |

## Speedup Analysis

- **Average conquer speedup (baseline/conquer):** 1.09x
- **Max conquer speedup:** 1.16x
- **Average total speedup (baseline/total):** 0.63x
- **Max total speedup:** 0.93x
