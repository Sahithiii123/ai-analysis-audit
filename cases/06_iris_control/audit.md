# Case 06 audit: Iris control

**Verdict: Reliable**

## Reproduction and data checks

The saved AI code exited 0 and reported 150 rows. Independent checks confirm 150 rows, three species with 50 observations each, 3 exact duplicate rows, no missing values, and no nonpositive measurements. Duplicate rows were retained because identical rounded measurements alone do not establish repeated specimens.
All 12 species-by-measure means agree with the blind reference to 0 cm maximum absolute difference; the largest t-interval endpoint difference is 0 cm.

## Species means and uncertainty

| Species | Measurement | n | Mean (cm) | 95% t CI | 95% bootstrap CI |
|---|---|---:|---:|---:|---:|
| Iris-setosa | sepal length | 50 | 5.006 | 4.906 to 5.106 | 4.908 to 5.100 |
| Iris-setosa | sepal width | 50 | 3.418 | 3.310 to 3.526 | 3.314 to 3.522 |
| Iris-setosa | petal length | 50 | 1.464 | 1.415 to 1.513 | 1.416 to 1.512 |
| Iris-setosa | petal width | 50 | 0.244 | 0.214 to 0.274 | 0.216 to 0.274 |
| Iris-versicolor | sepal length | 50 | 5.936 | 5.789 to 6.083 | 5.798 to 6.078 |
| Iris-versicolor | sepal width | 50 | 2.770 | 2.681 to 2.859 | 2.680 to 2.854 |
| Iris-versicolor | petal length | 50 | 4.260 | 4.126 to 4.394 | 4.124 to 4.386 |
| Iris-versicolor | petal width | 50 | 1.326 | 1.270 to 1.382 | 1.274 to 1.382 |
| Iris-virginica | sepal length | 50 | 6.588 | 6.407 to 6.769 | 6.416 to 6.766 |
| Iris-virginica | sepal width | 50 | 2.974 | 2.882 to 3.066 | 2.886 to 3.064 |
| Iris-virginica | petal length | 50 | 5.552 | 5.395 to 5.709 | 5.402 to 5.706 |
| Iris-virginica | petal width | 50 | 2.026 | 1.948 to 2.104 | 1.950 to 2.102 |

## Descriptive contrasts and observed ranges

The AI's mean-difference bootstrap intervals are pointwise 95% intervals across 12 pairwise comparisons, not simultaneous intervals. They are descriptive and do not replace a prespecified inferential analysis or adjust familywise error.

| Measurement | Contrast (first - second) | Mean difference (cm) | Pointwise 95% bootstrap CI | Cohen's d |
|---|---|---:|---:|---:|
| sepal length | Iris-setosa - Iris-versicolor | -0.930 | -1.098 to -0.758 | -2.10 |
| sepal length | Iris-setosa - Iris-virginica | -1.582 | -1.788 to -1.382 | -3.08 |
| sepal length | Iris-versicolor - Iris-virginica | -0.652 | -0.876 to -0.428 | -1.13 |
| sepal width | Iris-setosa - Iris-versicolor | +0.648 | +0.516 to +0.780 | +1.86 |
| sepal width | Iris-setosa - Iris-virginica | +0.444 | +0.306 to +0.578 | +1.26 |
| sepal width | Iris-versicolor - Iris-virginica | -0.204 | -0.328 to -0.078 | -0.64 |
| petal length | Iris-setosa - Iris-versicolor | -2.796 | -2.930 to -2.654 | -7.89 |
| petal length | Iris-setosa - Iris-virginica | -4.088 | -4.248 to -3.936 | -9.99 |
| petal length | Iris-versicolor - Iris-virginica | -1.292 | -1.490 to -1.096 | -2.52 |
| petal width | Iris-setosa - Iris-versicolor | -1.082 | -1.144 to -1.020 | -6.80 |
| petal width | Iris-setosa - Iris-virginica | -1.782 | -1.860 to -1.702 | -8.55 |
| petal width | Iris-versicolor - Iris-virginica | -0.700 | -0.790 to -0.608 | -2.93 |

| Measurement | Species pair | First range (cm) | Second range (cm) | Observed overlap |
|---|---|---:|---:|---|
| sepal length | Iris-setosa - Iris-versicolor | 4.3 to 5.8 | 4.9 to 7.0 | 0.9 cm |
| sepal length | Iris-setosa - Iris-virginica | 4.3 to 5.8 | 4.9 to 7.9 | 0.9 cm |
| sepal length | Iris-versicolor - Iris-virginica | 4.9 to 7.0 | 4.9 to 7.9 | 2.1 cm |
| sepal width | Iris-setosa - Iris-versicolor | 2.3 to 4.4 | 2.0 to 3.4 | 1.1 cm |
| sepal width | Iris-setosa - Iris-virginica | 2.3 to 4.4 | 2.2 to 3.8 | 1.5 cm |
| sepal width | Iris-versicolor - Iris-virginica | 2.0 to 3.4 | 2.2 to 3.8 | 1.2 cm |
| petal length | Iris-setosa - Iris-versicolor | 1.0 to 1.9 | 3.0 to 5.1 | none |
| petal length | Iris-setosa - Iris-virginica | 1.0 to 1.9 | 4.5 to 6.9 | none |
| petal length | Iris-versicolor - Iris-virginica | 3.0 to 5.1 | 4.5 to 6.9 | 0.6 cm |
| petal width | Iris-setosa - Iris-versicolor | 0.1 to 0.6 | 1.0 to 1.8 | none |
| petal width | Iris-setosa - Iris-virginica | 0.1 to 0.6 | 1.4 to 2.5 | none |
| petal width | Iris-versicolor - Iris-virginica | 1.0 to 1.8 | 1.4 to 2.5 | 0.4 cm |

## Assessment and limits

The descriptive claims reproduce: setosa has shorter, wider sepals on average and markedly smaller petals; virginica has higher means than versicolor on all four measurements. Observed petal ranges for setosa do not overlap either other species, while versicolor and virginica overlap on petal measurements. This supports a descriptive statement about separation in this sample, not validated classification.
The t and bootstrap intervals are uncertainty intervals for species means under row-resampling/independence assumptions. They are not individual-flower prediction intervals. Sampling provenance is not sufficient to generalize these results to all iris populations or infer biological causes.

No material numerical or interpretive error was reproduced. The response appropriately avoids causal, population-wide, and classifier-performance claims.
