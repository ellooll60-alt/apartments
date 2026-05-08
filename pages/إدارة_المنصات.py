import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from supabase import create_client

from utils.auth_utils import require_role

# ============================
# 🔒 حماية الصفحة
# ============================
require_role(["admin", "manager"])

# ============================
# ⚙️ إعداد الصفحة
# ============================
st.set_page_config(page_title="إدارة المنصات", page_icon="🌐", layout="wide")
st.markdown("<h2 style='text-align:right;'>🌐 إدارة المنصات</h2>", unsafe_allow_html=True)

# ============================
# 📡 الاتصال بـ Supabase
# ============================
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# ============================
# 📌 تحميل المنصات
# ============================
platforms = supabase.table("platforms").select("*").order("id").execute().data

# ============================
# ➕ إضافة منصة جديدة
# ============================
st.subheader("➕ إضافة منصة جديدة")

col1, col2 = st.columns(2)

with col1:
    new_name = st.text_input("اسم المنصة")

with col2:
    new_notes = st.text_input("ملاحظات (اختياري)")

if st.button("💾 حفظ المنصة"):
    if not new_name.strip():
        st.error("⚠️ اسم المنصة مطلوب.")
    else:
        supabase.table("platforms").insert({
            "name": new_name,
            "notes": new_notes
        }).execute()
        st.success("✔ تمت إضافة المنصة بنجاح.")
        st.rerun()

st.write("---")

# ============================
# 📋 عرض وتعديل المنصات
# ============================
st.subheader("📋 قائمة المنصات")

if not platforms:
    st.info("لا توجد منصات مسجلة.")
else:
    for p in platforms:
        with st.expander(f"🌐 منصة رقم {p['id']} — {p['name']}"):

            updated_name = st.text_input(
                f"اسم المنصة (ID {p['id']})",
                p["name"],
                key=f"name_{p['id']}"
            )

            updated_notes = st.text_input(
                "ملاحظات",
                p["notes"] or "",
                key=f"notes_{p['id']}"
            )

            colA, colB = st.columns(2)

            with colA:
                if st.button(f"💾 تحديث المنصة رقم {p['id']}", key=f"update_{p['id']}"):
                    supabase.table("platforms").update({
                        "name": updated_name,
                        "notes": updated_notes
                    }).eq("id", p["id"]).execute()
                    st.success("✔ تم تحديث المنصة.")
                    st.rerun()

            with colB:
                if st.button(f"🗑️ حذف المنصة رقم {p['id']}", key=f"delete_{p['id']}"):
                    supabase.table("platforms").delete().eq("id", p["id"]).execute()
                    st.warning("⚠️ تم حذف المنصة.")
                    st.rerun()
