import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="KPI Dashboard for Champs", layout="wide")

# Google Sheets auth
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)

# Sheet names
sheet_kpi_month = client.open("KPI Dashboard").worksheet("KPI Month")
sheet_kpi_day = client.open("KPI Dashboard").worksheet("KPI Day")
sheet_csat = client.open("KPI Dashboard").worksheet("CSAT Score")

# Load data
def load_data():
    kpi_month_df = pd.DataFrame(sheet_kpi_month.get_all_records())
    daily_df = pd.DataFrame(sheet_kpi_day.get_all_records())
    csat_df = pd.DataFrame(sheet_csat.get_all_records())
    return kpi_month_df, daily_df, csat_df

kpi_month_df, daily_df, csat_df = load_data()

st.title("KPI Dashboard for Champs")

emp_id = st.text_input("Enter EMP ID")

if emp_id:
    view_type = st.selectbox("Select View Type", ["Month", "Week", "Day"])

    if view_type == "Month":
        months = kpi_month_df[kpi_month_df['EMP ID'].astype(str) == emp_id]['Month'].unique()
        selection = st.selectbox("Select Month", sorted(months))

        if selection:
            filtered = kpi_month_df[
                (kpi_month_df['EMP ID'].astype(str) == emp_id) &
                (kpi_month_df['Month'] == selection)
            ]
            if filtered.empty:
                st.warning("No data found for the selected month.")
            else:
                row = filtered.iloc[0]
                st.subheader("🔹 Monthly Performance")
                perf_table = [
                    ["Average Hold Time", "Hold", row['Hold'], "sec"],
                    ["Average Wrap Time", "Wrap", row['Wrap'], "sec"],
                    ["Auto-On Compliance", "Auto-On", row['Auto-On'], "%"],
                    ["Schedule Adherence", "Schedule Adherence", row['Schedule Adherence'], "%"],
                    ["CSAT Resolution", "Resolution CSAT", row['Resolution CSAT'], "%"],
                    ["CSAT Behaviour", "Agent Behaviour", row['Agent Behaviour'], "%"],
                    ["Quality Score", "Quality", row['Quality'], "%"],
                    ["PKT", "PKT", row['PKT'], "%"],
                    ["SL + UPL", "SL + UPL", row['SL + UPL'], "%"],
                    ["Login Count", "LOGINS", row['LOGINS'], ""]
                ]
                perf_df = pd.DataFrame(perf_table, columns=["Description", "Metric Name", "Value", "Unit"])
                st.dataframe(perf_df, use_container_width=True)

                st.subheader("📊 KPI Scores")
                kpi_table = [
                    ["Hold", "Hold KPI Score", row['Hold KPI Score']],
                    ["Wrap", "Wrap KPI Score", row['Wrap KPI Score']],
                    ["Auto-On", "Auto-On KPI Score", row['Auto-On KPI Score']],
                    ["Schedule Adherence", "Schedule Adherence KPI Score", row['Schedule Adherence KPI Score']],
                    ["Resolution CSAT", "Resolution CSAT KPI Score", row['Resolution CSAT KPI Score']],
                    ["Agent Behaviour", "Agent Behaviour KPI Score", row['Agent Behaviour KPI Score']],
                    ["Quality", "Quality KPI Score", row['Quality KPI Score']],
                    ["PKT", "PKT KPI Score", row['PKT KPI Score']],
                    ["Grand Total", "Grand Total", row['Grand Total']]
                ]
                kpi_df = pd.DataFrame(kpi_table, columns=["KPI Metrics", "Metric Name", "Score"])
                st.dataframe(kpi_df, use_container_width=True)

                st.subheader("🎯 Target Committed")
                target_table = [
                    ["Target Committed for PKT", row.get("Target Committed for PKT", "N/A")],
                    ["Target Committed for CSAT (Agent Behaviour)", row.get("Target Committed for CSAT (Agent Behaviour)", "N/A")],
                    ["Target Committed for Quality", row.get("Target Committed for Quality", "N/A")]
                ]
                target_df = pd.DataFrame(target_table, columns=["Description", "Target"])
                st.dataframe(target_df, use_container_width=True)

    elif view_type == "Day":
        daily_df['Date_parsed'] = pd.to_datetime(daily_df['Date'], format="%m/%d/%Y", errors='coerce')
        valid_dates = daily_df['Date_parsed'].dropna().dt.strftime("%d-%m-%Y").unique()
        selection = st.selectbox("Select Date", sorted(valid_dates))

        if selection:
            selected_date = datetime.strptime(selection, "%d-%m-%Y").date()
            filtered_day = daily_df[
                (daily_df['EMP ID'].astype(str) == emp_id) &
                (pd.to_datetime(daily_df['Date'], format="%m/%d/%Y", errors='coerce').dt.date == selected_date)
            ]

            if filtered_day.empty:
                st.warning("No daily data found.")
            else:
                daily_data = filtered_day.iloc[0]
                st.subheader("🔹 Daily Performance")
                perf_table = [
                    ["Total Calls Handled", "Call Count", daily_data.get("Call Count", "N/A"), "Count"],
                    ["Average AHT", "AHT", daily_data.get("AHT", "N/A"), ""],
                    ["Average Hold", "Hold", daily_data.get("Hold", "N/A"), ""],
                    ["Average Wrap", "Wrap", daily_data.get("Wrap", "N/A"), ""],
                    ["CSAT Resolution", "CSAT Resolution", daily_data.get("CSAT Resolution", "N/A"), "%"],
                    ["CSAT Behaviour", "CSAT Behaviour", daily_data.get("CSAT Behaviour", "N/A"), "%"]
                ]
                perf_df = pd.DataFrame(perf_table, columns=["Description", "Metric Name", "Value", "Unit"])
                st.dataframe(perf_df, use_container_width=True)

    elif view_type == "Week":
        week_values = daily_df['Week'].dropna().astype(str).unique()
        selection = st.selectbox("Select Week", sorted(week_values))

        if selection:
            filtered_week = daily_df[
                (daily_df['EMP ID'].astype(str) == emp_id) &
                (daily_df['Week'].astype(str) == selection)
            ]

            csat_row = csat_df[
                (csat_df['EMP ID'].astype(str) == emp_id) &
                (csat_df['Week'].astype(str) == selection)
            ]

            if filtered_week.empty and csat_row.empty:
                st.warning("No weekly data found.")
            else:
                st.subheader("🔹 Weekly Performance")
                perf_table = [
                    ["Total Calls Handled", "Call Count", filtered_week['Call Count'].astype(float).sum(), "Count"],
                    ["Average AHT", "AHT", filtered_week['AHT'].astype(float).mean(), ""],
                    ["Average Hold", "Hold", filtered_week['Hold'].astype(float).mean(), ""],
                    ["Average Wrap", "Wrap", filtered_week['Wrap'].astype(float).mean(), ""]
                ]

                if not csat_row.empty:
                    csat_data = csat_row.iloc[0]
                    perf_table.append(["CSAT Resolution", "CSAT Resolution", csat_data.get("CSAT Resolution", "N/A"), "%"])
                    perf_table.append(["CSAT Behaviour", "CSAT Behaviour", csat_data.get("CSAT Behaviour", "N/A"), "%"])

                perf_df = pd.DataFrame(perf_table, columns=["Description", "Metric Name", "Value", "Unit"])
                st.dataframe(perf_df, use_container_width=True)
