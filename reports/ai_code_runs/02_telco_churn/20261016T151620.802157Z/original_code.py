import numpy as np
import pandas as pd
from scipy.io import arff
from scipy.stats import chi2_contingency
from sklearn.feature_selection import mutual_info_classif
import statsmodels.formula.api as smf

# 1. load
raw, _ = arff.loadarff("data/raw/02_telco_churn/telco-customer-churn.arff")
df = pd.DataFrame(raw)
for c in df.select_dtypes(object):
    df[c] = df[c].str.decode("utf-8") if isinstance(df[c].iloc[0], bytes) else df[c]
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
df["SeniorCitizen"] = pd.to_numeric(df["SeniorCitizen"], errors="coerce")
df["y"] = (df["Churn"] == "Yes").astype(int)
print(df.shape, "| overall churn rate:", round(df.y.mean(), 3))

# 2. churn by contract
ct = pd.crosstab(df["Contract"], df["Churn"])
print("\nCounts:\n", ct)
print("\nChurn rate by contract:\n", df.groupby("Contract")["y"].agg(["mean", "size"]).round(3))

# 3. chi-square + Cramér's V
chi2, p, dof, _ = chi2_contingency(ct)
v = np.sqrt(chi2 / (ct.values.sum() * (min(ct.shape) - 1)))
print(f"\nChi2={chi2:.1f}, p={p:.2e}, Cramér's V={v:.3f}")

# 4. mutual information ranking
X = df.drop(columns=["customerID", "Churn", "y"]).copy()
X["TotalCharges"] = X["TotalCharges"].fillna(0)
cat_cols = X.select_dtypes(exclude="number").columns
for c in cat_cols:
    X[c] = X[c].astype("category").cat.codes
mi = mutual_info_classif(X, df["y"], discrete_features=[c in cat_cols for c in X.columns],
                         random_state=0)
print("\nMutual information with churn:\n",
      pd.Series(mi, index=X.columns).sort_values(ascending=False).round(4))

# 5. adjusted logistic regression
d = df.rename(columns={"PaymentMethod": "Pay", "InternetService": "Internet"}).copy()
d["TotalCharges"] = d["TotalCharges"].fillna(0)
model = smf.logit(
    "y ~ C(Contract, Treatment('Month-to-month')) + tenure + MonthlyCharges"
    " + C(Internet) + C(OnlineSecurity) + C(TechSupport) + C(Pay)"
    " + C(PaperlessBilling) + SeniorCitizen + C(Partner) + C(Dependents)",
    data=d,
).fit(disp=False)
res = pd.DataFrame({"odds_ratio": np.exp(model.params),
                    "ci_low": np.exp(model.conf_int()[0]),
                    "ci_high": np.exp(model.conf_int()[1]),
                    "p": model.pvalues}).round(3)
print("\nAdjusted logistic regression:\n", res)

# 6. contract vs tenure overlap
print("\nMedian tenure by contract:\n", df.groupby("Contract")["tenure"].median())