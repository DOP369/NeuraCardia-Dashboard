
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF

st.set_page_config(page_title="NeuraCardia Doctor Dashboard", layout="wide")
st.title("🧠 NeuraCardia AI – Doctor Monitoring Dashboard")

# Upload files
st.sidebar.header("📁 Upload Data")
uploaded_biomarkers = st.sidebar.file_uploader("Upload Biomarker CSV", type=["csv"])
uploaded_demo = st.sidebar.file_uploader("Upload Demographics CSV", type=["csv"])

if uploaded_biomarkers and uploaded_demo:
    df = pd.read_csv(uploaded_biomarkers)
    demo_df = pd.read_csv(uploaded_demo)
    df = df.merge(demo_df, on="patient_id", how="left")

    alert_filter = st.sidebar.selectbox("🔍 Filter by Alert Level", ["All", "NO ALERT", "Watch Zone", "⚠️ ALERT: Cardiac Risk"])
    if alert_filter != "All" and "alert" in df.columns:
        df = df[df["alert"] == alert_filter]

    selected_id = st.selectbox("🩺 Select Patient ID", df["patient_id"].unique())
    patient_data = df[df["patient_id"] == selected_id].sort_values("time_hr")

    if not patient_data.empty and "alert" in patient_data.columns:
        latest = patient_data.iloc[-1]
        alert = latest["alert"]

        # Summary
        st.markdown("### 👤 Patient Summary")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🧬 Age", int(latest.get("age", "N/A")))
        col2.metric("⚥ Gender", latest.get("gender", "N/A"))
        col3.metric("📍 Location", latest.get("location", "N/A"))
        if "ALERT" in alert:
            col4.metric("🚨 Alert", alert, delta="Critical", delta_color="inverse")
        elif "Watch" in alert:
            col4.metric("⚠️ Alert", alert, delta="Moderate", delta_color="off")
        else:
            col4.metric("✅ Alert", alert, delta="Stable", delta_color="normal")

        # Tabs
        tab1, tab2, tab3 = st.tabs(["📈 Biomarkers", "📊 Trends", "📄 Full Table"])

        with tab1:
            st.subheader("📈 Cardiac Biomarker Levels Over Time")
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(patient_data["time_hr"], patient_data["troponin"], label="Troponin", marker='o')
            ax.plot(patient_data["time_hr"], patient_data["ckmb"], label="CK-MB", marker='s')
            ax.plot(patient_data["time_hr"], patient_data["myoglobin"], label="Myoglobin", marker='^')
            ax.set_xlabel("Time (hours)")
            ax.set_ylabel("Level")
            ax.set_title("Biomarkers Over Time")
            ax.legend()
            st.pyplot(fig)

        with tab2:
            st.subheader("📊 Biomarker Trends")
            st.dataframe(patient_data[["time_hr", "troponin_trend", "ckmb_trend", "myoglobin_trend"]].tail(10), use_container_width=True)

        with tab3:
            st.subheader("📄 Complete Biomarker Data")
            st.dataframe(patient_data.tail(20), use_container_width=True)

        # PDF export
        st.markdown("### 📝 Generate PDF Doctor Report")
        if st.button("📤 Export Patient Report"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="NeuraCardia AI - Doctor Report", ln=1, align="C")
            pdf.cell(200, 10, txt=f"Patient ID: {selected_id}", ln=2)
            pdf.cell(200, 10, txt=f"Age: {int(latest.get('age', 0))}, Gender: {latest.get('gender', 'N/A')}, Location: {latest.get('location', 'N/A')}", ln=3)
            pdf.cell(200, 10, txt=f"Latest Alert: {alert}", ln=4)
            pdf.ln(5)
            pdf.set_font("Arial", size=10)
            pdf.cell(200, 10, txt="Recent Biomarker Trends:", ln=5)
            for i in range(-5, 0):
                row = patient_data.iloc[i]
                pdf.cell(200, 8, txt=f"Time: {row['time_hr']}hr | Trop: {row['troponin']} | CKMB: {row['ckmb']} | Myo: {row['myoglobin']}", ln=1)
            pdf_output = BytesIO()
            pdf.output(pdf_output)
            st.download_button(label="📥 Download PDF", data=pdf_output.getvalue(), file_name=f"Patient_{selected_id}_Report.pdf")
    else:
        st.warning("⚠️ No data available or 'alert' column missing for this patient.")
