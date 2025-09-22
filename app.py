# -------------------------------------------------------------------
# Mode: Knowledge MCQs  (LEVEL MIX + MULTI-VERB ROTATION)
# -------------------------------------------------------------------
if mode == "Knowledge MCQs":
    st.subheader("MCQ Settings")

    cA, cB, cC = st.columns([1.3, 1, 1])
    with cA:
        # Level-mix toggle
        use_level_mix = st.checkbox("Use level mix (rotate across multiple Bloom levels)", value=True)
    with cB:
        total_mcqs = st.slider("Total MCQs (5–10)", 5, 10, 10)
    with cC:
        extra_verbs_raw = st.text_input("Extra verbs (optional, comma-separated)")

    # Choose levels
    if use_level_mix:
        # Multi-select levels (even rotation across chosen levels)
        chosen_levels = st.multiselect(
            "Bloom levels to include",
            options=list(BLOOMS.keys()),
            default=["Understand", "Apply", "Analyse"],
            help="We’ll rotate questions evenly across the levels you pick."
        )
        if not chosen_levels:
            chosen_levels = ["Understand"]

        # Build a combined verb bank for the selected levels
        bank_verbs = []
        for lvl in chosen_levels:
            bank_verbs.extend(BLOOMS[lvl])
    else:
        # Single-level mode
        single_level = st.selectbox("Bloom’s level", list(BLOOMS.keys()), index=2)
        chosen_levels = [single_level]
        bank_verbs = BLOOMS[single_level].copy()

    # Add extras and let user pick subset to rotate
    extra_verbs = [v.strip() for v in extra_verbs_raw.split(",") if v.strip()]
    full_verb_bank = list(dict.fromkeys(bank_verbs + extra_verbs))  # dedupe, keep order

    verb_choice = st.multiselect(
        "Verbs to use (we’ll rotate them automatically)",
        options=full_verb_bank,
        default=bank_verbs,  # preselect the base verbs
        help="Pick one or more verbs; generator will cycle these so stems vary."
    )

    verb_mode = st.selectbox(
        "Verb mode",
        ["Rotate selected verbs", "Use a single verb for all"],
        index=0
    )
    single_verb = None
    if verb_mode == "Use a single verb for all":
        single_verb = st.selectbox("Single verb", options=(verb_choice or full_verb_bank), index=0)

    def pick_level(i: int) -> str:
        """Rotate evenly across chosen levels."""
        return chosen_levels[i % len(chosen_levels)]

    def pick_verb(i: int, level: str) -> str:
        """Pick a verb for this item."""
        if single_verb:
            return single_verb
        # If user selected custom verbs, rotate those; if empty, fallback to the level’s base verbs
        bank = verb_choice or BLOOMS[level]
        return bank[i % len(bank)]

    if st.button("Generate MCQs", type="primary", use_container_width=True):
        if not segments:
            st.warning("Please upload a lesson file or paste content.")
        else:
            # Large pool => pick distinct topics
            pool = carve_topics(segments, want=total_mcqs * 4)
            if not pool:
                st.warning("Not enough clean topics found. Try pasting simpler text.")
            else:
                random.shuffle(pool)
                topics = pool[:total_mcqs]

                mcqs = []
                for i, topic in enumerate(topics):
                    lvl = pick_level(i)
                    v = pick_verb(i, lvl)
                    mcqs.append(build_mcq(topic, v, topics))

                st.success(f"Generated {len(mcqs)} MCQs (level-mixed across {', '.join(chosen_levels)})")

                letters = "abcd"
                text_out = []
                for i, q in enumerate(mcqs, 1):
                    st.markdown(f"**Q{i}. {q['stem']}**")
                    for j, opt in enumerate(q['options']):
                        st.markdown(f"{letters[j]}) {opt}")
                    st.markdown(f"*Correct: {q['correct']}*")
                    st.markdown("---")

                    text_out.append(f"Q{i}. {q['stem']}")
                    for j, opt in enumerate(q['options']):
                        text_out.append(f"{letters[j]}) {opt}")
                    text_out.append(f"Correct: {q['correct']}\n")

                # Downloads
                txt_blob = "\n".join(text_out)
                st.download_button(
                    "Download TXT",
                    txt_blob.encode("utf-8"),
                    file_name=f"ADI_MCQs_Week{week}_Lesson{lesson}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

                docx_bytes = export_docx_mcqs(mcqs, f"ADI MCQs — Week {week}, Lesson {lesson}")
                if docx_bytes:
                    st.download_button(
                        "Download Word (DOCX)",
                        docx_bytes,
                        file_name=f"ADI_MCQs_Week{week}_Lesson{lesson}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                else:
                    st.info("DOCX export not available on this runtime.")
