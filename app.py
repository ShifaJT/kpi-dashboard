import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ----------------------- GOOGLE SHEET SETUP -----------------------

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
client = gspread.authorize(creds)

# Open the actual Google Sheet (replace with your correct sheet name)
sheet = client.open("YTD KPI Sheet")

# Load individual sheets
kpi_month_sheet = sheet.worksheet("KPI Month")
kpi_day_sheet = sheet.worksheet("KPI Day")
csat_score_sheet = sheet.worksheet("CSAT Score")

# ----------------------- STREAMLIT INTERFACE -----------------------

st.set_page_config(page_title="KPI Dashboard", layout="wide")
st.title("📊 Employee KPI Dashboard")

emp_id = st.text_input("Enter your EMP ID")

view_type = st.selectbox("Choose View Type", ["Month", "Week", "Day"])

# Date/Month/Week input based on selected view
if view_type == "Month":
    selected_month = st.selectbox("Select Month", [f"{m:02}" for m in range(1, 13)])
elif view_type == "Week":
    selected_week = st.text_input("Enter Week (e.g. Week 1)")
elif view_type == "Day":
    selected_date = st.date_input("Select Date")

# ----------------------- HELPER FUNCTIONS -----------------------

def fetch_month_data(emp_id, month):
    df = pd.DataFrame(kpi_month_sheet.get_all_records())
    df = df[df["EMP ID"] == emp_id]
    df = df[df["Month"] == str(month)]
    return df

def fetch_day_data(emp_id, date_str):
    df = pd.DataFrame(kpi_day_sheet.get_all_records())
    df = df[df["EMP ID"] == emp_id]
    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")
    df = df[df["Date"] == pd.to_datetime(date_str)]
    return df

def fetch_week_data(emp_id, week):
    df_day = pd.DataFrame(kpi_day_sheet.get_all_records())
    df_csat = pd.DataFrame(csat_score_sheet.get_all_records())

    df_day = df_day[df_day["EMP ID"] == emp_id]
    df_week = df_day[df_day["Week"] == week]

    if df_week.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Convert relevant columns to numeric
    numeric_cols = ["Call Count", "AHT", "Hold", "Wrap"]
    for col in numeric_cols:
        df_week[col] = pd.to_numeric(df_week[col], errors="coerce")

    # Weekly average and sum
    weekly_perf = pd.DataFrame({
        "Call Count": [df_week["Call Count"].sum()],
        "AHT": [df_week["AHT"].mean()],
        "Hold": [df_week["Hold"].mean()],
        "Wrap": [df_week["Wrap"].mean()]
    })

    df_csat = df_csat[(df_csat["EMP ID"] == emp_id) & (df_csat["Week"] == week)]

    return weekly_perf, df_csat

# ----------------------- DISPLAY DATA -----------------------

if emp_id:
    if view_type == "Month" and selected_month:
        data = fetch_month_data(emp_id, selected_month)
        if not data.empty:
            st.subheader("📌 Performance Summary")
            st.dataframe(data[["Name", "Call Count", "AHT", "Hold", "Wrap"]])

            st.subheader("✅ KPI Scores")
            st.dataframe(data[["PKT Score", "CSAT (Agent Behaviour)", "Quality Score", "Grand Total"]])

            st.subheader("🎯 Target Commitments")
            st.markdown(f"""
                - **Target for PKT:** {data['Target Committed for PKT'].values[0]}
                - **Target for CSAT (Agent Behaviour):** {data['Target Committed for CSAT (Agent Behaviour)'].values[0]}
                - **Target for Quality:** {data['Target Committed for Quality'].values[0]}
            """)

            grand_total = float(data["Grand Total"].values[0])
            if grand_total >= 90:
                st.success("🌟 Excellent performance! Keep it up!")
            elif grand_total >= 75:
                st.info("👍 Good job! A little more push for excellence.")
            else:
                st.warning("⚠️ Needs improvement. Let's focus on key metrics!")

        else:
            st.warning("No data found for this EMP ID and month.")

    elif view_type == "Day" and selected_date:
        data = fetch_day_data(emp_id, selected_date.strftime("%m/%d/%Y"))
        if not data.empty:
            st.subheader("📅 Day Performance")
            st.dataframe(data[["Date", "Call Count", "AHT", "Hold", "Wrap", "CSAT Resolution", "CSAT Behaviour"]])
        else:
            st.warning("No day data found for this EMP ID and date.")

    elif view_type == "Week" and selected_week:
        perf, csat = fetch_week_data(emp_id, selected_week)
        if not perf.empty:
            st.subheader("🗓️ Week Performance")
            st.dataframe(perf)
            if not csat.empty:
                st.subheader("🎧 CSAT Scores")
                st.dataframe(csat[["CSAT Resolution", "CSAT Behaviour"]])
            else:
                st.warning("No CSAT data found for this EMP ID and week.")
        else:
            st.warning("No weekly performance data found for this EMP ID and week.")

else:
    st.info("Please enter your EMP ID to view data.")
