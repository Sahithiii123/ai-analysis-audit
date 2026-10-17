import numpy as np
import pandas as pd
from scipy.io import arff
from scipy import stats
from statsmodels.stats.multitest import multipletests
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score

path = "data/raw/05_multiple_comparisons/adult.arff"
data, meta = arff.loadarff(path)
df = pd.DataFrame(data)
for c in df.columns:
    if df[c].dtype == object:
        df[c] = df[c].apply(lambda x: x.decode() if isinstance(x, bytes) else x).str.strip()
df = df.replace("?", "Missing")
df["y"] = (df["class"] == ">50K").astype(int)
print("rows:", len(df), "| share >50K: %.3f" % df["y"].mean())

num_cols = ["age", "fnlwgt", "education-num", "capital-gain", "capital-loss", "hours-per-week"]
cat_cols = ["workclass", "education", "marital-status", "occupation",
            "relationship", "race", "sex", "native-country"]

rows = []
for c in num_cols:
    a = df.loc[df.y == 1, c]; b = df.loc[df.y == 0, c]
    u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    auc = u / (len(a) * len(b))          # P(high-income value > low-income value)
    rows.append((c, "numeric", p, abs(auc - 0.5) * 2, f"AUC={auc:.3f}, median {a.median():.0f} vs {b.median():.0f}"))

for c in cat_cols:
    ct = pd.crosstab(df[c], df["y"])
    chi2, p, _, _ = stats.chi2_contingency(ct)
    v = np.sqrt(chi2 / (ct.values.sum() * (min(ct.shape) - 1)))
    top = (df.groupby(c)["y"].mean().sort_values(ascending=False))
    rows.append((c, "categorical", p, v, f"highest: {top.index[0]} ({top.iloc[0]:.2f}); lowest: {top.index[-1]} ({top.iloc[-1]:.2f})"))

res = pd.DataFrame(rows, columns=["feature", "type", "p", "effect", "note"])
res["p_bh"] = multipletests(res.p, method="fdr_bh")[1]
res["p_bonf"] = multipletests(res.p, method="bonferroni")[1]
res = res.sort_values("effect", ascending=False)
pd.set_option("display.width", 200, "display.max_colwidth", 80)
print(res.to_string(index=False, float_format=lambda x: f"{x:.3g}"))

# Multivariable check (drop redundant 'education'; fnlwgt is a sampling weight)
X = df.drop(columns=["class", "y", "education", "fnlwgt"])
y = df["y"]
num_m = ["age", "education-num", "capital-gain", "capital-loss", "hours-per-week"]
cat_m = [c for c in cat_cols if c != "education"]
X = X.copy()
X["capital-gain"] = np.log1p(X["capital-gain"])
X["capital-loss"] = np.log1p(X["capital-loss"])

pre = ColumnTransformer([
    ("n", StandardScaler(), num_m),
    ("c", OneHotEncoder(handle_unknown="ignore", drop="first"), cat_m)])
model = Pipeline([("pre", pre), ("lr", LogisticRegression(max_iter=2000))])
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=0, stratify=y)
model.fit(Xtr, ytr)
print("\nHoldout AUC: %.3f" % roc_auc_score(yte, model.predict_proba(Xte)[:, 1]))

names = model.named_steps["pre"].get_feature_names_out()
coef = pd.Series(model.named_steps["lr"].coef_[0], index=names).sort_values()
print("\nTop negative (adjusted, log-odds):\n", coef.head(8).round(2))
print("\nTop positive (adjusted, log-odds):\n", coef.tail(8).round(2))