from datetime import datetime


def build_cv_parse_prompt(cv_text: str) -> str:
    today = datetime.now().strftime("%B %Y")
    return f"""You are an expert CV/resume parser for technical hiring.

Reference date for roles ending "Present" or with no end date: {today}

Document text:
{cv_text}

If this is NOT a CV/resume (certificate, transcript, invoice, letter, ID, image, etc.),
return ONLY this and nothing else:
{{"is_cv": false}}

Do NOT extract skills or jobs from non-CV documents under any circumstances.

If it IS a CV, return ONLY valid JSON (no markdown, no extra text):

{{
  "is_cv": true,
  "skills": ["..."],
  "education": "degree + field or Unknown",
  "domain": "one short inferred role e.g. Backend Developer",
  "jobs": [
    {{"company": "Employer Inc", "start": "MM/YYYY", "end": "MM/YYYY"}},
    {{"company": "Other Co", "start": "03/2024", "end": null}}
  ]
}}

Skills: Extract concrete tools, languages, frameworks, databases, platforms, and technical skills from Skills, Experience, Projects, and certifications. Deduplicate. Max 40 items.

jobs (required):
- One entry per paid role, clearly labeled internship, or explicit freelance engagement with dates in the CV Experience section.
- Use "start" and "end" as strings in MM/YYYY format (e.g. "07/2025", "03/2024"). Leading zeros optional on month.
- If a role is ongoing, set "end" to null (the system uses today's month as the end).
- Do NOT list education-only lines, student projects without employment dates, certifications, or training without real job dates.
- If the candidate has no qualifying jobs, use "jobs": [].

Do NOT return years_experience or total_experience_months; experience length is computed from jobs in code.

Return ONLY the JSON."""
