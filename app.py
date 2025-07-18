import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --------------------------- GOOGLE SHEET AUTH ---------------------------- #
SHEET_ID = "19aDfELEExMn0loj_w6D69ngGG4haEm6lsgqpxJC1OAA"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Authenticate with Google Sheets
credentials = Credentials.from_service_account_file(
    "creds.json",
    scopes=SCOPES
)
client = gspread.authorize(credentials)
sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
sheet = client.open_by_url(sheet_url)

# --------------------------- HELPER FUNCTIONS ---------------------------- #
def load_monthly_data(emp_id: str, month: str):
    worksheet = sheet.worksheet("KPI Month")
    df = pd.DataFrame(worksheet.get_all_records())
    emp_data = df[(df['EMP ID'] == emp_id) & (df['Month'] == month)]
    return emp_data

def load_previous_month_data(emp_id: str, month: str):
    worksheet = sheet.worksheet("KPI Month")
    df = pd.DataFrame(worksheet.get_all_records())
    months_order = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    if month not in months_order:
        return pd.DataFrame()
    current_index = months_order.index(month)
    if current_index == 0:
        return pd.DataFrame()
    prev_month = months_order[current_index - 1]
    emp_data = df[(df['EMP ID'] == emp_id) & (df['Month'] == prev_month)]
    return emp_data

def get_motivational_quote(score):
    if score >= 90:
        return "🌟 Outstanding work! Keep pushing the limits!"
    elif score >= 75:
        return "💪 Great job! You're on the path to excellence."
    elif score >= 60:
        return "👏 Good effort! Aim a bit higher next time."
    else:
        return "🔥 Let’s hustle and level up next month!"

# --------------------------- UI LAYOUT ---------------------------- #
st.title("📊 KPI Dashboard")
st.markdown("Enter your Employee ID and Month to view performance.")

emp_id = st.text_input("Enter your EMP ID")
month = st.selectbox("Select Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])

if emp_id and month:
    data = load_monthly_data(emp_id, month)
    if data.empty:
        st.warning("No data found for given EMP ID and Month.")
    else:
        name = data.iloc[0]['NAME']
        st.subheader(f"👤 Name: {name}")
        st.subheader(f"📅 Month: {month}")

        st.markdown("---")
        st.markdown("### 🔎 Performance Overview")
        perf_df = pd.DataFrame({
            "Description": [
                "Total Calls Handled", "Average Handling Time (AHT)", "Average Hold Time", "Wrap Time"
            ],
            "Metric Name": ["Call Count", "AHT", "Hold", "Wrap"],
            "Value": [
                data.iloc[0]['Call Count'],
                data.iloc[0]['AHT'],
                data.iloc[0]['Hold'],
                data.iloc[0]['Wrap']
            ],
            "Unit": ["calls", "seconds", "seconds", "seconds"]
        })
        st.dataframe(perf_df, hide_index=True)

        st.markdown("---")
        st.markdown("### 🧮 KPI Score Summary")

        kpi_weight = pd.DataFrame({
            "Weightage": ["40%", "30%", "30%"],
            "KPI Metrics": ["PKT", "CSAT (Agent Behaviour)", "Quality"],
            "Score": [
                data.iloc[0]['PKT Score'],
                data.iloc[0]['CSAT Behaviour Score'],
                data.iloc[0]['Quality Score']
            ]
        })
        st.dataframe(kpi_weight, hide_index=True)

        st.markdown("---")
        st.markdown("### 📈 Comparison with Previous Month")
        prev = load_previous_month_data(emp_id, month)
        if not prev.empty:
            comparison = pd.DataFrame({
                "KPI": ["PKT", "CSAT (Agent Behaviour)", "Quality", "Grand Total"],
                f"{month}": [
                    data.iloc[0]['PKT Score'],
                    data.iloc[0]['CSAT Behaviour Score'],
                    data.iloc[0]['Quality Score'],
                    data.iloc[0]['Grand Total']
                ],
                f"Previous Month ({prev.iloc[0]['Month']})": [
                    prev.iloc[0]['PKT Score'],
                    prev.iloc[0]['CSAT Behaviour Score'],
                    prev.iloc[0]['Quality Score'],
                    prev.iloc[0]['Grand Total']
                ]
            })
            st.dataframe(comparison, hide_index=True)
        else:
            st.info("No previous month data available for comparison.")

        st.markdown("---")
        st.markdown("### 💬 Motivational Message")
        st.success(get_motivational_quote(data.iloc[0]['Grand Total']))

        st.markdown("---")
        st.markdown("### 🎯 Target Committed for Next Month")
        targets = pd.DataFrame({
            "Target": [
                "Target Committed for PKT",
                "Target Committed for CSAT (Agent Behaviour)",
                "Target Committed for Quality"
            ],
            "Value": [
                data.iloc[0].get("Target Committed for PKT", "N/A"),
                data.iloc[0].get("Target Committed for CSAT (Agent Behaviour)", "N/A"),
                data.iloc[0].get("Target Committed for Quality", "N/A")
            ]
        })
        st.dataframe(targets, hide_index=True)
