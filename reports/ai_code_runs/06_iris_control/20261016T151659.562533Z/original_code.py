import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PATH = "data/raw/06_iris_control/data.csv"
RNG = np.random.default_rng(20261016)
N_BOOT = 10_000

df = pd.read_csv(PATH)
df.columns = [c.strip() for c in df.columns]
df["class"] = df["class"].astype(str).str.strip()
feats = ["sepal length", "sepal width", "petal length", "petal width"]

# ---- sanity checks ----
print("Shape:", df.shape)
print("Missing values:\n", df.isna().sum(), "\n")
print("Duplicate rows:", df.duplicated().sum())
print("Rows per species:\n", df["class"].value_counts(), "\n")
print("Non-positive values:", int((df[feats] <= 0).any(axis=1).sum()), "\n")

# ---- helpers ----
def t_ci(x, conf=0.95):
    x = np.asarray(x, float)
    n = len(x)
    m, se = x.mean(), stats.sem(x)
    h = stats.t.ppf((1 + conf) / 2, n - 1) * se
    return m - h, m + h

def boot_ci_mean(x, conf=0.95):
    x = np.asarray(x, float)
    idx = RNG.integers(0, len(x), size=(N_BOOT, len(x)))
    means = x[idx].mean(axis=1)
    a = (1 - conf) / 2
    return tuple(np.quantile(means, [a, 1 - a]))

def boot_ci_diff(a, b, conf=0.95):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ma = a[RNG.integers(0, len(a), size=(N_BOOT, len(a)))].mean(axis=1)
    mb = b[RNG.integers(0, len(b), size=(N_BOOT, len(b)))].mean(axis=1)
    d = ma - mb
    al = (1 - conf) / 2
    return tuple(np.quantile(d, [al, 1 - al]))

def cohens_d(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    sp = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1))
                 / (len(a) + len(b) - 2))
    return (a.mean() - b.mean()) / sp

# ---- per-species summary ----
rows = []
for sp, g in df.groupby("class"):
    for f in feats:
        x = g[f].dropna()
        lo, hi = t_ci(x)
        blo, bhi = boot_ci_mean(x)
        rows.append({
            "species": sp, "measure": f, "n": len(x),
            "mean": x.mean(), "sd": x.std(ddof=1), "median": x.median(),
            "min": x.min(), "max": x.max(),
            "t_CI_low": lo, "t_CI_high": hi,
            "boot_CI_low": blo, "boot_CI_high": bhi,
        })
summary = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print(summary.round(3).to_string(index=False), "\n")

# ---- pairwise descriptive comparison ----
species = sorted(df["class"].unique())
pairs = [(species[i], species[j]) for i in range(len(species))
         for j in range(i + 1, len(species))]
comp = []
for f in feats:
    for s1, s2 in pairs:
        a = df.loc[df["class"] == s1, f].dropna()
        b = df.loc[df["class"] == s2, f].dropna()
        lo, hi = boot_ci_diff(a, b)
        comp.append({
            "measure": f, "pair": f"{s1} - {s2}",
            "mean_diff": a.mean() - b.mean(),
            "boot_CI_low": lo, "boot_CI_high": hi,
            "cohens_d": cohens_d(a, b),
        })
comp = pd.DataFrame(comp)
print(comp.round(3).to_string(index=False), "\n")

# ---- overlap check: how much do species ranges overlap per measure? ----
for f in feats:
    rng = df.groupby("class")[f].agg(["min", "max"])
    print(f"{f} ranges:\n{rng}\n")

# ---- plot ----
fig, axes = plt.subplots(1, 4, figsize=(16, 4))
for ax, f in zip(axes, feats):
    data = [df.loc[df["class"] == s, f].dropna() for s in species]
    ax.boxplot(data, labels=[s.replace("Iris-", "") for s in species])
    ax.set_title(f + " (cm)")
plt.tight_layout()
plt.savefig("iris_boxplots.png", dpi=150)
print("Saved iris_boxplots.png")