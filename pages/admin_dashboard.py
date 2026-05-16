import streamlit as st
from supabase import create_client
from datetime import date, datetime, timedelta
import pandas as pd
import json

from utils.auth_utils import require_role

# ============================
# 🔒 حماية الصفحة للـ Admin فقط
# ============================
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
clients = supabase.table("clients").select("*").execute().data
users = supabase.table("users").select("*").execute().data

book_df = pd.DataFrame(bookings)
exp_df = pd.DataFrame(expenses)
comp_df = pd.DataFrame(compensations)
units_df = pd.DataFrame(units)
platforms_df = pd.DataFrame(platforms)
clients_df = pd.DataFrame(clients)
users_df = pd.DataFrame(users)

today = date.today()

# ============================
# 🧮 الحسابات المالية الموحدة
# ============================

# الدخل
total_income = float(book_df["price"].sum()) if "price" in book_df else 0

# المصاريف
total_expenses = float(exp_df["amount"].sum()) if "amount" in exp_df else 0

# التعويضات
total_comp = float(comp_df["amount"].sum()) if "amount" in comp_df else 0

# صافي الربح الصحيح
net_profit = total_income - total_expenses + total_comp

# ============================
# 🏘️ إحصائيات الوحدات
# ============================
total_units = len(units_df)

available_units = len(units_df[units_df["status"] == "متاحة"]) if "status" in units_df else 0
busy_units = len(units_df[units_df["status"] == "محجوزة"]) if "status" in units_df else 0
maintenance_units = len(units_df[units_df["status"] == "صيانة"]) if "status" in units_df else 0

# ============================
# 📊 إحصائيات عامة
# ============================
total_bookings = len(book_df)
total_platforms = len(platforms_df)
total_clients = len(clients_df)
total_users = len(users_df)

# ============================
# 🧱 Tabs علوية
# ============================
tab_labels = [
    "الإحصائيات العامة",
    "التقويم التفاعلي",
    "الحجوزات",
    "المتابعة",
    "المصاريف",
    "التعويضات",
    "الوحدات",
    "المنصات",
    "العملاء",
    "الموظفين",
]

(
    tab_stats,
    tab_calendar,
    tab_bookings,
    tab_monitor,
    tab_expenses,
    tab_comp,
    tab_units,
    tab_platforms,
    tab_clients,
    tab_employees,
) = st.tabs(tab_labels)

# ============================
# 🟦 Tab 1: الإحصائيات العامة
# ============================
with tab_stats:
    st.subheader("📊 الإحصائيات العامة")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 إجمالي الدخل", f"{total_income:,.2f} ريال")
    col2.metric("📉 المصاريف", f"{total_expenses:,.2f} ريال")
    col3.metric("🌿 التعويضات", f"{total_comp:,.2f} ريال")
    col4.metric("📈 صافي الربح", f"{net_profit:,.2f} ريال")

    st.write("---")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("🏠 عدد الوحدات", total_units)
    col6.metric("🟢 المتاحة", available_units)
    col7.metric("🔴 المحجوزة", busy_units)
    col8.metric("🟡 الصيانة", maintenance_units)

    st.write("---")

    col9, col10, col11, col12 = st.columns(4)
    col9.metric("📦 عدد الحجوزات", total_bookings)
    col10.metric("🌐 عدد المنصات", total_platforms)
    col11.metric("👥 عدد العملاء", total_clients)
    col12.metric("👨‍💼 عدد الموظفين", total_users)

# ============================
# 🟦 Tab 2: التقويم التفاعلي
# ============================
with tab_calendar:
    st.subheader("📅 تقويم الحجوزات (تفاعلي)")

    clean_events = []
    for b in bookings:
        try:
            start = str(datetime.fromisoformat(b["check_in"]).date())
            end = str(datetime.fromisoformat(b["check_out"]).date())
        except:
            continue

        clean_events.append({
            "id": b["id"],
            "title": f"{b.get('client_name', '')} – {b.get('unit_no', '')}",
            "start": start,
            "end": end,
            "color": "#007bff",
        })

    events_json = json.dumps(clean_events, ensure_ascii=False)

    calendar_html = f"""
    <div id='calendar'></div>

    <link href='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/main.min.css' rel='stylesheet' />
    <script src='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/main.min.js'></script>

    <script>
    var eventsData = JSON.parse(`{events_json}`);

    document.addEventListener('DOMContentLoaded', function() {{
        var calendarEl = document.getElementById('calendar');

        var calendar = new FullCalendar.Calendar(calendarEl, {{
            initialView: 'dayGridMonth',
            locale: 'ar',
            height: 650,
            selectable: true,
            events: eventsData,
        }});

        calendar.render();
    }});
    </script>
    """

    st.components.v1.html(calendar_html, height=700)

