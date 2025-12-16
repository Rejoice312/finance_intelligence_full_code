import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------
# PAGE CONFIG
# -----------------------------------
st.set_page_config(
    page_title="Company Finance Intelligence Dashboard",
    layout="wide"
)

st.title("Company Finance Intelligence Dashboard")
st.caption("1-Year Financial Performance, Cash Flow, Cost Control & Risk Monitoring")

# -----------------------------------
# LOAD DATA
# -----------------------------------
@st.cache_data
def load_data():
    file_path = "data.xlsx"
    transactions = pd.read_excel(file_path, sheet_name="transactions")
    categories = pd.read_excel(file_path, sheet_name="categories")
    monthly_targets = pd.read_excel(file_path, sheet_name="monthly_targets")
    merchant_rules = pd.read_excel(file_path, sheet_name="merchant_rules")
    return transactions, categories, monthly_targets, merchant_rules

transactions, categories, monthly_targets, merchant_rules = load_data()

transactions["transaction_date"] = pd.to_datetime(transactions["transaction_date"])
transactions["month"] = transactions["transaction_date"].dt.to_period("M").astype(str)

# -----------------------------------
# DERIVED METRICS
# -----------------------------------
monthly_summary = (
    transactions
    .groupby("month")["amount"]
    .sum()
    .reset_index(name="net_cash_flow")
)

monthly_revenue = (
    transactions[transactions["amount"] > 0]
    .groupby("month")["amount"]
    .sum()
    .reset_index(name="revenue")
)

monthly_expenses = (
    transactions[transactions["amount"] < 0]
    .groupby("month")["amount"]
    .sum()
    .reset_index(name="expenses")
)

monthly_finance = (
    monthly_revenue
    .merge(monthly_expenses, on="month")
    .merge(monthly_summary, on="month")
)

total_revenue = monthly_finance["revenue"].sum()
total_expenses = monthly_finance["expenses"].sum()
net_profit = total_revenue + total_expenses
profit_margin = (net_profit / total_revenue) * 100
ending_balance = transactions["account_balance"].iloc[-1]

# -----------------------------------
# KPI SECTION
# -----------------------------------
st.subheader("Executive Financial Overview")

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

kpi1.metric("Total Revenue", f"${total_revenue:,.0f}")
kpi2.metric("Total Expenses", f"${abs(total_expenses):,.0f}")
kpi3.metric("Net Profit", f"${net_profit:,.0f}")
kpi4.metric("Profit Margin", f"{profit_margin:.1f}%")
kpi5.metric("Ending Cash Balance", f"${ending_balance:,.0f}")

# -----------------------------------
# REVENUE VS EXPENSE TREND
# -----------------------------------
st.subheader("Revenue vs Expenses Trend")

rev_exp_fig = go.Figure()
rev_exp_fig.add_trace(go.Scatter(
    x=monthly_finance["month"],
    y=monthly_finance["revenue"],
    name="Revenue",
    mode="lines+markers"
))
rev_exp_fig.add_trace(go.Scatter(
    x=monthly_finance["month"],
    y=monthly_finance["expenses"]*-1,
    name="Expenses",
    mode="lines+markers"
))

rev_exp_fig.update_layout(
    xaxis_title="Month",
    yaxis_title="Amount",
    legend_title="Metric"
)

st.plotly_chart(rev_exp_fig, use_container_width=True)

# -----------------------------------
# CASH FLOW & BALANCE
# -----------------------------------
st.subheader("Cash Flow & Liquidity")

cash_col1, cash_col2 = st.columns(2)

with cash_col1:
    cashflow_fig = px.bar(
        monthly_finance,
        x="month",
        y="net_cash_flow",
        title="Monthly Net Cash Flow"
    )
    st.plotly_chart(cashflow_fig, use_container_width=True)

with cash_col2:
    balance_fig = px.line(
        transactions,
        x="transaction_date",
        y="account_balance",
        title="Account Balance Over Time"
    )
    st.plotly_chart(balance_fig, use_container_width=True)

# -----------------------------------
# EXPENSE BREAKDOWN
# -----------------------------------
st.subheader("Expense Structure & Cost Drivers")

expense_breakdown = (
    transactions[transactions["amount"] < 0]
    .groupby("category")["amount"]
    .sum()
    .abs()
    .reset_index()
)

expense_fig = px.pie(
    expense_breakdown,
    names="category",
    values="amount",
    title="Expense Distribution by Category"
)
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(expense_fig, use_container_width=True)

# -----------------------------------
# TOP MERCHANTS
# -----------------------------------
st.subheader("Top Merchants by Spend")

top_merchants = (
    transactions
    .groupby("merchant")["amount"]
    .sum()
    .reset_index()
    .sort_values("amount")
)

merchant_fig = px.bar(
    top_merchants,
    x="amount",
    y="merchant",
    orientation="h",
    title="Net Spend by Merchant"
)

with col2:
    st.plotly_chart(merchant_fig, use_container_width=True)

# -----------------------------------
# RISK & RECURRING EXPENSES
# -----------------------------------
st.subheader("Risk & Recurring Spend Monitoring")

risk_transactions = transactions.merge(
    merchant_rules,
    on="merchant",
    how="left"
)

risk_table = (
    risk_transactions
    .groupby(["merchant", "risk_flag"])["amount"]
    .sum()
    .reset_index()
    .sort_values("amount")
)

st.dataframe(risk_table, use_container_width=True)

# -----------------------------------
# BUDGET VS ACTUAL
# -----------------------------------
st.subheader("Budget vs Actual Performance")

actuals = (
    monthly_finance
    .merge(monthly_targets, left_on="month", right_on=monthly_targets["month"].dt.to_period("M").astype(str))
)

budget_fig = px.bar(
    actuals,
    x="month",
    y=["revenue", "revenue_target"],
    barmode="group",
    title="Actual Revenue vs Target"
)
st.plotly_chart(budget_fig, use_container_width=True)


