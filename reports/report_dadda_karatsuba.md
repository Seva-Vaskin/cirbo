# Multiplier Verification Experiment Report

## Summary

- **Total comparisons:** 9
- **Results matching:** 9/9
- **Conquer faster than baseline:** 7/9 (77.8%)

## Detailed Results

| Circuit 1 | Circuit 2 | depth | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |
|-----------|-----------|-------|----------|-------------|---------|------|-------|-------|-------|
| mul_dadda_8 | mul_karatsuba_8 | 1 | 6.8975 | **7.5966** |  | 5.6933 | 13.2899 | 2 | ✓ |
| mul_dadda_8 | mul_karatsuba_8 | 2 | 6.8975 | **5.2411** | **✓** | 11.9537 | 17.1948 | 4 | ✓ |
| mul_dadda_8 | mul_karatsuba_8 | 5 | 6.8975 | **11.2086** |  | 109.8568 | 121.0654 | 32 | ✓ |
| mul_dadda_9 | mul_karatsuba_9 | 1 | 37.1257 | **34.1787** | **✓** | 8.1661 | 42.3448 | 2 | ✓ |
| mul_dadda_9 | mul_karatsuba_9 | 2 | 37.1257 | **31.4287** | **✓** | 20.8239 | 52.2527 | 4 | ✓ |
| mul_dadda_9 | mul_karatsuba_9 | 5 | 37.1257 | **24.9625** | **✓** | 168.6299 | 193.5924 | 32 | ✓ |
| mul_dadda_10 | mul_karatsuba_10 | 1 | 260.7825 | **193.8656** | **✓** | 11.4703 | 205.3358 | 2 | ✓ |
| mul_dadda_10 | mul_karatsuba_10 | 2 | 260.7825 | **174.4218** | **✓** | 26.4989 | 200.9207 | 4 | ✓ |
| mul_dadda_10 | mul_karatsuba_10 | 5 | 260.7825 | **114.8224** | **✓** | 244.1449 | 358.9674 | 32 | ✓ |

## Best Configurations

| max_depth | solver | Wins |
|-----------|--------|------|
| 2 | cadical195 | 3 |
| 1 | cadical195 | 2 |
| 5 | cadical195 | 2 |

## Speedup Analysis

- **Average conquer speedup (baseline/conquer):** 1.30x
- **Max conquer speedup:** 2.27x
- **Average total speedup (baseline/total):** 0.67x
- **Max total speedup:** 1.30x

