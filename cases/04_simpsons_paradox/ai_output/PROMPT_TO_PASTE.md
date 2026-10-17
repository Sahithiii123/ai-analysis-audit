# User request

How do admission rates differ by applicant gender overall and within departments in the 1973 Berkeley data?

## Data file

The complete dataset is available at `data/raw/04_simpsons_paradox/UCBAdmissions.csv`, relative to the project root. Please read the full file in your Python code; the sample below is only a preview.

## Data schema

| Column | Description |
|---|---|
| `rownames` | Source row label; it identifies a contingency-table cell. |
| `Admit` | Admission outcome (`Admitted` or `Rejected`). |
| `Gender` | Applicant gender category in the table. |
| `Dept` | Department label (`A` through `F`). |
| `Freq` | Number of applicants in the corresponding table cell. |

Each row is an aggregate cell, not an individual applicant record.

## 20-row random sample

This sample was drawn from the real file with pandas `sample(n=20, random_state=20261016)`.

```csv
rownames,Admit,Gender,Dept,Freq
15,Admitted,Female,D,131
17,Admitted,Male,E,53
3,Admitted,Female,A,89
7,Admitted,Female,B,17
24,Rejected,Female,F,317
21,Admitted,Male,F,22
16,Rejected,Female,D,244
10,Rejected,Male,C,205
19,Admitted,Female,E,94
1,Admitted,Male,A,512
6,Rejected,Male,B,207
2,Rejected,Male,A,313
4,Rejected,Female,A,19
13,Admitted,Male,D,138
23,Admitted,Female,F,24
9,Admitted,Male,C,120
8,Rejected,Female,B,8
14,Rejected,Male,D,279
18,Rejected,Male,E,138
20,Rejected,Female,E,299
```

## Requested response

Please return exactly these three sections:

### Analysis plan

### Runnable Python code

Provide one Python code block that reads the complete CSV file from the path above and runs from the project root.

### Written conclusion