import streamlit as st
from supabase import create_client
from datetime import date, datetime, timedelta
from streamlit_calendar import calendar
from utils.auth_utils import require_role

# ============================
# 🔒 السماح للمدير + المدير المساعد فقط
# ============================
require_role(["admin", "manager"])

# ============================
# ⚙️ إعداد الصفحة
# ============================
st.set_page_config(page_title="لوحة تحكم المدير", page_icon="📊", layout="wide")
st.markdown("<h2 style='text-align:right;'>📊 لوحة تحكم المدير</h2>", unsafe_allow_html=True)

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
units = supabase.table("units_names").select("*").execute().data
clients = supabase.table("clients").select("*").execute().data

today = date.today()

# ============================
# 📊 الإحصائيات الرئيسية
# ============================
st.write("### 📊 الإحصائيات الرئيسية")

today_bookings = [b for b in bookings if b["check_in"] == str(today)]
available_units = [u for u in units if u["status"] == "متاحة"]
total_clients = len(clients)

col1, col2, col3 = st.columns(3)
col1.metric("📅 حجوزات اليوم", len(today_bookings))
col2.metric("🏘️ الوحدات المتاحة", len(available_units))
col3.metric("👥 عدد العملاء", total_clients)

# ============================
# 🔔 التنبيهات
# ============================
st.write("### 🔔 تنبيهات")

checkout_today = [b for b in bookings if b["check_out"] == str(today)]
recent_bookings = [
    b for b in bookings
    if "created_at" in b and (datetime.now() - datetime.fromisoformat(b["created_at"])).days < 1
]

if checkout_today:
    st.warning(f"📤 {len(checkout_today)} عميل سيغادر اليوم")

if recent_bookings:
    st.success(f"🆕 {len(recent_bookings)} حجز جديد خلال آخر 24 ساعة")

if not checkout_today and not recent_bookings:
    st.info("لا توجد تنبيهات حالياً.")

# ============================
# 📅 تقويم الحجوزات
# ============================
st.write("### 📅 تقويم الحجوزات")

events = []
for b in bookings:
    events.append({
        "title": f"{b['client_name']} – {b['unit_no']}",
        "start": b["check_in"],
        "end": b["check_out"]
    })

calendar(events=events, options={"initialView": "dayGridMonth", "locale": "ar", "height": 650})

# ============================
# 📆 Daily Monitor
# ============================
st.write("### 📆 المتابعة اليومية")

tomorrow = today + timedelta(days=1)

bookings_today = today_bookings
bookings_tomorrow = [b for b in bookings if b["check_in"] == str(tomorrow)]
checkout_tomorrow = [b for b in bookings if b["check_out"] == str(tomorrow)]

colA, colB, colC, colD = st.columns(4)
colA.metric("حجوزات اليوم", len(bookings_today))
colB.metric("حجوزات غداً", len(bookings_tomorrow))
colC.metric("مغادرين اليوم", len(checkout_today))
colD.metric("مغادرين غداً", len(checkout_tomorrow))

# ============================
# 📆 Weekly Monitor
# ============================
st.write("### 📆 المتابعة الأسبوعية")

week_start = today - timedelta(days=7)

weekly_bookings = [b for b in bookings if b["check_in"] >= str(week_start)]
weekly_checkout = [b for b in bookings if b["check_out"] >= str(week_start)]
weekly_income = sum(float(b["price"]) for b in weekly_bookings)

col1, col2, col3 = st.columns(3)
col1.metric("حجوزات الأسبوع", len(weekly_bookings))
col2.metric("مغادرين الأسبوع", len(weekly_checkout))
col3.metric("الدخل الأسبوعي", f"{weekly_income:,.2f} ريال")

# ============================
# 📅 Monthly Monitor
# ============================
st.write("### 📅 المتابعة الشهرية")

month_start = today - timedelta(days=30)

monthly_bookings = [b for b in bookings if b["check_in"] >= str(month_start)]
monthly_checkout = [b for b in bookings if b["check_out"] >= str(month_start)]
monthly_income = sum(float(b["price"]) for b in monthly_bookings)

col1, col2, col3 = st.columns(3)
col1.metric("حجوزات الشهر", len(monthly_bookings))
col2.metric("مغادرين الشهر", len(monthly_checkout))
col3.metric("الدخل الشهري", f"{monthly_income:,.2f} ريال")

# ============================
# 🚀 روابط سريعة
# ============================
st.write("### 🚀 روابط سريعة")

colA, colB, colC = st.columns(3)
colA.page_link("pages/حجز_جديد.py", label="📝 حجز جديد")
colB.page_link("pages/حالة_الوحدات.py", label="🏘️ حالة الوحدات")
colC.page_link("pages/العملاء.py", label="👥 العملاء")
