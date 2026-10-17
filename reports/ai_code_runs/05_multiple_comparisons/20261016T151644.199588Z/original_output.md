# Model Output Record

## Model metadata

- Model name: Sonnet 5.5
- Model version: medium
- Interface: claude.ai
- Date/time: 2026-10-16 18:00 IST
- Settings: not exposed

## Exact prompt sent

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

## Verbatim model response

Analysis plan
Load the full ARFF, strip whitespace, turn ? into missing (don’t drop rows, just treat as its own category).
Target = class == ">50K".
This is a multiple comparisons setup: ~13 features, plus many categorical levels. So I test per feature (not per level), then correct p-values.
Numeric features (age, fnlwgt, education-num, capital-gain, capital-loss, hours-per-week): Mann-Whitney U + effect size (AUC-style rank-biserial). Heavy zeros in capital gain/loss, so nonparametric is safer.
Categorical features: chi-square test + Cramér’s V.
Correct all feature-level p-values with Benjamini-Hochberg FDR (and Bonferroni as a strict check). With ~48k rows, almost everything is “significant,” so I rank by effect size, not p-value.
Then a multivariable logistic regression to see which features still matter after adjusting for each other (education and education-num are redundant, and relationship/marital-status overlap, so I drop education, and fnlwgt is a sampling weight, so I only check it, not interpret it).
Sanity check on redundancy and a train/test AUC so I’m not overselling.



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


Written conclusion

Run it and check the printed tables, but here’s what to expect (the well-known pattern in this dataset, so verify against your output):

Strongest associations with >50K: marital status / relationship (married-civ-spouse and husband/wife are way above never-married, own-child, unmarried), education level (education-num; bachelors, masters, doctorate, prof-school up top), age, capital gain, hours per week, and occupation (exec-managerial, prof-specialty up; other-service, handlers-cleaners down). Capital loss shows a smaller but real link.
Weaker: sex and race are significantly associated, but the effects are smaller than the big ones above. Note sex is tangled up with relationship/marital status (the dataset has a lot of “Husband” rows), so part of that gap is confounding with the other columns. Native country is small and mostly a US vs. rest-of-world thing, and many countries have tiny counts, so don’t read much into individual ones.
Multiple comparisons: with ~48k rows nearly every feature clears even Bonferroni, so significance is cheap here. Lean on the effect sizes (AUC distance from 0.5, Cramér’s V), not p-values. Per-level claims (like one specific country) would need their own correction and are shaky for small groups.
Caveats: this is association, not causation. Marital status and relationship overlap heavily, and education and education-num are the same info, so don’t treat them as independent findings. fnlwgt is a sampling weight, not a trait of the person. The ? values are mostly in workclass, occupation, and country, and they’re not random (they skew lower income), so “Missing” is itself a signal. The holdout AUC tells you how much of this holds up out of sample (usually ~0.9 for this dataset).
