import streamlit as st
from utils.auth import check_auth
import pandas as pd
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import tempfile
from supabase import create_client

# -----------------------------
# 🔗 الاتصال بـ Supabase
# -----------------------------
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

check_auth()

st.title("📊 التقارير المالية")

# -----------------------------
# 🔧 تحميل البيانات
# -----------------------------
def get_bookings():
    return supabase.table("bookings").select("*").execute().data

def get_expenses():
    return supabase.table("expenses").select("*").execute().data

def get_compensations():
    return supabase.table("compensations").select("*").execute().data

bookings = get_bookings()
expenses = get_expenses()
compensations = get_compensations()

df_bookings = pd.DataFrame(bookings)
df_expenses = pd.DataFrame(expenses)
df_comp = pd.DataFrame(compensations)

# -----------------------------
# 🧮 حساب الدخل
# -----------------------------
total_income_bookings = sum(float(b["total_price"]) for b in bookings)
total_compensations = sum(float(c["amount"]) for c in compensations)
total_income = total_income_bookings + total_compensations

# -----------------------------
# 🧮 حساب المصاريف
# -----------------------------
total_expenses = sum(float(e["amount"]) for e in expenses)

# -----------------------------
# 🧮 صافي الربح العام
# -----------------------------
net_profit = total_income - total_expenses

# -----------------------------
# 🌐 الدخل حسب المنصة
# -----------------------------
income_per_platform = df_bookings.groupby("platform")["total_price"].sum().reset_index()

# -----------------------------
# 🏠 الدخل حسب الوحدة
# -----------------------------
income_per_unit = df_bookings.groupby("unit_no")["total_price"].sum().reset_index()

# -----------------------------
# 💸 مصاريف الوحدة
# -----------------------------
if "unit_no" in df_expenses.columns:
    expenses_per_unit = df_expenses.groupby("unit_no")["amount"].sum().reset_index()
else:
    expenses_per_unit = pd.DataFrame(columns=["unit_no", "amount"])

# -----------------------------
# 📈 صافي الربح لكل وحدة
# -----------------------------
unit_profit = pd.merge(income_per_unit, expenses_per_unit, on="unit_no", how="left")
unit_profit["amount"] = unit_profit["amount"].fillna(0)
unit_profit["net_profit"] = unit_profit["total_price"] - unit_profit["amount"]

# -----------------------------
# 📌 عرض الملخص
# -----------------------------
st.subheader("📌 الملخص المالي")

col1, col2, col3, col4 = st.columns(4)

col1.metric("💰 دخل الحجوزات", f"{total_income_bookings} ريال")
col2.metric("🌿 التعويضات", f"{total_compensations} ريال")
col3.metric("📉 المصاريف", f"{total_expenses} ريال")
col4.metric("📈 صافي الربح", f"{net_profit} ريال")

# -----------------------------
# 🌐 الدخل حسب المنصة
# -----------------------------
st.subheader("🌐 الدخل حسب المنصة")
st.dataframe(income_per_platform)

# -----------------------------
# 🏠 الدخل حسب الوحدة
# -----------------------------
st.subheader("🏠 الدخل حسب الوحدة")
st.dataframe(income_per_unit)

# -----------------------------
# 💸 مصاريف الوحدة
# -----------------------------
st.subheader("💸 مصاريف كل وحدة")
st.dataframe(expenses_per_unit)

# -----------------------------
# 📈 صافي الربح لكل وحدة
# -----------------------------
st.subheader("📈 صافي الربح لكل وحدة")
st.dataframe(unit_profit)

# -----------------------------
# 🖨 إنشاء PDF
# -----------------------------
def generate_pdf():
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(temp_file.name, pagesize=A4)

    width, height = A4
    y = height - 30

    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, y, "التقرير المالي")
    y -= 30

    c.setFont("Helvetica", 12)
    c.drawString(30, y, f"💰 دخل الحجوزات: {total_income_bookings} ريال")
    y -= 20
    c.drawString(30, y, f"🌿 التعويضات: {total_compensations} ريال")
    y -= 20
    c.drawString(30, y, f"📉 المصاريف: {total_expenses} ريال")
    y -= 20
    c.drawString(30, y, f"📈 صافي الربح: {net_profit} ريال")
    y -= 40

    # دخل المنصات
    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, y, "🌐 الدخل حسب المنصة")
    y -= 25

    c.setFont("Helvetica", 11)
    for _, row in income_per_platform.iterrows():
        c.drawString(40, y, f"{row['platform']}: {row['total_price']} ريال")
        y -= 18

    y -= 20

    # دخل الوحدات
    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, y, "🏠 الدخل حسب الوحدة")
    y -= 25

    c.setFont("Helvetica", 11)
    for _, row in income_per_unit.iterrows():
        c.drawString(40, y, f"وحدة {row['unit_no']}: {row['total_price']} ريال")
        y -= 18

    y -= 20

    # مصاريف الوحدات
    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, y, "💸 مصاريف كل وحدة")
    y -= 25

    c.setFont("Helvetica", 11)
    for _, row in expenses_per_unit.iterrows():
        c.drawString(40, y, f"وحدة {row['unit_no']}: {row['amount']} ريال")
        y -= 18

    y -= 20

    # صافي الربح لكل وحدة
    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, y, "📈 صافي الربح لكل وحدة")
    y -= 25

    c.setFont("Helvetica", 11)
    for _, row in unit_profit.iterrows():
        c.drawString(40, y, f"وحدة {row['unit_no']}: {row['net_profit']} ريال")
        y -= 18

    c.save()
    return temp_file.name

# -----------------------------
# 📄 زر تصدير PDF
# -----------------------------
st.subheader("📄 تصدير التقرير")

if st.button("📄 تصدير التقرير PDF"):
    pdf_path = generate_pdf()
    with open(pdf_path, "rb") as f:
        st.download_button(
            label="⬇ تحميل التقرير PDF",
            data=f,
            file_name="financial_report.pdf",
            mime="application/pdf"
        )
