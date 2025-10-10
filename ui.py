import streamlit as st

def render_sidebar():
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Saudi_Arabian_Military_Industries_logo.svg/2560px-Saudi_Arabian_Military_Industries_logo.svg.png", use_column_width=True)
    st.sidebar.markdown("### ADI Builder")
    st.sidebar.markdown("Create AI-powered questions aligned with Bloom's Taxonomy.")

def render_course_details():
    st.markdown("### Course Details")
    col1, col2, col3 = st.columns(3)
    course = col1.text_input("Course Name")
    instructor = col2.selectbox("Instructor", ["Ben", "Abdulmalik", "Gerhard", "Faiz Lazam", "Mohammed Alfarhan", "Nerdeen", "Dari", "Ghamza", "Michail", "Meshari", "Mohammed Alwuthaylah", "Myra", "Meshal", "Ibrahim", "Khalil", "Salem", "Rana", "Daniel", "Ahmed Albader"])
    date = col3.date_input("Date")
    return {"course": course, "instructor": instructor, "date": date}

def render_bloom_panels():
    st.markdown("### Bloom's Taxonomy Levels")
    selected = []

    with st.container():
        st.markdown("#### Low (Weeks 1–4)")
        low_verbs = ["define", "identify", "list"]
        cols = st.columns(len(low_verbs))
        for i, verb in enumerate(low_verbs):
            if cols[i].checkbox(verb, key=f"low_{verb}"):
                selected.append(verb)

    with st.container():
        st.markdown("#### Medium (Weeks 5–9)")
        med_verbs = ["apply", "analyze", "solve"]
        cols = st.columns(len(med_verbs))
        for i, verb in enumerate(med_verbs):
            if cols[i].checkbox(verb, key=f"med_{verb}"):
                selected.append(verb)

    with st.container():
        st.markdown("#### High (Weeks 10–14)")
        high_verbs = ["evaluate", "synthesize", "design"]
        cols = st.columns(len(high_verbs))
        for i, verb in enumerate(high_verbs):
            if cols[i].checkbox(verb, key=f"high_{verb}"):
                selected.append(verb)

    return selected
