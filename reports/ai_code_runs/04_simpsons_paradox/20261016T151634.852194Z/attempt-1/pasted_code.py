import pandas as pd

df = pd.read_csv("data/raw/04_simpsons_paradox/UCBAdmissions.csv")

# Wide table: one row per (Dept, Gender) with admitted/rejected counts
t = df.pivot_table(index=["Dept", "Gender"], columns="Admit",
                   values="Freq", aggfunc="sum").reset_index()
t["Applicants"] = t["Admitted"] + t["Rejected"]
t["Rate"] = t["Admitted"] / t["Applicants"]

# 1) Overall by gender
overall = t.groupby("Gender")[["Admitted", "Applicants"]].sum()
overall["Rate"] = overall["Admitted"] / overall["Applicants"]
print("=== Overall admission rate by gender ===")
print(overall.round(3), "\n")

# 2) Within each department
by_dept = t.pivot(index="Dept", columns="Gender", values="Rate")
by_dept["Female_minus_Male"] = by_dept["Female"] - by_dept["Male"]
print("=== Admission rate by dept and gender ===")
print(by_dept.round(3), "\n")

# 3) Dept difficulty + where each gender applied
dept_tot = t.groupby("Dept")[["Admitted", "Applicants"]].sum()
dept_tot["Dept_Rate"] = dept_tot["Admitted"] / dept_tot["Applicants"]
share = t.pivot(index="Dept", columns="Gender", values="Applicants")
share = share / share.sum()
share.columns = [f"{c}_application_share" for c in share.columns]
print("=== Dept overall rate and application share by gender ===")
print(dept_tot[["Dept_Rate"]].join(share).round(3), "\n")

# 4) Standardized (common dept mix) rates
weights = dept_tot["Applicants"] / dept_tot["Applicants"].sum()
rates = t.pivot(index="Dept", columns="Gender", values="Rate")
std = rates.mul(weights, axis=0).sum()
print("=== Dept-mix-adjusted admission rate (weights = all applicants) ===")
print(std.round(3))

# Weighted dept-level gap
print("\nAdjusted gap (F - M):", round(std["Female"] - std["Male"], 3))