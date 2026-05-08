import streamlit as st
from supabase import create_client
from datetime import date
from utils.auth_utils import require_role

# ============================
# 🔒 السماح للموظف فقط
# ============================
require_role(["employee"])

# ============================
# ⚙️ إعداد الصفحة
# ============================
st.set_page_config(page_title="لوحة تحكم الموظف", page_icon="🧑‍💼", layout="wide")
st.markdown("<h2 style='text-align:right;'>🧑‍💼 لوحة تحكم الموظف</h2>", unsafe_allow_html=True)

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

today = date.today()

# ============================
# 📊 الإحصائيات الأساسية
# ============================
st.write("### 📊 الإحصائيات الأساسية")

today_bookings = [b for b in bookings if b["check_in"] == str(today)]
available_units = [u for u in units if u["status"] == "متاحة"]

col1, col2 = st.columns(2)
col1.metric("📅 حجوزات اليوم", len(today_bookings))
col2.metric("🏘️ الوحدات المتاحة", len(available_units))

# ============================
# 🚀 روابط سريعة
# ============================
st.write("### 🚀 روابط سريعة")

colA, colB = st.columns(2)

colA.page_link("pages/حجز_جديد.py", label="📝 إضافة حجز")
colB.page_link("pages/حالة_الوحدات.py", label="🏘️ حالة الوحدات")
