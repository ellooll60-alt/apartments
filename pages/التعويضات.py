import streamlit as st
from utils.supabase_client import supabase
from utils.auth import check_auth
from datetime import datetime

check_auth()

st.title("🌿 إدارة التعويضات")

# -----------------------------
# 🔧 تحميل البيانات الأساسية
# -----------------------------
def get_bookings():
    return supabase.table("bookings").select("*").execute().data

def get_compensations():
    return supabase.table("compensations").select("*").order("id", desc=True).execute().data

def add_compensation(data):
    return supabase.table("compensations").insert(data).execute()

def update_compensation(cid, data):
    return supabase.table("compensations").update(data).eq("id", cid).execute()

def delete_compensation(cid):
    return supabase.table("compensations").delete().eq("id", cid).execute()

bookings = get_bookings()
compensations = get_compensations()

# -----------------------------
# 🟩 إضافة تعويض جديد
# -----------------------------
st.subheader("➕ إضافة تعويض جديد")

with st.form("add_compensation_form"):
    booking_id = st.selectbox(
        "اختر الحجز",
        options=[b["id"] for b in bookings],
        format_func=lambda x: f"حجز #{x}"
    )

    reason = st.text_input("سبب التعويض")
    amount = st.number_input("قيمة التعويض (ريال)", min_value=0.0, step=1.0)
    date = st.date_input("تاريخ التعويض", datetime.today())

    submitted = st.form_submit_button("إضافة التعويض")

    if submitted:
        if amount <= 0:
            st.error("قيمة التعويض يجب أن تكون أكبر من صفر")
        else:
            add_compensation({
                "booking_id": booking_id,
                "reason": reason,
                "amount": amount,  # ✔ موجبة دائمًا
                "date": str(date)
            })
            st.success("تم إضافة التعويض بنجاح")
            st.rerun()

# -----------------------------
# 📋 عرض التعويضات
# -----------------------------
st.subheader("📄 قائمة التعويضات")

if not compensations:
    st.info("لا توجد تعويضات مسجلة")
else:
    for comp in compensations:
        with st.expander(f"تعويض #{comp['id']} — {comp['amount']} ريال"):
            st.write(f"**الحجز:** {comp['booking_id']}")
            st.write(f"**السبب:** {comp['reason']}")
            st.write(f"**التاريخ:** {comp['date']}")

            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"✏ تعديل_{comp['id']}"):
                    st.session_state["edit_id"] = comp["id"]

            with col2:
                if st.button(f"🗑 حذف_{comp['id']}"):
                    delete_compensation(comp["id"])
                    st.success("تم حذف التعويض")
                    st.rerun()

# -----------------------------
# ✏ تعديل تعويض
# -----------------------------
if "edit_id" in st.session_state:
    cid = st.session_state["edit_id"]
    comp = next((c for c in compensations if c["id"] == cid), None)

    st.subheader("✏ تعديل التعويض")

    with st.form("edit_compensation_form"):
        new_reason = st.text_input("سبب التعويض", comp["reason"])
        new_amount = st.number_input("قيمة التعويض", min_value=0.0, value=float(comp["amount"]))
        new_date = st.date_input("تاريخ التعويض", datetime.strptime(comp["date"], "%Y-%m-%d"))

        save = st.form_submit_button("حفظ التعديلات")

        if save:
            update_compensation(cid, {
                "reason": new_reason,
                "amount": new_amount,
                "date": str(new_date)
            })
            st.success("تم تحديث التعويض")
            del st.session_state["edit_id"]
            st.rerun()
