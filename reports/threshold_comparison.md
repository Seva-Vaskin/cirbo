# Miter Verification Experiment Report

## Summary

- **Total runs:** 6
- **Baseline timeouts:** 0
- **CnC timeouts:** 0
- **Results matching:** 6/6
- **Conquer faster than baseline:** 2/6 (33.3%)

## Detailed Results

| Miter | depth | min_size | candidates | threshold | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |
|-------|-------|----------|------------|-----------|----------|-------------|---------|------|-------|-------|-------|
| mul_9_dadda_vs_karatsuba.aig | None | 1 | 10 | 30.0 | 32.4667 | **26.1332** | **✓** | 2.2251 | 28.3582 | 6 | ✓ |
| mul_9_dadda_vs_karatsuba.aig | None | 1 | 10 | 32.0 | 32.4667 | **26.8567** | **✓** | 2.2329 | 29.0896 | 6 | ✓ |
| mul_9_dadda_vs_karatsuba.aig | None | 1 | 10 | 34.0 | 32.4667 | **34.5851** |  | 0.0345 | 34.6196 | 1 | ✓ |
| mul_9_dadda_vs_karatsuba.aig | None | 1 | 10 | 36.0 | 32.4667 | **35.5494** |  | 0.0719 | 35.6213 | 1 | ✓ |
| mul_9_dadda_vs_karatsuba.aig | None | 1 | 10 | 38.0 | 32.4667 | **35.1255** |  | 0.0350 | 35.1605 | 1 | ✓ |
| mul_9_dadda_vs_karatsuba.aig | None | 1 | 10 | 40.0 | 32.4667 | **35.0281** |  | 0.0503 | 35.0785 | 1 | ✓ |

## Speedup Analysis

- **Average conquer speedup (baseline/conquer):** 1.03x
- **Max conquer speedup:** 1.24x
- **Average total speedup (baseline/total):** 0.99x
- **Max total speedup:** 1.14x
