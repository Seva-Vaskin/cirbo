# Multiplier Verification Experiment Report

## Summary

- **Total comparisons:** 9
- **Results matching:** 9/9
- **Conquer faster than baseline:** 8/9 (88.9%)

## Detailed Results

| Circuit 1 | Circuit 2 | depth | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |
|-----------|-----------|-------|----------|-------------|---------|------|-------|-------|-------|
| mul_default_8 | mul_karatsuba_8 | 1 | 6.1207 | **5.6755** | **✓** | 4.8210 | 10.4965 | 2 | ✓ |
| mul_default_8 | mul_karatsuba_8 | 2 | 6.1207 | **5.1063** | **✓** | 10.9374 | 16.0438 | 4 | ✓ |
| mul_default_8 | mul_karatsuba_8 | 5 | 6.1207 | **9.5717** |  | 97.0145 | 106.5862 | 32 | ✓ |
| mul_default_9 | mul_karatsuba_9 | 1 | 31.9321 | **29.8985** | **✓** | 7.0094 | 36.9079 | 2 | ✓ |
| mul_default_9 | mul_karatsuba_9 | 2 | 31.9321 | **24.8414** | **✓** | 17.2002 | 42.0416 | 4 | ✓ |
| mul_default_9 | mul_karatsuba_9 | 5 | 31.9321 | **24.6612** | **✓** | 146.2091 | 170.8704 | 32 | ✓ |
| mul_default_10 | mul_karatsuba_10 | 1 | 211.7105 | **172.5362** | **✓** | 9.6437 | 182.1799 | 2 | ✓ |
| mul_default_10 | mul_karatsuba_10 | 2 | 211.7105 | **165.8855** | **✓** | 31.3233 | 197.2088 | 4 | ✓ |
| mul_default_10 | mul_karatsuba_10 | 5 | 211.7105 | **104.0222** | **✓** | 240.7190 | 344.7412 | 32 | ✓ |

## Best Configurations

| max_depth | solver | Wins |
|-----------|--------|------|
| 1 | cadical195 | 3 |
| 2 | cadical195 | 3 |
| 5 | cadical195 | 2 |

## Speedup Analysis

- **Average conquer speedup (baseline/conquer):** 1.23x
- **Max conquer speedup:** 2.04x
- **Average total speedup (baseline/total):** 0.63x
- **Max total speedup:** 1.16x
