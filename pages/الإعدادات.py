import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from supabase import create_client
import base64

from utils.auth_utils import require_role

# ============================
# 🔒 حماية الصفحة
# ============================
require_role(["admin"])   # فقط المدير

# ============================
# ⚙️ إعداد الصفحة
# ============================
st.set_page_config(page_title="الإعدادات", page_icon="⚙️", layout="wide")
st.markdown("<h2 style='text-align:right;'>⚙️ الإعدادات العامة للنظام</h2>", unsafe_allow_html=True)

# ============================
# 📡 الاتصال بـ Supabase
# ============================
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# ============================
# 🛠 إضافة الأعمدة الناقصة تلقائيًا
# ============================
def ensure_columns():
    queries = [
        "ALTER TABLE settings ADD COLUMN IF NOT EXISTS VAT_percent text;",
        "ALTER TABLE settings ADD COLUMN IF NOT EXISTS logo_base64 text;",
        "ALTER TABLE settings ADD COLUMN IF NOT EXISTS stamp_base64 text;",
        "ALTER TABLE settings ADD COLUMN IF NOT EXISTS signature_base64 text;"
    ]
    for q in queries:
        try:
            supabase.rpc("execute_sql", {"sql": q}).execute()
        except:
            pass

ensure_columns()

# ============================
# 📌 قراءة الإعدادات الحالية
# ============================
settings = supabase.table("settings").select("*").execute().data
settings_row = settings[0] if settings else {}

company_name = settings_row.get("company_name", "")
whatsapp = settings_row.get("whatsapp", "")
logo_url = settings_row.get("logo_url", "")
background_url = settings_row.get("background_url", "")
language = settings_row.get("language", "ar")
VAT_percent = settings_row.get("VAT_percent", "15")

logo_base64 = settings_row.get("logo_base64")
stamp_base64 = settings_row.get("stamp_base64")
signature_base64 = settings_row.get("signature_base64")

# ============================
# 📤 رفع الصور وتحويلها Base64
# ============================
def upload_and_convert(label):
    file = st.file_uploader(label, type=["png", "jpg", "jpeg"])
    if file:
        return base64.b64encode(file.read()).decode("utf-8")
    return None

# ============================
# 📝 واجهة الإعدادات
# ============================
col1, col2 = st.columns(2)

with col1:
    company_name = st.text_input("اسم الشركة", company_name)
    whatsapp = st.text_input("رقم الواتساب", whatsapp)
    VAT_percent = st.text_input("نسبة الضريبة VAT", VAT_percent)
    language = st.selectbox("اللغة", ["ar", "en"], index=0 if language == "ar" else 1)

with col2:
    logo_url = st.text_input("رابط الشعار (اختياري)", logo_url)
    background_url = st.text_input("رابط الخلفية (اختياري)", background_url)

    st.write("**رفع الشعار (Base64)**")
    new_logo_b64 = upload_and_convert("رفع الشعار")

    st.write("**رفع الختم (Base64)**")
    new_stamp_b64 = upload_and_convert("رفع الختم")

    st.write("**رفع التوقيع (Base64)**")
    new_signature_b64 = upload_and_convert("رفع التوقيع")

# استبدال الصور القديمة بالجديدة إذا رفع المستخدم صورًا جديدة
if new_logo_b64:
    logo_base64 = new_logo_b64
if new_stamp_b64:
    stamp_base64 = new_stamp_b64
if new_signature_b64:
    signature_base64 = new_signature_b64

# ============================
# 💾 حفظ الإعدادات
# ============================
if st.button("💾 حفظ الإعدادات"):
    data = {
        "company_name": company_name,
        "whatsapp": whatsapp,
        "logo_url": logo_url,
        "background_url": background_url,
        "language": language,
        "VAT_percent": VAT_percent,
        "logo_base64": logo_base64,
        "stamp_base64": stamp_base64,
        "signature_base64": signature_base64,
    }

    supabase.table("settings").update(data).eq("id", settings_row.get("id")).execute()

    st.success("✔ تم حفظ الإعدادات بنجاح.")
    st.balloons()
