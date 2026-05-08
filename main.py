import streamlit as st
from supabase import create_client

# ============================
# ⚙️ إعداد الصفحة
# ============================
st.set_page_config(page_title="تسجيل الدخول", page_icon="🔐", layout="wide")

# ============================
# 🔗 الاتصال بـ Supabase
# ============================
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# ============================
# 🔒 تهيئة حالة الجلسة
# ============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_role" not in st.session_state:
    st.session_state.user_role = ""

# ============================
# 🔐 شاشة تسجيل الدخول
# ============================
if not st.session_state.logged_in:

    st.markdown("<h2 style='text-align:center;'>🔐 تسجيل الدخول</h2>", unsafe_allow_html=True)

    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة المرور", type="password")

    if st.button("تسجيل الدخول"):

        # ============================
        # 🔥 أهم تعديل يمنع APIError
        # ============================
        try:
            result = (
                supabase.table("users")
                .select("id, username, password, role")
                .eq("username", username)
                .limit(1)
                .execute()
            )
        except Exception as e:
            st.error("⚠️ خطأ في الاتصال بقاعدة البيانات")
            st.stop()

        # ============================
        # ❗ منع انهيار الكود لو النتيجة فاضية
        # ============================
        if not result.data or len(result.data) == 0:
            st.error("❌ اسم المستخدم غير موجود")
            st.stop()

        user = result.data[0]

        # ============================
        # ❗ التحقق من كلمة المرور
        # ============================
        if user.get("password") != password:
            st.error("❌ كلمة المرور غير صحيحة")
            st.stop()

        # ============================
        # ✔ تسجيل الدخول
        # ============================
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.user_role = user["role"]

        st.success("✔ تم تسجيل الدخول بنجاح")

        # ============================
        # 🔀 التوجيه حسب الدور
        # ============================
        if user["role"] == "admin":
            st.switch_page("pages/admin_dashboard.py")

        elif user["role"] == "manager":
            st.switch_page("pages/مدير_لوحة_التحكم.py")

        elif user["role"] == "employee":
            st.switch_page("pages/موظف_لوحة_التحكم.py")

        st.rerun()

    st.stop()

# ============================
# 🚪 زر تسجيل الخروج
# ============================
if st.button("🚪 تسجيل الخروج"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_role = ""
    st.success("تم تسجيل الخروج")
    st.rerun()
