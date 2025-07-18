import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- Google Sheets Setup ---
SHEET_ID = "19aDfELEExMn0loj_w6D69ngGG4haEm6lsgqpxJC1OAA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/19aDfELEExMn0loj_w6D69ngGG4haEm6lsgqpxJC1OAA"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = Credentials.from_service_account_file(
    "creds.json",
    scopes=SCOPES
)

client = gspread.authorize(credentials)
sheet = client.open_by_key(SHEET_ID)
kpi_month = sheet.worksheet("KPI Month")
kpi_day = sheet.worksheet("KPI Day")
csat_score = sheet.worksheet("CSAT Score")

# --- Streamlit UI ---
st.set_page_config(page_title="KPI Dashboard", layout="wide")
st.title("📊 KPI Dashboard")

emp_id = st.text_input("Enter your EMP ID")
view_type = st.selectbox("Select View Type", ["Month", "Week", "Day"])

if emp_id:
    df_month = pd.DataFrame(kpi_month.get_all_records())
    df_day = pd.DataFrame(kpi_day.get_all_records())
    df_csat = pd.DataFrame(csat_score.get_all_records())

    df_month = df_month[df_month['EMP ID'] == emp_id]
    df_day = df_day[df_day['EMP ID'] == emp_id]
    df_csat = df_csat[df_csat['EMP ID'] == emp_id]

    if view_type == "Month":
        month = st.selectbox("Select Month", df_month['Month'].unique())
        if month:
            data = df_month[df_month['Month'] == month]
            if not data.empty:
                st.subheader("Performance")
                perf_cols = ['Call Count', 'AHT', 'Hold', 'Wrap']
                perf_units = ['calls', 'seconds', 'seconds', 'seconds']
                for col, unit in zip(perf_cols, perf_units):
                    val = data[col].values[0]
                    st.write(f"**{col}**: {val} {unit}")

                st.subheader("KPI Scores")
                kpi_weights = {
                    "PKT": 40,
                    "CSAT (Resolution)": 30,
                    "CSAT (Agent Behaviour)": 20,
                    "Quality": 10
                }
                for metric, weight in kpi_weights.items():
                    score = data.get(metric, ["N/A"])[0]
                    st.write(f"**{metric}** (Weight: {weight}%): {score}")

                st.subheader("Comparison with Previous Month")
                months = sorted(df_month['Month'].unique())
                current_index = months.index(month)
                if current_index > 0:
                    prev_month = months[current_index - 1]
                    prev_data = df_month[df_month['Month'] == prev_month]
                    if not prev_data.empty:
                        current_score = data['Grand Total KPI'].values[0]
                        prev_score = prev_data['Grand Total KPI'].values[0]
                        st.write(f"**{month} KPI**: {current_score}")
                        st.write(f"**{prev_month} KPI**: {prev_score}")

                st.subheader("Motivational Quote")
                kpi = data['Grand Total KPI'].values[0]
                try:
                    kpi = float(kpi)
                    if kpi >= 90:
                        st.success("Excellent work! Keep it up 💪")
                    elif kpi >= 75:
                        st.info("You're doing good. Aim for more 🌟")
                    else:
                        st.warning("Let's push harder next month 🚀")
                except:
                    st.write("KPI score not available")

                st.subheader("Target Committed")
                for target_col in [
                    'Target Committed for PKT',
                    'Target Committed for CSAT (Agent Behaviour)',
                    'Target Committed for Quality']:
                    val = data.get(target_col, ["N/A"])[0]
                    st.write(f"**{target_col}**: {val}")
            else:
                st.error("No data found for selected month.")
    else:
        st.warning("Only monthly view is currently supported. Weekly and daily views coming soon.")
