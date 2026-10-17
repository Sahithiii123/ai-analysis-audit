# User request

What drives customer churn? Which factors are most associated with churn, and what can this dataset establish about contract type?

## Data file

The complete dataset is available at `data/raw/02_telco_churn/telco-customer-churn.arff`, relative to the project root. Please read the full ARFF file in your Python code; the sample below is only a preview. The sample values retain the single-quote notation used in the ARFF data section.

## Data schema

| Column | Description |
|---|---|
| `customerID` | Customer identifier. |
| `gender` | Recorded gender category. |
| `SeniorCitizen` | Senior-citizen indicator. |
| `Partner` | Whether a partner is recorded. |
| `Dependents` | Whether dependents are recorded. |
| `tenure` | Number of months the customer has stayed with the service. |
| `PhoneService` | Whether phone service is subscribed to. |
| `MultipleLines` | Multiple-lines service category. |
| `InternetService` | Internet service category. |
| `OnlineSecurity` | Online-security service category. |
| `OnlineBackup` | Online-backup service category. |
| `DeviceProtection` | Device-protection service category. |
| `TechSupport` | Technical-support service category. |
| `StreamingTV` | Streaming-TV service category. |
| `StreamingMovies` | Streaming-movies service category. |
| `Contract` | Recorded contract category. |
| `PaperlessBilling` | Whether paperless billing is enabled. |
| `PaymentMethod` | Recorded payment method. |
| `MonthlyCharges` | Monthly charges. |
| `TotalCharges` | Total charges recorded to date. |
| `Churn` | Whether the customer left (`Yes` or `No`). |

## 20-row random sample

This sample was drawn from the real file with pandas `sample(n=20, random_state=20261016)`.

```csv
customerID,gender,SeniorCitizen,Partner,Dependents,tenure,PhoneService,MultipleLines,InternetService,OnlineSecurity,OnlineBackup,DeviceProtection,TechSupport,StreamingTV,StreamingMovies,Contract,PaperlessBilling,PaymentMethod,MonthlyCharges,TotalCharges,Churn
9030-QGZNL,Female,0,No,No,8,Yes,No,No,'No internet service','No internet service','No internet service','No internet service','No internet service','No internet service','Two year',No,'Mailed check',20.85,161.65,No
4119-ZYPZY,Male,1,No,No,71,Yes,Yes,'Fiber optic',No,Yes,No,Yes,Yes,Yes,'Two year',Yes,'Electronic check',106.8,7623.2,No
4234-XTNEA,Male,0,No,No,2,Yes,No,'Fiber optic',No,No,No,No,Yes,No,Month-to-month,Yes,'Electronic check',79.95,174.45,No
8468-FZTOE,Female,0,Yes,Yes,72,Yes,No,DSL,Yes,Yes,Yes,Yes,No,Yes,'Two year',Yes,'Electronic check',74.35,5237.4,No
0207-MDKNV,Female,0,No,No,15,Yes,No,'Fiber optic',Yes,No,Yes,Yes,Yes,Yes,Month-to-month,No,'Electronic check',105.1,1582.75,Yes
2958-NHPPS,Male,0,No,No,23,Yes,No,No,'No internet service','No internet service','No internet service','No internet service','No internet service','No internet service',Month-to-month,No,'Electronic check',20.85,473.9,No
1684-FLBGS,Female,0,Yes,Yes,23,Yes,Yes,DSL,No,Yes,No,Yes,Yes,No,Month-to-month,Yes,'Credit card (automatic)',69.5,1652.1,No
2887-JPYLU,Female,0,No,Yes,41,Yes,No,DSL,No,No,No,No,No,No,Month-to-month,No,'Bank transfer (automatic)',45.2,1841.9,No
4611-ANLQC,Female,0,Yes,No,60,No,'No phone service',DSL,Yes,Yes,Yes,No,No,Yes,'One year',No,'Electronic check',50.05,2911.5,No
3900-AQPHZ,Female,0,No,No,1,Yes,No,No,'No internet service','No internet service','No internet service','No internet service','No internet service','No internet service',Month-to-month,No,'Mailed check',19.9,19.9,Yes
1271-UODNO,Male,0,No,No,39,Yes,Yes,DSL,No,No,No,Yes,No,No,'Two year',Yes,'Credit card (automatic)',53.85,2200.7,No
2839-RFSQE,Female,0,No,No,2,Yes,No,No,'No internet service','No internet service','No internet service','No internet service','No internet service','No internet service',Month-to-month,No,'Mailed check',20.65,38.7,Yes
2242-MFOTG,Male,0,No,No,33,Yes,Yes,'Fiber optic',Yes,No,No,No,No,No,'One year',No,'Bank transfer (automatic)',80.1,2603.3,No
8788-DOXSU,Male,0,No,No,59,Yes,No,DSL,No,No,Yes,No,No,Yes,'One year',Yes,'Bank transfer (automatic)',61.35,3645.5,No
5902-WBLSE,Female,0,Yes,Yes,70,Yes,No,No,'No internet service','No internet service','No internet service','No internet service','No internet service','No internet service','Two year',Yes,'Credit card (automatic)',20.15,1411.2,No
9174-FKWZE,Female,1,No,No,1,Yes,No,No,'No internet service','No internet service','No internet service','No internet service','No internet service','No internet service',Month-to-month,Yes,'Electronic check',19.45,19.45,Yes
9467-ROOLM,Female,0,No,No,25,Yes,No,No,'No internet service','No internet service','No internet service','No internet service','No internet service','No internet service',Month-to-month,No,'Mailed check',19.05,461.3,No
9931-DCEZH,Male,0,No,Yes,28,Yes,No,DSL,No,Yes,No,Yes,No,No,'One year',Yes,'Credit card (automatic)',54.4,1516.6,No
4193-ORFCL,Female,1,No,No,1,Yes,No,DSL,No,No,No,No,No,No,Month-to-month,No,'Mailed check',45.1,45.1,Yes
4837-PZTIC,Female,0,No,No,47,No,'No phone service',DSL,Yes,No,Yes,Yes,No,No,'Two year',No,'Mailed check',41.9,1875.25,No
```

## Requested response

Please return exactly these three sections:

### Analysis plan

### Runnable Python code

Read the full ARFF file from the path above, not just the sample. Provide one Python code block that runs from the project root.

### Written conclusion