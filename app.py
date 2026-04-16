import streamlit as st
import pandas as pd
import plotly.express as px
import os
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from datetime import date

# --- 1. CONFIGURATION & USER LOADING ---
CONFIG_FILE = "config.yaml"

if not os.path.exists(CONFIG_FILE):
    initial_config = {
        'credentials': {'usernames': {}},
        'cookie': {'expiry_days': 30, 'key': 'auth_key', 'name': 'expense_cookie'}
    }
    with open(CONFIG_FILE, 'w') as file:
        yaml.dump(initial_config, file)

with open(CONFIG_FILE) as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

st.set_page_config(page_title="Personal Spend Tracker", layout="wide")

# --- 2. AUTHENTICATION & UI SWITCH ---

if not st.session_state.get("authentication_status"):
    st.title("🔐 Access Portal")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab2:
        try:
            # register_user returns True if the user successfully fills the form
            if authenticator.register_user(location='main'):
                # We save the config only if the registration was successful
                with open(CONFIG_FILE, 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)
                st.success('User registered successfully! Now go to the Login tab.')
        except Exception as e:
            # If the username already exists, the library throws an error
            # We catch it here and show a helpful message
            if "already exists" in str(e).lower():
                st.error("This username is already taken. Please choose another one.")
            else:
                st.error(f"Registration Error: {e}")

    with tab1:
        authenticator.login(location='main')
        
        if st.session_state.get("authentication_status") == False:
            st.error("Username/password is incorrect")
        elif st.session_state.get("authentication_status") == None:
            st.info("Please login or register to manage your expenses.")

# --- 3. DASHBOARD LOGIC (Runs only when status is True) ---
elif st.session_state.get("authentication_status"):
    
    # Custom CSS to force logout to bottom of sidebar and add red hover
    st.markdown("""
        <style>
            /* This targets the sidebar container to allow bottom alignment */
            [data-testid="stSidebarNav"] + div {
                display: flex;
                flex-direction: column;
                height: 100%;
            }
            
            /* Target the logout button specifically */
            .stLogout button {
                width: 100%;
                background-color: transparent;
                color: #ff4b4b; /* Text is red by default */
                border: 1px solid #ff4b4b;
                transition: 0.3s;
                margin-top: auto; /* Pushes it to the bottom */
            }

            /* Red hover effect */
            .stLogout button:hover {
                background-color: #ff4b4b !important;
                color: white !important;
                border: 1px solid #ff4b4b;
            }
        </style>
    """, unsafe_allow_html=True)

    # Extract user info
    name = st.session_state["name"]
    username = st.session_state["username"]

    # Welcome info in sidebar
    st.sidebar.title(f"👋 Welcome, {name}")
    st.sidebar.markdown("---")

    # --- 4. USER-SPECIFIC DATA SANDBOX ---
    USER_FILE = f"data_{username}_expenses.csv"
    
    if not os.path.exists(USER_FILE):
        df = pd.DataFrame(columns=["Date", "Category", "Item", "Amount"])
        df.to_csv(USER_FILE, index=False)

    # --- 5. INPUT SECTION ---
    st.sidebar.header("📝 Add Transaction")
    with st.sidebar.form("expense_form"):
        exp_date = st.date_input("Date", date.today())
        category = st.selectbox("Category", ["Food", "Transport", "Bills", "Shopping", "Entertainment", "Other"])
        item = st.text_input("Item Name")
        amount = st.number_input("Amount", min_value=0)
        
        if st.form_submit_button("Save"):
            new_row = pd.DataFrame([[exp_date, category, item, amount]], columns=["Date", "Category", "Item", "Amount"])
            new_row.to_csv(USER_FILE, mode='a', header=False, index=False)
            st.success("Entry Recorded!")
            st.rerun()

    # --- 6. DASHBOARD SECTION (Charts/History) ---
    # [KEEP YOUR EXISTING DASHBOARD CODE HERE]
    # ...
    # [KEEP YOUR DATA MANAGEMENT CODE HERE]
    # ...

    # --- FINALLY: LOGOUT AT THE BOTTOM ---
    # Placing this last ensures it appears at the bottom of the sidebar
    

    # --- 6. DASHBOARD SECTION ---
    df = pd.read_csv(USER_FILE)
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
        
        st.title(f"📊 {name}'s Spending Dashboard")
        
        st.sidebar.markdown("---")
        st.sidebar.header("🔍 Filter Analytics")
        view_option = st.sidebar.radio("Select Scope:", ["All-Time", "Current Month", "Custom Date Range"])
        
        display_df = df 
        
        if view_option == "Current Month":
            current_month = date.today().strftime('%Y-%m')
            display_df = df[df['Date'].dt.strftime('%Y-%m') == current_month]
            title_text = f"Stats for {date.today().strftime('%B %Y')}"
            
        elif view_option == "Custom Date Range":
            today = date.today()
            start_default = today - pd.Timedelta(days=7)
            date_range = st.sidebar.date_input("Select Range", value=(start_default, today), max_value=today)
            
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range
                display_df = df[(df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)]
                title_text = f"Stats from {start_date} to {end_date}"
            else:
                st.info("Please select both a start and end date in the sidebar.")
                st.stop()
        else:
            title_text = "All-Time Statistics"
        st.sidebar.markdown("---")
        authenticator.logout("Logout", "sidebar")

        total = display_df['Amount'].sum()
        avg_transaction = display_df['Amount'].mean() if not display_df.empty else 0
        
        st.subheader(title_text)
        
        m1, m2 = st.columns(2)
        m1.metric("Total Spent", f"Rs{total:,.2f}")
        m2.metric("Average Transaction", f"Rs{avg_transaction:,.2f}")
        
        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            fig_pie = px.pie(display_df, values='Amount', names='Category', hole=0.1, title="Spending by Category")
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            daily_trend = display_df.groupby('Date')['Amount'].sum().reset_index()
            fig_line = px.area(daily_trend, x='Date', y='Amount', title="Daily Spending Trend")
            st.plotly_chart(fig_line, use_container_width=True)

        st.markdown("---")
        st.subheader("📜 Full Transaction History")
        st.dataframe(
            display_df.sort_values("Date", ascending=False), 
            use_container_width=True,
            column_config={
                "Amount": st.column_config.NumberColumn(format="Rs%.2f"),
                "Date": st.column_config.DateColumn(format="DD/MM/YYYY")
            }
        )

        with st.expander("🛠️ Filtered Data Management"):
            col_del1, col_del2 = st.columns(2)

            with col_del1:
                st.write("**Delete Specific Entry**")
                if not display_df.empty:
                    delete_options = {f"{i}: {row['Item']} (Rs{row['Amount']})": i for i, row in display_df.iterrows()}
                    to_delete = st.selectbox("Select item from filtered list:", options=list(delete_options.keys()))
                    if st.button("Confirm Delete", type="secondary"):
                        df = df.drop(delete_options[to_delete])
                        df.to_csv(USER_FILE, index=False)
                        st.success("Entry removed!")
                        st.rerun()

            with col_del2:
                st.write(f"**Wipe {view_option} Data**")
                st.caption(f"This will remove {len(display_df)} records shown above.")
                confirm_clear = st.checkbox("Enable Filtered Reset")
                if st.button(f"Clear {view_option} Records", type="primary", disabled=not confirm_clear):
                    df = df[~df.index.isin(display_df.index)]
                    df.to_csv(USER_FILE, index=False)
                    st.warning(f"Cleared records for {view_option}!")
                    st.rerun()
    else:
        st.title(f"Hello {name}!")
        st.info("Your database is currently empty. Use the sidebar to add your first expense!")