import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# === CONFIG ===
SHEET_ID = "19aDfELEExMn0loj_w6D69ngGG4haEm6lsgqpxJC1OAA"
SHEET_MONTHLY = "KPI Month"
SHEET_DAILY = "KPI Day"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)

monthly_df = pd.DataFrame(sheet.worksheet(SHEET_MONTHLY).get_all_records())
daily_df = pd.DataFrame(sheet.worksheet(SHEET_DAILY).get_all_records())

st.title("📊 KPI Dashboard for Champs")

emp_id = st.text_input("Enter EMP ID")
view_type = st.selectbox("Select View Type", ["Month", "Week", "Day"])

if not emp_id:
    st.stop()

if view_type == "Month":
    month = st.selectbox("Select Month", sorted(monthly_df['Month'].unique()))
    emp_data = monthly_df[(monthly_df['EMP ID'].astype(str) == emp_id) & (monthly_df['Month'] == month)]

    if emp_data.empty:
        st.warning("No data found.")
    else:
        emp_data = emp_data.iloc[0]
        st.subheader("🔹 Performance Metrics")
        performance = [
            ["Average hold used", "Hold", emp_data["Hold"], "HH:MM:SS"],
            ["Average time taken to wrap the call", "Wrap", emp_data["Wrap"], "HH:MM:SS"],
            ["Average duration of champ using auto on", "Auto-On", emp_data["Auto-On"], "HH:MM:SS"],
            ["Shift adherence for the month", "Schedule Adherence", emp_data["Schedule Adherence"], "%"],
            ["Customer feedback on resolution given", "Resolution CSAT", emp_data["Resolution CSAT"], "%"],
            ["customer feedback on champ behaviour", "Agent Behaviour", emp_data["Agent Behaviour"], "%"],
            ["Average Quality Score achieved for the month", "Quality", emp_data["Quality"], "%"],
            ["Process knowledge test", "PKT", emp_data["PKT"], "%"],
            ["Number of sick and unplanned leaves", "SL + UPL", emp_data["SL + UPL"], "Days"],
            ["Number of days logged in", "LOGINS", emp_data["LOGINS"], "Days"],
        ]
        perf_df = pd.DataFrame(performance, columns=["Description", "Metric Name", "Value", "Unit"])
        st.dataframe(perf_df, use_container_width=True)

        st.subheader("✅ KPI Scores")
        kpi = [
            ["0%", "Hold KPI Score", emp_data["Hold KPI Score"]],
            ["30%", "Auto-On KPI Score", emp_data["Auto-On KPI Score"]],
            ["10%", "Schedule Adherence KPI Score", emp_data["Schedule Adherence KPI Score"]],
            ["10%", "Resolution CSAT KPI Score", emp_data["Resolution CSAT KPI Score"]],
            ["20%", "Agent Behaviour KPI Score", emp_data["Agent Behaviour KPI Score"]],
            ["20%", "Quality KPI Score", emp_data["Quality KPI Score"]],
            ["10%", "PKT KPI Score", emp_data["PKT KPI Score"]],
        ]
        kpi_df = pd.DataFrame(kpi, columns=["Weightage", "KPI Metrics", "Score"])
        st.dataframe(kpi_df, use_container_width=True)

        st.subheader("🏁 Grand Total")
        grand_total = emp_data['Grand Total']
        st.metric("Grand Total KPI", f"{grand_total}")

        # Motivational Message
        if grand_total >= 4.5:
            st.success("Outstanding performance! Keep it up!")
        elif grand_total >= 3.5:
            st.info("Good job! Aim even higher next month.")
        else:
            st.warning("Let’s improve! We believe in you.")

        # Previous Month Comparison
        months = sorted(monthly_df['Month'].unique())
        current_index = months.index(month)
        if current_index > 0:
            prev_month = months[current_index - 1]
            prev_data = monthly_df[(monthly_df['EMP ID'].astype(str) == emp_id) & (monthly_df['Month'] == prev_month)]
            if not prev_data.empty:
                prev_score = prev_data.iloc[0]['Grand Total']
                diff = round(grand_total - prev_score, 2)
                st.markdown(f"You {'improved' if diff >= 0 else 'dropped'} by {diff:+} points since last month ({prev_month})")

        # Target Committed
        st.subheader("🎯 Target Committed for Next Month")
        targets = [
            ["Target Committed for PKT", emp_data.get("Target Committed for PKT", "Not available")],
            ["Target Committed for CSAT (Agent Behaviour)", emp_data.get("Target Committed for CSAT (Agent Behaviour)", "Not available")],
            ["Target Committed for Quality", emp_data.get("Target Committed for Quality", "Not available")],
        ]
        st.table(pd.DataFrame(targets, columns=["Target", "Value"]))

elif view_type == "Day":
    available_dates = sorted(daily_df['Date'].unique())
    selected_date = st.selectbox("Select Date", available_dates)
    filtered = daily_df[(daily_df['EMP ID'].astype(str) == emp_id) & (daily_df['Date'] == selected_date)]
    if filtered.empty:
        st.warning("No data found for selected day.")
    else:
        filtered = filtered.iloc[0]
        perf = [
            ["Call count handled", "Call Count", filtered['Call Count'], "Count"],
            ["Average handle time", "AHT", filtered['AHT'], "HH:MM:SS"],
            ["Hold time", "Hold", filtered['Hold'], "HH:MM:SS"],
            ["Wrap time", "Wrap", filtered['Wrap'], "HH:MM:SS"],
            ["Resolution CSAT", "CSAT Resolution", filtered['CSAT Resolution'], "%"],
            ["Behaviour CSAT", "CSAT Behaviour", filtered['CSAT Behaviour'], "%"],
        ]
        st.dataframe(pd.DataFrame(perf, columns=["Description", "Metric Name", "Value", "Unit"]))

elif view_type == "Week":
    week_numbers = sorted(daily_df['Week'].dropna().unique())
    selected_week = st.selectbox("Select Week Number", week_numbers)
    weekly_data = daily_df[(daily_df['EMP ID'].astype(str) == emp_id) & (daily_df['Week'] == selected_week)]

    if weekly_data.empty:
        st.warning("No data for selected week.")
    else:
        avg_data = weekly_data[['Call Count', 'AHT', 'Hold', 'Wrap', 'CSAT Resolution', 'CSAT Behaviour']].astype(str)
        avg_df = weekly_data[['Call Count', 'CSAT Resolution', 'CSAT Behaviour']].astype(float).mean().round(2)
        perf = [
            ["Avg Call count handled", "Call Count", avg_df['Call Count'], "Count"],
            ["Avg handle time", "AHT", weekly_data['AHT'].iloc[0], "HH:MM:SS"],
            ["Avg Hold time", "Hold", weekly_data['Hold'].iloc[0], "HH:MM:SS"],
            ["Avg Wrap time", "Wrap", weekly_data['Wrap'].iloc[0], "HH:MM:SS"],
            ["Avg Resolution CSAT", "CSAT Resolution", avg_df['CSAT Resolution'], "%"],
            ["Avg Behaviour CSAT", "CSAT Behaviour", avg_df['CSAT Behaviour'], "%"],
        ]
        st.dataframe(pd.DataFrame(perf, columns=["Description", "Metric Name", "Value", "Unit"]))
