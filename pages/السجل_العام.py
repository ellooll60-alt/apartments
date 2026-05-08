import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd

from utils.auth_utils import require_role

# ============================
# 🔒 حماية الصفحة
# ============================
require_role(["admin", "manager"])

# ============================
# ⚙️ إعداد الصفحة
# ============================
st.set_page_config(page_title="السجل العام", page_icon="📋", layout="wide")
st.markdown("<h2 style='text-align:right;'>📋 السجل العام للحجوزات</h2>", unsafe_allow_html=True)

# ============================
# 📡 الاتصال بـ Supabase
# ============================
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# ============================
# 📌 تحميل الحجوزات
# ============================
bookings = supabase.table("bookings").select("*").order("id", desc=True).execute().data

if not bookings:
    st.warning("لا توجد حجوزات مسجلة.")
    st.stop()

# ============================
# 🔍 البحث
# ============================
search = st.text_input("🔍 ابحث باسم العميل أو رقم الهوية أو رقم الوحدة")

def match(b):
    s = search.strip()
    if s == "":
        return True
    return (
        s in str(b.get("client_name", "")) or
        s in str(b.get("id_number", "")) or
        s in str(b.get("unit_no", ""))
    )

filtered = [b for b in bookings if match(b)]

# ============================
# 📋 عرض النتائج
# ============================
st.write(f"عدد النتائج: {len(filtered)}")

for b in filtered:
    with st.expander(f"📌 الحجز رقم {b['id']} — {b['client_name']}"):

        col1, col2, col3 = st.columns(3)

        # ============================
        # 📄 معلومات الحجز
        # ============================
        with col1:
            st.write(f"**اسم العميل:** {b['client_name']}")
            st.write(f"**رقم الهوية:** {b['id_number']}")
            st.write(f"**الهاتف:** {b['phone']}")
            st.write(f"**العنوان:** {b.get('address', '')}")

        with col2:
            st.write(f"**الوحدة:** {b['unit_no']}")
            st.write(f"**المنصة:** {b.get('platform', '')}")
            st.write(f"**الدخول:** {b['check_in']}")
            st.write(f"**الخروج:** {b['check_out']}")

        with col3:
            st.write(f"**سعر الليلة:** {b['night_price']} ريال")
            st.write(f"**الخصم:** {b.get('discount', 0)} ({b.get('discount_type', '')})")
            st.write(f"**التأمين:** {b.get('deposit', 0)} ريال")
            st.write(f"**الإجمالي:** {b['price']} ريال")

        st.write("**ملاحظات:**")
        st.info(b.get("notes", ""))

        # ============================
        # ✏️ تعديل الحجز
        # ============================
        st.write("---")
        st.subheader("✏️ تعديل الحجز")

        new_name = st.text_input("اسم العميل", b["client_name"], key=f"name_{b['id']}")
        new_phone = st.text_input("الهاتف", b["phone"], key=f"phone_{b['id']}")
        new_id = st.text_input("رقم الهوية", b["id_number"], key=f"id_{b['id']}")
        new_address = st.text_input("العنوان", b.get("address", ""), key=f"addr_{b['id']}")
        new_notes = st.text_area("ملاحظات", b.get("notes", ""), key=f"notes_{b['id']}")

        if st.button("💾 حفظ التعديلات", key=f"save_{b['id']}"):
            supabase.table("bookings").update({
                "client_name": new_name,
                "phone": new_phone,
                "id_number": new_id,
                "address": new_address,
                "notes": new_notes
            }).eq("id", b["id"]).execute()

            st.success("✔ تم حفظ التعديلات بنجاح.")
            st.rerun()

        # ============================
        # 🗑️ حذف الحجز
        # ============================
        st.write("---")
        if st.button("🗑️ حذف الحجز", key=f"delete_{b['id']}"):
            supabase.table("bookings").delete().eq("id", b["id"]).execute()
            st.error("⚠️ تم حذف الحجز.")
            st.rerun()
