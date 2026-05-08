import streamlit as st
from supabase import create_client
import json

st.set_page_config(page_title="التقويم", layout="wide")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# ============================
# جلب الأحداث من Supabase
# ============================
events = supabase.table("calendar_events").select("*").execute().data

calendar_events = [
    {
        "id": e["id"],
        "title": e["title"],
        "start": e["start_date"],
        "end": e["end_date"],
        "color": e["color"]
    }
    for e in events
]

events_json = json.dumps(calendar_events)

# ============================
# HTML + FullCalendar
# ============================
calendar_html = f"""
<!DOCTYPE html>
<html>
<head>
<link href='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/main.min.css' rel='stylesheet' />
<script src='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/main.min.js'></script>

<style>
  #calendar {{
    max-width: 100%;
    margin: 20px auto;
  }}
</style>

</head>
<body>

<div id='calendar'></div>

<script>

document.addEventListener('DOMContentLoaded', function() {{
    var calendarEl = document.getElementById('calendar');

    var calendar = new FullCalendar.Calendar(calendarEl, {{
        initialView: 'dayGridMonth',
        selectable: true,
        events: {events_json},

        dateClick: function(info) {{
            window.parent.postMessage(
                {{ "action": "add", "date": info.dateStr }},
                "*"
            );
        }},

        eventClick: function(info) {{
            window.parent.postMessage(
                {{ "action": "edit", "id": info.event.id }},
                "*"
            );
        }}
    }});

    calendar.render();
}});

</script>

</body>
</html>
"""

st.components.v1.html(calendar_html, height=700)

# ============================
# استقبال رسائل JS
# ============================
message = st.experimental_get_query_params()

if "action" in message:
    st.write(message)

