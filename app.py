import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Set page config
st.set_page_config(page_title="KPI Dashboard for Champs", layout="centered")
st.title("KPI Dashboard for Champs")

# Google Sheets Authentication
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("creds.json", scopes=scope)
client = gspread.authorize(creds)

# Load sheets
sheet = client.open_by_key("19aDfELEExMn0loj_w6D69ngGG4haEm6IsgqpxJC1OAA")
kpi_month_df = pd.DataFrame(sheet.worksheet("KPI Month").get_all_records())
kpi_day_df = pd.DataFrame(sheet.worksheet("KPI Day").get_all_records())
csat_score_df = pd.DataFrame(sheet.worksheet("CSAT Score").get_all_records())

# Input EMP ID
emp_id = st.text_input("Enter EMP ID")

if emp_id:
    view_type = st.selectbox("Select View Type", ["Day", "Week", "Month"])

    if view_type == "Day":
        try:
            kpi_day_df["Date"] = pd.to_datetime(kpi_day_df["Date"], format="%m/%d/%Y", errors="coerce")
            available_dates = kpi_day_df.loc[kpi_day_df['EMP ID'] == int(emp_id), "Date"].dropna().unique()
            if len(available_dates) == 0:
                st.warning("No daily data found.")
            else:
                selected_date = st.date_input("Select Date", value=pd.to_datetime("today"))
                selected_data = kpi_day_df[
                    (kpi_day_df['EMP ID'] == int(emp_id)) & 
                    (kpi_day_df['Date'] == pd.to_datetime(selected_date))
                ]
                if selected_data.empty:
                    st.warning("No daily data found for this date.")
                else:
                    st.write("### Day View Data")
                    st.dataframe(selected_data)
        except Exception as e:
            st.error(f"Error loading daily data: {e}")

    elif view_type == "Week":
        try:
            kpi_day_df["Week"] = kpi_day_df["Week"].astype(str)
            week_options = sorted(kpi_day_df.loc[kpi_day_df['EMP ID'] == int(emp_id), "Week"].dropna().unique())
            selected_week = st.selectbox("Select Week", week_options)

            week_data = kpi_day_df[
                (kpi_day_df['EMP ID'] == int(emp_id)) & 
                (kpi_day_df['Week'] == selected_week)
            ]
            csat_week_data = csat_score_df[
                (csat_score_df['EMP ID'] == int(emp_id)) & 
                (csat_score_df['Week'] == selected_week)
            ]

            if week_data.empty and csat_week_data.empty:
                st.warning("No weekly data found for this employee and week.")
            else:
                st.write("### Week View Data")
                numeric_cols = ["Call Count", "AHT", "Hold", "Wrap"]
                week_agg = week_data[numeric_cols].apply(pd.to_numeric, errors='coerce').mean().to_frame(name="Average").T
                week_agg["CSAT Resolution"] = csat_week_data["CSAT Resolution"].values[0] if not csat_week_data.empty else "NA"
                week_agg["CSAT Behaviour"] = csat_week_data["CSAT Behaviour"].values[0] if not csat_week_data.empty else "NA"
                st.dataframe(week_agg)
        except Exception as e:
            st.error(f"Error loading weekly data: {e}")

    elif view_type == "Month":
        try:
            month_options = sorted(kpi_month_df.loc[kpi_month_df['EMP ID'] == int(emp_id), "Month"].unique())
            selected_month = st.selectbox("Select Month", month_options)
            selected_data = kpi_month_df[
                (kpi_month_df['EMP ID'] == int(emp_id)) & 
                (kpi_month_df['Month'] == selected_month)
            ]
            if selected_data.empty:
                st.warning("No monthly data found.")
            else:
                st.write("### Month View Data")
                st.dataframe(selected_data)
        except Exception as e:
            st.error(f"Error loading monthly data: {e}")
