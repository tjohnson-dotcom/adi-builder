def generate_questions(topic, level):
    templates = {
        "Remember": f"What is {topic}?",
        "Understand": f"Explain the concept of {topic}.",
        "Apply": f"How would you use {topic} in a real-world scenario?",
        "Analyze": f"What are the components of {topic}?",
        "Evaluate": f"Assess the effectiveness of {topic}.",
        "Create": f"Design a project using {topic}."
    }
    return [templates[level]]

def generate_activities(topic, level):
    activities = {
        "Remember": f"Create a flashcard set for {topic}.",
        "Understand": f"Write a summary of {topic}.",
        "Apply": f"Develop a case study involving {topic}.",
        "Analyze": f"Compare and contrast {topic} with related concepts.",
        "Evaluate": f"Debate the pros and cons of {topic}.",
        "Create": f"Build a prototype or model using {topic}."
    }
    return [activities[level]]
