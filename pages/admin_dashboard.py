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
# 🧮 حسابات أساسية
# ============================
total_income = float(book_df["price"].sum()) if not book_df.empty and "price" in book_df.columns else 0
total_expenses = float(exp_df["amount"].sum()) if not exp_df.empty and "amount" in exp_df.columns else 0
total_comp = float(comp_df["amount"].sum()) if not comp_df.empty and "amount" in comp_df.columns else 0
net_profit = total_income - total_expenses - total_comp

total_units = len(units_df)
available_units = len(units_df[units_df["status"] == "متاحة"]) if not units_df.empty and "status" in units_df.columns else 0
busy_units = len(units_df[units_df["status"] == "محجوزة"]) if not units_df.empty and "status" in units_df.columns else 0
maintenance_units = len(units_df[units_df["status"] == "صيانة"]) if not units_df.empty and "status" in units_df.columns else 0

total_bookings = len(book_df)
total_platforms = len(platforms_df)
total_clients = len(clients_df)
total_users = len(users_df)

# ============================
# 🧱 Tabs علوية (قابلة للتمرير)
# ============================
tab_labels = [
    "الإحصائيات العامة",
    "التقويم التفاعلي",
    "الحجوزات",
    "المتابعة",
    "التقارير",
    "المصاريف",
    "التعويضات",
    "الوحدات",
    "المنصات",
    "العملاء",
    "الموظفين",
    "الصيانة",
    "التسويق",
    "API & Integrations",
    "الإعدادات",
]

(
    tab_stats,
    tab_calendar,
    tab_bookings,
    tab_monitor,
    tab_reports,
    tab_expenses,
    tab_comp,
    tab_units,
    tab_platforms,
    tab_clients,
    tab_employees,
    tab_maintenance,
    tab_marketing,
    tab_api,
    tab_settings,
) = st.tabs(tab_labels)

# ============================
# 🟦 Tab 1: الإحصائيات العامة
# ============================
with tab_stats:
    st.subheader("📊 الإحصائيات العامة")

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

    # استقبال رسائل التقويم (لو كنت تستخدم query_params من صفحة خارجية)
    if "action" in st.query_params:
        action = st.query_params["action"]
        if action == "add":
            st.session_state["new_booking_date"] = st.query_params.get("date")
            st.switch_page("pages/حجز_جديد.py")
        elif action == "edit":
            st.session_state["edit_booking_id"] = st.query_params.get("id")
            st.switch_page("pages/تعديل_حجز.py")

# ============================
# 🟦 Tab 3: الحجوزات (جدول تفاعلي)
# ============================
with tab_bookings:
    st.subheader("📋 جدول الحجوزات (تفاعلي وقابل للبحث)")

    if not book_df.empty:
        # تنظيف الأعمدة النصية
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
            "expenses",
            "compensations",
            "note",
        ] if c in filtered.columns]

        st.dataframe(filtered[cols_to_show], use_container_width=True)
    else:
        st.info("لا توجد حجوزات.")

# ============================
# 🟦 Tab 4: المتابعة (يومي – أسبوعي – شهري)
# ============================
with tab_monitor:
    st.subheader("📆 المتابعة اليومية / الأسبوعية / الشهرية")

    # يومي
    st.markdown("#### المتابعة اليومية")
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

    # أسبوعي
    st.markdown("#### المتابعة الأسبوعية")
    week_start = today - timedelta(days=7)

    weekly_bookings = [b for b in bookings if b.get("check_in", "") >= str(week_start)]
    weekly_checkout = [b for b in bookings if b.get("check_out", "") >= str(week_start)]
    weekly_income = sum(float(b.get("price", 0) or 0) for b in weekly_bookings)

    col1, col2, col3 = st.columns(3)
    col1.metric("حجوزات الأسبوع", len(weekly_bookings))
    col2.metric("مغادرين الأسبوع", len(weekly_checkout))
    col3.metric("الدخل الأسبوعي", f"{weekly_income:,.2f} ريال")

    st.write("---")

    # شهري
    st.markdown("#### المتابعة الشهرية")
    month_start = today - timedelta(days=30)

    monthly_bookings = [b for b in bookings if b.get("check_in", "") >= str(month_start)]
    monthly_checkout = [b for b in bookings if b.get("check_out", "") >= str(month_start)]
    monthly_income = sum(float(b.get("price", 0) or 0) for b in monthly_bookings)

    col4, col5, col6 = st.columns(3)
    col4.metric("حجوزات الشهر", len(monthly_bookings))
    col5.metric("مغادرين الشهر", len(monthly_checkout))
    col6.metric("الدخل الشهري", f"{monthly_income:,.2f} ريال")

