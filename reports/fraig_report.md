# FRAIG Transformation Experiment Report

## Summary

- **Total miter circuits processed:** 18
- **Total original gates:** 73620
- **Total updated gates:** 51467
- **Total reduction:** 22153 gates (30.1%)
- **Total operation time:** 4.3605s

## Detailed Results

| Name 1 | Name 2 | Size | Original Size | Updated Size | Reduction | Reduction % | Time (s) |
|--------|--------|------|---------------|--------------|-----------|-------------|----------|
| mul_karatsuba | mul_dadda | 8 | 3287 | 2389 | 898 | 27.3% | 0.1039 |
| mul_karatsuba | mul_wallace | 8 | 2968 | 1928 | 1040 | 35.0% | 0.3005 |
| mul_karatsuba | mul_default | 8 | 3086 | 2088 | 998 | 32.3% | 0.2086 |
| mul_dadda | mul_wallace | 8 | 3169 | 2089 | 1080 | 34.1% | 0.0831 |
| mul_dadda | mul_default | 8 | 3287 | 2418 | 869 | 26.4% | 0.0746 |
| mul_wallace | mul_default | 8 | 2968 | 1918 | 1050 | 35.4% | 0.2954 |
| mul_karatsuba | mul_dadda | 9 | 4255 | 3183 | 1072 | 25.2% | 0.0907 |
| mul_karatsuba | mul_wallace | 9 | 3853 | 2557 | 1296 | 33.6% | 0.3779 |
| mul_karatsuba | mul_default | 9 | 3992 | 2823 | 1169 | 29.3% | 0.2849 |
| mul_dadda | mul_wallace | 9 | 4116 | 2689 | 1427 | 34.7% | 0.0904 |
| mul_dadda | mul_default | 9 | 4255 | 3203 | 1052 | 24.7% | 0.0923 |
| mul_wallace | mul_default | 9 | 3853 | 2505 | 1348 | 35.0% | 0.4038 |
| mul_karatsuba | mul_dadda | 10 | 5339 | 4019 | 1320 | 24.7% | 0.1248 |
| mul_karatsuba | mul_wallace | 10 | 4838 | 3261 | 1577 | 32.6% | 0.6643 |
| mul_karatsuba | mul_default | 10 | 4998 | 3584 | 1414 | 28.3% | 0.4705 |
| mul_dadda | mul_wallace | 10 | 5179 | 3500 | 1679 | 32.4% | 0.1068 |
| mul_dadda | mul_default | 10 | 5339 | 4065 | 1274 | 23.9% | 0.1040 |
| mul_wallace | mul_default | 10 | 4838 | 3248 | 1590 | 32.9% | 0.4840 |

## Results by Size

### Size 8

- Pairs processed: 6
- Average original size: 3128
- Average updated size: 2138
- Average reduction: 31.6%
- Total time: 1.0660s

### Size 9

- Pairs processed: 6
- Average original size: 4054
- Average updated size: 2827
- Average reduction: 30.3%
- Total time: 1.3401s

### Size 10

- Pairs processed: 6
- Average original size: 5088
- Average updated size: 3613
- Average reduction: 29.0%
- Total time: 1.9544s

