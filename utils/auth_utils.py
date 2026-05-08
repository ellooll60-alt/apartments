import streamlit as st

def require_role(allowed_roles=None):
    """
    يتحقق من أن المستخدم مسجّل دخول وله صلاحية مناسبة.
    """

    # التحقق من تسجيل الدخول
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.error("🚫 يجب تسجيل الدخول أولًا.")
        st.stop()

    # التحقق من وجود دور للمستخدم
    if "user_role" not in st.session_state:
        st.error("❌ لا يوجد دور للمستخدم.")
        st.stop()

    # التحقق من الصلاحيات
    if allowed_roles is not None and st.session_state.user_role not in allowed_roles:
        st.error("⛔ ليس لديك صلاحية الوصول لهذه الصفحة.")
        st.stop()
