from __future__ import annotations

from datetime import date, datetime, time, timedelta

import pandas as pd
import streamlit as st

from booking_service import BookingError, BookingService
from parser import parse_datetime, parse_duration, parse_room, resolve_day_word


st.set_page_config(page_title="Interview Room Bot", page_icon="📅", layout="wide")
service = BookingService()

DEFAULT_DRAFT = {
    "duration_minutes": None, "candidate_name": "", "room": None, "day": None,
    "start": None, "implementation_partner": "", "client": "", "role": "",
}
if "draft" not in st.session_state:
    st.session_state.draft = DEFAULT_DRAFT.copy()
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Welcome. How long is your interview? For example: **90 minutes**.",
    }]


def add(role, content):
    st.session_state.messages.append({"role": role, "content": content})


def next_prompt(draft):
    if not draft["duration_minutes"]:
        return "How long is your interview?"
    if not draft["candidate_name"]:
        return "What is the candidate's name?"
    if not draft["room"]:
        return "Which room: Room 1 (upper room) or Room 2 (hall)?"
    if not draft["day"]:
        return "Which day? You can book from today through the next four days."
    if not draft["start"]:
        return "What time does the interview start?"
    if not draft["implementation_partner"]:
        return "What is the implementation partner?"
    if not draft["client"]:
        return "Who is the client?"
    if not draft["role"]:
        return "What is the job role?"
    return None


def consume_answer(text):
    draft = st.session_state.draft
    if not draft["duration_minutes"]:
        draft["duration_minutes"] = parse_duration(text)
        if not draft["duration_minutes"]:
            return "Enter a duration such as **60 minutes** or **1.5 hours**."
    elif not draft["candidate_name"]:
        draft["candidate_name"] = text.strip()
    elif not draft["room"]:
        draft["room"] = parse_room(text)
        if not draft["room"]:
            return "I couldn't identify the room. Use **upper room**, **setup room**, **Room 1**, **hall**, or **Room 2**."
    elif not draft["day"]:
        parsed_day, parsed_time = parse_datetime(text)
        draft["day"] = resolve_day_word(text) or parsed_day
        draft["start"] = parsed_time
        if not draft["day"]:
            return "I couldn't identify the date. Try **tomorrow** or **July 18**."
    elif not draft["start"]:
        _, parsed_time = parse_datetime(text)
        draft["start"] = parsed_time
        if not draft["start"]:
            return "I couldn't identify the time. Try **2 PM** or **10:30 AM**."
    elif not draft["implementation_partner"]:
        draft["implementation_partner"] = text.strip()
    elif not draft["client"]:
        draft["client"] = text.strip()
    elif not draft["role"]:
        draft["role"] = text.strip()

    prompt = next_prompt(draft)
    if prompt:
        return prompt
    try:
        booking_id, end = service.create_booking(**draft)
        response = (
            f"✅ Booking **{booking_id}** confirmed: **{draft['room']}**, "
            f"**{draft['day']:%a, %b %d}**, **{draft['start']:%-I:%M %p}–{end:%-I:%M %p}** "
            f"for **{draft['candidate_name']}**."
        )
        st.session_state.draft = DEFAULT_DRAFT.copy()
        return response + "\n\nTo create another booking, tell me the interview duration."
    except BookingError as exc:
        alternatives = service.alternatives(
            draft["room"], draft["day"], draft["start"], draft["duration_minutes"]
        )
        draft["room"] = draft["day"] = draft["start"] = None
        suffix = " " + " ".join(alternatives) if alternatives else ""
        return f"⚠️ {exc}{suffix}\n\nChoose a room, date and time again."


st.title("Interview Room Booking Bot")
st.caption("No registration · Room 1 (upper/setup room) · Room 2 (hall) · Today through +4 days")

chat_tab, schedule_tab, cancel_tab = st.tabs(["💬 Book", "📅 Schedule", "❌ Cancel"])

with chat_tab:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if text := st.chat_input("Reply to the bot"):
        add("user", text)
        add("assistant", consume_answer(text))
        st.rerun()
    if st.button("Start over"):
        st.session_state.draft = DEFAULT_DRAFT.copy()
        st.session_state.messages = [{"role": "assistant", "content": "How long is your interview?"}]
        st.rerun()

with schedule_tab:
    bookings = service.list_bookings()
    if not bookings:
        st.info("No active bookings in the current window.")
    else:
        table = pd.DataFrame(bookings)
        table = table[["booking_id", "date", "start_time", "end_time", "room", "candidate_name", "client", "role"]]
        st.dataframe(table, use_container_width=True, hide_index=True)
    st.download_button(
        "Download Excel schedule", data=service.path.read_bytes(), file_name="interview_room_bookings.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

with cancel_tab:
    booking_id = st.text_input("Booking ID")
    if st.button("Cancel booking", type="primary"):
        if service.cancel_booking(booking_id):
            st.success(f"Booking {booking_id.upper()} cancelled.")
        else:
            st.error("Active booking ID not found.")
