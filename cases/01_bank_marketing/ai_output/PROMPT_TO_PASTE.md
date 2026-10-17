# User request

Build a model to predict which customers will subscribe to a term deposit and tell me how good it is.

## Data file

The complete dataset is available at `data/raw/01_bank_marketing/data.csv`, relative to the project root. Please read the full file in your Python code; the sample below is only a preview.

## Data schema

| Column | Description |
|---|---|
| `age` | Customer age in years. |
| `job` | Customer occupation category. |
| `marital` | Marital-status category. |
| `education` | Education category. |
| `default` | Whether credit in default is recorded. |
| `balance` | Average yearly account balance. |
| `housing` | Whether a housing loan is recorded. |
| `loan` | Whether a personal loan is recorded. |
| `contact` | Contact communication channel. |
| `day_of_week` | Day value recorded for the last contact. |
| `month` | Month of the last contact. |
| `duration` | Duration of the last contact, in seconds. |
| `campaign` | Number of contacts in the current campaign for this customer, including the last contact. |
| `pdays` | Days since a previous-campaign contact; `-1` means no previous contact. |
| `previous` | Number of contacts before the current campaign. |
| `poutcome` | Recorded outcome of the previous campaign. |
| `y` | Whether the customer subscribed to a term deposit (`yes` or `no`). |

## 20-row random sample

This sample was drawn from the real file with pandas `sample(n=20, random_state=20261016)`.

```csv
age,job,marital,education,default,balance,housing,loan,contact,day_of_week,month,duration,campaign,pdays,previous,poutcome,y
36,technician,married,tertiary,no,341,no,no,cellular,12,feb,419,2,183,1,success,yes
50,management,married,tertiary,no,5108,yes,no,cellular,18,dec,406,1,182,2,failure,yes
42,management,divorced,secondary,no,284,no,no,cellular,25,jul,1173,4,-1,0,,no
27,blue-collar,married,secondary,no,72,yes,no,,19,may,105,1,-1,0,,no
33,management,married,tertiary,no,415,no,no,cellular,4,may,75,5,167,1,other,no
39,management,married,tertiary,no,-233,yes,no,cellular,19,nov,249,1,-1,0,,no
24,admin.,married,secondary,no,541,yes,no,,5,jun,622,4,-1,0,,no
35,entrepreneur,married,tertiary,no,355,yes,no,cellular,6,may,183,2,355,1,failure,no
31,blue-collar,single,secondary,no,1979,yes,yes,cellular,6,may,1205,1,-1,0,,yes
51,technician,married,tertiary,no,1537,no,yes,cellular,14,jul,400,3,-1,0,,no
42,technician,married,secondary,no,27,no,no,cellular,14,aug,259,4,-1,0,,no
53,management,married,tertiary,no,-670,no,yes,cellular,11,jul,86,2,-1,0,,no
37,admin.,married,secondary,no,0,yes,no,cellular,14,jul,235,3,-1,0,,no
50,blue-collar,married,primary,no,0,yes,no,cellular,23,jul,137,1,-1,0,,no
54,retired,married,primary,no,11,yes,yes,cellular,18,aug,48,10,-1,0,,no
36,services,divorced,secondary,no,543,yes,no,cellular,17,apr,101,1,269,2,failure,no
38,admin.,divorced,secondary,no,673,yes,no,cellular,7,may,429,1,170,3,other,no
33,management,married,tertiary,no,644,no,no,cellular,11,aug,99,2,-1,0,,no
38,management,married,tertiary,no,2278,yes,yes,cellular,13,may,244,1,-1,0,,no
42,management,married,tertiary,no,144,no,no,cellular,4,mar,148,1,87,4,failure,yes
```

## Requested response

Please return exactly these three sections:

### Analysis plan

### Runnable Python code

Provide one Python code block that reads the complete dataset from the path above and can run from the project root.

### Written conclusion