# Circuit Verification Experiment Report

## Summary

- **Total runs:** 9
- **Baseline timeouts:** 0
- **CnC timeouts:** 0
- **Results matching:** 9/9
- **Conquer faster than baseline:** 1/9 (11.1%)

## Detailed Results

| Circuit 1 | Circuit 2 | depth | Baseline | **Conquer** | Faster? | Cube | Total | Cubes | Match |
|-----------|-----------|-------|----------|-------------|---------|------|-------|-------|-------|
| mul_dadda_4 | mul_karatsuba_4 | 1 | 0.0193 | **0.0180** | **✓** | 0.4094 | 0.4274 | 2 | ✓ |
| mul_dadda_4 | mul_karatsuba_4 | 2 | 0.0193 | **0.0231** |  | 0.9640 | 0.9871 | 4 | ✓ |
| mul_dadda_4 | mul_karatsuba_4 | 5 | 0.0193 | **0.1223** |  | 6.0663 | 6.1886 | 32 | ✓ |
| mul_dadda_5 | mul_karatsuba_5 | 1 | 0.0835 | **0.0914** |  | 0.8853 | 0.9767 | 2 | ✓ |
| mul_dadda_5 | mul_karatsuba_5 | 2 | 0.0835 | **0.0991** |  | 2.0628 | 2.1619 | 4 | ✓ |
| mul_dadda_5 | mul_karatsuba_5 | 5 | 0.0835 | **0.2757** |  | 15.7880 | 16.0637 | 32 | ✓ |
| mul_dadda_6 | mul_karatsuba_6 | 1 | 0.2485 | **0.3235** |  | 1.7147 | 2.0382 | 2 | ✓ |
| mul_dadda_6 | mul_karatsuba_6 | 2 | 0.2485 | **0.4374** |  | 3.9100 | 4.3475 | 4 | ✓ |
| mul_dadda_6 | mul_karatsuba_6 | 5 | 0.2485 | **0.8837** |  | 32.9688 | 33.8525 | 32 | ✓ |

## Speedup Analysis

- **Average conquer speedup (baseline/conquer):** 0.64x
- **Max conquer speedup:** 1.07x
- **Average total speedup (baseline/total):** 0.04x
- **Max total speedup:** 0.12x
