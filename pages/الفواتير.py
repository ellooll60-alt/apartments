import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from supabase import create_client
from datetime import datetime
import qrcode
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader   # ← NEW

from utils.auth_utils import require_role

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
qr_data = f"{company_name}\nInvoice: {invoice_number}\nTotal: {total} SAR"
qr_img = qrcode.make(qr_data)
buf = BytesIO()
qr_img.save(buf, format="PNG")
qr_bytes = buf.getvalue()

# ============================
# 📄 إنشاء PDF
# ============================
def generate_pdf():
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    y = 800

    # عنوان الشركة
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, company_name)
    y -= 40

    # بيانات الفاتورة
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Invoice Number: {invoice_number}")
    y -= 20
    c.drawString(50, y, f"Client: {booking['client_name']}")
    y -= 20
    c.drawString(50, y, f"Nights: {nights}")
    y -= 20
    c.drawString(50, y, f"Base Price: {base_price} SAR")
    y -= 20
    c.drawString(50, y, f"Discount: {discount_value} SAR")
    y -= 20
    c.drawString(50, y, f"VAT ({VAT_percent}%): {vat_value} SAR")
    y -= 20
    c.drawString(50, y, f"Deposit: {deposit} SAR")
    y -= 20
    c.drawString(50, y, f"Total: {total} SAR")
    y -= 40

    # QR Code (FIXED)
    qr_image = ImageReader(BytesIO(qr_bytes))
    c.drawImage(qr_image, 50, y - 150, width=120, height=120)

    c.showPage()
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
