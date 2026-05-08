import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from supabase import create_client
import pandas as pd

from utils.auth_utils import require_role

# ============================
# 🔒 حماية الصفحة
# ============================
require_role(["admin", "manager", "employee"])

# ============================
# ⚙️ إعداد الصفحة
# ============================
st.set_page_config(page_title="حالة الوحدات", page_icon="🏘️", layout="wide")
st.markdown("<h2 style='text-align:right;'>🏘️ حالة الوحدات</h2>", unsafe_allow_html=True)

# ============================
# 📡 الاتصال بـ Supabase
# ============================
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# ============================
# 📌 تحميل الوحدات
# ============================
units = supabase.table("units_names").select("*").order("id").execute().data

if not units:
    st.info("لا توجد وحدات مسجلة.")
    st.stop()

# ============================
# 🎨 ألوان الحالات
# ============================
status_colors = {
    "available": "#4CAF50",
    "محجوزة": "#F44336",
    "صيانة": "#FFC107"
}

# ============================
# 🔍 البحث + الفلترة
# ============================
col_search, col_filter = st.columns([2, 1])

with col_search:
    search_query = st.text_input("🔎 بحث باسم الوحدة")

with col_filter:
    filter_status = st.selectbox("فلترة حسب الحالة", ["الكل", "available", "محجوزة", "صيانة"])

# تطبيق البحث
if search_query.strip():
    units = [u for u in units if search_query.strip() in (u["name"] or "")]

# تطبيق الفلترة
if filter_status != "الكل":
    units = [u for u in units if u["status"] == filter_status]

# ============================
# 🧱 عرض الوحدات في Grid
# ============================
cols_per_row = 4
rows = (len(units) + cols_per_row - 1) // cols_per_row

st.write("")

for r in range(rows):
    cols = st.columns(cols_per_row)
    for i in range(cols_per_row):
        index = r * cols_per_row + i
        if index < len(units):
            u = units[index]
            color = status_colors.get(u["status"], "#999")

            with cols[i]:
                if st.button(
                    f"{u['name']}",
                    key=f"unit_{u['id']}",
                    help="اضغط لعرض التفاصيل",
                ):
                    st.session_state["selected_unit"] = u

                st.markdown(
                    f"""
                    <div style="
                        background-color: {color};
                        padding: 20px;
                        border-radius: 12px;
                        text-align: center;
                        color: white;
                        font-size: 20px;
                        font-weight: bold;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
                        margin-bottom: 15px;
                    ">
                        {u['name']}
                        <br>
                        <span style="font-size:14px; font-weight:normal;">
                            {u['status']}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# ============================
# 🪟 نافذة تفاصيل الوحدة
# ============================
if "selected_unit" in st.session_state:
    u = st.session_state["selected_unit"]

    st.write("---")
    st.subheader(f"📄 تفاصيل الوحدة: {u['name']}")

    st.write(f"**رقم الوحدة:** {u['unit_no']}")
    st.write(f"**سعر الليلة:** {u['night_price']} ريال")

    # تغيير الحالة
    new_status = st.selectbox(
        "تغيير حالة الوحدة",
        ["available", "محجوزة", "صيانة"],
        index=["available", "محجوزة", "صيانة"].index(u["status"])
    )

    if st.button("💾 حفظ الحالة الجديدة"):
        supabase.table("units_names").update({"status": new_status}).eq("id", u["id"]).execute()
        st.success("✔ تم تحديث حالة الوحدة.")
        del st.session_state["selected_unit"]
        st.rerun()

    # عرض الحجوزات الخاصة بهذه الوحدة
    if st.button("📦 عرض الحجوزات الخاصة بهذه الوحدة"):
        bookings = supabase.table("bookings").select("*").eq("unit_no", u["unit_no"]).execute().data

        st.write("### الحجوزات الخاصة بهذه الوحدة")

        if bookings:
            df = pd.DataFrame(bookings)
            st.table(df[["id", "client_name", "check_in", "check_out", "price"]])
        else:
            st.info("لا توجد حجوزات لهذه الوحدة.")

    # الانتقال لصفحة الحجز
    if st.button("📝 الانتقال إلى صفحة الحجز لهذه الوحدة"):
        st.session_state["selected_unit_for_booking"] = u["unit_no"]
        st.success("✔ تم تجهيز الوحدة لصفحة الحجز. انتقل الآن إلى صفحة الحجز.")

    if st.button("إغلاق التفاصيل"):
        del st.session_state["selected_unit"]
        st.rerun()
