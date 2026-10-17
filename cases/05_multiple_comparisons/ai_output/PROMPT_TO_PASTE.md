# User request

Which recorded characteristics are associated with income above $50,000 in this dataset?

## Data file

The complete dataset is available at `data/raw/05_multiple_comparisons/adult.arff`, relative to the project root. Please read the full ARFF file in your Python code; the sample below is only a preview.

## Data schema

| Column | Description |
|---|---|
| `age` | Age in years. |
| `workclass` | Employment sector/category. |
| `fnlwgt` | Census sampling weight included with each record. |
| `education` | Highest recorded education category. |
| `education-num` | Numeric coding associated with education level. |
| `marital-status` | Recorded marital-status category. |
| `occupation` | Recorded occupation category. |
| `relationship` | Household relationship category. |
| `race` | Recorded race category. |
| `sex` | Recorded sex category. |
| `capital-gain` | Capital-gain amount. |
| `capital-loss` | Capital-loss amount. |
| `hours-per-week` | Hours worked per week. |
| `native-country` | Recorded country-of-origin category. |
| `class` | Income category (`>50K` or `<=50K`). |

## 20-row random sample

This sample was drawn from the real file with pandas `sample(n=20, random_state=20261016)`.

```csv
age,workclass,fnlwgt,education,education-num,marital-status,occupation,relationship,race,sex,capital-gain,capital-loss,hours-per-week,native-country,class
29, Private, 233168, Bachelors, 13, Married-civ-spouse, Prof-specialty, Wife, White, Female, 0, 0, 46, United-States, >50K
22, Private, 60668, Some-college, 10, Never-married, Craft-repair, Not-in-family, White, Male, 0, 0, 40, United-States, <=50K
28, Private, 152951, HS-grad, 9, Divorced, Handlers-cleaners, Not-in-family, White, Male, 0, 0, 40, United-States, <=50K
21, ?, 120998, Some-college, 10, Never-married, ?, Own-child, White, Male, 0, 0, 40, United-States, <=50K
68, Private, 107910, HS-grad, 9, Never-married, Sales, Not-in-family, White, Female, 0, 0, 40, United-States, <=50K
22, Private, 205970, 10th, 6, Separated, Other-service, Unmarried, White, Female, 0, 0, 35, United-States, <=50K
40, Private, 140559, HS-grad, 9, Widowed, Other-service, Unmarried, White, Female, 0, 0, 25, United-States, <=50K
46, Local-gov, 170092, Masters, 14, Never-married, Prof-specialty, Not-in-family, White, Female, 0, 0, 43, United-States, <=50K
37, Private, 163199, Some-college, 10, Divorced, Tech-support, Not-in-family, Amer-Indian-Eskimo, Female, 0, 0, 40, United-States, <=50K
24, Private, 283092, HS-grad, 9, Never-married, Adm-clerical, Other-relative, Black, Male, 0, 0, 40, Jamaica, <=50K
45, State-gov, 112761, Some-college, 10, Divorced, Adm-clerical, Not-in-family, White, Female, 0, 0, 45, United-States, <=50K
43, Local-gov, 188280, Masters, 14, Divorced, Prof-specialty, Unmarried, White, Female, 914, 0, 40, United-States, <=50K
33, Private, 144064, Bachelors, 13, Married-civ-spouse, Exec-managerial, Husband, White, Male, 0, 0, 50, United-States, <=50K
26, Private, 219815, Some-college, 10, Married-spouse-absent, Adm-clerical, Unmarried, White, Female, 0, 0, 40, United-States, <=50K
51, Private, 190762, 1st-4th, 2, Widowed, Craft-repair, Not-in-family, White, Male, 0, 0, 40, Mexico, <=50K
24, Private, 279175, HS-grad, 9, Married-civ-spouse, Craft-repair, Husband, White, Male, 0, 0, 40, United-States, <=50K
19, Private, 197377, Some-college, 10, Never-married, Adm-clerical, Own-child, Black, Male, 0, 0, 20, United-States, <=50K
30, Private, 144949, Bachelors, 13, Never-married, Adm-clerical, Own-child, White, Male, 0, 2559, 40, United-States, >50K
47, Private, 223342, HS-grad, 9, Divorced, Adm-clerical, Unmarried, White, Female, 0, 1504, 35, United-States, <=50K
49, Private, 94342, Bachelors, 13, Married-civ-spouse, Craft-repair, Husband, White, Male, 0, 0, 60, United-States, <=50K
```

## Requested response

Please return exactly these three sections:

### Analysis plan

### Runnable Python code

Read the full ARFF file from the path above, not just the sample. Provide one Python code block that runs from the project root.

### Written conclusion