# ============================
# 🟦 Tab 3: الحجوزات
# ============================
with tab_bookings:
    st.subheader("📋 جدول الحجوزات")

    if not book_df.empty:
        for col in ["check_in", "check_out", "created_at"]:
            if col in book_df.columns:
                book_df[col] = book_df[col].astype(str)

        st.dataframe(book_df, use_container_width=True)
    else:
        st.info("لا توجد حجوزات.")

# ============================
# 🟦 Tab 4: المتابعة
# ============================
with tab_monitor:
    st.subheader("📆 المتابعة اليومية / الأسبوعية / الشهرية")

    # تحويل check_in إلى تاريخ
    def to_date(d):
        try:
            return datetime.fromisoformat(d).date()
        except:
            return None

    # يومي
    bookings_today = [b for b in bookings if to_date(b.get("check_in")) == today]
    bookings_tomorrow = [b for b in bookings if to_date(b.get("check_in")) == today + timedelta(days=1)]
    checkout_today = [b for b in bookings if to_date(b.get("check_out")) == today]
    checkout_tomorrow = [b for b in bookings if to_date(b.get("check_out")) == today + timedelta(days=1)]

    colA, colB, colC, colD = st.columns(4)
    colA.metric("حجوزات اليوم", len(bookings_today))
    colB.metric("حجوزات غداً", len(bookings_tomorrow))
    colC.metric("مغادرين اليوم", len(checkout_today))
    colD.metric("مغادرين غداً", len(checkout_tomorrow))

    st.write("---")

    # أسبوعي
    week_start = today - timedelta(days=7)
    weekly_bookings = [b for b in bookings if to_date(b.get("check_in")) and to_date(b.get("check_in")) >= week_start]
    weekly_income = sum(float(b.get("price", 0)) for b in weekly_bookings)

    col1, col2 = st.columns(2)
    col1.metric("حجوزات الأسبوع", len(weekly_bookings))
    col2.metric("الدخل الأسبوعي", f"{weekly_income:,.2f} ريال")

    st.write("---")

    # شهري
    month_start = today - timedelta(days=30)
    monthly_bookings = [b for b in bookings if to_date(b.get("check_in")) and to_date(b.get("check_in")) >= month_start]
    monthly_income = sum(float(b.get("price", 0)) for b in monthly_bookings)

    col3, col4 = st.columns(2)
    col3.metric("حجوزات الشهر", len(monthly_bookings))
    col4.metric("الدخل الشهري", f"{monthly_income:,.2f} ريال")

# ============================
# 🟦 Tab 5: المصاريف
# ============================
with tab_expenses:
    st.subheader("📉 المصاريف")

    if not exp_df.empty:
        exp_df["date_added"] = exp_df["date_added"].astype(str)
        st.dataframe(exp_df, use_container_width=True)
    else:
        st.info("لا توجد مصاريف.")

# ============================
# 🟦 Tab 6: التعويضات
# ============================
with tab_comp:
    st.subheader("🌿 التعويضات")

    if not comp_df.empty:
        comp_df["date_added"] = comp_df["date_added"].astype(str)
        st.dataframe(comp_df, use_container_width=True)
    else:
        st.info("لا توجد تعويضات.")

# ============================
# 🟦 Tab 7: الوحدات
# ============================
with tab_units:
    st.subheader("🏘️ الوحدات")

    if not units_df.empty:
        st.dataframe(units_df, use_container_width=True)
    else:
        st.info("لا توجد وحدات.")

# ============================
# 🟦 Tab 8: المنصات
# ============================
with tab_platforms:
    st.subheader("🌐 المنصات")

    if not platforms_df.empty:
        st.dataframe(platforms_df, use_container_width=True)
    else:
        st.info("لا توجد منصات.")

# ============================
# 🟦 Tab 9: العملاء
# ============================
with tab_clients:
    st.subheader("👥 العملاء")

    if not clients_df.empty:
        st.dataframe(clients_df, use_container_width=True)
    else:
        st.info("لا يوجد عملاء.")

# ============================
# 🟦 Tab 10: الموظفين
# ============================
with tab_employees:
    st.subheader("👨‍💼 الموظفون")

    if not users_df.empty:
        st.dataframe(users_df, use_container_width=True)
    else:
        st.info("لا يوجد موظفون.")
