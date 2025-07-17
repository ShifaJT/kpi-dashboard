import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# === CONFIG ===
SHEET_ID = "19aDfELEExMn0loj_w6D69ngGG4haEm6lsgqpxJC1OAA"
MONTHLY_SHEET_NAME = "KPI Month"
DAILY_SHEET_NAME = "KPI Day"

# === Google Auth ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)
monthly_ws = sheet.worksheet(MONTHLY_SHEET_NAME)
daily_ws = sheet.worksheet(DAILY_SHEET_NAME)

@st.cache_data
def load_monthly_data():
    return pd.DataFrame(monthly_ws.get_all_records())

@st.cache_data
def load_daily_data():
    return pd.DataFrame(daily_ws.get_all_records())

monthly_df = load_monthly_data()
daily_df = load_daily_data()

st.title("KPI Dashboard for Champs")

emp_id = st.text_input("Enter EMP ID")
view_type = st.selectbox("Select View Type", ["Month", "Week", "Day"])

# Dynamic selection
selection = None
if view_type == "Month":
    def month_num(month_name):
        try:
            return datetime.strptime(month_name, "%B").month
        except:
            return 13
    month_options = sorted(monthly_df['Month'].dropna().unique(), key=month_num)
    selection = st.selectbox("Select Month", month_options)

elif view_type == "Week":
    week_options = sorted(daily_df['Week'].dropna().unique())
    selection = st.selectbox("Select Week", week_options)

elif view_type == "Day":
    def safe_parse_date(date_str):
        try:
            return datetime.strptime(date_str, "%d-%m-%Y")
        except:
            return datetime.max
    dates = sorted(daily_df['Date'].dropna().unique(), key=safe_parse_date)
    selection = st.selectbox("Select Date", dates)

