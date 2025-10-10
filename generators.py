def generate_questions(verbs):
    questions = []
    for verb in verbs:
        questions.append(f"What does it mean to {verb} this concept?")
    return questions
