import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from datetime import datetime

# === SETUP GOOGLE SHEET ACCESS ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPES
)
client = gspread.authorize(credentials)
sheet_id = "19aDfELEExMn0loj_w6D69ngGG4haEm6lsgqpxJC1OAA"

# === LOAD SHEETS ===
kpi_month = pd.DataFrame(client.open_by_key(sheet_id).worksheet("KPI Month").get_all_records())
kpi_day = pd.DataFrame(client.open_by_key(sheet_id).worksheet("KPI Day").get_all_records())
csat_score = pd.DataFrame(client.open_by_key(sheet_id).worksheet("CSAT Score").get_all_records())

# === STREAMLIT UI ===
st.title("📊 KPI Dashboard")
st.markdown("---")

emp_id = st.text_input("Enter EMP ID")
view_type = st.selectbox("Select View", ["Month", "Week", "Day"])

if emp_id:
    if view_type == "Month":
        month = st.selectbox("Select Month", sorted(kpi_month["Month"].unique()))
        data = kpi_month[(kpi_month["EMP ID"] == emp_id) & (kpi_month["Month"] == month)]

        if not data.empty:
            st.subheader("Performance")
            st.dataframe(data[["Call Count", "AHT", "Hold", "Wrap"]])

            st.subheader("KPI Scores")
            st.dataframe(data[["PKT", "CSAT (Agent Behaviour)", "Quality"]])

            st.subheader("Target Committed")
            st.dataframe(data[[
                "Target Committed for PKT",
                "Target Committed for CSAT (Agent Behaviour)",
                "Target Committed for Quality"
            ]])

            st.subheader("Motivational Message")
            grand_total = data["Grand Total KPI"].values[0]
            if grand_total >= 90:
                st.success("🚀 Outstanding! Keep pushing boundaries!")
            elif grand_total >= 75:
                st.info("👏 Good job! Let’s aim higher next month.")
            else:
                st.warning("💡 You’ve got potential! Let’s bounce back stronger.")

            # Previous Month Comparison
            all_months = sorted(kpi_month["Month"].unique())
            current_index = all_months.index(month)
            if current_index > 0:
                previous_month = all_months[current_index - 1]
                prev_data = kpi_month[(kpi_month["EMP ID"] == emp_id) & (kpi_month["Month"] == previous_month)]
                if not prev_data.empty:
                    prev_score = prev_data["Grand Total KPI"].values[0]
                    st.markdown(f"### 📈 Previous Month ({previous_month}) KPI Score: {prev_score}")
        else:
            st.error("No data found for selected EMP ID and Month.")

    elif view_type == "Week":
        selected_week = st.selectbox("Select Week", sorted(csat_score["Week"].unique()))
        day_data = kpi_day[(kpi_day["EMP ID"] == emp_id) & (kpi_day["Week"] == selected_week)]
        csat_data = csat_score[(csat_score["EMP ID"] == emp_id) & (csat_score["Week"] == selected_week)]

        if not day_data.empty:
            agg = {
                "Call Count": "sum",
                "AHT": "mean",
                "Hold": "mean",
                "Wrap": "mean"
            }
            weekly_perf = day_data.agg(agg)
            st.subheader("Weekly Performance")
            st.dataframe(weekly_perf.to_frame(name="Value"))
        else:
            st.warning("No weekly performance data found.")

        if not csat_data.empty:
            st.subheader("Weekly CSAT")
            st.dataframe(csat_data[["CSAT Resolution", "CSAT Behaviour"]])

    elif view_type == "Day":
        selected_date = st.date_input("Select Date")
        formatted_date = selected_date.strftime("%m/%d/%Y")
        day_data = kpi_day[(kpi_day["EMP ID"] == emp_id) & (kpi_day["Date"] == formatted_date)]

        if not day_data.empty:
            st.subheader("Daily Performance")
            st.dataframe(day_data[["Call Count", "AHT", "Hold", "Wrap", "CSAT Resolution", "CSAT Behaviour"]])
        else:
            st.warning("No data found for selected date.")
