
import json
import time
from datetime import date, datetime
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="StudyHelp", page_icon=":)", layout="wide")

DATA_FILE = Path("assignments.json")


def load_assignments():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_assignments():
    with open(DATA_FILE, "w") as file:
        json.dump(st.session_state.assignments, file, indent=4)


if "assignments" not in st.session_state:
    st.session_state.assignments = load_assignments()

if "timer_end" not in st.session_state:
    st.session_state.timer_end = None

if "remaining" not in st.session_state:
    st.session_state.remaining = 25 * 60

if "timer_running" not in st.session_state:
    st.session_state.timer_running = False

st.title(":) StudyHelp")
st.write("Stay organized, prioritize your work, and focus one sprint at a time.")

# Dashboard
assignments = st.session_state.assignments
total = len(assignments)
completed = sum(1 for task in assignments if task["completed"])
remaining_tasks = [task for task in assignments if not task["completed"]]
study_minutes = sum(task["minutes"] for task in remaining_tasks)

col1, col2, col3 = st.columns(3)
col1.metric("Total Assignments", total)
col2.metric("Completed", completed)
col3.metric("Study Minutes Left", study_minutes)

if total > 0:
    st.progress(completed / total, text=f"{completed} of {total} assignments completed")

st.divider()

# Add assignment
st.header(" Add an Assignment")

with st.form("assignment_form", clear_on_submit=True):
    title = st.text_input("Assignment Name")
    course = st.text_input("Course")
    due_date = st.date_input("Due Date", value=date.today())
    minutes = st.number_input("Estimated Study Time (minutes)", min_value=5, max_value=600, value=30, step=5)
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
    submitted = st.form_submit_button("Add Assignment")

    if submitted:
        if title.strip() and course.strip():
            st.session_state.assignments.append({
                "id": str(time.time_ns()),
                "title": title.strip(),
                "course": course.strip(),
                "due_date": due_date.isoformat(),
                "minutes": int(minutes),
                "difficulty": difficulty,
                "completed": False
            })
            save_assignments()
            st.success("Assignment added!")
        else:
            st.error("Please enter both an assignment name and course.")

st.divider()

# Assignment list
st.header(" Your Assignments")

if not st.session_state.assignments:
    st.info("No assignments yet. Add one above to get started.")
else:
    def priority(task):
        days_left = (date.fromisoformat(task["due_date"]) - date.today()).days
        urgency = 3 if days_left < 0 else 2 if days_left == 0 else 1 if days_left <= 2 else 0
        difficulty_score = {"Easy": 0, "Medium": 1, "Hard": 2}.get(task["difficulty"], 0)
        return (task["completed"], -urgency, -difficulty_score, task["due_date"])

    ordered = sorted(st.session_state.assignments, key=priority)

    for task in ordered:
        with st.container(border=True):
            left, right = st.columns([5, 1])

            with left:
                st.subheader(task["title"])
                st.write(f"**Course:** {task['course']}")
                st.write(
                    f"**Due:** {task['due_date']} · "
                    f"**Study time:** {task['minutes']} minutes · "
                    f"**Difficulty:** {task['difficulty']}"
                )

                days_left = (date.fromisoformat(task["due_date"]) - date.today()).days
                if task["completed"]:
                    st.success("Completed")
                elif days_left < 0:
                    st.error("Overdue")
                elif days_left == 0:
                    st.warning("Due today")
                elif days_left <= 2:
                    st.warning("Due soon")
                else:
                    st.caption("Upcoming")

            with right:
                if task["completed"]:
                    if st.button("Undo", key=f"undo_{task['id']}"):
                        task["completed"] = False
                        save_assignments()
                        st.rerun()
                else:
                    if st.button("Complete", key=f"complete_{task['id']}"):
                        task["completed"] = True
                        save_assignments()
                        st.rerun()

                if st.button("Delete", key=f"delete_{task['id']}"):
                    st.session_state.assignments = [
                        item for item in st.session_state.assignments
                        if item["id"] != task["id"]
                    ]
                    save_assignments()
                    st.rerun()

st.divider()

# Focus timer
st.header(" Focus Timer")
st.write("Choose a session length, start focusing, and take a break when you're done.")

duration = st.selectbox(
    "Focus session length",
    [5, 15, 25, 30, 45, 60],
    index=2,
    format_func=lambda minutes: f"{minutes} minutes",
    disabled=st.session_state.timer_running
)

if st.button("Set Timer", disabled=st.session_state.timer_running):
    st.session_state.remaining = duration * 60
    st.session_state.timer_end = None

if st.session_state.timer_running and st.session_state.timer_end is not None:
    st.session_state.remaining = max(
        0, int(st.session_state.timer_end - time.time())
    )

minutes_left, seconds_left = divmod(st.session_state.remaining, 60)
st.subheader(f"{minutes_left:02d}:{seconds_left:02d}")

if st.session_state.remaining == 0 and st.session_state.timer_running:
    st.session_state.timer_running = False
    st.session_state.timer_end = None
    st.success("Focus session complete! Great work!")

timer_col1, timer_col2, timer_col3 = st.columns(3)

with timer_col1:
    if st.button("Start / Resume", disabled=st.session_state.timer_running or st.session_state.remaining == 0):
        st.session_state.timer_end = time.time() + st.session_state.remaining
        st.session_state.timer_running = True
        st.rerun()

with timer_col2:
    if st.button("Pause", disabled=not st.session_state.timer_running):
        st.session_state.remaining = max(0, int(st.session_state.timer_end - time.time()))
        st.session_state.timer_running = False
        st.session_state.timer_end = None
        st.rerun()

with timer_col3:
    if st.button("Reset"):
        st.session_state.remaining = duration * 60
        st.session_state.timer_running = False
        st.session_state.timer_end = None
        st.rerun()

if st.session_state.timer_running:
    time.sleep(1)
    st.rerun()