# ============================
# 🟦 Tab 5: التقارير (مقارنة – أداء – توقعات)
# ============================
with tab_reports:
    st.subheader("📊 التقارير والتحليلات")

    # مقارنة الشهر الحالي والسابق
    st.markdown("#### مقارنة الشهر الحالي بالشهر السابق")

    month_start = today - timedelta(days=30)
    prev_month_start = today - timedelta(days=60)

    monthly_bookings = [b for b in bookings if b.get("check_in", "") >= str(month_start)]
    previous_month_bookings = [
        b for b in bookings
        if str(prev_month_start) <= b.get("check_in", "") < str(month_start)
    ]

    monthly_income = sum(float(b.get("price", 0) or 0) for b in monthly_bookings)
    previous_month_income = sum(float(b.get("price", 0) or 0) for b in previous_month_bookings)

    col1, col2, col3 = st.columns(3)
    col1.metric("حجوزات الشهر الحالي", len(monthly_bookings))
    col2.metric("حجوزات الشهر السابق", len(previous_month_bookings))
    col3.metric("فرق الدخل", f"{(monthly_income - previous_month_income):,.2f} ريال")

    st.write("---")

    # تقرير الأداء السنوي
    st.markdown("#### تقرير الأداء السنوي")

    year_start = today.replace(month=1, day=1)
    yearly_bookings = [b for b in bookings if b.get("check_in", "") >= str(year_start)]
    yearly_income = sum(float(b.get("price", 0) or 0) for b in yearly_bookings)

    yearly_clients = [
        c for c in users
        if c.get("created_at") and c["created_at"] >= str(year_start)
    ]

    col4, col5, col6 = st.columns(3)
    col4.metric("حجوزات السنة", len(yearly_bookings))
    col5.metric("الدخل السنوي", f"{yearly_income:,.2f} ريال")
    col6.metric("عملاء جدد", len(yearly_clients))

    st.write("---")

    # Forecasting بسيط
    st.markdown("#### التوقعات المستقبلية (Forecasting مبسط)")

    def to_date(d):
        try:
            return datetime.fromisoformat(d).date()
        except Exception:
            return None

    sorted_bookings = sorted(bookings, key=lambda b: to_date(b.get("check_in", "")) or today)

    daily_income = {}
    for b in sorted_bookings:
        d = to_date(b.get("check_in", ""))
        if d:
            daily_income[d] = daily_income.get(d, 0) + float(b.get("price", 0) or 0)

    last_7_days = [daily_income.get(today - timedelta(days=i), 0) for i in range(7)]
    avg_7 = sum(last_7_days) / 7 if last_7_days else 0

    last_30_days = [daily_income.get(today - timedelta(days=i), 0) for i in range(30)]
    avg_30 = sum(last_30_days) / 30 if last_30_days else 0

    growth_rate = (avg_7 - avg_30) / avg_30 if avg_30 > 0 else 0

    forecast_week = avg_7 * (1 + growth_rate) * 7
    forecast_month = avg_30 * (1 + growth_rate) * 30
    forecast_bookings = int(len(monthly_bookings) * (1 + growth_rate)) if monthly_bookings else 0

    col7, col8, col9 = st.columns(3)
    col7.metric("الحجوزات المتوقعة", forecast_bookings)
    col8.metric("الدخل المتوقع (أسبوع)", f"{forecast_week:,.2f} ريال")
    col9.metric("الدخل المتوقع (شهر)", f"{forecast_month:,.2f} ريال")

