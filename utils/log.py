from supabase import create_client
import streamlit as st

def log_action(action, details=""):
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)

    user = st.session_state.get("name", "Unknown")

    supabase.table("activity_log").insert({
        "user_name": user,
        "action": action,
        "details": details
    }).execute()
