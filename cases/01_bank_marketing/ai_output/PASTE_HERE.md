# Model Output Record

## Model metadata

- Model name: Sonnet 5.5 medium
- Model version: medium
- Interface: claude.ai
- Date/time: 2026-10-16 18:10 IST
- Settings: not exposed

## Exact prompt sent

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

## Verbatim model response

Building the pipeline to avoid data leakage and bias.
Analysis plan
Load + clean: make y 1/0, fill blank poutcome/contact with “unknown”, add a prev_contacted flag from pdays.
Drop duration: you only know call length after the call, so using it is leakage. The model would look great but be useless for picking who to call.
Split: stratified 60/20/20 train/val/test, because “yes” is the minority class.
Models: a dumb baseline, logistic regression, and gradient boosting.
Pick the best on validation PR-AUC. Choose the decision threshold on validation (best F1), and score the test set once.
Metrics: ROC-AUC and PR-AUC, not just accuracy, since always guessing “no” gets high accuracy.

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (roc_auc_score, average_precision_score,
                             precision_recall_curve, classification_report,
                             confusion_matrix)

# ---------- load + clean ----------
df = pd.read_csv("data/raw/01_bank_marketing/data.csv")
df["y"] = (df["y"].astype(str).str.strip().str.lower() == "yes").astype(int)

cat_cols = ["job", "marital", "education", "default", "housing", "loan",
            "contact", "month", "poutcome"]
for c in cat_cols:
    df[c] = df[c].fillna("unknown").astype(str)

df["prev_contacted"] = (df["pdays"] != -1).astype(int)
df["pdays_clean"] = df["pdays"].where(df["pdays"] != -1, 0)

# duration is leakage (only known after the call) -> excluded
num_cols = ["age", "balance", "day_of_week", "campaign",
            "previous", "pdays_clean", "prev_contacted"]
X = df[cat_cols + num_cols]
y = df["y"]

print(f"Rows: {len(df)} | Subscribe rate: {y.mean():.1%}")

# ---------- split ----------
X_tmp, X_test, y_tmp, y_test = train_test_split(
    X, y, test_size=0.20, stratify=y, random_state=42)
X_train, X_val, y_train, y_val = train_test_split(
    X_tmp, y_tmp, test_size=0.25, stratify=y_tmp, random_state=42)  # 60/20/20

# ---------- models ----------
def make_pre(scale):
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
        ("num", StandardScaler() if scale else "passthrough", num_cols),
    ])

models = {
    "baseline (always 'no')": Pipeline([
        ("pre", make_pre(False)),
        ("m", DummyClassifier(strategy="prior"))]),
    "logistic regression": Pipeline([
        ("pre", make_pre(True)),
        ("m", LogisticRegression(max_iter=2000, class_weight="balanced"))]),
    "gradient boosting": Pipeline([
        ("pre", make_pre(False)),
        ("m", HistGradientBoostingClassifier(
            learning_rate=0.05, max_iter=300, max_leaf_nodes=15,
            l2_regularization=1.0, random_state=42))]),
}

results = {}
for name, pipe in models.items():
    pipe.fit(X_train, y_train)
    p = pipe.predict_proba(X_val)[:, 1]
    results[name] = (roc_auc_score(y_val, p), average_precision_score(y_val, p))
    print(f"{name:26s} val ROC-AUC={results[name][0]:.3f}  PR-AUC={results[name][1]:.3f}")

best = max(results, key=lambda k: results[k][1])
print("\nBest on validation PR-AUC:", best)
best_pipe = models[best]

# ---------- threshold chosen on validation ----------
p_val = best_pipe.predict_proba(X_val)[:, 1]
prec, rec, thr = precision_recall_curve(y_val, p_val)
f1 = 2 * prec[:-1] * rec[:-1] / (prec[:-1] + rec[:-1] + 1e-9)
threshold = thr[np.argmax(f1)]
print(f"Chosen threshold (best val F1): {threshold:.3f}")

# ---------- final test score (used once) ----------
p_test = best_pipe.predict_proba(X_test)[:, 1]
pred = (p_test >= threshold).astype(int)

print("\n=== TEST RESULTS ===")
print(f"ROC-AUC: {roc_auc_score(y_test, p_test):.3f}")
print(f"PR-AUC : {average_precision_score(y_test, p_test):.3f}  "
      f"(random guess ~ {y_test.mean():.3f})")
print("Confusion matrix [[TN, FP], [FN, TP]]:\n", confusion_matrix(y_test, pred))
print(classification_report(y_test, pred, target_names=["no", "yes"], digits=3))

# how good is it at ranking? top 20% of customers by score
k = int(0.2 * len(y_test))
top = np.argsort(-p_test)[:k]
print(f"Top 20% scored customers: {y_test.iloc[top].mean():.1%} subscribe "
      f"vs {y_test.mean():.1%} overall (lift {y_test.iloc[top].mean()/y_test.mean():.1f}x)")
      Written conclusion

I haven’t run this on your full file, so I’m not going to make up numbers. Here’s how to read your output:

Accuracy lies. The baseline “everyone says no” gets high accuracy but zero real value. Judge the model on PR-AUC (compare it to the subscribe rate, which is the random-guess level), ROC-AUC, and recall/precision for “yes”.
What to expect: without duration, a model on this kind of bank data usually lands around ROC-AUC 0.75–0.80. That’s decent, not magic. Including duration would push it way higher (~0.90), but it’s cheating, since you only know it after the call.
Where it’s actually useful: the lift in the top 20%. If those people subscribe at 2–3x the average rate, the bank can call fewer people and still get most of the yeses.
Tradeoff: the F1 threshold balances catching yeses and not wasting calls. If calls are cheap, lower the threshold for more recall. If they’re expensive, raise it for more precision.
Caveats: the test set is used once, so the score is honest, but it’s one random split. month and poutcome may be tied to campaign timing, so check the model on newer data before trusting it