# ============================
# 🟦 Tab 6: المصاريف
# ============================
with tab_expenses:
    st.subheader("📉 المصاريف")

    if not exp_df.empty:
        exp_df_display = exp_df.copy()
        if "date_added" in exp_df_display.columns:
            exp_df_display["date_added"] = exp_df_display["date_added"].astype(str)

        st.dataframe(exp_df_display, use_container_width=True)

        st.markdown("#### آخر 5 مصاريف")
        last5_exp = exp_df_display.sort_values("id", ascending=False).head(5)
        cols = [c for c in ["id", "expense_type", "amount", "date_added"] if c in last5_exp.columns]
        st.table(last5_exp[cols])
    else:
        st.info("لا توجد مصاريف مسجلة.")

# ============================
# 🟦 Tab 7: التعويضات
# ============================
with tab_comp:
    st.subheader("⚠️ التعويضات")

    if not comp_df.empty:
        comp_df_display = comp_df.copy()
        if "date_added" in comp_df_display.columns:
            comp_df_display["date_added"] = comp_df_display["date_added"].astype(str)

        st.dataframe(comp_df_display, use_container_width=True)

        st.markdown("#### آخر 5 تعويضات")
        last5_comp = comp_df_display.sort_values("id", ascending=False).head(5)
        cols = [c for c in ["id", "client_name", "unit_no", "amount", "date_added"] if c in last5_comp.columns]
        st.table(last5_comp[cols])
    else:
        st.info("لا توجد تعويضات مسجلة.")

# ============================
# 🟦 Tab 8: الوحدات
# ============================
with tab_units:
    st.subheader("🏘️ إدارة الوحدات")

    if not units_df.empty:
        st.dataframe(units_df, use_container_width=True)

        st.markdown("#### ملخص الحالات")
        col1, col2, col3 = st.columns(3)
        col1.metric("متاحة", available_units)
        col2.metric("محجوزة", busy_units)
        col3.metric("صيانة", maintenance_units)
    else:
        st.info("لا توجد وحدات مسجلة.")

# ============================
# 🟦 Tab 9: المنصات
# ============================
with tab_platforms:
    st.subheader("🌐 المنصات")

    if not platforms_df.empty:
        st.dataframe(platforms_df, use_container_width=True)
    else:
        st.info("لا توجد منصات مسجلة.")

# ============================
# 🟦 Tab 10: العملاء
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

# ============================
# 🟦 Tab 11: الموظفين
# ============================
with tab_employees:
    st.subheader("👨‍💼 الموظفون / المستخدمون")

    if not users_df.empty:
        users_df_display = users_df.copy()
        if "created_at" in users_df_display.columns:
            users_df_display["created_at"] = users_df_display["created_at"].astype(str)

        st.dataframe(users_df_display, use_container_width=True)
    else:
        st.info("لا يوجد مستخدمون مسجلون.")

# ============================
# 🟦 Tab 12: الصيانة
# ============================
with tab_maintenance:
    st.subheader("🛠️ الصيانة")

    st.info("يمكن لاحقًا ربط جدول خاص بالصيانة (maintenance_requests) لعرض طلبات الصيانة وسجلها.")

# ============================
# 🟦 Tab 13: التسويق
# ============================
with tab_marketing:
    st.subheader("📣 التسويق وتحليل المنصات")

    if not book_df.empty and "platform" in book_df.columns and "price" in book_df.columns:
        platform_stats = book_df.groupby("platform")["price"].agg(["count", "sum"]).reset_index()
        platform_stats.rename(columns={"count": "عدد الحجوزات", "sum": "إجمالي الدخل"}, inplace=True)
        st.dataframe(platform_stats, use_container_width=True)
    else:
        st.info("لا توجد بيانات كافية لتحليل أداء المنصات.")

# ============================
# 🟦 Tab 14: API & Integrations
# ============================
with tab_api:
    st.subheader("🔌 API & Integrations")

    st.info("هنا يمكن لاحقًا إضافة إعدادات API Keys و Webhooks والتكامل مع أنظمة خارجية.")

# ============================
# 🟦 Tab 15: الإعدادات
# ============================
with tab_settings:
    st.subheader("⚙️ إعدادات النظام")

    st.info("يمكن لاحقًا إضافة إعدادات عامة للنظام (الألوان، اللغة، صلاحيات إضافية، إلخ).")
