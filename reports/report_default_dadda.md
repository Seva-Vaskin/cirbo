# Multiplier Verification Experiment Report

## Summary

- **Total comparisons:** 9
- **Results matching:** 9/9
- **Conquer faster than baseline:** 8/9 (88.9%)

## Detailed Results

| Circuit 1 | Circuit 2 | depth | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |
|-----------|-----------|-------|----------|-------------|---------|------|-------|-------|-------|
| mul_dadda_8 | mul_default_8 | 1 | 7.0779 | **6.6755** | **✓** | 5.8518 | 12.5273 | 2 | ✓ |
| mul_dadda_8 | mul_default_8 | 2 | 7.0779 | **6.4352** | **✓** | 13.3301 | 19.7653 | 4 | ✓ |
| mul_dadda_8 | mul_default_8 | 5 | 7.0779 | **11.9356** |  | 119.3956 | 131.3312 | 32 | ✓ |
| mul_dadda_9 | mul_default_9 | 1 | 40.5922 | **34.5483** | **✓** | 9.6402 | 44.1884 | 2 | ✓ |
| mul_dadda_9 | mul_default_9 | 2 | 40.5922 | **28.1982** | **✓** | 18.2739 | 46.4721 | 4 | ✓ |
| mul_dadda_9 | mul_default_9 | 5 | 40.5922 | **24.4986** | **✓** | 149.7687 | 174.2673 | 32 | ✓ |
| mul_dadda_10 | mul_default_10 | 1 | 199.6915 | **158.9527** | **✓** | 9.6966 | 168.6493 | 2 | ✓ |
| mul_dadda_10 | mul_default_10 | 2 | 199.6915 | **149.0826** | **✓** | 24.5344 | 173.6170 | 4 | ✓ |
| mul_dadda_10 | mul_default_10 | 5 | 199.6915 | **105.1289** | **✓** | 208.6423 | 313.7712 | 32 | ✓ |

## Best Configurations

| max_depth | solver | Wins |
|-----------|--------|------|
| 1 | cadical195 | 3 |
| 2 | cadical195 | 3 |
| 5 | cadical195 | 2 |

## Speedup Analysis

- **Average conquer speedup (baseline/conquer):** 1.28x
- **Max conquer speedup:** 1.90x
- **Average total speedup (baseline/total):** 0.66x
- **Max total speedup:** 1.18x
