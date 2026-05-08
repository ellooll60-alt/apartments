import streamlit as st
from supabase import create_client
from datetime import date, datetime, timedelta
import pandas as pd
import json

# ============================
# 🔒 حماية الصفحة للـ Admin فقط
# ============================
from utils.auth_utils import require_role
require_role(["admin"])

# ============================
# ⚙️ إعداد الصفحة
# ============================
st.set_page_config(page_title="لوحة التحكم - Admin", page_icon="📊", layout="wide")
st.markdown("<h2 style='text-align:right;'>📊 لوحة التحكم (Admin)</h2>", unsafe_allow_html=True)

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
expenses = supabase.table("expenses").select("*").execute().data
compensations = supabase.table("compensations").select("*").execute().data
units = supabase.table("units_names").select("*").execute().data
platforms = supabase.table("platforms").select("*").execute().data
users = supabase.table("users").select("*").execute().data

book_df = pd.DataFrame(bookings)
exp_df = pd.DataFrame(expenses)
comp_df = pd.DataFrame(compensations)

today = date.today()

# ============================
# 🧮 الحسابات الأساسية
# ============================
total_income = book_df["price"].sum() if not book_df.empty else 0
total_expenses = exp_df["amount"].sum() if not exp_df.empty else 0
total_comp = comp_df["amount"].sum() if not comp_df.empty else 0
net_profit = total_income - total_expenses - total_comp

total_units = len(units)
available_units = len([u for u in units if u["status"] == "متاحة"])
busy_units = len([u for u in units if u["status"] == "محجوزة"])
maintenance_units = len([u for u in units if u["status"] == "صيانة"])

total_bookings = len(book_df)
total_platforms = len(platforms)
total_users = len(users)

# ============================
# 📊 الإحصائيات العامة
# ============================
st.write("### 📊 الإحصائيات العامة")

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 إجمالي الدخل", f"{total_income:,.2f} ريال")
col2.metric("📉 المصاريف", f"{total_expenses:,.2f} ريال")
col3.metric("⚠️ التعويضات", f"{total_comp:,.2f} ريال")
col4.metric("📈 صافي الربح", f"{net_profit:,.2f} ريال")

st.write("---")

col5, col6, col7, col8 = st.columns(4)
col5.metric("🏠 عدد الوحدات", total_units)
col6.metric("🟢 المتاحة", available_units)
col7.metric("🔴 المحجوزة", busy_units)
col8.metric("🟡 الصيانة", maintenance_units)

st.write("---")

col9, col10, col11 = st.columns(3)
col9.metric("📦 عدد الحجوزات", total_bookings)
col10.metric("🌐 عدد المنصات", total_platforms)
col11.metric("👥 عدد الموظفين", total_users)

# ============================
# 📅 تقويم الحجوزات التفاعلي
# ============================
st.write("### 📅 تقويم الحجوزات (تفاعلي)")

calendar_events = []

for b in bookings:
    if not b.get("check_in") or not b.get("check_out"):
        continue

    try:
        start = str(datetime.fromisoformat(b["check_in"]).date())
        end = str(datetime.fromisoformat(b["check_out"]).date())
    except:
        start = b["check_in"].split("T")[0]
        end = b["check_out"].split("T")[0]

    calendar_events.append({
        "id": b["id"],
        "title": f"{b['client_name']} – {b['unit_no']}",
        "start": start,
        "end": end,
        "color": "#007bff"
    })

events_json = json.dumps(calendar_events)

calendar_html = f"""
<!DOCTYPE html>
<html>
<head>
<link href='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/main.min.css' rel='stylesheet' />
<script src='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/main.min.js'></script>

<style>
  #calendar {{
    max-width: 100%;
    margin: 20px auto;
  }}
</style>
</head>
<body>

<div id='calendar'></div>

<script>
document.addEventListener('DOMContentLoaded', function() {{
    var calendarEl = document.getElementById('calendar');

    var calendar = new FullCalendar.Calendar(calendarEl, {{
        initialView: 'dayGridMonth',
        locale: 'ar',
        height: 650,
        selectable: true,
        events: {events_json},

        dateClick: function(info) {{
            window.parent.postMessage(
                {{ "action": "add", "date": info.dateStr }},
                "*"
            );
        }},

        eventClick: function(info) {{
            window.parent.postMessage(
                {{ "action": "edit", "id": info.event.id }},
                "*"
            );
        }}
    }});

    calendar.render();
}});
</script>

</body>
</html>
"""

st.components.v1.html(calendar_html, height=700)

# ============================
# 📥 استقبال الرسائل من التقويم
# ============================
msg = st.experimental_get_query_params()

if "action" in msg:
    action = msg["action"][0]

    # إضافة حجز جديد
    if action == "add":
        selected_date = msg["date"][0]
        st.session_state["new_booking_date"] = selected_date
        st.switch_page("pages/حجز_جديد.py")

    # تعديل حجز
    if action == "edit":
        booking_id = msg["id"][0]
        st.session_state["edit_booking_id"] = booking_id
        st.switch_page("pages/تعديل_حجز.py")


