import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe
from datetime import datetime
import calendar

# --- Authenticate with Google Sheets ---
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
client = gspread.authorize(creds)

# --- Load Sheets ---
sheet = client.open("KPI Dashboard")
kpi_month = sheet.worksheet("KPI Month")
kpi_day = sheet.worksheet("KPI Day")
csat_score = sheet.worksheet("CSAT Score")

# --- Streamlit UI ---
st.title("📊 KPI Dashboard")

emp_id = st.text_input("Enter EMP ID")
view_type = st.selectbox("Select View", ["Month", "Week", "Day"])

def get_month_name(month_num):
    return calendar.month_name[int(month_num)]

# --- Main Logic ---
if emp_id:
    if view_type == "Month":
        df = pd.DataFrame(kpi_month.get_all_records())
        df = df[df["EMP ID"] == emp_id]

        months = df["Month"].unique().tolist()
        selected_month = st.selectbox("Select Month", months)

        data = df[df["Month"] == selected_month]

        if not data.empty:
            name = data["NAME"].values[0]

            st.subheader(f"Performance for {name} - {selected_month}")
            performance = {
                "Description": ["Total Calls", "Average AHT", "Average Hold", "Average Wrap"],
                "Metric Name": ["Call Count", "AHT", "Hold", "Wrap"],
                "Value": [
                    data["Call Count"].values[0],
                    data["AHT"].values[0],
                    data["Hold"].values[0],
                    data["Wrap"].values[0]
                ],
                "Unit": ["Calls", "Minutes", "Minutes", "Minutes"]
            }
            st.dataframe(pd.DataFrame(performance))

            st.subheader("KPI Scores & Weightage")
            kpi = {
                "KPI Metrics": ["PKT Score", "CSAT Score (Agent Behaviour)", "Quality Score", "Grand Total"],
                "Score": [
                    data["PKT Score"].values[0],
                    data["CSAT Score (Agent Behaviour)"].values[0],
                    data["Quality Score"].values[0],
                    data["Grand Total"].values[0]
                ],
                "Weightage": ["40%", "30%", "30%", "100%"]
            }
            st.dataframe(pd.DataFrame(kpi))

            st.subheader("Target Committed")
            st.write("🎯 **PKT**:", data["Target Committed for PKT"].values[0])
            st.write("🎯 **CSAT (Agent Behaviour)**:", data["Target Committed for CSAT (Agent Behaviour)"].values[0])
            st.write("🎯 **Quality**:", data["Target Committed for Quality"].values[0])

            # Month-over-month comparison
            all_months = df["Month"].tolist()
            idx = all_months.index(selected_month)
            if idx > 0:
                prev_month = all_months[idx - 1]
                prev_data = df[df["Month"] == prev_month]
                if not prev_data.empty:
                    prev_score = prev_data["Grand Total"].values[0]
                    curr_score = data["Grand Total"].values[0]
                    diff = round(curr_score - prev_score, 2)
                    st.markdown(f"📈 **Grand Total Change from {prev_month}**: {diff:+}")
            else:
                st.info("No previous month data for comparison.")

            # Motivational message
            grand_total = data["Grand Total"].values[0]
            if grand_total >= 90:
                st.success("🌟 Excellent work! You're a star performer!")
            elif grand_total >= 75:
                st.info("👍 Good job! Keep pushing to reach the top!")
            else:
                st.warning("🚀 Let’s aim higher next month!")

        else:
            st.error("No data found for this month.")

    elif view_type == "Day":
        date_input = st.date_input("Select Date")
        df_day = pd.DataFrame(kpi_day.get_all_records())
        df_day["Date"] = pd.to_datetime(df_day["Date"], format="%m/%d/%Y")

        data = df_day[(df_day["EMP ID"] == emp_id) & (df_day["Date"] == pd.to_datetime(date_input))]
        if not data.empty:
            st.subheader("Daily Data")
            st.dataframe(data)
        else:
            st.warning("No data for this EMP ID on selected date.")

    elif view_type == "Week":
        week_input = st.text_input("Enter Week (e.g. Week 1)")
        df_day = pd.DataFrame(kpi_day.get_all_records())
        df_csat = pd.DataFrame(csat_score.get_all_records())

        df_day = df_day[df_day["EMP ID"] == emp_id]
        df_csat = df_csat[df_csat["EMP ID"] == emp_id]

        df_week = df_day[df_day["Week"] == week_input]
        csat_week = df_csat[df_csat["Week"] == week_input]

        if not df_week.empty:
            st.subheader("Weekly Performance")

            call_count = df_week["Call Count"].astype(float).sum()
            aht = df_week["AHT"].astype(float).mean()
            hold = df_week["Hold"].astype(float).mean()
            wrap = df_week["Wrap"].astype(float).mean()

            st.write("📞 Call Count:", round(call_count))
            st.write("🕒 AHT:", round(aht, 2))
            st.write("✋ Hold:", round(hold, 2))
            st.write("🎬 Wrap:", round(wrap, 2))
        else:
            st.warning("No weekly performance data.")

        if not csat_week.empty:
            st.subheader("Weekly CSAT")
            st.write("✅ CSAT Resolution:", csat_week["CSAT Resolution"].values[0])
            st.write("🤝 CSAT Behaviour:", csat_week["CSAT Behaviour"].values[0])
        else:
            st.warning("No CSAT data for this week.")