# Main processing
if emp_id and selection:
    if view_type == "Month":
        emp_data = monthly_df[(monthly_df["EMP ID"].astype(str) == emp_id) & (monthly_df["Month"] == selection)]
        if emp_data.empty:
            st.warning("No data found.")
        else:
            emp_data = emp_data.iloc[0]

            st.subheader("🔹 Performance Metrics")
            perf_table = [
                ["Average hold used", "Hold", emp_data.get("Hold", "N/A"), "HH:MM:SS"],
                ["Average time taken to wrap the call", "Wrap", emp_data.get("Wrap", "N/A"), "HH:MM:SS"],
                ["Average duration of champ using auto on", "Auto-On", emp_data.get("Auto-On", "N/A"), "HH:MM:SS"],
                ["Shift adherence for the month", "Schedule Adherence", emp_data.get("Schedule Adherence", "N/A"), "%"],
                ["Customer feedback on resolution given", "Resolution CSAT", emp_data.get("Resolution CSAT", "N/A"), "%"],
                ["customer feedback on champ behaviour", "Agent Behaviour", emp_data.get("Agent Behaviour", "N/A"), "%"],
                ["Average Quality Score achieved for the month", "Quality", emp_data.get("Quality", "N/A"), "%"],
                ["Process knowledge test", "PKT", emp_data.get("PKT", "N/A"), "%"],
                ["Number of sick and unplanned leaves", "SL + UPL", emp_data.get("SL + UPL", "N/A"), "Days"],
                ["Number of days logged in", "LOGINS", emp_data.get("LOGINS", "N/A"), "Days"],
            ]
            st.dataframe(pd.DataFrame(perf_table, columns=["Description", "Metric Name", "Value", "Unit"]), use_container_width=True)

            st.subheader("✅ KPI Scores")
            kpi_weights = {
                "Hold KPI Score": 0,
                "Wrap KPI Score": 0,
                "Auto-On KPI Score": 30,
                "Schedule Adherence KPI Score": 10,
                "Resolution CSAT KPI Score": 10,
                "Agent Behaviour KPI Score": 20,
                "Quality KPI Score": 20,
                "PKT KPI Score": 10,
            }
            kpi_data = [[f"{weight}%", kpi, emp_data.get(kpi, "N/A")] for kpi, weight in kpi_weights.items()]
            st.dataframe(pd.DataFrame(kpi_data, columns=["Weightage", "KPI Metrics", "Score"]), use_container_width=True)

            st.subheader("🏁 Grand Total")
            grand_total = emp_data.get("Grand Total", 0)
            st.metric("Grand Total KPI", grand_total)

            prev_data_all = monthly_df[monthly_df["EMP ID"].astype(str) == emp_id]
            prev_data_all["Month_num"] = prev_data_all["Month"].apply(month_num)
            prev_data_all = prev_data_all.sort_values("Month_num")
            current_index = prev_data_all[prev_data_all["Month"] == selection].index[0]
            prev_index = current_index - 1

            if prev_index in prev_data_all.index:
                prev_month = prev_data_all.loc[prev_index, "Month"]
                prev_total = prev_data_all.loc[prev_index, "Grand Total"]
                delta = round(grand_total - prev_total, 2)
                trend = "improved" if delta > 0 else "dropped"
                st.success(f"You {trend} by {delta:+} points since last month ({prev_month})!")

                # Motivation
                if grand_total >= 4.5:
                    st.info("Outstanding performance! Keep setting the benchmark.")
                elif grand_total >= 4:
                    st.info("Great job! Let's aim even higher.")
                elif grand_total >= 3:
                    st.info("You're on the right track. Keep pushing!")
                else:
                    st.info("Let’s work together and improve next month!")

            st.subheader("🎯 Target Committed for Next Month")
            pkt = emp_data.get("Target Committed for PKT", "N/A")
            csat = emp_data.get("Target Committed for CSAT (Agent Behaviour)", "N/A")
            quality = emp_data.get("Target Committed for Quality", "N/A")

            if any(val != "N/A" for val in [pkt, csat, quality]):
                st.write(f"**Target Committed for PKT**: {pkt}")
                st.write(f"**Target Committed for CSAT (Agent Behaviour)**: {csat}")
                st.write(f"**Target Committed for Quality**: {quality}")
            else:
                st.warning("No target data available.")

    elif view_type == "Week":
        weekly_data = daily_df[(daily_df["EMP ID"].astype(str) == emp_id) & (daily_df["Week"] == selection)]
        if weekly_data.empty:
            st.warning("No weekly data found.")
        else:
            weekly_data.replace("", 0, inplace=True)
            weekly_data.fillna(0, inplace=True)

            sum_call = pd.to_numeric(weekly_data["Call Count"], errors="coerce").sum()

            avg_cols = ["AHT", "Hold", "Wrap", "CSAT Resolution", "CSAT Behaviour"]
            for col in avg_cols:
                weekly_data[col] = pd.to_numeric(weekly_data[col], errors="coerce")

            avg_vals = weekly_data[avg_cols].mean().round(2)

            table = [["Total Calls Handled", "Call Count", sum_call, "Count"]]
            table += [[f"Average {col}", col, avg_vals[col], ""] for col in avg_cols]

            st.subheader("🔹 Weekly Performance")
            st.dataframe(pd.DataFrame(table, columns=["Description", "Metric Name", "Value", "Unit"]), use_container_width=True)

    elif view_type == "Day":
        day_data = daily_df[(daily_df["EMP ID"].astype(str) == emp_id) & (daily_df["Date"] == selection)]
        if day_data.empty:
            st.warning("No daily data found.")
        else:
            day_data = day_data.iloc[0]
            table = [
                ["Total Calls Handled", "Call Count", day_data.get("Call Count", "N/A"), "Count"],
                ["Average AHT", "AHT", day_data.get("AHT", "N/A"), ""],
                ["Average Hold", "Hold", day_data.get("Hold", "N/A"), ""],
                ["Average Wrap", "Wrap", day_data.get("Wrap", "N/A"), ""],
                ["CSAT Resolution", "CSAT Resolution", day_data.get("CSAT Resolution", "N/A"), "%"],
                ["CSAT Behaviour", "CSAT Behaviour", day_data.get("CSAT Behaviour", "N/A"), "%"],
            ]
            st.subheader("🔹 Daily Performance")
            st.dataframe(pd.DataFrame(table, columns=["Description", "Metric Name", "Value", "Unit"]), use_container_width=True)
