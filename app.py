import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date

FILE_NAME = "expenses.csv"

# --- INITIALIZE CSV ---
if not os.path.exists(FILE_NAME):
    df = pd.DataFrame(columns=["Date", "Category", "Item", "Amount"])
    df.to_csv(FILE_NAME, index=False)

st.set_page_config(page_title="Expense Analytics", layout="wide")

# --- SIDEBAR: DATA INPUT ---
st.sidebar.header("📝 Add Expense")
with st.sidebar.form("expense_form"):
    exp_date = st.date_input("Date", date.today())
    category = st.selectbox("Category", ["Food", "Transport", "Bills", "Shopping", "Entertainment", "Other"])
    item = st.text_input("Item Name")
    amount = st.number_input("Amount", min_value=0 , step = 1)
    
    if st.form_submit_button("Save"):
        new_row = pd.DataFrame([[exp_date, category, item, amount]], columns=["Date", "Category", "Item", "Amount"])
        new_row.to_csv(FILE_NAME, mode='a', header=False, index=False)
        st.rerun()

# --- LOAD & PREPARE DATA ---
df = pd.read_csv(FILE_NAME)
if not df.empty:
    df['Date'] = pd.to_datetime(df['Date'])
    # Create helper columns for filtering
    df['Month-Year'] = df['Date'].dt.strftime('%b %Y') 
    
    # --- SIDEBAR: FILTERING ---
    st.sidebar.markdown("---")
    st.sidebar.header("Filter")
    
    view_option = st.sidebar.radio("Select Scope:", ["All-Time Stats", "Particular Month"])
    
    if view_option == "Particular Month":
        unique_months = df['Month-Year'].unique()
        selected_month = st.sidebar.selectbox("Select Month", unique_months)
        display_df = df[df['Month-Year'] == selected_month]
        title_suffix = f"for {selected_month}"
    else:
        display_df = df
        title_suffix = "(All-Time)"

    # --- DASHBOARD UI ---
    st.title(f"📊 Spending {title_suffix}")
    
    # Top Row Metrics
    total = display_df['Amount'].sum()
    avg = display_df['Amount'].mean() if not display_df.empty else 0
    
    m1, m2 = st.columns(2)
    m1.metric("Total Spent", f"Rs{total:,.2f}")
    m2.metric("Average Transaction", f"Rs{avg:,.2f}")

    # Charts
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Category Breakdown")
        fig_pie = px.pie(display_df, values='Amount', names='Category')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("Spending over Time")
        # Grouping to ensure the line chart is clean
        line_data = display_df.groupby('Date')['Amount'].sum().reset_index()
        fig_line = px.area(line_data, x='Date', y='Amount', line_shape="spline")
        st.plotly_chart(fig_line, use_container_width=True)

    st.subheader("Transaction History")
    st.dataframe(display_df.sort_values("Date", ascending=False), use_container_width=True)

else:
    st.title("📊 Expense Dashboard")
    st.info("Input your first expense in the sidebar to generate the dashboard.")