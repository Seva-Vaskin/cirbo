# Multiplier Verification Experiment Report

## Summary

- **Total comparisons:** 9
- **Results matching:** 9/9
- **Conquer faster than baseline:** 8/9 (88.9%)

## Detailed Results

| Circuit 1 | Circuit 2 | depth | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |
|-----------|-----------|-------|----------|-------------|---------|------|-------|-------|-------|
| mul_karatsuba_8 | mul_wallace_8 | 1 | 8.4710 | **5.6041** | **✓** | 4.9511 | 10.5553 | 2 | ✓ |
| mul_karatsuba_8 | mul_wallace_8 | 2 | 8.4710 | **5.4247** | **✓** | 10.5846 | 16.0092 | 4 | ✓ |
| mul_karatsuba_8 | mul_wallace_8 | 5 | 8.4710 | **10.4171** |  | 98.6991 | 109.1163 | 32 | ✓ |
| mul_karatsuba_9 | mul_wallace_9 | 1 | 32.7335 | **32.1547** | **✓** | 7.1106 | 39.2653 | 2 | ✓ |
| mul_karatsuba_9 | mul_wallace_9 | 2 | 32.7335 | **28.1246** | **✓** | 18.1870 | 46.3116 | 4 | ✓ |
| mul_karatsuba_9 | mul_wallace_9 | 5 | 32.7335 | **24.1525** | **✓** | 150.8818 | 175.0342 | 32 | ✓ |
| mul_karatsuba_10 | mul_wallace_10 | 1 | 200.2212 | **167.8118** | **✓** | 10.6965 | 178.5083 | 2 | ✓ |
| mul_karatsuba_10 | mul_wallace_10 | 2 | 200.2212 | **168.2985** | **✓** | 23.6475 | 191.9460 | 4 | ✓ |
| mul_karatsuba_10 | mul_wallace_10 | 5 | 200.2212 | **94.5815** | **✓** | 212.8389 | 307.4204 | 32 | ✓ |

## Best Configurations

| max_depth | solver | Wins |
|-----------|--------|------|
| 1 | cadical195 | 3 |
| 2 | cadical195 | 3 |
| 5 | cadical195 | 2 |

## Speedup Analysis

- **Average conquer speedup (baseline/conquer):** 1.32x
- **Max conquer speedup:** 2.12x
- **Average total speedup (baseline/total):** 0.66x
- **Max total speedup:** 1.12x
