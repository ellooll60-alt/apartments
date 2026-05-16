import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from supabase import create_client
from datetime import datetime
import qrcode
from io import BytesIO

# PDF + Arabic
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import arabic_reshaper
from bidi.algorithm import get_display

from utils.auth_utils import require_role

# ============================
# 🔐 دالة تجهيز النص العربي (مع إصلاح المستطيل الأبيض)
# ============================
def ar(text: str) -> str:
    # إضافة ZERO WIDTH NON-JOINER لمنع ظهور مربعات في أول وآخر الحروف
    text = f"\u200C{text}\u200C"
    reshaped = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped)
    return bidi_text

# ============================
# 🔒 حماية الصفحة
# ============================
require_role(["admin", "manager"])

# ============================
# ⚙️ إعداد الصفحة
# ============================
st.set_page_config(page_title="الفواتير", page_icon="🧾", layout="wide")
st.markdown("<h2 style='text-align:right;'>🧾 إنشاء فاتورة</h2>", unsafe_allow_html=True)

# ============================
# 📡 الاتصال بـ Supabase
# ============================
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# ============================
# 🖋️ تسجيل الخط العربي
# ============================
pdfmetrics.registerFont(TTFont("Arabic", "fonts/Tajawal-Regular.ttf"))

# ============================
# 📌 تحميل الإعدادات
# ============================
settings = supabase.table("settings").select("*").execute().data
settings = settings[0] if settings else {}

company_name = settings.get("company_name", "")
whatsapp = settings.get("whatsapp", "")
VAT_percent = float(settings.get("VAT_percent", "15"))

# ============================
# 📌 تحميل الحجوزات
# ============================
bookings = supabase.table("bookings").select("*").order("id", desc=True).execute().data
booking_list = {f"{b['id']} - {b['client_name']}": b for b in bookings}

selected = st.selectbox("اختر الحجز", list(booking_list.keys()) if booking_list else [])

if not selected:
    st.stop()

booking = booking_list[selected]

# ============================
# 🧮 حساب الفاتورة
# ============================
check_in = datetime.strptime(booking["check_in"], "%Y-%m-%d").date()
check_out = datetime.strptime(booking["check_out"], "%Y-%m-%d").date()
nights = (check_out - check_in).days

night_price = float(booking.get("night_price", 0))
discount = float(booking.get("discount", 0))
discount_type = booking.get("discount_type", "amount")
deposit = float(booking.get("deposit", 0))

base_price = nights * night_price

# الخصم
if discount_type == "percentage":
    discount_value = base_price * (discount / 100)
else:
    discount_value = discount

price_after_discount = base_price - discount_value

# الضريبة
vat_value = price_after_discount * (VAT_percent / 100)

# الإجمالي النهائي
total = price_after_discount + vat_value + deposit

# ============================
# 🔢 رقم الفاتورة
# ============================
invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{booking['id']}"

# ============================
# 🔳 QR Code
# ============================
qr_data = f"Invoice: {invoice_number}\nTotal: {total} SAR"
qr_img = qrcode.make(qr_data)
buf = BytesIO()
qr_img.save(buf, format="PNG")
qr_bytes = buf.getvalue()

# ============================
# 📄 إنشاء PDF (Arabic + Tajawal)
# ============================
def generate_pdf():
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4
    y = height - 40
    RIGHT_MARGIN = 80  # هامش أكبر لمنع قص الحروف

    # عنوان الشركة
    c.setFont("Arabic", 22)
    c.drawRightString(width - RIGHT_MARGIN, y, ar(company_name))
    y -= 30

    c.line(40, y, width - 40, y)
    y -= 40

    # عنوان الفاتورة
    c.setFont("Arabic", 20)
    c.drawRightString(width - RIGHT_MARGIN, y, ar("فاتورة"))
    y -= 45

    # بيانات الفاتورة
    c.setFont("Arabic", 15)
    info = [
        f"رقم الفاتورة: {invoice_number}",
        f"العميل: {booking['client_name']}",
        f"رقم الوحدة: {booking['unit_no']}",
        f"عدد الليالي: {nights}",
        f"تاريخ الدخول: {check_in.strftime('%Y-%m-%d')}",
        f"تاريخ الخروج: {check_out.strftime('%Y-%m-%d')}",
    ]

    for line in info:
        c.drawRightString(width - RIGHT_MARGIN, y, ar(line))
        y -= 28

    y -= 10
    c.line(40, y, width - 40, y)
    y -= 40

    # جدول الأسعار
    c.setFont("Arabic", 18)
    c.drawRightString(width - RIGHT_MARGIN, y, ar("تفاصيل المبلغ"))
    y -= 40

    c.setFont("Arabic", 15)
    rows = [
        ("سعر الأساس", f"{base_price} ريال"),
        ("الخصم", f"{discount_value} ريال"),
        (f"الضريبة ({VAT_percent}%)", f"{vat_value} ريال"),
        ("التأمين", f"{deposit} ريال"),
    ]

    for title, value in rows:
        c.drawRightString(width - RIGHT_MARGIN, y, ar(value))
        c.drawRightString(width - 260, y, ar(title))
        y -= 28

    c.line(40, y, width - 40, y)
    y -= 40

    # الإجمالي النهائي
    c.setFont("Arabic", 20)
    c.drawRightString(width - RIGHT_MARGIN, y, ar(f"الإجمالي النهائي: {total} ريال"))
    y -= 70

    # QR Code
    qr_image = ImageReader(BytesIO(qr_bytes))
    c.drawImage(qr_image, width - 160, y - 140, width=120, height=120)

    y -= 160

    # فوتر
    c.setFont("Arabic", 13)
    c.drawCentredString(width / 2, 40, ar(f"للتواصل: {whatsapp}"))

    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

# ============================
# 📥 زر تحميل PDF
# ============================
pdf_file = generate_pdf()

st.download_button(
    label="📄 تحميل الفاتورة PDF",
    data=pdf_file,
    file_name=f"{invoice_number}.pdf",
    mime="application/pdf"
)
