# Multiplier Verification Experiment Report

## Summary

- **Total comparisons:** 9
- **Results matching:** 9/9
- **Conquer faster than baseline:** 8/9 (88.9%)

## Detailed Results

| Circuit 1 | Circuit 2 | depth | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |
|-----------|-----------|-------|----------|-------------|---------|------|-------|-------|-------|
| mul_dadda_8 | mul_wallace_8 | 1 | 6.7602 | **5.3343** | **✓** | 4.7132 | 10.0475 | 2 | ✓ |
| mul_dadda_8 | mul_wallace_8 | 2 | 6.7602 | **5.8817** | **✓** | 11.5991 | 17.4808 | 4 | ✓ |
| mul_dadda_8 | mul_wallace_8 | 5 | 6.7602 | **10.0779** |  | 107.1150 | 117.1930 | 32 | ✓ |
| mul_dadda_9 | mul_wallace_9 | 1 | 38.5512 | **32.1118** | **✓** | 7.8349 | 39.9467 | 2 | ✓ |
| mul_dadda_9 | mul_wallace_9 | 2 | 38.5512 | **30.1926** | **✓** | 19.0205 | 49.2132 | 4 | ✓ |
| mul_dadda_9 | mul_wallace_9 | 5 | 38.5512 | **24.5855** | **✓** | 159.3020 | 183.8875 | 32 | ✓ |
| mul_dadda_10 | mul_wallace_10 | 1 | 240.0281 | **193.8500** | **✓** | 10.1807 | 204.0307 | 2 | ✓ |
| mul_dadda_10 | mul_wallace_10 | 2 | 240.0281 | **179.0476** | **✓** | 26.8061 | 205.8537 | 4 | ✓ |
| mul_dadda_10 | mul_wallace_10 | 5 | 240.0281 | **117.4626** | **✓** | 230.2335 | 347.6961 | 32 | ✓ |

## Best Configurations

| max_depth | solver | Wins |
|-----------|--------|------|
| 1 | cadical195 | 3 |
| 2 | cadical195 | 3 |
| 5 | cadical195 | 2 |

## Speedup Analysis

- **Average conquer speedup (baseline/conquer):** 1.31x
- **Max conquer speedup:** 2.04x
- **Average total speedup (baseline/total):** 0.68x
- **Max total speedup:** 1.18x
<!--  -->