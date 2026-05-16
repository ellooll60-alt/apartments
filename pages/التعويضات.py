import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date

# -----------------------------
# 🔐 التحقق من تسجيل الدخول
# -----------------------------
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("يجب تسجيل الدخول للوصول إلى هذه الصفحة.")
    st.stop()

# -----------------------------
# 🔗 الاتصال بـ Supabase
# -----------------------------
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("🌿 إدارة التعويضات")

# -----------------------------
# 🔧 تحميل البيانات
# -----------------------------
def get_bookings():
    return supabase.table("bookings").select("*").execute().data

def get_compensations():
    return supabase.table("compensations").select("*").execute().data

bookings = get_bookings()
compensations = get_compensations()

booking_list = {f"{b['id']} - {b['client_name']}": b["id"] for b in bookings}

# -----------------------------
# ➕ إضافة تعويض جديد
# -----------------------------
st.subheader("➕ إضافة تعويض جديد")

col1, col2 = st.columns(2)

with col1:
    selected_booking = st.selectbox("اختر الحجز", list(booking_list.keys()))
    amount = st.number_input("المبلغ", min_value=0.0, step=1.0)

with col2:
    reason = st.text_input("سبب التعويض")
    comp_date = st.date_input("التاريخ", date.today())

if st.button("💾 حفظ التعويض"):
    supabase.table("compensations").insert({
        "booking_id": booking_list[selected_booking],
        "amount": amount,
        "reason": reason,
        "date": str(comp_date)
    }).execute()

    st.success("تم حفظ التعويض بنجاح.")
    st.experimental_rerun()

# -----------------------------
# 📋 عرض التعويضات
# -----------------------------
st.subheader("📋 قائمة التعويضات")

if compensations:
    df = pd.DataFrame(compensations)
    st.dataframe(df)
else:
    st.info("لا توجد تعويضات مسجلة.")
