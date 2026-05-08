import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date, datetime

from utils.auth_utils import require_role

# ============================
# 🔒 حماية الصفحة
# ============================
require_role(["admin", "manager"])

# ============================
# ⚙️ إعداد الصفحة
# ============================
st.set_page_config(page_title="التقارير المالية", page_icon="📊", layout="wide")
st.markdown("<h2 style='text-align:right;'>📊 التقارير المالية</h2>", unsafe_allow_html=True)

# ============================
# 📡 الاتصال بـ Supabase
# ============================
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# ============================
# 📌 تحميل البيانات
# ============================
bookings = supabase.table("bookings").select("*").execute().data
expenses = supabase.table("expenses").select("*").execute().data if "expenses" in st.secrets else []
compensations = supabase.table("compensations").select("*").execute().data

# ============================
# 📊 الحسابات الأساسية
# ============================
total_income = sum(float(b["price"]) for b in bookings)
total_expenses = sum(float(e["amount"]) for e in expenses) if expenses else 0
total_compensations = sum(float(c["amount"]) for c in compensations)

net_profit = total_income - total_expenses - total_compensations

# ============================
# 📌 عرض الملخص
# ============================
col1, col2, col3, col4 = st.columns(4)

col1.metric("💰 إجمالي الدخل", f"{total_income} ريال")
col2.metric("📉 المصاريف", f"{total_expenses} ريال")
col3.metric("⚠️ التعويضات", f"{total_compensations} ريال")
col4.metric("📊 صافي الربح", f"{net_profit} ريال")

# ============================
# 📅 تقارير حسب التاريخ
# ============================
st.write("---")
st.subheader("📅 التقارير حسب التاريخ")

start_date = st.date_input("من تاريخ", date.today().replace(day=1))
end_date = st.date_input("إلى تاريخ", date.today())

filtered_bookings = [
    b for b in bookings
    if start_date <= date.fromisoformat(b["check_in"]) <= end_date
]

filtered_comp = [
    c for c in compensations
    if start_date <= date.fromisoformat(c["date_added"]) <= end_date
]

filtered_expenses = [
    e for e in expenses
    if start_date <= date.fromisoformat(e["date_added"]) <= end_date
] if expenses else []

st.metric("💰 دخل الفترة", f"{sum(float(b['price']) for b in filtered_bookings)} ريال")
st.metric("⚠️ تعويضات الفترة", f"{sum(float(c['amount']) for c in filtered_comp)} ريال")
st.metric("📉 مصاريف الفترة", f"{sum(float(e['amount']) for e in filtered_expenses)} ريال")

# ============================
# 📋 جدول الحجوزات
# ============================
st.write("---")
st.subheader("📋 الحجوزات")

if filtered_bookings:
    st.dataframe(pd.DataFrame(filtered_bookings))
else:
    st.info("لا توجد حجوزات في هذه الفترة.")

# ============================
# ⚠️ جدول التعويضات
# ============================
st.write("---")
st.subheader("⚠️ التعويضات")

if compensations:
    df_comp = pd.DataFrame(compensations)
    st.dataframe(df_comp[["id", "unit_no", "client_name", "damage_type", "amount", "date_added"]])
else:
    st.info("لا توجد تعويضات.")

# ============================
# 📉 جدول المصاريف
# ============================
st.write("---")
st.subheader("📉 المصاريف")

if expenses:
    df_exp = pd.DataFrame(expenses)
    st.dataframe(df_exp)
else:
    st.info("لا توجد مصاريف.")
