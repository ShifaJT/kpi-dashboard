import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe
from datetime import datetime

# --- Authenticate with Google Sheets ---
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
client = gspread.authorize(creds)

# --- Sheet References ---
sheet_kpi_month = client.open("Your Google Sheet Name").worksheet("KPI Month")
sheet_kpi_day = client.open("Your Google Sheet Name").worksheet("KPI Day")
sheet_csat_score = client.open("Your Google Sheet Name").worksheet("CSAT Score")

# --- Title ---
st.title("KPI Dashboard")

# --- Inputs ---
emp_id = st.text_input("Enter EMP ID")
view_option = st.selectbox("View Type", ["Month", "Week", "Day"])

if emp_id:
    if view_option == "Month":
        month_input = st.selectbox("Select Month", pd.date_range("2024-01-01", periods=12, freq='MS').strftime("%B"))
        df_month = pd.DataFrame(sheet_kpi_month.get_all_records())

        df_filtered = df_month[(df_month["EMP ID"] == emp_id) & (df_month["Month"] == month_input)]
        if not df_filtered.empty:
            st.subheader("Performance")
            st.dataframe(df_filtered[["EMP ID", "NAME", "Month", "Call Count", "AHT", "Wrap", "Hold"]])

            st.subheader("KPI Scores")
            st.dataframe(df_filtered[["PKT Score", "CSAT Score (Agent Behaviour)", "Quality Score", "Grand Total"]])

            st.subheader("Targets Committed")
            st.write("Target Committed for PKT:", df_filtered["Target Committed for PKT"].values[0])
            st.write("Target Committed for CSAT (Agent Behaviour):", df_filtered["Target Committed for CSAT (Agent Behaviour)"].values[0])
            st.write("Target Committed for Quality:", df_filtered["Target Committed for Quality"].values[0])
        else:
            st.warning("No monthly data found for this EMP ID.")

    elif view_option == "Day":
        date_input = st.date_input("Select Date")
        df_day = pd.DataFrame(sheet_kpi_day.get_all_records())
        df_day["Date"] = pd.to_datetime(df_day["Date"], format="%m/%d/%Y")

        df_filtered = df_day[(df_day["EMP ID"] == emp_id) & (df_day["Date"] == pd.to_datetime(date_input))]
        if not df_filtered.empty:
            st.subheader("Daily Data")
            st.dataframe(df_filtered)
        else:
            st.warning("No daily data found for this EMP ID and date.")

    elif view_option == "Week":
        week_input = st.text_input("Enter Week (e.g. Week 1)")
        df_day = pd.DataFrame(sheet_kpi_day.get_all_records())
        df_csat = pd.DataFrame(sheet_csat_score.get_all_records())

        df_day = df_day[df_day["EMP ID"] == emp_id]
        df_csat = df_csat[df_csat["EMP ID"] == emp_id]

        df_day_week = df_day[df_day["Week"] == week_input]
        df_csat_week = df_csat[df_csat["Week"] == week_input]

        if not df_day_week.empty:
            # Calculate average/sum of weekly performance
            call_count = df_day_week["Call Count"].astype(float).sum()
            aht = df_day_week["AHT"].astype(float).mean()
            hold = df_day_week["Hold"].astype(float).mean()
            wrap = df_day_week["Wrap"].astype(float).mean()

            st.subheader("Weekly Performance")
            st.write("Call Count:", round(call_count, 2))
            st.write("AHT:", round(aht, 2))
            st.write("Hold:", round(hold, 2))
            st.write("Wrap:", round(wrap, 2))
        else:
            st.warning("No weekly performance data found.")

        if not df_csat_week.empty:
            st.subheader("Weekly CSAT")
            st.write("CSAT Resolution:", df_csat_week["CSAT Resolution"].values[0])
            st.write("CSAT Behaviour:", df_csat_week["CSAT Behaviour"].values[0])
        else:
            st.warning("No CSAT data for selected week.")

