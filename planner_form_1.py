import streamlit as st
import requests

from dotenv import load_dotenv
import os
import openai

from datetime import datetime, timezone, time
import re

# === Set up the page ===
st.set_page_config(page_title="⏰ StudyStride", layout="wide")
st.title("⏰ StudyStride")
st.markdown("Your prioritization buddy")

# Make two columns: one for input, one for the assistant
col1, col2 = st.columns([2, 1])

# Placeholder for putting the final schedule on top
schedule_placeholder = st.empty()
formatted_assignments = []
assignments = []

with col1:
    st.header("🥅 What are your goals?")
    goals = st.text_area("🌟 What do you want to get done this week?", placeholder="Study for math test, practice for math olympiad...")
    st.subheader("🏫 School Timing")
    school_start = st.time_input("When does school start?", value=time(8, 0))
    school_end = st.time_input("When does school end?", value=time(15, 0))

    st.subheader("🎯 Extracurricular Activities")
    st.markdown("Use the sliders to tell me when you're busy on each day. 🕓")
    extracurriculars = {}
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    for day in days:
        with st.expander(f"📅 {day}"):
            time_range = st.slider(
                f"When are you busy on {day}?",
                value=(time(16, 0), time(18, 0)),
                key=f"{day}_range"
            )
            extracurriculars[day] = {"start": time_range[0], "end": time_range[1]} if time_range else None

    st.markdown("---")
    load_dotenv()

    openai_api_key = os.getenv("OPENAI_API_KEY")
    canvas_token = os.getenv("CANVAS_TOKEN")
    
    # === Login tokens and courses (hardcoded for now) ===
   
    subjects = {
        "Language Arts": 1023,
        "Math": 972,
        "Media Arts": 999,
        "Science": 971,
        "Social Studies": 1005
    }

    generate = st.button("✨ Make My Plan!")

    # === Get Assignments from Canvas ===
    def get_all_assignments(canvas_token, subjects):
        headers = {"Authorization": f"Bearer {canvas_token}"}
        canvas_url = "https://saratogausd.instructure.com/api/v1"
        all_assignments = []

        for subject, course_id in subjects.items():
            url = f"{canvas_url}/courses/{course_id}/assignments?per_page=100"
            while url:
                response = requests.get(url, headers=headers)
                if response.status_code != 200:
                    st.error(f"Oops! Couldn't get assignments for {subject}.")
                    break
                course_assignments = response.json()
                for a in course_assignments:
                    a['subject'] = subject
                    all_assignments.append(a)
                link_header = response.headers.get("Link", "")
                next_match = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
                url = next_match.group(1) if next_match else None

        return all_assignments

    def format_assignments(assignments):
        now_utc = datetime.now(timezone.utc)
        lines = []
        for a in assignments:
            name = a.get('name', 'Unnamed')
            due = a.get('due_at')
            points = a.get('points_possible', 'N/A')
            subject = a.get('subject', 'Unknown Subject')
            if due:
                try:
                    due_dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
                    if due_dt > now_utc:
                        lines.append(f"[{subject}] {name} (Due: {due_dt.date()}, Points: {points})")
                except:
                    continue
        return "\n".join(lines) if lines else "No upcoming assignments."

    def build_schedule_prompt(goals, school_start=None, school_end=None, extracurriculars=None, assignment_data=None):
        school_start = school_start or st.session_state.get("school_start")
        school_end = school_end or st.session_state.get("school_end")
        extracurriculars = extracurriculars or st.session_state.get("extracurriculars", {})
        assignment_data = assignment_data or st.session_state.get("assignment_data", {})
        ec_formatted = ""
        for day, times in extracurriculars.items():
            if times:
                ec_formatted += f"- {day}: {times['start']} to {times['end']}\n"
            else:
                ec_formatted += f"- {day}: None\n"

        return f"""
You are a world class student assistant that makes practical, effective schedules for student 

Here's what you should know:
- My Goals: {goals}
- School Time: {school_start} to {school_end}
- After School Activities:
{ec_formatted}
- My Assignments:
{assignment_data}

Make a nice plan for 1 week starting from the day I am asking you. I want study time, homework time, and chill time too!
"""

    if generate:
        with st.spinner("Grabbing assignments and thinking hard 🧠..."):
            assignments = get_all_assignments(canvas_token, subjects)
            formatted_assignments = format_assignments(assignments)

        full_schedule_context = build_schedule_prompt(goals, school_start, school_end, extracurriculars, formatted_assignments)
        st.session_state['schedule_context'] = full_schedule_context
        openai.api_key = openai_api_key

        with st.spinner("Building your schedule... 🧱"):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You're a friendly student planner."},
                        {"role": "user", "content": full_schedule_context}
                    ]
                )
                output = response['choices'][0]['message']['content']
                st.session_state['schedule_output'] = output

                with schedule_placeholder.container():
                    st.markdown("<script>window.scrollTo(0, document.body.scrollHeight);</script>", unsafe_allow_html=True)
                    st.markdown("---")
                    st.subheader("📚 What's Coming Up?")
                    st.code(formatted_assignments)
                    st.subheader("🗓️ Here's Your Schedule!")
                    st.markdown(output)

            except Exception as e:
                st.error(f"OpenAI messed up: {e}")

# === Assistant Chat ===
with col2:
    st.markdown("""
📌 **Instructions:**
- Fill in your weekly goals
- Set your school start and end times
- Use the sliders to input extracurricular activities for each weekday
- Then press **Make My Plan** to generate your personalized schedule below
""")
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("👋 **Hi! I'm your AI helper. Ask me anything about your week!**")
    st.header("🧙‍♂️ Ask Your Helper")
    assistant_prompt = st.text_area("What do you wanna know or change?")

    if st.button("🧠 Ask AI"):
        if assistant_prompt:
            openai.api_key = openai_api_key
            with st.spinner("Thinking really hard... 🧠"):
                try:
                    assignments = get_all_assignments(canvas_token, subjects)
                    formatted_assignments = format_assignments(assignments)
                    new_prompt = build_schedule_prompt(
                        assistant_prompt + " (regenerate the whole schedule to adjust workload)",
                        school_start,
                        school_end,
                        extracurriculars,
                        formatted_assignments
                    )
                    response = openai.ChatCompletion.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "Readjust the schedule to the new prompt and print the whole schedule"},
                            {"role": "user", "content": new_prompt}
                        ]
                    )
                    new_output = response['choices'][0]['message']['content']
                    st.session_state['schedule_output'] = new_output
                    with schedule_placeholder.container():
                       st.markdown("<script>window.scrollTo(0, document.body.scrollHeight);</script>", unsafe_allow_html=True)
                       st.markdown("---")
                       st.subheader("🗓️ Here's Your Updated Schedule!")
                       st.markdown(new_output)
                except Exception as e:
                    st.error(f"Yikes! Something broke: {e}")
        else:
            st.warning("Please type something first!")