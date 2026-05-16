import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from supabase import create_client

from utils.auth_utils import require_role

# ============================
# 🔒 حماية الصفحة
# ============================
require_role(["admin", "manager", "reception"])

# ============================
# ⚙️ إعداد الصفحة
# ============================
st.set_page_config(page_title="إدارة العملاء", page_icon="🧍‍♂️", layout="wide")
st.markdown("<h2 style='text-align:right;'>🧍‍♂️ إدارة العملاء</h2>", unsafe_allow_html=True)

# ============================
# 🔗 الاتصال بـ Supabase
# ============================
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# ============================
# 📌 جلب العملاء
# ============================
response = supabase.table("clients").select("*").order("id", desc=False).execute()
clients = response.data or []

# ============================
# ➕ إضافة عميل جديد
# ============================
st.subheader("➕ إضافة عميل جديد")

col1, col2 = st.columns(2)

with col1:
    name = st.text_input("اسم العميل")

with col2:
    phone = st.text_input("رقم الجوال")

notes = st.text_area("ملاحظات", height=80)

if st.button("💾 حفظ العميل"):
    if not name or not phone:
        st.error("اسم العميل ورقم الجوال مطلوبان.")
    else:
        supabase.table("clients").insert({
            "name": name,
            "phone": phone,
            "notes": notes,
            "stay_count": 0
        }).execute()
        st.success("✔ تم إضافة العميل بنجاح.")
        st.rerun()

st.markdown("---")

# ============================
# 📋 قائمة العملاء
# ============================
st.subheader("📋 قائمة العملاء")

if not clients:
    st.info("لا يوجد عملاء.")
else:
    for idx, client in enumerate(clients):
        cid = client.get("id", idx)

        with st.container():
            st.markdown("<div style='padding:10px; border:1px solid #ddd; border-radius:8px;'>", unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

            with col1:
                st.write(f"👤 **{client.get('name', 'بدون اسم')}**")

            with col2:
                st.write(f"📞 {client.get('phone', 'غير متوفر')}")

            with col3:
                st.write(f"📊 مرات الإقامة: {client.get('stay_count', 0)}")

            with col4:
                if st.button("🗑 حذف", key=f"del_client_{cid}"):
                    supabase.table("clients").delete().eq("id", client["id"]).execute()
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
