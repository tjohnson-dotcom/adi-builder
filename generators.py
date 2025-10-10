# generators.py — MCQ, skills, revision generators
def generate_mcqs(n, topic, low, med, high):
    seeds = (high or med or low or ["analyze"])
    qs = []
    for i in range(n):
        v = seeds[i % len(seeds)]
        stem = topic.strip() or "Explain the role of inspection in quality management."
        stem = f"Using the verb **{v}**, {stem}"
        qs.append({
            "stem": stem,
            "A": "To verify conformance",
            "B": "To set company policy",
            "C": "To hire staff",
            "D": "To control budgets",
            "correct": "A"
        })
    return qs

def generate_skills(verbs_med, lesson, week):
    if not verbs_med:
        verbs_med = ["apply"]
    prompts = []
    for i, v in enumerate(verbs_med, start=1):
        prompts.append(f"Week {week}, Lesson {lesson}: In teams of 3, **{v}** the method to a real part from your project; produce a 1-page evidence sheet.")
    return prompts

def generate_revision(verbs_low, verbs_high):
    prompts = []
    for v in (verbs_low or ["define"]):
        prompts.append(f"Flash-cards: **{v}** five key terms from this module.")
    for v in (verbs_high or ["evaluate"]):
        prompts.append(f"Exit ticket: **{v}** your process and justify improvements.")
