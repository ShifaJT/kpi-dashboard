import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import calendar

st.set_page_config(page_title="KPI Dashboard for Champs", layout="centered")

# Load credentials from Streamlit secrets
service_account_info = st.secrets["gcp_service_account"]
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
client = gspread.authorize(creds)

# Fetch data
kpi_month_df = pd.DataFrame(client.open("YTD KPI Sheet").worksheet("KPI Month").get_all_records())
daily_df = pd.DataFrame(client.open("YTD KPI Sheet").worksheet("KPI Day").get_all_records())
csat_df = pd.DataFrame(client.open("YTD KPI Sheet").worksheet("CSAT Score").get_all_records())

# Ensure correct types
daily_df['Date'] = pd.to_datetime(daily_df['Date'], format="%m/%d/%Y", errors='coerce')
daily_df['Week'] = daily_df['Week'].astype(str)
csat_df['Week'] = csat_df['Week'].astype(str)

st.title("KPI Dashboard for Champs")

emp_id = st.text_input("Enter EMP ID")

if emp_id:
    view_type = st.selectbox("Select View Type", ["Day", "Week", "Month"])

    if view_type == "Day":
        available_dates = daily_df[daily_df["EMP ID"] == emp_id]["Date"].dropna().dt.strftime("%d-%m-%Y").unique()
        selected_date = st.selectbox("Select Date", sorted(available_dates))

        if selected_date:
            parsed_date = datetime.strptime(selected_date, "%d-%m-%Y")
            emp_day_data = daily_df[(daily_df["EMP ID"] == emp_id) & (daily_df["Date"] == parsed_date)]

            if not emp_day_data.empty:
                st.subheader("Performance (Day)")
                st.dataframe(emp_day_data.drop(columns=["EMP ID", "Date", "Week"]))
            else:
                st.warning("No daily data found.")

    elif view_type == "Week":
        weeks = daily_df[daily_df["EMP ID"] == emp_id]["Week"].dropna().unique()
        selected_week = st.selectbox("Select Week", sorted(weeks))

        if selected_week:
            week_data = daily_df[(daily_df["EMP ID"] == emp_id) & (daily_df["Week"] == selected_week)]

            if not week_data.empty:
                call_count = week_data["Call Count"].astype(float).sum()
                aht = week_data["AHT"].astype(float).mean()
                hold = week_data["Hold"].astype(float).mean()
                wrap = week_data["Wrap"].astype(float).mean()

                csat_row = csat_df[(csat_df["EMP ID"] == emp_id) & (csat_df["Week"] == selected_week)]
                csat_res = csat_row["CSAT Resolution"].values[0] if not csat_row.empty else "N/A"
                csat_beh = csat_row["CSAT Behaviour"].values[0] if not csat_row.empty else "N/A"

                perf = {
                    "Call Count": call_count,
                    "AHT": round(aht, 2),
                    "Hold": round(hold, 2),
                    "Wrap": round(wrap, 2),
                    "CSAT Resolution": csat_res,
                    "CSAT Behaviour": csat_beh
                }

                st.subheader("Performance (Week)")
                st.dataframe(pd.DataFrame(perf.items(), columns=["Metric", "Value"]))
            else:
                st.warning("No weekly data found.")

    elif view_type == "Month":
        months = kpi_month_df[kpi_month_df["EMP ID"] == emp_id]["Month"].unique()
        selected_month = st.selectbox("Select Month", sorted(months))

        if selected_month:
            emp_month_data = kpi_month_df[(kpi_month_df["EMP ID"] == emp_id) & (kpi_month_df["Month"] == selected_month)]

            if not emp_month_data.empty:
                perf_cols = ["Hold", "Wrap", "Auto-On", "Schedule Adherence", "Resolution CSAT", "Agent Behaviour", "Quality", "PKT", "SL + UPL", "LOGINS"]
                kpi_cols = ["Hold KPI Score", "Wrap KPI Score", "Auto-On KPI Score", "Schedule Adherence KPI Score", "Resolution CSAT KPI Score", "Agent Behaviour KPI Score", "Quality KPI Score", "PKT KPI Score", "Grand Total"]
                target_cols = [
                    "Target Committed for PKT",
                    "Target Committed for CSAT (Agent Behaviour)",
                    "Target Committed for Quality"
                ]

                perf_data = emp_month_data[perf_cols].T.reset_index()
                perf_data.columns = ["Metric", "Value"]
                st.subheader("Performance (Month)")
                st.dataframe(perf_data)

                kpi_data = emp_month_data[kpi_cols].T.reset_index()
                kpi_data.columns = ["KPI Metric", "Score"]
                st.subheader("KPI Scores")
                st.dataframe(kpi_data)

                target_data = emp_month_data[target_cols].T.reset_index()
                target_data.columns = ["Target Committed", "Value"]
                st.subheader("Targets Committed for Next Month")
                st.dataframe(target_data)
            else:
                st.warning("No monthly data found.")
