import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# === CONFIG ===
SHEET_NAME = "KPI"  # Sheet/tab name
SHEET_ID = "19aDfELEExMn0loj_w6D69ngGG4haEm6lsgqpxJC1OAA"  # Google Sheet ID

# === Google Auth from Streamlit Secrets ===
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"])
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)
worksheet = sheet.worksheet(SHEET_NAME)

# === Load Data ===
@st.cache_data
def load_data():
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

df = load_data()

# === Streamlit UI ===
st.title("📊 KPI Dashboard for Champs")

emp_id = st.text_input("Enter EMP ID (e.g., 1070)")
month = st.selectbox("Select Month", sorted(df['Month'].unique()))

if emp_id and month:
    emp_data = df[(df["EMP ID"].astype(str) == emp_id) & (df["Month"] == month)]

    if emp_data.empty:
        st.warning("No data found for that EMP ID and month.")
    else:
        st.success(f"KPI Data for EMP ID: {emp_id} | Month: {month}")

        # Display raw performance + KPI scores
        st.subheader("🔹 Performance Metrics")
        perf_cols = ["Hold", "Wrap", "Auto-On", "Schedule Adherence", "Resolution CSAT",
                     "Agent Behaviour", "Quality", "PKT", "SL + UPL", "LOGINS"]
        st.write(emp_data[perf_cols].T)

        st.subheader("✅ KPI Scores")
        kpi_cols = [col for col in emp_data.columns if "KPI Score" in col]
        st.write(emp_data[kpi_cols].T)

        st.subheader("🏁 Grand Total")
        st.metric("Grand Total KPI", f"{emp_data['Grand Total'].values[0]}")
