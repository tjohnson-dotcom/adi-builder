st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Hero band header
st.markdown(
    """
    <div class="brandband">
      <div class="brandtitle">ADI Builder <span class="badge">v1.0</span></div>
      <div class="brandsub">A clean, staff-friendly tool to generate questions and skills activities</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Optional logo + status card
logo_path = Path(__file__).with_name("logo.png")
if logo_path.exists():
    col_logo, col_text = st.columns([1,3])
    with col_logo:
        st.image(str(logo_path), width=120)
    with col_text:
        st.markdown(
            "<div class='card'><b>Status:</b> Ready &nbsp;·&nbsp; Upload lesson (PDF/DOCX/PPTX), pick week & lesson, then generate.</div>",
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        "<div class='card'><b>Status:</b> Ready &nbsp;·&nbsp; Upload lesson (PDF/DOCX/PPTX), pick week & lesson, then generate.</div>",
        unsafe_allow_html=True,
    )

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

  
