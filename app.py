import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# === CONFIG ===
SHEET_ID = "19aDfELEExMn0loj_w6D69ngGG4haEm6lsgqpxJC1OAA"  # Replace with your actual sheet ID
MONTHLY_SHEET_NAME = "KPI Month"
DAILY_SHEET_NAME = "KPI Day"

# === Google Auth from Secrets ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)
monthly_ws = sheet.worksheet(MONTHLY_SHEET_NAME)
daily_ws = sheet.worksheet(DAILY_SHEET_NAME)

@st.cache_data

def load_data():
    monthly_df = pd.DataFrame(monthly_ws.get_all_records())
    daily_df = pd.DataFrame(daily_ws.get_all_records())
    # Clean headers
    monthly_df.columns = monthly_df.columns.str.strip()
    daily_df.columns = daily_df.columns.str.strip()
    return monthly_df, daily_df

monthly_df, daily_df = load_data()

# === UI ===
st.title("KPI Dashboard for Champs")

emp_id = st.text_input("Enter EMP ID")
view_type = st.selectbox("Select View Type", ["Month", "Week", "Day"])

selected_value = None

if view_type == "Month":
    selected_value = st.selectbox("Select Month", sorted(monthly_df['Month'].unique()))
elif view_type == "Week":
    selected_value = st.selectbox("Select Week", sorted(daily_df['Week'].dropna().unique()))
elif view_type == "Day":
    selected_value = st.selectbox("Select Date", sorted(daily_df['Date'].dropna().unique()))

if emp_id and selected_value:
    st.markdown("---")

    if view_type == "Month":
        data = monthly_df[(monthly_df['EMP ID'].astype(str) == emp_id) & (monthly_df['Month'] == selected_value)]
        if data.empty:
            st.warning("No data found for given EMP ID and month")
        else:
            name = data['NAME'].values[0]
            st.subheader(f"Performance View for {name} | Month: {selected_value}")

            # --- Performance Table ---
            perf_rows = [
                ["Average hold used", "Hold", data['Hold'].values[0], "HH:MM:SS"],
                ["Average time taken to wrap the call", "Wrap", data['Wrap'].values[0], "HH:MM:SS"],
                ["Average duration of champ using auto on", "Auto-On", data['Auto-On'].values[0], "HH:MM:SS"],
                ["Shift adherence for the month", "Schedule Adherence", data['Schedule Adherence'].values[0], "%"],
                ["Customer feedback on resolution given", "Resolution CSAT", data['Resolution CSAT'].values[0], "%"],
                ["Customer feedback on champ behaviour", "Agent Behaviour", data['Agent Behaviour'].values[0], "%"],
                ["Average Quality Score achieved for the month", "Quality", data['Quality'].values[0], "%"],
                ["Process knowledge test", "PKT", data['PKT'].values[0], "%"],
                ["Number of sick and unplanned leaves", "SL + UPL", data['SL + UPL'].values[0], "Days"],
                ["Number of days logged in", "LOGINS", data['LOGINS'].values[0], "Days"]
            ]
            perf_df = pd.DataFrame(perf_rows, columns=["Description", "Metric Name", "Value", "Unit"])
            st.dataframe(perf_df, use_container_width=True)

            # --- KPI Table ---
            kpi_rows = [
                ["0%", "Hold KPI Score", data['Hold KPI Score'].values[0]],
                ["10%", "Wrap KPI Score", data['Wrap KPI Score'].values[0]],
                ["30%", "Auto-On KPI Score", data['Auto-On KPI Score'].values[0]],
                ["10%", "Schedule Adherence KPI Score", data['Schedule Adherence KPI Score'].values[0]],
                ["10%", "Resolution CSAT KPI Score", data['Resolution CSAT KPI Score'].values[0]],
                ["20%", "Agent Behaviour KPI Score", data['Agent Behaviour KPI Score'].values[0]],
                ["20%", "Quality KPI Score", data['Quality KPI Score'].values[0]],
                ["10%", "PKT KPI Score", data['PKT KPI Score'].values[0]]
            ]
            kpi_df = pd.DataFrame(kpi_rows, columns=["Weightage", "KPI Metrics", "Score"])
            st.dataframe(kpi_df, use_container_width=True)

            # --- Grand Total ---
            total = data['Grand Total'].values[0]
            st.metric("Grand Total KPI", f"{total}")

            # --- Comparison with Previous Month ---
            all_months = sorted(monthly_df['Month'].unique().tolist())
            current_index = all_months.index(selected_value)
            if current_index > 0:
                prev_month = all_months[current_index - 1]
                prev_data = monthly_df[(monthly_df['EMP ID'].astype(str) == emp_id) & (monthly_df['Month'] == prev_month)]
                if not prev_data.empty:
                    prev_score = prev_data['Grand Total'].values[0]
                    diff = round(float(total) - float(prev_score), 2)
                    st.info(f"You {'improved' if diff >= 0 else 'dropped'} by {diff:+} points since last month ({prev_month})")

                    if float(total) >= 4.5:
                        st.success("Excellent work! You're a top performer. Keep it up!")
                    elif float(total) >= 3.5:
                        st.info("Good job! Aim a little higher for excellence.")
                    else:
                        st.warning("There's room to grow. Let's push harder next month!")

            # --- Target Committed ---
            st.subheader("Target Committed for Next Month")
            try:
                pkt = data['Target Committed for PKT'].values[0]
                csat = data['Target Committed for CSAT (Agent Behaviour)'].values[0]
                qual = data['Target Committed for Quality'].values[0]
                st.write("- Target Committed for PKT:", pkt)
                st.write("- Target Committed for CSAT (Agent Behaviour):", csat)
                st.write("- Target Committed for Quality:", qual)
            except:
                st.warning("Target commitment data not available.")

    elif view_type == "Day":
        daily_data = daily_df[(daily_df['EMP ID'].astype(str) == emp_id) & (daily_df['Date'] == selected_value)]
        if daily_data.empty:
            st.warning("No data found for this date")
        else:
            st.subheader(f"Daily Performance for {daily_data['NAME'].values[0]} | Date: {selected_value}")
            day_perf = daily_data[['Call Count', 'AHT', 'Hold', 'Wrap', 'CSAT Resolution', 'CSAT Behaviour']].T
            day_perf.columns = ['Value']
            st.dataframe(day_perf, use_container_width=True)

    elif view_type == "Week":
        week_data = daily_df[(daily_df['EMP ID'].astype(str) == emp_id) & (daily_df['Week'].astype(str) == str(selected_value))]
        if week_data.empty:
            st.warning("No data found for this week")
        else:
            st.subheader(f"Weekly Averages for EMP ID: {emp_id} | Week: {selected_value}")
            cols_to_avg = ['Call Count', 'CSAT Resolution', 'CSAT Behaviour']
            for col in cols_to_avg:
                week_data[col] = pd.to_numeric(week_data[col], errors='coerce')
            avg_df = week_data[cols_to_avg].mean().round(2).to_frame(name='Average')
            st.dataframe(avg_df, use_container_width=True)
