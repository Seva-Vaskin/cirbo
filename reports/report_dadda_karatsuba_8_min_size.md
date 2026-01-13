# Miter Verification Experiment Report

## Summary

- **Total runs:** 9
- **Baseline timeouts:** 0
- **CnC timeouts:** 0
- **Results matching:** 9/9
- **Conquer faster than baseline:** 8/9 (88.9%)

## Detailed Results

| Miter | depth | min_size | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |
|-------|-------|----------|----------|-------------|---------|------|-------|-------|-------|
| mul_2_dadda_vs_karatsuba.aig | None | 20 | 0.0006 | **0.0004** | **✓** | 0.0064 | 0.0068 | 1 | ✓ |
| mul_2_dadda_vs_karatsuba.aig | None | 30 | 0.0006 | **0.0004** | **✓** | 0.0059 | 0.0063 | 1 | ✓ |
| mul_2_dadda_vs_karatsuba.aig | None | 40 | 0.0006 | **0.0004** | **✓** | 0.0054 | 0.0058 | 1 | ✓ |
| mul_3_dadda_vs_karatsuba.aig | None | 20 | 0.0021 | **0.0017** | **✓** | 0.0280 | 0.0297 | 1 | ✓ |
| mul_3_dadda_vs_karatsuba.aig | None | 30 | 0.0021 | **0.0017** | **✓** | 0.0268 | 0.0285 | 1 | ✓ |
| mul_3_dadda_vs_karatsuba.aig | None | 40 | 0.0021 | **0.0017** | **✓** | 0.0312 | 0.0329 | 1 | ✓ |
| mul_4_dadda_vs_karatsuba.aig | None | 20 | 0.0111 | **0.0131** |  | 0.1765 | 0.1896 | 1 | ✓ |
| mul_4_dadda_vs_karatsuba.aig | None | 30 | 0.0111 | **0.0105** | **✓** | 0.1060 | 0.1165 | 1 | ✓ |
| mul_4_dadda_vs_karatsuba.aig | None | 40 | 0.0111 | **0.0109** | **✓** | 0.0857 | 0.0966 | 1 | ✓ |

## Speedup Analysis

- **Average conquer speedup (baseline/conquer):** 1.22x
- **Max conquer speedup:** 1.49x
- **Average total speedup (baseline/total):** 0.08x
- **Max total speedup:** 0.12x
