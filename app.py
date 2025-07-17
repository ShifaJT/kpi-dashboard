import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# === CONFIG ===
SHEET_ID = "19aDfELEExMn0loj_w6D69ngGG4haEm6lsgqpxJC1OAA"
MONTHLY_SHEET_NAME = "KPI Month"
DAILY_SHEET_NAME = "KPI Day"

# === Google Auth from Secrets ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)

# Load Sheets
monthly_df = pd.DataFrame(sheet.worksheet(MONTHLY_SHEET_NAME).get_all_records())
daily_df = pd.DataFrame(sheet.worksheet(DAILY_SHEET_NAME).get_all_records())

# Convert date to datetime and ensure numeric fields
daily_df['Date'] = pd.to_datetime(daily_df['Date'], errors='coerce')
daily_df['Week'] = pd.to_numeric(daily_df['Week'], errors='coerce')

# === UI ===
st.title("KPI Dashboard for Champs")

emp_id = st.text_input("Enter EMP ID")
view_type = st.selectbox("Select View Type", ["Month", "Week", "Day"])

# Get user selection based on view type
selected_value = None
if view_type == "Month":
    selected_value = st.selectbox("Select Month", sorted(monthly_df['Month'].unique()))
elif view_type == "Week":
    selected_value = st.selectbox("Select Week Number", sorted(daily_df['Week'].dropna().unique()))
elif view_type == "Day":
    selected_value = st.date_input("Select Date")

# Helper functions for UI

def display_performance_section(data):
    st.subheader("Performance Metrics")
    metrics = [
        ("Average hold used", "Hold", data.get("Hold", "N/A"), "HH:MM:SS"),
        ("Average time taken to wrap the call", "Wrap", data.get("Wrap", "N/A"), "HH:MM:SS"),
        ("Average duration of champ using auto on", "Auto-On", data.get("Auto-On", "N/A"), "HH:MM:SS"),
        ("Shift adherence for the month", "Schedule Adherence", data.get("Schedule Adherence", "N/A"), "Percentage"),
        ("Customer feedback on resolution given", "Resolution CSAT", data.get("Resolution CSAT", "N/A"), "Percentage"),
        ("Customer feedback on champ behaviour", "Agent Behaviour", data.get("Agent Behaviour", "N/A"), "Percentage"),
        ("Average Quality Score achieved for the month", "Quality", data.get("Quality", "N/A"), "Percentage"),
        ("Process knowledge test", "PKT", data.get("PKT", "N/A"), "Percentage"),
        ("Number of sick and unplanned leaves", "SL + UPL", data.get("SL + UPL", "N/A"), "Days"),
        ("Number of days logged in", "LOGINS", data.get("LOGINS", "N/A"), "Days")
    ]
    df_perf = pd.DataFrame(metrics, columns=["Description", "Metric Name", "Value", "Unit"])
    st.dataframe(df_perf, use_container_width=True)


def display_kpi_section(data):
    st.subheader("KPI Scores")
    kpi_scores = [
        ("0%", "Hold KPI Score", data.get("Hold KPI Score", "N/A")),
        ("10%", "Wrap KPI Score", data.get("Wrap KPI Score", "N/A")),
        ("30%", "Auto-On KPI Score", data.get("Auto-On KPI Score", "N/A")),
        ("10%", "Schedule Adherence KPI Score", data.get("Schedule Adherence KPI Score", "N/A")),
        ("10%", "Resolution CSAT KPI Score", data.get("Resolution CSAT KPI Score", "N/A")),
        ("20%", "Agent Behaviour KPI Score", data.get("Agent Behaviour KPI Score", "N/A")),
        ("20%", "Quality KPI Score", data.get("Quality KPI Score", "N/A")),
        ("10%", "PKT KPI Score", data.get("PKT KPI Score", "N/A")),
    ]
    df_kpi = pd.DataFrame(kpi_scores, columns=["Weightage", "KPI Metrics", "Score"])
    st.dataframe(df_kpi, use_container_width=True)

# === Show Data ===
if emp_id and selected_value:
    emp_data = None

    if view_type == "Month":
        emp_data = monthly_df[(monthly_df['EMP ID'].astype(str) == emp_id) & (monthly_df['Month'] == selected_value)]
    elif view_type == "Day":
        emp_data = daily_df[(daily_df['EMP ID'].astype(str) == emp_id) & (daily_df['Date'] == pd.to_datetime(selected_value))]
    elif view_type == "Week":
        week_data = daily_df[(daily_df['EMP ID'].astype(str) == emp_id) & (daily_df['Week'] == selected_value)]
        emp_data = week_data.groupby('EMP ID').mean(numeric_only=True).reset_index()

    if emp_data is None or emp_data.empty:
        st.warning("No data found for the given selection.")
    else:
        data_row = emp_data.iloc[0]
        st.markdown(f"### Data for EMP ID: {emp_id} ({view_type}: {selected_value})")

        display_performance_section(data_row)
        display_kpi_section(data_row)

        # Grand Total
        if "Grand Total" in data_row:
            st.metric("Grand Total KPI", f"{data_row['Grand Total']}")

        # Comparison with Previous Month
        if view_type == "Month":
            month_list = sorted(monthly_df['Month'].unique())
            if selected_value in month_list:
                idx = month_list.index(selected_value)
                if idx > 0:
                    previous_month = month_list[idx - 1]
                    prev_data = monthly_df[(monthly_df['EMP ID'].astype(str) == emp_id) & (monthly_df['Month'] == previous_month)]
                    if not prev_data.empty:
                        prev_total = prev_data.iloc[0]['Grand Total']
                        curr_total = data_row['Grand Total']
                        change = round(curr_total - prev_total, 2)
                        msg = f"You {'improved' if change > 0 else 'dropped'} by {abs(change)} points since last month ({previous_month})!"
                        st.info(msg)

                        if curr_total >= 4.5:
                            st.success("Outstanding performance! Keep it up!")
                        elif curr_total >= 3.5:
                            st.success("Good job! Aim even higher!")
                        elif curr_total >= 2.5:
                            st.warning("Fair performance. Focus on improvements.")
                        else:
                            st.error("Needs immediate improvement. Let’s work on it together!")

        # Target Committed
        target_keys = ["Target Committed for PKT", "Target Committed for CSAT (Agent Behaviour)", "Target Committed for Quality"]
        target_data = [(k, data_row.get(k, "N/A")) for k in target_keys]
        st.markdown("### ✨ Target Committed for Next Month")
        df_target = pd.DataFrame(target_data, columns=["Target", "Value"])
        st.dataframe(df_target, use_container_width=True)
