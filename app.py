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
    data = monthly_ws.get_all_records()
    return pd.DataFrame(data)

@st.cache_data
def load_daily_data():
    data = daily_ws.get_all_records()
    return pd.DataFrame(data)

monthly_df = load_monthly_data()
daily_df = load_daily_data()

st.title("KPI Dashboard for Champs")

emp_id = st.text_input("Enter EMP ID")
view_type = st.selectbox("Select View Type", ["Month", "Week", "Day"])

# Entry selection based on view
selection = None
if view_type == "Month":
    selection = st.selectbox("Select Month", sorted(monthly_df['Month'].unique(), key=lambda x: datetime.strptime(x, "%B")))
elif view_type == "Week":
    selection = st.selectbox("Select Week", sorted(daily_df['Week'].unique()))
elif view_type == "Day":
    selection = st.selectbox("Select Date", sorted(daily_df['Date'].unique(), key=lambda x: datetime.strptime(x, "%d-%m-%Y")))

if emp_id and selection:
    if view_type == "Month":
        df = monthly_df
        emp_data = df[(df["EMP ID"].astype(str) == emp_id) & (df["Month"] == selection)]

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
            perf_df = pd.DataFrame(perf_table, columns=["Description", "Metric Name", "Value", "Unit"])
            st.dataframe(perf_df, use_container_width=True)

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
            kpi_df = pd.DataFrame(kpi_data, columns=["Weightage", "KPI Metrics", "Score"])
            st.dataframe(kpi_df, use_container_width=True)

            st.subheader("🏁 Grand Total")
            grand_total = emp_data.get("Grand Total", 0)
            st.metric("Grand Total KPI", grand_total)

            prev_months = monthly_df[(monthly_df["EMP ID"].astype(str) == emp_id)]
            prev_months_sorted = sorted(prev_months['Month'].unique(), key=lambda x: datetime.strptime(x, "%B"))
            current_index = prev_months_sorted.index(selection)
            if current_index > 0:
                prev_month = prev_months_sorted[current_index - 1]
                prev_data = prev_months[prev_months['Month'] == prev_month]
                if not prev_data.empty:
                    prev_total = prev_data.iloc[0].get("Grand Total", 0)
                    delta = round(grand_total - prev_total, 2)
                    trend = "improved" if delta > 0 else "dropped"
                    st.success(f"You {trend} by {delta:+} points since last month ({prev_month})!")

                    if grand_total >= 4.5:
                        st.info("Outstanding performance! Keep setting the benchmark.")
                    elif grand_total >= 4:
                        st.info("Great job! Let's aim even higher.")
                    elif grand_total >= 3:
                        st.info("You're on the right track. Keep pushing!")
                    else:
                        st.info("Let’s work together and improve next month!")

            st.subheader("🎯 Target Committed for Next Month")
            tc_pkt = emp_data.get("Target Committed for PKT", "N/A")
            tc_csat = emp_data.get("Target Committed for CSAT (Agent Behaviour)", "N/A")
            tc_quality = emp_data.get("Target Committed for Quality", "N/A")

            if any(val != "N/A" for val in [tc_pkt, tc_csat, tc_quality]):
                st.write(f"**Target Committed for PKT**: {tc_pkt}")
                st.write(f"**Target Committed for CSAT (Agent Behaviour)**: {tc_csat}")
                st.write(f"**Target Committed for Quality**: {tc_quality}")
            else:
                st.warning("No target data available.")

    elif view_type == "Week":
        df = daily_df
        weekly_data = df[(df['EMP ID'].astype(str) == emp_id) & (df['Week'] == selection)]

        if weekly_data.empty:
            st.warning("No weekly data found.")
        else:
            weekly_data = weekly_data.replace("", "0")
            weekly_data = weekly_data.fillna(0)
            weekly_data["Call Count"] = pd.to_numeric(weekly_data["Call Count"], errors="coerce")
            sum_call = weekly_data["Call Count"].sum()

            avg_cols = ["AHT", "Hold", "Wrap", "CSAT Resolution", "CSAT Behaviour"]
            avg_vals = weekly_data[avg_cols].apply(pd.to_numeric, errors="coerce").mean().round(2)

            st.subheader("🔹 Weekly Performance")
            perf_table = [["Total Calls Handled", "Call Count", sum_call, "Count"]]
            perf_table += [[f"Average {col}", col, avg_vals[col], ""] for col in avg_cols]
            perf_df = pd.DataFrame(perf_table, columns=["Description", "Metric Name", "Value", "Unit"])
            st.dataframe(perf_df, use_container_width=True)

    elif view_type == "Day":
        df = daily_df
        daily_data = df[(df['EMP ID'].astype(str) == emp_id) & (df['Date'] == selection)]

        if daily_data.empty:
            st.warning("No daily data found.")
        else:
            daily_data = daily_data.iloc[0]
            st.subheader("🔹 Daily Performance")
            perf_table = [
                ["Total Calls Handled", "Call Count", daily_data.get("Call Count", "N/A"), "Count"],
                ["Average AHT", "AHT", daily_data.get("AHT", "N/A"), ""],
                ["Average Hold", "Hold", daily_data.get("Hold", "N/A"), ""],
                ["Average Wrap", "Wrap", daily_data.get("Wrap", "N/A"), ""],
                ["CSAT Resolution", "CSAT Resolution", daily_data.get("CSAT Resolution", "N/A"), "%"],
                ["CSAT Behaviour", "CSAT Behaviour", daily_data.get("CSAT Behaviour", "N/A"), "%"],
            ]
            perf_df = pd.DataFrame(perf_table, columns=["Description", "Metric Name", "Value", "Unit"])
            st.dataframe(perf_df, use_container_width=True)
