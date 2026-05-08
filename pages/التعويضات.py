import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from supabase import create_client
from datetime import date

from utils.auth_utils import require_role

# ============================
# 🔒 حماية الصفحة
# ============================
require_role(["admin", "manager"])

# ============================
# ⚙️ إعداد الصفحة
# ============================
st.set_page_config(page_title="إدارة التعويضات", page_icon="⚠️", layout="wide")
st.markdown("<h2 style='text-align:right;'>⚠️ إدارة التعويضات</h2>", unsafe_allow_html=True)

# ============================
# 📡 الاتصال بـ Supabase
# ============================
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# ============================
# 📌 تحميل البيانات
# ============================
units = supabase.table("units_names").select("*").order("id").execute().data
bookings = supabase.table("bookings").select("*").order("id", desc=True).execute().data

unit_list = [u["unit_no"] for u in units]

# ============================
# 🏘️ اختيار الوحدة
# ============================
st.subheader("➕ إضافة تعويض جديد")

selected_unit = st.selectbox("🏘️ اختر الوحدة", [""] + unit_list)

# فلترة الحجوزات حسب الوحدة
filtered_bookings = [
    b for b in bookings if b["unit_no"] == selected_unit
] if selected_unit else []

booking_list = {
    f"{b['id']} - {b['client_name']} - {b['unit_no']}": b
    for b in filtered_bookings
}

col1, col2 = st.columns(2)

with col1:
    selected_booking = st.selectbox(
        "اختر الحجز",
        list(booking_list.keys()) if booking_list else []
    )
    damage_type = st.text_input("نوع الضرر")
    amount = st.number_input("المبلغ", min_value=0.0, value=0.0)

with col2:
    date_added = st.date_input("تاريخ الإضافة", date.today())
    notes = st.text_area("ملاحظات")

if st.button("💾 حفظ التعويض"):
    if not selected_booking:
        st.error("⚠️ الرجاء اختيار حجز.")
    else:
        b = booking_list[selected_booking]

        data = {
            "booking_id": b["id"],
            "unit_no": b["unit_no"],
            "client_name": b["client_name"],
            "damage_type": damage_type,
            "amount": amount,
            "notes": notes,
            "date_added": str(date_added)
        }

        supabase.table("compensations").insert(data).execute()
        st.success("✔ تم حفظ التعويض بنجاح.")
        st.rerun()

# ============================
# 📋 عرض التعويضات
# ============================
st.write("---")
st.subheader("📋 قائمة التعويضات")

compensations = supabase.table("compensations").select("*").order("id", desc=True).execute().data

if not compensations:
    st.info("لا توجد تعويضات مسجلة.")
else:
    for comp in compensations:
        with st.expander(
            f"⚠️ تعويض رقم {comp['id']} — {comp['client_name']} — {comp['amount']} ريال"
        ):

            colA, colB = st.columns(2)

            with colA:
                new_damage = st.text_input(
                    "نوع الضرر",
                    comp["damage_type"],
                    key=f"damage_{comp['id']}"
                )
                new_amount = st.number_input(
                    "المبلغ",
                    min_value=0.0,
                    value=float(comp["amount"]),
                    key=f"amount_{comp['id']}"
                )

            with colB:
                new_date = st.date_input(
                    "التاريخ",
                    date.fromisoformat(comp["date_added"]),
                    key=f"date_{comp['id']}"
                )
                new_notes = st.text_area(
                    "ملاحظات",
                    comp.get("notes", ""),
                    key=f"notes_{comp['id']}"
                )

            # ============================
            # ✏️ تعديل التعويض
            # ============================
            if st.button("💾 حفظ التعديلات", key=f"save_{comp['id']}"):
                supabase.table("compensations").update({
                    "damage_type": new_damage,
                    "amount": new_amount,
                    "date_added": str(new_date),
                    "notes": new_notes
                }).eq("id", comp["id"]).execute()

                st.success("✔ تم تحديث التعويض بنجاح.")
                st.rerun()

            # ============================
            # 🗑️ حذف التعويض
            # ============================
            if st.button("🗑️ حذف التعويض", key=f"delete_{comp['id']}"):
                supabase.table("compensations").delete().eq("id", comp["id"]).execute()
                st.error("⚠️ تم حذف التعويض.")
                st.rerun()
