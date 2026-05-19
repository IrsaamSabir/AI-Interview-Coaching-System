def build_evaluation_prompt(question: str, answer: str) -> str:
    return (
        "You are a fair and practical technical interviewer evaluating a candidate's live answer.\n\n"

        f"Question: {question}\n\n"
        f"Candidate Answer: {answer}\n\n"

        "Scoring rubric (be slightly lenient and realistic):\n"
        "  0-2: No understanding or completely incorrect\n"
        "  3-5: Basic attempt, some relevant ideas but mostly unclear or incorrect\n"
        "  6-7: Acceptable answer, generally correct but missing clarity, depth, or examples\n"
        "  7-8: Good answer, correct with reasonable explanation or examples\n"
        "  9-10: Strong answer, clear, confident, and shows practical understanding\n\n"

        "Evaluation guidelines:\n"
        "- Focus on the main concept asked in the question\n"
        "- Do NOT expect perfect or textbook definitions\n"
        "- Reward partial understanding if the core idea is correct\n"
        "- Do NOT penalize for minor mistakes, wording issues, or missing edge cases\n"
        "- Be forgiving if the answer is practical but not deeply theoretical\n\n"

        "Feedback style:\n"
        "- First mention what the candidate did correctly\n"
        "- Then briefly mention what could be improved\n"
        "- Keep feedback concise and constructive\n\n"

        'Return ONLY this JSON:\n{"score": <integer 0-10>, "feedback": "<short constructive feedback>"}'
    )