# ============================
# 📆 Daily Monitor
# ============================
st.write("### 📆 المتابعة اليومية")

tomorrow = today + timedelta(days=1)

bookings_today = [b for b in bookings if b["check_in"] == str(today)]
bookings_tomorrow = [b for b in bookings if b["check_in"] == str(tomorrow)]
checkout_today = [b for b in bookings if b["check_out"] == str(today)]
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
st.write("### 📆 المتابعة الشهرية")

month_start = today - timedelta(days=30)

monthly_bookings = [b for b in bookings if b["check_in"] >= str(month_start)]
monthly_checkout = [b for b in bookings if b["check_out"] >= str(month_start)]
monthly_income = sum(float(b["price"]) for b in monthly_bookings)

col1, col2, col3 = st.columns(3)
col1.metric("حجوزات الشهر", len(monthly_bookings))
col2.metric("مغادرين الشهر", len(monthly_checkout))
col3.metric("الدخل الشهري", f"{monthly_income:,.2f} ريال")

# ============================
# 📊 مقارنة الشهر الحالي والسابق
# ============================
st.write("### 📊 مقارنة الشهر الحالي بالشهر السابق")

prev_month_start = today - timedelta(days=60)

previous_month_bookings = [
    b for b in bookings
    if str(prev_month_start) <= b["check_in"] < str(month_start)
]

previous_month_income = sum(float(b["price"]) for b in previous_month_bookings)

col1, col2 = st.columns(2)
col1.metric("حجوزات الشهر الحالي", len(monthly_bookings))
col2.metric("حجوزات الشهر السابق", len(previous_month_bookings))

# ============================
# 📅 تقرير الأداء السنوي
# ============================
st.write("### 📅 تقرير الأداء السنوي")

year_start = today.replace(month=1, day=1)

yearly_bookings = [b for b in bookings if b["check_in"] >= str(year_start)]
yearly_income = sum(float(b["price"]) for b in yearly_bookings)
yearly_clients = [
    c for c in users
    if "created_at" in c and c["created_at"] >= str(year_start)
]

col1, col2, col3 = st.columns(3)
col1.metric("حجوزات السنة", len(yearly_bookings))
col2.metric("الدخل السنوي", f"{yearly_income:,.2f} ريال")
col3.metric("عملاء جدد", len(yearly_clients))

# ============================
# 🔮 Forecasting
# ============================
st.write("### 🔮 التوقعات المستقبلية")

def to_date(d):
    try:
        return datetime.fromisoformat(d).date()
    except:
        return None

sorted_bookings = sorted(bookings, key=lambda b: to_date(b["check_in"]) or today)

daily_income = {}
for b in sorted_bookings:
    d = to_date(b["check_in"])
    if d:
        daily_income[d] = daily_income.get(d, 0) + float(b["price"])

last_7_days = [daily_income.get(today - timedelta(days=i), 0) for i in range(7)]
avg_7 = sum(last_7_days) / 7

last_30_days = [daily_income.get(today - timedelta(days=i), 0) for i in range(30)]
avg_30 = sum(last_30_days) / 30

growth_rate = (avg_7 - avg_30) / avg_30 if avg_30 > 0 else 0

forecast_week = avg_7 * (1 + growth_rate) * 7
forecast_month = avg_30 * (1 + growth_rate) * 30
forecast_bookings = int(len(weekly_bookings) * (1 + growth_rate))

col1, col2, col3 = st.columns(3)
col1.metric("الحجوزات المتوقعة", forecast_bookings)
col2.metric("الدخل المتوقع (أسبوع)", f"{forecast_week:,.2f} ريال")
col3.metric("الدخل المتوقع (شهر)", f"{forecast_month:,.2f} ريال")

# ============================
# 📋 آخر 5 حجوزات
# ============================
st.write("### 📋 آخر 5 حجوزات")

if not book_df.empty:
    last5 = book_df.sort_values("id", ascending=False).head(5)
    st.table(last5[["id", "client_name", "unit_no", "check_in", "check_out", "price"]])
else:
    st.info("لا توجد حجوزات.")

# ============================
# 📋 آخر 5 مصاريف
# ============================
st.write("### 📋 آخر 5 مصاريف")

if not exp_df.empty:
    last5_exp = exp_df.sort_values("id", ascending=False).head(5)
    st.table(last5_exp[["id", "expense_type", "amount", "date_added"]])
else:
    st.info("لا توجد مصاريف.")

# ============================
# 📋 آخر 5 تعويضات
# ============================
st.write("### 📋 آخر 5 تعويضات")

if not comp_df.empty:
    last5_comp = comp_df.sort_values("id", ascending=False).head(5)
    st.table(last5_comp[["id", "client_name", "unit_no", "amount", "date_added"]])
else:
    st.info("لا توجد تعويضات.")
