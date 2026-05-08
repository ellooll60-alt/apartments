import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from supabase import create_client

from utils.auth_utils import require_role

# ============================
# 🔒 حماية الصفحة
# ============================
require_role(["admin"])   # فقط المدير

# ============================
# ⚙️ إعداد الصفحة
# ============================
st.set_page_config(page_title="إدارة الموظفين", page_icon="👥", layout="wide")
st.markdown("<h2 style='text-align:right;'>👥 إدارة الموظفين</h2>", unsafe_allow_html=True)

# ============================
# 📡 الاتصال بـ Supabase
# ============================
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# ============================
# 📌 تحميل الموظفين
# ============================
users = supabase.table("users").select("*").order("id").execute().data

# ============================
# ➕ إضافة موظف جديد
# ============================
st.subheader("➕ إضافة موظف جديد")

col1, col2 = st.columns(2)

with col1:
    new_name = st.text_input("اسم الموظف")

with col2:
    new_role = st.selectbox("الصلاحية", ["admin", "manager", "employee"])

col3, col4 = st.columns(2)

with col3:
    new_username = st.text_input("اسم المستخدم")

with col4:
    new_password = st.text_input("كلمة المرور", type="password")

if st.button("💾 حفظ الموظف"):
    if not new_name or not new_username or not new_password:
        st.error("⚠️ جميع الحقول مطلوبة.")
    else:
        supabase.table("users").insert({
            "name": new_name,
            "role": new_role,
            "username": new_username,
            "password": new_password
        }).execute()
        st.success("✔ تمت إضافة الموظف بنجاح.")
        st.rerun()

st.write("---")

# ============================
# 📋 عرض وتعديل الموظفين
# ============================
st.subheader("📋 قائمة الموظفين")

if not users:
    st.info("لا يوجد موظفين مسجلين.")
else:
    for u in users:
        with st.expander(f"👤 الموظف رقم {u['id']} — {u['name']}"):

            updated_name = st.text_input(
                f"اسم الموظف (ID {u['id']})",
                u["name"],
                key=f"name_{u['id']}"
            )

            updated_role = st.selectbox(
                "الصلاحية",
                ["admin", "manager", "employee"],
                index=["admin", "manager", "employee"].index(u["role"]),
                key=f"role_{u['id']}"
            )

            updated_username = st.text_input(
                "اسم المستخدم",
                u["username"],
                key=f"user_{u['id']}"
            )

            updated_password = st.text_input(
                "كلمة المرور",
                u["password"],
                key=f"pass_{u['id']}"
            )

            colA, colB = st.columns(2)

            with colA:
                if st.button(f"💾 تحديث الموظف رقم {u['id']}", key=f"update_{u['id']}"):
                    supabase.table("users").update({
                        "name": updated_name,
                        "role": updated_role,
                        "username": updated_username,
                        "password": updated_password
                    }).eq("id", u["id"]).execute()
                    st.success("✔ تم تحديث بيانات الموظف.")
                    st.rerun()

            with colB:
                if st.button(f"🗑️ حذف الموظف رقم {u['id']}", key=f"delete_{u['id']}"):
                    supabase.table("users").delete().eq("id", u["id"]).execute()
                    st.warning("⚠️ تم حذف الموظف.")
                    st.rerun()
