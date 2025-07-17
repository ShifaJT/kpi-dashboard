import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# === CONFIG ===
SHEET_ID = "19aDfELEExMn0loj_w6D69ngGG4haEm6lsgqpxJC1OAA"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)
month_ws = sheet.worksheet("KPI Month")
day_ws = sheet.worksheet("KPI Day")

@st.cache_data
def load_month_data():
    data = month_ws.get_all_records()
    return pd.DataFrame(data)

@st.cache_data
def load_day_data():
    data = day_ws.get_all_records()
    return pd.DataFrame(data)

df_month = load_month_data()
df_day = load_day_data()

st.title("📊 KPI Dashboard for Champs")
st.markdown("📘 **About This Dashboard**")
st.markdown("This dashboard allows employees to view their KPI performance metrics for a selected time frame (Day, Week, or Month).")

emp_id = st.text_input("Enter EMP ID (e.g., 1070)")
view_type = st.selectbox("Select View Type", ["Month", "Week", "Day"])

filtered_data = None
selected_period = None

if emp_id:
    if view_type == "Month":
        selected_period = st.selectbox("Select Month", sorted(df_month["Month"].unique()))
        filtered_data = df_month[(df_month["EMP ID"].astype(str) == emp_id) & (df_month["Month"] == selected_period)]
    elif view_type == "Week":
        selected_period = st.selectbox("Select Week", sorted(df_day["Week"].unique()))
        week_data = df_day[(df_day["EMP ID"].astype(str) == emp_id) & (df_day["Week"] == selected_period)]
        if not week_data.empty:
            filtered_data = pd.DataFrame(week_data.mean(numeric_only=True)).transpose()
            filtered_data["EMP ID"] = emp_id
            filtered_data["Week"] = selected_period
    elif view_type == "Day":
        selected_period = st.selectbox("Select Date", sorted(df_day["Date"].unique()))
        filtered_data = df_day[(df_day["EMP ID"].astype(str) == emp_id) & (df_day["Date"] == selected_period)]

if filtered_data is not None and not filtered_data.empty:
    name = df_month[df_month["EMP ID"].astype(str) == emp_id]["NAME"].values[0] if view_type == "Month" else df_day[df_day["EMP ID"].astype(str) == emp_id]["NAME"].values[0]
    st.success(f"Performance Data for **{name}** | **{view_type}**: {selected_period}")

    st.subheader("🔹 Performance Metrics")
    perf_table = pd.DataFrame([
        ["Average hold used", "Hold", filtered_data.get("Hold", ["N/A"])[0], "HH:MM:SS"],
        ["Average time taken to wrap the call", "Wrap", filtered_data.get("Wrap", ["N/A"])[0], "HH:MM:SS"],
        ["Average duration of champ using auto on", "Auto-On", filtered_data.get("Auto-On", ["N/A"])[0], "HH:MM:SS"],
        ["Shift adherence for the period", "Schedule Adherence", f"{filtered_data.get('Schedule Adherence', [0])[0]}%", "Percentage"],
        ["Customer feedback on resolution given", "Resolution CSAT", f"{filtered_data.get('Resolution CSAT', [0])[0]}%", "Percentage"],
        ["Customer feedback on champ behaviour", "Agent Behaviour", f"{filtered_data.get('Agent Behaviour', [0])[0]}%", "Percentage"],
        ["Average Quality Score", "Quality", f"{filtered_data.get('Quality', [0])[0]}%", "Percentage"],
        ["Process knowledge test", "PKT", f"{filtered_data.get('PKT', [0])[0]}%", "Percentage"],
        ["Sick & unplanned leaves", "SL + UPL", filtered_data.get("SL + UPL", [0])[0], "Days"],
        ["Login days", "LOGINS", filtered_data.get("LOGINS", [0])[0], "Days"]
    ], columns=["Description", "Metric Name", "Value", "Unit"])
    st.dataframe(perf_table, use_container_width=True, hide_index=True)

    if view_type == "Month":
        st.subheader("✅ KPI Scores")
        kpi_table = pd.DataFrame([
            [0, "Hold KPI Score", filtered_data["Hold KPI Score"].values[0]],
            [0, "Wrap KPI Score", filtered_data["Wrap KPI Score"].values[0]],
            [30, "Auto-On KPI Score", filtered_data["Auto-On KPI Score"].values[0]],
            [10, "Schedule Adherence KPI Score", filtered_data["Schedule Adherence KPI Score"].values[0]],
            [10, "Resolution CSAT KPI Score", filtered_data["Resolution CSAT KPI Score"].values[0]],
            [20, "Agent Behaviour KPI Score", filtered_data["Agent Behaviour KPI Score"].values[0]],
            [20, "Quality KPI Score", filtered_data["Quality KPI Score"].values[0]],
            [10, "PKT KPI Score", filtered_data["PKT KPI Score"].values[0]]
        ], columns=["Weightage", "KPI Metrics", "Score"])
        st.dataframe(kpi_table, use_container_width=True, hide_index=True)

        st.subheader("🏁 Grand Total")
        grand_total = filtered_data["Grand Total"].values[0]
        st.metric("Grand Total KPI", f"{grand_total}")

        # Previous Month Comparison
        months = sorted(df_month["Month"].unique())
        current_idx = months.index(selected_period)
        if current_idx > 0:
            prev_month = months[current_idx - 1]
            prev_data = df_month[(df_month["EMP ID"].astype(str) == emp_id) & (df_month["Month"] == prev_month)]
            if not prev_data.empty:
                prev_score = prev_data["Grand Total"].values[0]
                diff = round(grand_total - prev_score, 2)
                if diff > 0:
                    st.success(f"👍 You improved by **+{diff} points** since last month ({prev_month})!")
                elif diff < 0:
                    st.warning(f"⚠️ Your score dropped by **{abs(diff)} points** since last month ({prev_month}).")
                else:
                    st.info("🔁 No change from last month.")

        # Motivational Quote
        if grand_total >= 4.5:
            msg = "🌟 Excellent work! Keep up the top performance!"
        elif grand_total >= 3.5:
            msg = "✅ Good job! A little push will take you higher!"
        elif grand_total >= 2.5:
            msg = "💪 You're getting there. Focus on key KPIs."
        else:
            msg = "📈 Let’s work together to improve. You got this!"
        st.subheader("💬 Motivation")
        st.write(msg)

        # Target Committed
        st.subheader("🎯 Target Committed for Next Month")
        target_cols = ["Target Committed for PKT", "Target Committed for CSAT (Agent Behaviour)", "Target Committed for Quality"]
        if all(col in filtered_data.columns for col in target_cols):
            st.write(filtered_data[target_cols].T.rename(columns={filtered_data.index[0]: "Target"}))
        else:
            st.write("No target data available.")
else:
    if emp_id:
        st.warning("No data found for the selected inputs.")
