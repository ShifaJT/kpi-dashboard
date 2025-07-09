import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# === CONFIG ===
SHEET_NAME = "KPI"
SHEET_ID = "19aDfELEExMn0loj_w6D69ngGG4haEm6lsgqpxJC1OAA"

# === Google Auth from Secrets ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)
worksheet = sheet.worksheet(SHEET_NAME)

@st.cache_data
def load_data():
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

df = load_data()

# === Styling ===
st.markdown("""
    st.markdown("""
    <style>
    body {
        font-family: 'Segoe UI', sans-serif;
        color: #222;
    }
    .stApp {
        background-color: #f9f9f9;
    }
    .stMetric {
        font-size: 20px;
    }
    .card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    .section-title {
        font-size: 20px;
        font-weight: 600;
        color: #333333;
        margin-bottom: 10px;
    }
    /* NEW TABLE STYLING */
    thead tr th {
        font-size: 16px !important;
        color: #111 !important;
    }
    tbody tr td {
        font-size: 16px !important;
        color: #222 !important;
    }
    .dataframe {
        border-radius: 8px;
        border: 1px solid #ddd;
    }
    </style>
""", unsafe_allow_html=True)

# === Title ===
st.title("📊 KPI Dashboard for Champs")

# === Input Section ===
emp_id = st.text_input("Enter EMP ID (e.g., 1070)")
month = st.selectbox("Select Month", sorted(df['Month'].unique()))

# === Result Section ===
if emp_id and month:
    emp_data = df[(df["EMP ID"].astype(str) == emp_id) & (df["Month"] == month)]

    if emp_data.empty:
        st.warning("No data found for that EMP ID and month.")
    else:
        emp_name = emp_data["NAME"].values[0]
        st.markdown(f"### ✅ KPI Data for **{emp_name}** (EMP ID: {emp_id}) | Month: **{month}**")

        # === Performance Section ===
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🔹 Performance Metrics</div>', unsafe_allow_html=True)
        perf_cols = ["Hold", "Wrap", "Auto-On", "Schedule Adherence", "Resolution CSAT",
                     "Agent Behaviour", "Quality", "PKT", "SL + UPL", "LOGINS"]
        st.dataframe(emp_data[perf_cols].T, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # === KPI Scores Section ===
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">✅ KPI Scores</div>', unsafe_allow_html=True)
        kpi_cols = [col for col in emp_data.columns if "KPI Score" in col]
        st.dataframe(emp_data[kpi_cols].T, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # === Grand Total ===
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🏁 Grand Total</div>', unsafe_allow_html=True)
        st.metric("Grand Total KPI", f"{emp_data['Grand Total'].values[0]}")
        st.markdown('</div>', unsafe_allow_html=True)

        # === Target Committed Section ===
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎯 Target Committed for Next Month</div>', unsafe_allow_html=True)
        target_cols = [
            "Target Committed for PKT",
            "Target Committed for CSAT",
            "Target Committed for Quality"
        ]
        if all(col in emp_data.columns for col in target_cols):
            targets = emp_data[target_cols].T
            targets.columns = ["Target"]
            st.table(targets)
        else:
            st.warning("Target data not available yet.")
        st.markdown('</div>', unsafe_allow_html=True)
