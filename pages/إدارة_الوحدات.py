import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from supabase import create_client

from utils.auth_utils import require_role

# ============================
# 🔒 حماية الصفحة
# ============================
require_role(["admin", "manager"])   # فقط المدير والمشرف

# ============================
# ⚙️ إعداد الصفحة
# ============================
st.set_page_config(page_title="إدارة الوحدات", page_icon="🧱", layout="wide")
st.markdown("<h2 style='text-align:right;'>🧱 إدارة الوحدات</h2>", unsafe_allow_html=True)

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

# ============================
# ➕ إضافة وحدة جديدة
# ============================
st.subheader("➕ إضافة وحدة جديدة")

col1, col2 = st.columns(2)

with col1:
    new_name = st.text_input("اسم الوحدة")

with col2:
    new_unit_no = st.text_input("رقم الوحدة")

col3, col4 = st.columns(2)

with col3:
    new_night_price = st.number_input("سعر الليلة", min_value=0.0)

with col4:
    new_status = st.selectbox("الحالة", ["available", "محجوزة", "صيانة"])

if st.button("💾 حفظ الوحدة"):
    if not new_name.strip():
        st.error("⚠️ اسم الوحدة مطلوب.")
    else:
        supabase.table("units_names").insert({
            "name": new_name,
            "unit_no": new_unit_no,
            "night_price": new_night_price,
            "status": new_status
        }).execute()
        st.success("✔ تمت إضافة الوحدة بنجاح.")
        st.rerun()

st.write("---")

# ============================
# 📋 عرض وتعديل الوحدات
# ============================
st.subheader("📋 قائمة الوحدات")

if not units:
    st.info("لا توجد وحدات مسجلة.")
else:
    for u in units:
        with st.expander(f"🏘️ وحدة رقم {u['id']} — {u['name']}"):

            updated_name = st.text_input(
                f"اسم الوحدة (ID {u['id']})",
                u["name"],
                key=f"name_{u['id']}"
            )

            updated_unit_no = st.text_input(
                "رقم الوحدة",
                u["unit_no"] or "",
                key=f"unitno_{u['id']}"
            )

            updated_price = st.number_input(
                "سعر الليلة",
                min_value=0.0,
                value=float(u["night_price"] or 0),
                key=f"price_{u['id']}"
            )

            updated_status = st.selectbox(
                "الحالة",
                ["available", "محجوزة", "صيانة"],
                index=["available", "محجوزة", "صيانة"].index(u["status"]),
                key=f"status_{u['id']}"
            )

            colA, colB = st.columns(2)

            with colA:
                if st.button(f"💾 تحديث الوحدة رقم {u['id']}", key=f"update_{u['id']}"):
                    supabase.table("units_names").update({
                        "name": updated_name,
                        "unit_no": updated_unit_no,
                        "night_price": updated_price,
                        "status": updated_status
                    }).eq("id", u["id"]).execute()
                    st.success("✔ تم تحديث بيانات الوحدة.")
                    st.rerun()

            with colB:
                if st.button(f"🗑️ حذف الوحدة رقم {u['id']}", key=f"delete_{u['id']}"):
                    supabase.table("units_names").delete().eq("id", u["id"]).execute()
                    st.warning("⚠️ تم حذف الوحدة.")
                    st.rerun()
