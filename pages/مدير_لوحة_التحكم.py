import streamlit as st
from supabase import create_client
from datetime import date, datetime, timedelta
from utils.auth_utils import require_role
import pandas as pd
import json

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
# 📅 تقويم الحجوزات (تفاعلي)
# ============================
st.write("### 📅 تقويم الحجوزات (تفاعلي)")

clean_events = []
for b in bookings:
    if not b.get("check_in") or not b.get("check_out"):
        continue

    try:
        start = str(datetime.fromisoformat(b["check_in"]).date())
        end = str(datetime.fromisoformat(b["check_out"]).date())
    except:
        continue

    clean_events.append({
        "id": b["id"],
        "title": f"{b['client_name']} – {b['unit_no']}",
        "start": start,
        "end": end,
        "color": "#007bff"
    })

events_json = json.dumps(clean_events, ensure_ascii=False)

calendar_html = f"""
<div id='calendar'></div>

<script src='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/main.min.js'></script>
<link href='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/main.min.css' rel='stylesheet' />

<script>
var eventsData = JSON.parse(`{events_json}`);

document.addEventListener('DOMContentLoaded', function() {{
    var calendar = new FullCalendar.Calendar(document.getElementById('calendar'), {{
        initialView: 'dayGridMonth',
        locale: 'ar',
        height: 650,
        selectable: true,
        events: eventsData,

        dateClick: function(info) {{
            window.parent.postMessage({{ action: "add", date: info.dateStr }}, "*");
        }},

        eventClick: function(info) {{
            window.parent.postMessage({{ action: "edit", id: info.event.id }}, "*");
        }}
    }});
    calendar.render();
}});
</script>
"""

st.components.v1.html(calendar_html, height=700)

# استقبال رسائل التقويم
if "action" in st.query_params:
    action = st.query_params["action"]

    if action == "add":
        st.session_state["new_booking_date"] = st.query_params["date"]
        st.switch_page("pages/حجز_جديد.py")

    if action == "edit":
        st.session_state["edit_booking_id"] = st.query_params["id"]
        st.switch_page("pages/تعديل_حجز.py")

# ============================
# 📋 جدول الحجوزات التفاعلي (قابل للبحث)
# ============================
st.write("### 📋 جدول الحجوزات (تفاعلي وقابل للبحث)")

if bookings:
    df = pd.DataFrame(bookings)

    for col in ["check_in", "check_out", "created_at"]:
        if col in df.columns:
            df[col] = df[col].astype(str)

    search = st.text_input("🔍 بحث عن حجز (اسم العميل، رقم الوحدة، المنصة):", "")

    if search:
        search_lower = search.lower()
        df = df[df.apply(lambda row:
            search_lower in str(row.get("client_name", "")).lower() or
            search_lower in str(row.get("unit_no", "")).lower() or
            search_lower in str(row.get("platform", "")).lower()
        , axis=1)]

    st.dataframe(df, use_container_width=True)
else:
    st.info("لا توجد حجوزات.")
