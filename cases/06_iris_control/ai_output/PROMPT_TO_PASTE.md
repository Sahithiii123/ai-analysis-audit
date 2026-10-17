# User request

For each iris species in this sample, summarize sepal and petal measurements with uncertainty intervals, compare the species descriptively, and state what these data do and do not support.

## Data file

The complete dataset is available at `data/raw/06_iris_control/data.csv`, relative to the project root. Please read the full file in your Python code; the sample below is only a preview. Measurement values are in centimeters.

## Data schema

| Column | Description |
|---|---|
| `sepal length` | Sepal length, centimeters. |
| `sepal width` | Sepal width, centimeters. |
| `petal length` | Petal length, centimeters. |
| `petal width` | Petal width, centimeters. |
| `class` | Iris species category: setosa, versicolor, or virginica. |

## 20-row random sample

This sample was drawn from the real file with pandas `sample(n=20, random_state=20261016)`.

```csv
sepal length,sepal width,petal length,petal width,class
6.2,2.9,4.3,1.3,Iris-versicolor
5.7,2.6,3.5,1.0,Iris-versicolor
6.3,3.4,5.6,2.4,Iris-virginica
6.7,3.3,5.7,2.5,Iris-virginica
5.5,2.4,3.7,1.0,Iris-versicolor
4.8,3.0,1.4,0.1,Iris-setosa
4.4,2.9,1.4,0.2,Iris-setosa
6.7,3.3,5.7,2.1,Iris-virginica
4.8,3.4,1.6,0.2,Iris-setosa
5.8,4.0,1.2,0.2,Iris-setosa
5.9,3.2,4.8,1.8,Iris-versicolor
5.2,4.1,1.5,0.1,Iris-setosa
4.9,3.1,1.5,0.1,Iris-setosa
5.5,2.6,4.4,1.2,Iris-versicolor
6.8,2.8,4.8,1.4,Iris-versicolor
5.8,2.7,3.9,1.2,Iris-versicolor
5.0,3.5,1.3,0.3,Iris-setosa
5.5,2.4,3.8,1.1,Iris-versicolor
6.0,2.9,4.5,1.5,Iris-versicolor
5.4,3.9,1.3,0.4,Iris-setosa
```

## Requested response

Please return exactly these three sections:

### Analysis plan

### Runnable Python code

Provide one Python code block that reads the complete CSV file from the path above and runs from the project root.

### Written conclusion