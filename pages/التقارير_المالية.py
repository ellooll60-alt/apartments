import streamlit as st
from utils.supabase_client import supabase
from utils.auth import check_auth
import pandas as pd
from datetime import datetime

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

# -----------------------------
# 🧮 حساب الدخل
# -----------------------------
total_income_bookings = sum(float(b["total_price"]) for b in bookings)

# ✔ التعويضات تُحسب كدخل
total_compensations = sum(float(c["amount"]) for c in compensations)

# ✔ إجمالي الدخل = دخل الحجوزات + التعويضات
total_income = total_income_bookings + total_compensations

# -----------------------------
# 🧮 حساب المصاريف
# -----------------------------
total_expenses = sum(float(e["amount"]) for e in expenses)

# -----------------------------
# 🧮 صافي الربح
# -----------------------------
net_profit = total_income - total_expenses

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
# 📅 التقارير حسب التاريخ
# -----------------------------
st.subheader("📅 التقارير حسب التاريخ")

selected_date = st.date_input("اختر التاريخ", datetime.today())
selected_date_str = selected_date.strftime("%Y-%m-%d")

# دخل الحجوزات في اليوم
daily_bookings = [b for b in bookings if b["date_added"].startswith(selected_date_str)]
daily_income = sum(float(b["total_price"]) for b in daily_bookings)

# ✔ تعويضات اليوم
daily_comp = [c for c in compensations if c["date"].startswith(selected_date_str)]
daily_comp_total = sum(float(c["amount"]) for c in daily_comp)

# مصاريف اليوم
daily_exp = [e for e in expenses if e["date"].startswith(selected_date_str)]
daily_exp_total = sum(float(e["amount"]) for e in daily_exp)

daily_net = (daily_income + daily_comp_total) - daily_exp_total

colA, colB, colC, colD = st.columns(4)
colA.metric("دخل اليوم", f"{daily_income} ريال")
colB.metric("تعويضات اليوم", f"{daily_comp_total} ريال")
colC.metric("مصاريف اليوم", f"{daily_exp_total} ريال")
colD.metric("صافي اليوم", f"{daily_net} ريال")

# -----------------------------
# 📋 جدول التعويضات داخل التقارير
# -----------------------------
st.subheader("📋 تقرير التعويضات")

if compensations:
    df_comp = pd.DataFrame(compensations)
    df_comp = df_comp[["id", "booking_id", "reason", "amount", "date"]]
    st.dataframe(df_comp)
else:
    st.info("لا توجد تعويضات مسجلة.")
