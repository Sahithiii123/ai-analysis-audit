import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportion_confint

BASE = "data/raw/03_olist_delivery_reviews/"
orders = pd.read_csv(
    BASE + "olist_orders_dataset.csv",
    parse_dates=[
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
)
items = pd.read_csv(BASE + "olist_order_items_dataset.csv")
reviews = pd.read_csv(
    BASE + "olist_order_reviews_dataset.csv",
    parse_dates=["review_creation_date", "review_answer_timestamp"],
)
sellers = pd.read_csv(BASE + "olist_sellers_dataset.csv")
customers = pd.read_csv(BASE + "olist_customers_dataset.csv")  # loaded for completeness

# ---- 1-2. Delivered orders and lateness -------------------------------------
d = orders[
    (orders["order_status"] == "delivered")
    & orders["order_delivered_customer_date"].notna()
    & orders["order_estimated_delivery_date"].notna()
].copy()
d["days_late"] = (
    d["order_delivered_customer_date"] - d["order_estimated_delivery_date"]
).dt.total_seconds() / 86400
d["is_late"] = d["days_late"] > 0
d["late_bucket"] = pd.cut(
    d["days_late"],
    bins=[-np.inf, 0, 3, 7, np.inf],
    labels=["on time / early", "1-3 days late", "4-7 days late", ">7 days late"],
)

# ---- 3. One (latest) review per order ---------------------------------------
rv = (
    reviews.sort_values("review_answer_timestamp")
    .drop_duplicates("order_id", keep="last")[["order_id", "review_score"]]
)
d = d.merge(rv, on="order_id", how="inner")
print(f"Delivered orders with a review: {len(d):,}")
print(f"Platform late rate: {d['is_late'].mean():.1%}\n")

# ---- 4. Late vs review score ------------------------------------------------
g = d.groupby("is_late")["review_score"].agg(["count", "mean", "median"])
g["pct_1_star"] = d.groupby("is_late")["review_score"].apply(lambda s: (s == 1).mean())
g["pct_5_star"] = d.groupby("is_late")["review_score"].apply(lambda s: (s == 5).mean())
print("Review score by lateness:\n", g.round(3), "\n")

print("Review score by days-late bucket:")
print(
    d.groupby("late_bucket", observed=True)["review_score"]
    .agg(["count", "mean"])
    .round(3),
    "\n",
)

late_s = d.loc[d["is_late"], "review_score"]
ontime_s = d.loc[~d["is_late"], "review_score"]
u, p = stats.mannwhitneyu(late_s, ontime_s, alternative="two-sided")
rank_biserial = 1 - 2 * u / (len(late_s) * len(ontime_s))  # sign: negative => late lower
rho, p_rho = stats.spearmanr(d["days_late"], d["review_score"])
print(f"Mann-Whitney p={p:.2e}, rank-biserial effect={-rank_biserial:.3f} (positive => on-time higher)")
print(f"Spearman(days_late, score) rho={rho:.3f}, p={p_rho:.2e}\n")

# ---- 5. Seller-level late rates ---------------------------------------------
so = items[["order_id", "seller_id"]].drop_duplicates()
so = so.merge(d[["order_id", "is_late", "review_score"]], on="order_id", how="inner")
s = so.groupby("seller_id").agg(
    orders=("order_id", "nunique"),
    late=("is_late", "sum"),
    avg_score=("review_score", "mean"),
)
s["late_rate"] = s["late"] / s["orders"]
s = s.join(sellers.set_index("seller_id")[["seller_state", "seller_city"]])

platform_rate = d["is_late"].mean()
MIN_ORDERS = 30
big = s[s["orders"] >= MIN_ORDERS].copy()
lo, hi = proportion_confint(big["late"], big["orders"], alpha=0.05, method="wilson")
big["ci_low"], big["ci_high"] = lo, hi
big["significantly_above_platform"] = big["ci_low"] > platform_rate

print(f"Sellers total: {len(s):,}; with >= {MIN_ORDERS} delivered orders: {len(big):,}")
print("Seller late-rate quantiles (sellers with >=30 orders):")
print(big["late_rate"].quantile([0.1, 0.25, 0.5, 0.75, 0.9, 0.99]).round(3))
print(f"Share of sellers with late rate >10%: {(big['late_rate'] > 0.10).mean():.1%}")
print(f"Share of sellers with late rate >20%: {(big['late_rate'] > 0.20).mean():.1%}")
print(f"Sellers significantly above platform rate: {big['significantly_above_platform'].sum()}\n")

print("Worst 10 sellers (>=30 orders):")
print(
    big.sort_values("late_rate", ascending=False)
    .head(10)[["orders", "late_rate", "ci_low", "ci_high", "avg_score", "seller_state"]]
    .round(3),
    "\n",
)

state = (
    big.groupby("seller_state")
    .agg(sellers=("late_rate", "size"), median_late_rate=("late_rate", "median"))
    .query("sellers >= 5")
    .sort_values("median_late_rate", ascending=False)
)
print("Median seller late rate by seller state (>=5 sellers):\n", state.round(3), "\n")

# ---- 6. Seller late rate vs seller review score -----------------------------
r, pr = stats.spearmanr(big["late_rate"], big["avg_score"])
print(f"Seller-level Spearman(late_rate, avg_score) = {r:.3f}, p={pr:.2e}")
