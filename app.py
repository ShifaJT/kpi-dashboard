import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# === CONFIG ===
MONTHLY_SHEET_NAME = "KPI"
DAILY_SHEET_NAME = "KPI Day"
SHEET_ID = "19aDfELEExMn0loj_w6D69ngGG4haEm6lsgqpxJC1OAA"

# === Google Auth from Secrets ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)
worksheet_monthly = sheet.worksheet(MONTHLY_SHEET_NAME)
worksheet_daily = sheet.worksheet(DAILY_SHEET_NAME)

@st.cache_data
def load_data():
    monthly_data = pd.DataFrame(worksheet_monthly.get_all_records())
    daily_data = pd.DataFrame(worksheet_daily.get_all_records())
    return monthly_data, daily_data

def get_value(data, column):
    try:
        return data[column].values[0] if column in data.columns else "N/A"
    except:
        return "N/A"

monthly_df, daily_df = load_data()

# === UI ===
st.title("KPI Dashboard for Champs")
st.subheader("📘 About This Dashboard")

emp_id = st.text_input("Enter EMP ID")
view_type = st.selectbox("Select View Type", ["Month", "Week", "Day"])

if emp_id:
    filtered_data = None
    if view_type == "Month":
        selected_month = st.selectbox("Select Month", sorted(monthly_df['Month'].unique()))
        filtered_data = monthly_df[(monthly_df['EMP ID'].astype(str) == emp_id) & (monthly_df['Month'] == selected_month)]
    elif view_type == "Day":
        selected_date = st.selectbox("Select Date", sorted(daily_df['Date'].unique()))
        filtered_data = daily_df[(daily_df['EMP ID'].astype(str) == emp_id) & (daily_df['Date'] == selected_date)]
    elif view_type == "Week":
        selected_week = st.selectbox("Select Week", sorted(daily_df['Week'].unique()))
        filtered_data = daily_df[(daily_df['EMP ID'].astype(str) == emp_id) & (daily_df['Week'] == selected_week)]
        filtered_data = filtered_data.groupby("EMP ID").mean(numeric_only=True).reset_index()

    if filtered_data is not None and not filtered_data.empty:
        name = get_value(filtered_data, "NAME")
        st.success(f"KPI Data for {name} | View: {view_type}")

        # === Performance Table ===
        perf_table = pd.DataFrame([
            ["Average hold used", "Hold", get_value(filtered_data, "Hold"), "HH:MM:SS"],
            ["Average time taken to wrap the call", "Wrap", get_value(filtered_data, "Wrap"), "HH:MM:SS"],
            ["Average duration of champ using auto on", "Auto-On", get_value(filtered_data, "Auto-On"), "HH:MM:SS"],
            ["Shift adherence for the period", "Schedule Adherence", f"{get_value(filtered_data, 'Schedule Adherence')}%", "Percentage"],
            ["Customer feedback on resolution given", "Resolution CSAT", f"{get_value(filtered_data, 'Resolution CSAT')}%", "Percentage"],
            ["Customer feedback on champ behaviour", "Agent Behaviour", f"{get_value(filtered_data, 'Agent Behaviour')}%", "Percentage"],
            ["Average Quality Score", "Quality", f"{get_value(filtered_data, 'Quality')}%", "Percentage"],
            ["Process knowledge test", "PKT", f"{get_value(filtered_data, 'PKT')}%", "Percentage"],
            ["Sick & unplanned leaves", "SL + UPL", get_value(filtered_data, "SL + UPL"), "Days"],
            ["Login days", "LOGINS", get_value(filtered_data, "LOGINS"), "Days"]
        ], columns=["Description", "Metric Name", "Value", "Unit"])

        st.subheader("🔹 Performance Metrics")
        st.dataframe(perf_table, use_container_width=True, hide_index=True)

        # === KPI Table ===
        kpi_table = pd.DataFrame([
            ["0%", "Hold KPI Score", get_value(filtered_data, "Hold KPI Score")],
            ["30%", "Auto-On KPI Score", get_value(filtered_data, "Auto-On KPI Score")],
            ["10%", "Schedule Adherence KPI Score", get_value(filtered_data, "Schedule Adherence KPI Score")],
            ["10%", "Resolution CSAT KPI Score", get_value(filtered_data, "Resolution CSAT KPI Score")],
            ["20%", "Agent Behaviour KPI Score", get_value(filtered_data, "Agent Behaviour KPI Score")],
            ["20%", "Quality KPI Score", get_value(filtered_data, "Quality KPI Score")],
            ["10%", "PKT KPI Score", get_value(filtered_data, "PKT KPI Score")],
        ], columns=["Weightage", "KPI Metrics", "Score"])

        st.subheader("✅ KPI Scores")
        st.dataframe(kpi_table, use_container_width=True, hide_index=True)

        # === Grand Total and Motivational Message ===
        if view_type == "Month":
            grand_total = get_value(filtered_data, "Grand Total")
            st.subheader("🏁 Grand Total KPI")
            st.metric("Grand Total KPI", grand_total)

            # Compare with previous month
            all_months = sorted(monthly_df['Month'].unique().tolist())
            current_index = all_months.index(selected_month)
            prev_month = all_months[current_index - 1] if current_index > 0 else None

            if prev_month:
                prev_data = monthly_df[(monthly_df['EMP ID'].astype(str) == emp_id) & (monthly_df['Month'] == prev_month)]
                if not prev_data.empty:
                    prev_score = prev_data['Grand Total'].values[0]
                    diff = round(float(grand_total) - float(prev_score), 2)
                    msg = f"You {'improved' if diff >= 0 else 'dropped'} by {diff:+} points since last month ({prev_month})!"
                    st.info(msg)

                    # Motivational message
                    if float(grand_total) >= 4.5:
                        st.success("🌟 Outstanding performance! Keep up the great work!")
                    elif float(grand_total) >= 3.5:
                        st.info("👍 Good job! Let’s push for even better next month.")
                    else:
                        st.warning("📈 You can do better! Let’s aim higher next month.")

        # === Target Committed ===
        if view_type == "Month":
            st.subheader("🎯 Target Committed for Next Month")
            target_pkt = get_value(filtered_data, "Target Committed for PKT")
            target_csat = get_value(filtered_data, "Target Committed for CSAT (Agent Behaviour)")
            target_quality = get_value(filtered_data, "Target Committed for Quality")

            if target_pkt != "N/A" or target_csat != "N/A" or target_quality != "N/A":
                target_table = pd.DataFrame([
                    ["PKT", target_pkt],
                    ["CSAT (Agent Behaviour)", target_csat],
                    ["Quality", target_quality]
                ], columns=["Metric", "Target Committed"])
                st.dataframe(target_table, use_container_width=True, hide_index=True)
            else:
                st.info("No target data available.")
    else:
        st.warning("No data found for the selected criteria.")
