import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from supabase import create_client
from datetime import date, datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import requests

from utils.auth_utils import require_role

# ============================
# 🔒 حماية الصفحة
# ============================
require_role(["admin", "manager", "employee"])

# ============================
# ⚙️ إعداد الصفحة
# ============================
st.set_page_config(page_title="حجز جديد", page_icon="📝", layout="wide")
st.markdown("<h2 style='text-align:right;'>📝 حجز جديد</h2>", unsafe_allow_html=True)

# ============================
# 📡 الاتصال بـ Supabase
# ============================
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# ============================
# 📌 تحميل البيانات
# ============================
units = supabase.table("units_names").select("*").execute().data
clients = supabase.table("clients").select("*").execute().data
bookings = supabase.table("bookings").select("*").execute().data

unit_list = [u["unit_no"] for u in units if u["unit_no"]]

# استقبال الوحدة المختارة من صفحة حالة الوحدات
preselected_unit = st.session_state.get("selected_unit_for_booking")

# ============================
# 🏘️ اختيار الوحدة
# ============================
unit_search = st.text_input("🔎 بحث عن الوحدة")
filtered_units = [u for u in unit_list if unit_search in u] if unit_search else unit_list

unit_no = st.selectbox(
    "رقم الوحدة",
    filtered_units,
    index=filtered_units.index(preselected_unit) if preselected_unit in filtered_units else 0
)

# ============================
# 👤 اختيار أو إضافة عميل
# ============================
client_names = [c["name"] for c in clients]

client_choice = st.selectbox(
    "👤 اختر العميل أو اكتب اسم جديد",
    client_names + ["➕ إضافة عميل جديد"]
)

if client_choice == "➕ إضافة عميل جديد":
    client_name = st.text_input("اسم العميل الجديد")
    id_number = st.text_input("رقم الهوية (10 أرقام)", max_chars=10)
    phone = st.text_input("رقم الهاتف")
else:
    client_name = client_choice
    selected_client = next((c for c in clients if c["name"] == client_choice), None)
    id_number = st.text_input("رقم الهوية (10 أرقام)", selected_client["id_number"] if selected_client else "", max_chars=10)
    phone = st.text_input("رقم الهاتف", selected_client["phone"] if selected_client else "")

# ============================
# ⚠️ التحقق من رقم الهوية
# ============================
if id_number and len(id_number) != 10:
    st.error("❌ رقم الهوية يجب أن يكون 10 أرقام فقط")

# ============================
# ⚠️ تنبيه إذا كان العميل لديه حجز سابق
# ============================
client_bookings = [b for b in bookings if b["client_name"] == client_name]

if client_bookings:
    st.warning(f"⚠️ هذا العميل لديه {len(client_bookings)} حجز سابق")
    for b in client_bookings[-3:]:
        st.info(f"حجز: {b['unit_no']} — من {b['check_in']} إلى {b['check_out']}")

# ============================
# 📅 التواريخ
# ============================
col1, col2 = st.columns(2)

with col1:
    check_in = st.date_input("تاريخ الدخول", date.today())

with col2:
    check_out = st.date_input("تاريخ الخروج", date.today())

# ============================
# ⚠️ التحقق من التعارض
# ============================
conflicts = []
for b in bookings:
    if b["unit_no"] == unit_no:
        existing_in = date.fromisoformat(b["check_in"])
        existing_out = date.fromisoformat(b["check_out"])

        if (check_in <= existing_out) and (check_out >= existing_in):
            conflicts.append(b)

if conflicts:
    st.error("⚠️ تنبيه: هذه الوحدة محجوزة في نفس التاريخ!")
    for c in conflicts:
        st.warning(f"حجز سابق: {c['client_name']} — من {c['check_in']} إلى {c['check_out']}")

# ============================
# 💰 السعر
# ============================
night_price = st.number_input("سعر الليلة", min_value=0.0)

nights = (check_out - check_in).days
if nights < 1:
    st.warning("يجب أن يكون تاريخ الخروج بعد تاريخ الدخول.")
else:
    st.info(f"عدد الليالي: {nights}")

total_price = nights * night_price
st.success(f"إجمالي السعر: {total_price} ريال")

notes = st.text_area("ملاحظات")

# ============================
# 💾 حفظ الحجز
# ============================
if st.button("💾 حفظ الحجز"):

    # التحقق من رقم الهوية
    if len(id_number) != 10:
        st.error("❌ رقم الهوية يجب أن يكون 10 أرقام بالضبط")
        st.stop()

    if nights < 1:
        st.error("تاريخ الخروج يجب أن يكون بعد الدخول.")
        st.stop()

    if conflicts:
        st.error("لا يمكن حفظ الحجز بسبب وجود تعارض في التواريخ.")
        st.stop()

    if not client_name.strip():
        st.error("اسم العميل مطلوب.")
        st.stop()

    # حفظ الحجز
    data = {
        "client_name": client_name,
        "id_number": id_number,
        "phone": phone,
        "unit_no": unit_no,
        "check_in": str(check_in),
        "check_out": str(check_out),
        "night_price": night_price,
        "price": total_price,
        "notes": notes,
        "created_at": datetime.now().isoformat()
    }

    supabase.table("bookings").insert(data).execute()

    # تحديث حالة الوحدة إلى محجوزة
    supabase.table("units_names").update({"status": "محجوزة"}).eq("unit_no", unit_no).execute()

    # تحديث بيانات العميل أو إضافته
    existing = next((c for c in clients if c["name"] == client_name), None)

    if existing:
        supabase.table("clients").update({
            "id_number": id_number,
            "phone": phone
        }).eq("name", client_name).execute()
    else:
        supabase.table("clients").insert({
            "name": client_name,
            "id_number": id_number,
            "phone": phone
        }).execute()

    # حذف الوحدة المختارة من الجلسة
    st.session_state.pop("selected_unit_for_booking", None)

    st.success("✔ تم حفظ الحجز بنجاح.")

    # ============================
    # 📄 إنشاء فاتورة PDF باستخدام ReportLab
    # ============================
    pdf_file = f"invoice_{client_name}_{datetime.now().timestamp()}.pdf"
    c = canvas.Canvas(pdf_file, pagesize=A4)

    c.setFont("Helvetica", 14)
    c.drawString(200, 800, "فاتورة الحجز")

    c.setFont("Helvetica", 12)
    y = 760
    lines = [
        f"اسم العميل: {client_name}",
        f"رقم الوحدة: {unit_no}",
        f"تاريخ الدخول: {check_in}",
        f"تاريخ الخروج: {check_out}",
        f"عدد الليالي: {nights}",
        f"سعر الليلة: {night_price} ريال",
        f"الإجمالي: {total_price} ريال",
    ]

    for line in lines:
        c.drawString(50, y, line)
        y -= 25

    c.save()

    with open(pdf_file, "rb") as f:
        st.download_button("📄 تحميل الفاتورة PDF", f, file_name=pdf_file)

    # ============================
    # 📲 إرسال إشعار واتساب
    # ============================
    message = f"""
تم تأكيد الحجز بنجاح
العميل: {client_name}
الوحدة: {unit_no}
الدخول: {check_in}
الخروج: {check_out}
الإجمالي: {total_price} ريال
"""

    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={message}&apikey=123456"
        requests.get(url)
        st.success("📲 تم إرسال إشعار واتساب للعميل")
    except:
        st.warning("تعذر إرسال رسالة واتساب")

    st.rerun()
