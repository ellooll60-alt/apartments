import streamlit as st
from supabase import create_client
from datetime import date, datetime, timedelta
import pandas as pd
import json

from utils.auth_utils import require_role

# ============================
# 🔒 السماح للمدير + المدير المساعد
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
platforms = supabase.table("platforms").select("*").execute().data

book_df = pd.DataFrame(bookings)
units_df = pd.DataFrame(units)
clients_df = pd.DataFrame(clients)
platforms_df = pd.DataFrame(platforms)

today = date.today()

total_units = len(units_df)
available_units = len(units_df[units_df["status"] == "متاحة"]) if not units_df.empty and "status" in units_df.columns else 0
busy_units = len(units_df[units_df["status"] == "محجوزة"]) if not units_df.empty and "status" in units_df.columns else 0
total_bookings = len(book_df)
total_clients = len(clients_df)

# ============================
# 🧱 Tabs علوية (قابلة للتمرير)
# ============================
tab_labels = [
    "الإحصائيات العامة",
    "التقويم التفاعلي",
    "الحجوزات",
    "المتابعة",
    "التقارير",
    "الوحدات",
    "المنصات",
    "العملاء",
]

(
    tab_stats,
    tab_calendar,
    tab_bookings,
    tab_monitor,
    tab_reports,
    tab_units,
    tab_platforms,
    tab_clients,
) = st.tabs(tab_labels)

# ============================
# 🟩 Tab 1: الإحصائيات العامة
# ============================
with tab_stats:
    st.subheader("📊 الإحصائيات الرئيسية")

    col1, col2, col3 = st.columns(3)
    col1.metric("📦 عدد الحجوزات", total_bookings)
    col2.metric("🏘️ عدد الوحدات", total_units)
    col3.metric("👥 عدد العملاء", total_clients)

    st.write("---")

    col4, col5 = st.columns(2)
    col4.metric("🟢 الوحدات المتاحة", available_units)
    col5.metric("🔴 الوحدات المحجوزة", busy_units)

# ============================
# 🟩 Tab 2: التقويم التفاعلي
# ============================
with tab_calendar:
    st.subheader("📅 تقويم الحجوزات (تفاعلي)")

    clean_events = []
    for b in bookings:
        if not b.get("check_in") or not b.get("check_out"):
            continue

        try:
            start = str(datetime.fromisoformat(b["check_in"]).date())
            end = str(datetime.fromisoformat(b["check_out"]).date())
        except Exception:
            try:
                start = b["check_in"].split("T")[0]
                end = b["check_out"].split("T")[0]
            except Exception:
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

# ============================
# 🟩 Tab 3: الحجوزات (جدول تفاعلي)
# ============================
with tab_bookings:
    st.subheader("📋 جدول الحجوزات (تفاعلي وقابل للبحث)")

    if not book_df.empty:
        for col in ["check_in", "check_out", "created_at"]:
            if col in book_df.columns:
                book_df[col] = book_df[col].astype(str)

        search = st.text_input("🔍 بحث (اسم العميل، رقم الوحدة، المنصة):", "")

        filtered = book_df.copy()
        if search:
            s = search.lower()
            def match_row(row):
                client = str(row.get("client_name", "")).lower()
                unit_no = str(row.get("unit_no", "")).lower()
                platform = str(row.get("platform", "")).lower()
                return (s in client) or (s in unit_no) or (s in platform)
            filtered = filtered[filtered.apply(match_row, axis=1)]

        cols_to_show = [c for c in [
            "id",
            "client_name",
            "unit_no",
            "platform",
            "check_in",
            "check_out",
            "price",
            "note",
        ] if c in filtered.columns]

        st.dataframe(filtered[cols_to_show], use_container_width=True)
    else:
        st.info("لا توجد حجوزات.")

# ============================
# 🟩 Tab 4: المتابعة
# ============================
with tab_monitor:
    st.subheader("📆 المتابعة اليومية / الأسبوعية / الشهرية")

    tomorrow = today + timedelta(days=1)

    bookings_today = [b for b in bookings if b.get("check_in") == str(today)]
    bookings_tomorrow = [b for b in bookings if b.get("check_in") == str(tomorrow)]
    checkout_today = [b for b in bookings if b.get("check_out") == str(today)]
    checkout_tomorrow = [b for b in bookings if b.get("check_out") == str(tomorrow)]

    colA, colB, colC, colD = st.columns(4)
    colA.metric("حجوزات اليوم", len(bookings_today))
    colB.metric("حجوزات غداً", len(bookings_tomorrow))
    colC.metric("مغادرين اليوم", len(checkout_today))
    colD.metric("مغادرين غداً", len(checkout_tomorrow))

    st.write("---")

    week_start = today - timedelta(days=7)
    weekly_bookings = [b for b in bookings if b.get("check_in", "") >= str(week_start)]
    weekly_checkout = [b for b in bookings if b.get("check_out", "") >= str(week_start)]

    col1, col2 = st.columns(2)
    col1.metric("حجوزات الأسبوع", len(weekly_bookings))
    col2.metric("مغادرين الأسبوع", len(weekly_checkout))

# ============================
# 🟩 Tab 5: التقارير
# ============================
with tab_reports:
    st.subheader("📊 تقارير بسيطة للمدير")

    month_start = today - timedelta(days=30)
    monthly_bookings = [b for b in bookings if b.get("check_in", "") >= str(month_start)]
    monthly_income = sum(float(b.get("price", 0) or 0) for b in monthly_bookings)

    col1, col2 = st.columns(2)
    col1.metric("حجوزات الشهر", len(monthly_bookings))
    col2.metric("الدخل الشهري (تقريبي)", f"{monthly_income:,.2f} ريال")

    if not book_df.empty and "platform" in book_df.columns and "price" in book_df.columns:
        st.markdown("#### أداء المنصات")
        platform_stats = book_df.groupby("platform")["price"].agg(["count", "sum"]).reset_index()
        platform_stats.rename(columns={"count": "عدد الحجوزات", "sum": "إجمالي الدخل"}, inplace=True)
        st.dataframe(platform_stats, use_container_width=True)

# ============================
# 🟩 Tab 6: الوحدات
# ============================
with tab_units:
    st.subheader("🏘️ الوحدات")

    if not units_df.empty:
        st.dataframe(units_df, use_container_width=True)
    else:
        st.info("لا توجد وحدات مسجلة.")

# ============================
# 🟩 Tab 7: المنصات
# ============================
with tab_platforms:
    st.subheader("🌐 المنصات")

    if not platforms_df.empty:
        st.dataframe(platforms_df, use_container_width=True)
    else:
        st.info("لا توجد منصات مسجلة.")

# ============================
# 🟩 Tab 8: العملاء
# ============================
with tab_clients:
    st.subheader("👥 العملاء")

    if not clients_df.empty:
        clients_df_display = clients_df.copy()
        if "created_at" in clients_df_display.columns:
            clients_df_display["created_at"] = clients_df_display["created_at"].astype(str)

        search_client = st.text_input("🔍 بحث عن عميل بالاسم أو الجوال:", "")
        filtered_clients = clients_df_display
        if search_client:
            s = search_client.lower()
            def match_client(row):
                name = str(row.get("name", "")).lower()
                phone = str(row.get("phone", "")).lower()
                return (s in name) or (s in phone)
            filtered_clients = filtered_clients[filtered_clients.apply(match_client, axis=1)]

        st.dataframe(filtered_clients, use_container_width=True)
    else:
        st.info("لا يوجد عملاء مسجلين.")
