# Multiplier Verification Experiment Report

## Summary

- **Total comparisons:** 9
- **Results matching:** 9/9
- **Conquer faster than baseline:** 6/9 (66.7%)

## Detailed Results

| Circuit 1 | Circuit 2 | depth | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |
|-----------|-----------|-------|----------|-------------|---------|------|-------|-------|-------|
| mul_default_8 | mul_wallace_8 | 1 | 6.1494 | **7.6800** |  | 4.7464 | 12.4263 | 2 | ✓ |
| mul_default_8 | mul_wallace_8 | 2 | 6.1494 | **5.3554** | **✓** | 12.7607 | 18.1161 | 4 | ✓ |
| mul_default_8 | mul_wallace_8 | 5 | 6.1494 | **9.9122** |  | 94.6275 | 104.5397 | 32 | ✓ |
| mul_default_9 | mul_wallace_9 | 1 | 35.7349 | **28.9280** | **✓** | 6.5195 | 35.4475 | 2 | ✓ |
| mul_default_9 | mul_wallace_9 | 2 | 35.7349 | **29.1994** | **✓** | 16.8606 | 46.0600 | 4 | ✓ |
| mul_default_9 | mul_wallace_9 | 5 | 35.7349 | **26.8821** | **✓** | 139.1012 | 165.9833 | 32 | ✓ |
| mul_default_10 | mul_wallace_10 | 1 | 186.3432 | **165.4259** | **✓** | 9.0483 | 174.4742 | 2 | ✓ |
| mul_default_10 | mul_wallace_10 | 2 | 186.3432 | **191.7323** |  | 27.0678 | 218.8001 | 4 | ✓ |
| mul_default_10 | mul_wallace_10 | 5 | 186.3432 | **103.1879** | **✓** | 204.8816 | 308.0695 | 32 | ✓ |

## Best Configurations

| max_depth | solver | Wins |
|-----------|--------|------|
| 2 | cadical195 | 2 |
| 1 | cadical195 | 2 |
| 5 | cadical195 | 2 |

## Speedup Analysis

- **Average conquer speedup (baseline/conquer):** 1.14x
- **Max conquer speedup:** 1.81x
- **Average total speedup (baseline/total):** 0.60x
- **Max total speedup:** 1.07x
