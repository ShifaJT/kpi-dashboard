import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
from datetime import datetime
import calendar

# Authenticate using Streamlit secrets (service account)
creds_dict = st.secrets["gcp_service_account"]
creds = service_account.Credentials.from_service_account_info(creds_dict)
client = gspread.authorize(creds)

# Sheet ID (not name)
SHEET_ID = "1rzLUfrgf4G_1a8_jfUmD2dF2lfp9R7jAygMbCeBikqM"

# Open Sheets
kpi_month = client.open_by_key(SHEET_ID).worksheet("KPI Month")
kpi_day = client.open_by_key(SHEET_ID).worksheet("KPI Day")
csat_score = client.open_by_key(SHEET_ID).worksheet("CSAT Score")

# Load Data
df_month = pd.DataFrame(kpi_month.get_all_records())
df_day = pd.DataFrame(kpi_day.get_all_records())
df_csat = pd.DataFrame(csat_score.get_all_records())

# Parse date
df_day['Date'] = pd.to_datetime(df_day['Date'], format="%m/%d/%Y")

# Sidebar Inputs
st.sidebar.title("KPI Dashboard")
emp_id = st.sidebar.text_input("Enter Employee ID")

view_option = st.sidebar.selectbox("Select View Type", ["Month", "Week", "Day"])

if view_option == "Month":
    month = st.sidebar.selectbox("Select Month", sorted(df_month['Month'].unique()))
elif view_option == "Week":
    week = st.sidebar.selectbox("Select Week", sorted(df_day['Week'].unique()))
else:
    date_selected = st.sidebar.date_input("Select Date")

if emp_id:
    name = df_month[df_month['EMP ID'] == emp_id]['NAME'].iloc[0] if emp_id in df_month['EMP ID'].values else "Unknown"
    st.header(f"Performance Report for {name}")

    if view_option == "Month":
        df_filtered = df_month[(df_month['EMP ID'] == emp_id) & (df_month['Month'] == month)]
    elif view_option == "Week":
        df_day_emp = df_day[(df_day['EMP ID'] == emp_id) & (df_day['Week'] == week)]
        df_csat_emp = df_csat[(df_csat['EMP ID'] == emp_id) & (df_csat['Week'] == week)]

        if not df_day_emp.empty:
            agg_funcs = {
                'Call Count': 'sum',
                'AHT': 'mean',
                'Hold': 'mean',
                'Wrap': 'mean'
            }
            perf_summary = df_day_emp.agg(agg_funcs).to_frame().reset_index()
            perf_summary.columns = ['Metric', 'Value']

            if not df_csat_emp.empty:
                csat_res = df_csat_emp['CSAT Resolution'].iloc[0]
                csat_beh = df_csat_emp['CSAT Behaviour'].iloc[0]
                perf_summary = perf_summary.append({'Metric': 'CSAT Resolution', 'Value': csat_res}, ignore_index=True)
                perf_summary = perf_summary.append({'Metric': 'CSAT Behaviour', 'Value': csat_beh}, ignore_index=True)
            st.subheader(f"Weekly Performance (Week {week})")
            st.dataframe(perf_summary.set_index("Metric"))
        else:
            st.warning("No data found for this week.")

    elif view_option == "Day":
        df_day_emp = df_day[(df_day['EMP ID'] == emp_id) & (df_day['Date'] == pd.to_datetime(date_selected))]
        if not df_day_emp.empty:
            st.subheader(f"Daily Performance - {date_selected.strftime('%d %b %Y')}")
            st.dataframe(df_day_emp.drop(columns=['EMP ID', 'NAME', 'Week']).T.rename(columns={df_day_emp.index[0]: 'Value'}))
        else:
            st.warning("No data for this day.")

    if view_option == "Month" and not df_filtered.empty:
        # Show performance
        perf_fields = ['Call Count', 'AHT', 'Hold', 'Wrap', 'CSAT Resolution', 'CSAT Behaviour']
        perf_table = df_filtered[perf_fields].T.reset_index()
        perf_table.columns = ['Metric', 'Value']
        st.subheader("Monthly Performance")
        st.dataframe(perf_table.set_index("Metric"))

        # Show KPI Scores
        st.subheader("KPI Scores")
        kpi_fields = ['PKT', 'CSAT (Agent Behaviour)', 'Quality']
        kpi_scores = df_filtered[kpi_fields].T.reset_index()
        kpi_scores.columns = ['KPI Metric', 'Score']
        st.dataframe(kpi_scores.set_index("KPI Metric"))

        # Show Target Committed
        st.subheader("Target Committed for Next Month")
        for col in ['Target Committed for PKT', 'Target Committed for CSAT (Agent Behaviour)', 'Target Committed for Quality']:
            if col in df_filtered.columns:
                st.markdown(f"**{col}**: {df_filtered[col].iloc[0]}")
            else:
                st.markdown(f"**{col}**: _Not Available_")

else:
    st.info("Please enter a valid EMP ID in the sidebar.")
