import streamlit as st

# Initialize session state
if "courses" not in st.session_state:
    st.session_state.courses = []
if "teachers" not in st.session_state:
    st.session_state.teachers = []
if "selected_course" not in st.session_state:
    st.session_state.selected_course = None
if "selected_teacher" not in st.session_state:
    st.session_state.selected_teacher = None
if "selected_week" not in st.session_state:
    st.session_state.selected_week = None
if "bloom_level" not in st.session_state:
    st.session_state.bloom_level = None

# Sidebar for course and teacher management
st.sidebar.title("ADI Builder Navigation")

# Course management
st.sidebar.subheader("Courses")
for i, course in enumerate(st.session_state.courses):
    if st.sidebar.button(f"Select: {course}", key=f"select_course_{i}"):
        st.session_state.selected_course = course
    if st.sidebar.button(f"➖ Remove {course}", key=f"remove_course_{i}"):
        st.session_state.courses.pop(i)
        st.experimental_rerun()
new_course = st.sidebar.text_input("Add New Course")
if st.sidebar.button("➕ Add Course"):
    if new_course:
        st.session_state.courses.append(new_course)

# Teacher management
st.sidebar.subheader("Teachers")
for i, teacher in enumerate(st.session_state.teachers):
    if st.sidebar.button(f"Select: {teacher}", key=f"select_teacher_{i}"):
        st.session_state.selected_teacher = teacher
    if st.sidebar.button(f"➖ Remove {teacher}", key=f"remove_teacher_{i}"):
        st.session_state.teachers.pop(i)
        st.experimental_rerun()
new_teacher = st.sidebar.text_input("Add New Teacher")
if st.sidebar.button("➕ Add Teacher"):
    if new_teacher:
        st.session_state.teachers.append(new_teacher)

# Week selection
st.sidebar.subheader("Weeks 1–14")
for week in range(1, 15):
    if st.sidebar.button(f"Week {week}", key=f"week_{week}"):
        st.session_state.selected_week = week
        if week <= 4:
            st.session_state.bloom_level = "Low"
        elif week <= 9:
            st.session_state.bloom_level = "Medium"
        else:
            st.session_state.bloom_level = "High"

# Main panel
st.title("ADI Builder")

if st.session_state.selected_course:
    st.markdown(f"### Selected Course: `{st.session_state.selected_course}`")
if st.session_state.selected_teacher:
    st.markdown(f"### Instructor: `{st.session_state.selected_teacher}`")
if st.session_state.selected_week:
    st.markdown(f"### Week {st.session_state.selected_week} — Bloom Level: `{st.session_state.bloom_level}`")

# Generate and Export buttons
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.button("🚀 Generate Questions", use_container_width=True)
with col2:
    st.button("📦 Export Lesson", use_container_width=True)
