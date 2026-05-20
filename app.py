import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px
from datetime import date

# --- 1. LUXURY PAGE CONFIG ---
st.set_page_config(page_title="Prime Properties Elite", layout="wide", page_icon="💎")

# --- 2. ADVANCED CSS (Luxury & Beautiful UI) ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.8)), 
                    url("https://images.unsplash.com/photo-1512917774080-9991f1c4c750?q=80&w=2070");
        background-size: cover;
        background-attachment: fixed;
    }
    /* Glassmorphism containers */
    div[data-testid="stMetric"], .stDataFrame, div[data-testid="stForm"], .stTable {
        background: rgba(255, 255, 255, 0.04) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 20px !important;
        padding: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    h1, h2, h3 {
        color: #00d4ff !important;
        font-family: 'Inter', sans-serif;
        text-shadow: 0px 0px 10px rgba(0, 212, 255, 0.5);
    }
    .stButton>button {
        background: linear-gradient(45deg, #00d4ff, #0055ff) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        height: 3em;
        font-weight: bold;
        width: 100%;
    }
    section[data-testid="stSidebar"] { background-color: rgba(10, 15, 25, 0.95) !important; }
    </style>
    """, unsafe_allow_html=True)


# --- 3. CONNECTION ---
# Is line ko ya toh hata dein ya 'ttl' add karein
@st.cache_resource(ttl=3600) # Iska matlab har 1 ghante baad connection refresh hoga
def get_conn():
    return snowflake.connector.connect(
        user='Humairali',
        password='Humairali_abro2',
        account='XXOVLEZ-VH13552',
        warehouse='COMPUTE_WH',
        role='ACCOUNTADMIN'
    )

conn = get_conn()

# --- 4. MAIN INTERFACE ---
if conn:
    st.sidebar.title("🏢 Navigation")
    menu = st.sidebar.selectbox("Choose Dashboard",
                                ["🏠 Main Dashboard", "💰 Financial Reports", "📢 Sell Your Property"])

    # Database Paths
    DB_LANDING = "PRIME_PROPERTIES_DW.LANDING"
    DB_ANALYTICS = "PRIME_PROPERTIES_DW.ANALYTICS"

    # --- TAB 1: MAIN DASHBOARD ---
    if menu == "🏠 Main Dashboard":
        st.title("🏙️ Property Market Overview")
        df_prop = pd.read_sql(f"SELECT * FROM {DB_LANDING}.STG_PROPERTIES", conn)

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Listings", len(df_prop))
        m2.metric("Locations", df_prop['CITY'].nunique())
        m3.metric("Live Updates", "Active")

        st.markdown("### 📋 Current Inventory Table")
        st.dataframe(df_prop, use_container_width=True)

        fig = px.pie(df_prop, names='CITY', title="City Distribution", hole=0.5, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB 2: FINANCIAL REPORTS ---
    elif menu == "💰 Financial Reports":
        st.title("💹 Financial Performance")
        df_trans = pd.read_sql(f"SELECT * FROM {DB_ANALYTICS}.FACT_TRANSACTIONS", conn)

        st.metric("Total Sales Volume", f"PKR {df_trans['AMOUNT'].sum():,.2f}")

        fig_bar = px.bar(df_trans, x='TRANSACTION_DATE', y='AMOUNT', color='TRANSACTION_TYPE',
                         title="Revenue Growth", template="plotly_dark")
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- TAB 3: SELL YOUR PROPERTY (New Feature) ---
    elif menu == "📢 Sell Your Property":
        st.title("📢 List Your Property for Sale")
        st.markdown("Apni property ki details enter karein taaki hum usay apne database mein register kar sakein.")

        with st.form("sell_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                p_id = st.text_input("Property ID (Unique ID)")
                p_type = st.selectbox("Property Type", ["Apartment", "House", "Commercial"])
                client = st.text_input("Owner Name")
            with col2:
                city = st.selectbox("City", ["Karachi", "Lahore", "Islamabad"])
                area = st.text_input("Area Location")
                price = st.number_input("Asking Price (PKR)", min_value=100000)

            submit = st.form_submit_button("Post My Ad")

            if submit:
                if p_id and client and area:
                    try:
                        cursor = conn.cursor()
                        # 1. Properties table mein add karein
                        cursor.execute(
                            f"INSERT INTO {DB_LANDING}.STG_PROPERTIES VALUES ('{p_id}', '{p_type}', '{city}', '{area}')")
                        # 2. Transactions table mein register karein as 'Sale'
                        cursor.execute(f"""
                            INSERT INTO {DB_LANDING}.STG_TRANSACTIONS (TRANSACTION_ID, TRANSACTION_DATE, PROPERTY_ID, CLIENT_NAME, TRANSACTION_TYPE, AMOUNT) 
                            VALUES ('T-{p_id}', '{date.today()}', '{p_id}', '{client}', 'Sale', {price})
                        """)
                        conn.commit()
                        st.success("✅ Aapki property sale ke liye register ho gayi hai!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Meharbani karke saari details bharein!")

else:
    st.error("Snowflake Connection Failed!")