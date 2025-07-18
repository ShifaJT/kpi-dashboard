import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
from datetime import datetime
import calendar

# Setup connection
creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets"])
client = gspread.authorize(creds)

# Load data from Google Sheets
sheet = client.open("YTD KPI Sheet")
kpi_month_df = pd.DataFrame(sheet.worksheet("KPI Month").get_all_records())
kpi_day_df = pd.DataFrame(sheet.worksheet("KPI Day").get_all_records())
csat_df = pd.DataFrame(sheet.worksheet("CSAT Score").get_all_records())

# Preprocess KPI Day date column
kpi_day_df['Date'] = pd.to_datetime(kpi_day_df['Date'], format='%m/%d/%Y')

# Page config
st.set_page_config(page_title="KPI Dashboard", layout="centered")

st.title("📊 KPI Dashboard")

# Input: EMP ID
emp_id = st.text_input("Enter your EMP ID:")

# Input: View Type
view_type = st.selectbox("Select View", ["Month", "Week", "Day"])

# Get unique values based on view
if view_type == "Month":
    options = kpi_month_df['Month'].unique()
elif view_type == "Week":
    options = sorted(kpi_day_df['Week'].unique())
else:
    options = kpi_day_df['Date'].dt.strftime('%Y-%m-%d').unique()

# Select specific value
selected_option = st.selectbox(f"Select {view_type}", options)

# Filter based on selected view
if emp_id:
    if view_type == "Month":
        data = kpi_month_df[(kpi_month_df['EMP ID'] == emp_id) & (kpi_month_df['Month'] == selected_option)]
    elif view_type == "Day":
        selected_date = pd.to_datetime(selected_option)
        data = kpi_day_df[(kpi_day_df['EMP ID'] == emp_id) & (kpi_day_df['Date'] == selected_date)]
    elif view_type == "Week":
        week_data = kpi_day_df[(kpi_day_df['EMP ID'] == emp_id) & (kpi_day_df['Week'].astype(str) == str(selected_option))]
        if not week_data.empty:
            # Aggregate
            agg_data = {
                'Call Count': week_data['Call Count'].astype(float).sum(),
                'AHT': pd.to_timedelta(week_data['AHT']).mean(),
                'Hold': pd.to_timedelta(week_data['Hold']).mean(),
                'Wrap': pd.to_timedelta(week_data['Wrap']).mean(),
            }
            data = pd.DataFrame([agg_data])
            # Add CSAT from csat_df
            csat_row = csat_df[(csat_df['EMP ID'] == emp_id) & (csat_df['Week'].astype(str) == str(selected_option))]
            if not csat_row.empty:
                data['CSAT Resolution'] = csat_row.iloc[0]['CSAT Resolution']
                data['CSAT Behaviour'] = csat_row.iloc[0]['CSAT Behaviour']
            else:
                data['CSAT Resolution'] = 'N/A'
                data['CSAT Behaviour'] = 'N/A'
        else:
            data = pd.DataFrame()

    # Show Performance Table
    if not data.empty:
        st.subheader("📈 Performance")
        performance = {
            "Description": ["Calls", "AHT", "Hold", "Wrap", "CSAT Resolution", "CSAT Behaviour"],
            "Metric Name": ["Call Count", "AHT", "Hold", "Wrap", "CSAT Resolution", "CSAT Behaviour"],
            "Value": [data[col].values[0] if col in data.columns else 'N/A' for col in ["Call Count", "AHT", "Hold", "Wrap", "CSAT Resolution", "CSAT Behaviour"]],
            "Unit": ["count", "HH:MM:SS", "HH:MM:SS", "HH:MM:SS", "%", "%"]
        }
        st.table(pd.DataFrame(performance))

        # Show KPI section (only for Monthly view)
        if view_type == "Month":
            st.subheader("🧮 KPI Scorecard")
            kpi_metrics = [
                {"KPI Metrics": "Product Knowledge Test", "Weightage": "20%", "Score": data["PKT"].values[0]},
                {"KPI Metrics": "CSAT (Resolution)", "Weightage": "40%", "Score": data["CSAT Resolution Score"].values[0]},
                {"KPI Metrics": "CSAT (Agent Behaviour)", "Weightage": "20%", "Score": data["CSAT Behaviour Score"].values[0]},
                {"KPI Metrics": "Quality", "Weightage": "20%", "Score": data["Quality Score"].values[0]},
            ]
            st.table(pd.DataFrame(kpi_metrics)[["Weightage", "KPI Metrics", "Score"]])

            # Previous month comparison
            all_months = list(kpi_month_df['Month'].unique())
            if len(all_months) > 1 and selected_option in all_months:
                current_index = all_months.index(selected_option)
                if current_index > 0:
                    prev_month = all_months[current_index - 1]
                    prev_data = kpi_month_df[(kpi_month_df['EMP ID'] == emp_id) & (kpi_month_df['Month'] == prev_month)]
                    if not prev_data.empty:
                        prev_score = prev_data["Grand Total"].values[0]
                        curr_score = data["Grand Total"].values[0]
                        diff = round(curr_score - prev_score, 2)
                        symbol = "⬆️" if diff >= 0 else "⬇️"
                        st.markdown(f"### 📊 Grand Total: **{curr_score}** ({symbol} {abs(diff)} from {prev_month})")

            # Motivation
            score = data["Grand Total"].values[0]
            if score >= 85:
                msg = "🌟 Excellent! Keep up the great work!"
            elif score >= 70:
                msg = "👍 Good job! Aim higher next month."
            else:
                msg = "⚠️ Let’s improve. You got this!"
            st.markdown(f"#### 💡 {msg}")

            # Target Committed
            st.subheader("🎯 Target Committed")
            st.markdown(f"""
            - **PKT**: {data.get("Target Committed for PKT", ['N/A'])[0]}
            - **CSAT (Agent Behaviour)**: {data.get("Target Committed for CSAT (Agent Behaviour)", ['N/A'])[0]}
            - **Quality**: {data.get("Target Committed for Quality", ['N/A'])[0]}
            """)

    else:
        st.warning("No data found for the selected EMP ID and date/week/month.")
