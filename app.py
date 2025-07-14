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

# === Helper Function for Styled Table ===
def styled_table(df):
    return df.to_html(classes='styled-table', border=0)

# === Styling ===
st.markdown("""
    <style>
    body {
        font-family: 'Segoe UI', sans-serif;
        color: #222;
    }
    .stApp {
        background-color: #f9f9f9;
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
        color: #222;
        margin-bottom: 10px;
    }
    .styled-table {
        font-size: 16px;
        color: #111111;
        width: 100%;
        border-collapse: collapse;
    }
    .styled-table th, .styled-table td {
        border: 1px solid #ddd;
        padding: 10px 14px;
        text-align: left;
        color: #111111 !important;
    }
    .styled-table tr:nth-child(even) {
        background-color: #f8f8f8;
    }
    .styled-table th {
        background-color: #eaeaea;
        font-weight: bold;
        color: #111111 !important;
    }
    </style>
""", unsafe_allow_html=True)

# === Title ===
st.title("📊 KPI Dashboard for Champs")

# === KPI Meaning and Metric Definition (no sample values) ===
st.markdown("## 📘 About This Dashboard")

# KPI Weightage Table
st.markdown("### 🎯 KPI Weightage and Score Calculation")
weightage_table = pd.DataFrame({
    "Weightage": ["0%", "30%", "10%", "10%", "20%", "20%", "10%"],
    "KPI Metrics": [
        "Hold KPI Score",
        "Auto-On KPI Score",
        "Schedule Adherence KPI Score",
        "Resolution CSAT KPI Score",
        "Agent Behaviour KPI Score",
        "Quality KPI Score",
        "PKT KPI Score"
    ],
    "Score": ["2", "2", "4", "5", "4", "1", "2.6"]
})
st.table(weightage_table)

# KPI Metric Definitions
st.markdown("### 📖 KPI Metric Definitions")
definitions_table = pd.DataFrame({
    "Description": [
        "Average hold time used",
        "Average time taken to wrap the call",
        "Average duration of champ using auto on",
        "Shift adherence for the month",
        "Customer feedback on resolution given",
        "Customer feedback on champ behaviour",
        "Average Quality Score achieved for the month",
        "Process knowledge test",
        "Number of sick and unplanned leaves",
        "Number of days logged in"
    ],
    "Metric Name": [
        "Hold", "Wrap", "Auto-On", "Schedule Adherence", "Resolution CSAT",
        "Agent Behaviour", "Quality", "PKT", "SL + UPL", "LOGINS"
    ],
    "Unit": [
        "HH:MM:SS", "HH:MM:SS", "HH:MM:SS", "Percentage", "Percentage", "Percentage",
        "Percentage", "Percentage", "Days", "Days"
    ]
})
st.table(definitions_table)

# === Input Fields ===
emp_id = st.text_input("Enter EMP ID (e.g., 1070)")
month = st.selectbox("Select Month", sorted(df['Month'].unique(), key=lambda m: [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
].index(m)))

# === Result Display ===
if emp_id and month:
    emp_data = df[(df["EMP ID"].astype(str) == emp_id) & (df["Month"] == month)]

    if emp_data.empty:
        st.warning("No data found for that EMP ID and month.")
    else:
        emp_name = emp_data["NAME"].values[0]
        st.markdown(f"### ✅ KPI Data for **{emp_name}** (EMP ID: {emp_id}) | Month: **{month}**")

        # === Performance Metrics ===
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🔹 Performance Metrics</div>', unsafe_allow_html=True)
        perf_cols = ["Hold", "Wrap", "Auto-On", "Schedule Adherence", "Resolution CSAT",
                     "Agent Behaviour", "Quality", "PKT", "SL + UPL", "LOGINS"]
        perf_data = emp_data[perf_cols].T.rename(columns={emp_data.index[0]: 'Value'})
        st.markdown(styled_table(perf_data), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # === KPI Scores ===
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">✅ KPI Scores</div>', unsafe_allow_html=True)
        kpi_cols = [col for col in emp_data.columns if "KPI Score" in col]
        kpi_data = emp_data[kpi_cols].T.rename(columns={emp_data.index[0]: 'Score'})
        st.markdown(styled_table(kpi_data), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # === Grand Total ===
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🏁 Grand Total</div>', unsafe_allow_html=True)
        current_score = emp_data['Grand Total'].values[0]
        st.metric("Grand Total KPI", f"{current_score}")
        st.markdown('</div>', unsafe_allow_html=True)

        # === Target Committed ===
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎯 Target Committed for Next Month</div>', unsafe_allow_html=True)
        target_cols = [
            "Target Committed for PKT",
            "Target Committed for CSAT",
            "Target Committed for Quality"
        ]
        if all(col in emp_data.columns for col in target_cols):
            target_data = emp_data[target_cols].T.rename(columns={emp_data.index[0]: 'Target'})
            st.markdown(styled_table(target_data), unsafe_allow_html=True)
        else:
            st.warning("Target data not available yet.")
        st.markdown('</div>', unsafe_allow_html=True)
