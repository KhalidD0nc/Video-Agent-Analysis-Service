"""
Prompt templates for the Gemini tactical-analysis stages.

Each function accepts the dynamic data and returns the fully-formatted prompt
string, keeping the templates in one place instead of duplicated across
modal_app.py, run_pipeline.py, and run_but_by_youtube.py.
"""


def json_tactical_prompt(csv_data: str) -> str:
    """Stage 3 — ask Gemini for a structured JSON tactical breakdown."""
    return f"""\
You are an elite UEFA Pro License Football Analyst and Data Scientist.

**CRITICAL DATA CONTEXT:**
Use this CSV data as your absolute source of truth for timestamps and events:
<csv_data>
{csv_data}
</csv_data>

**OUTPUT FORMAT:** EXCLUSIVELY a raw, valid JSON array. No markdown.

**JSON SCHEMA REQUIREMENTS:**
For each distinct tactical phase, generate an object with the following keys:
1. "start_timestamp": "MM:SS" (The exact start time of the tactical phase)
2. "end_timestamp": "MM:SS" (The exact end time of the tactical phase)
3. "phase_of_play": (e.g., "Build-up", "Counter-Attack", "Defensive Transition")
4. "possession_team": (Color/Name of the attacking team)
5. "pitch_zone": (e.g., "Defensive Third - Central", "Zone 14", "Wide Channel")
6. "event_type": (e.g., "Vertical Pass", "Interception", "Line-Breaking Pass")
7. "tactical_description": Detailed narrative of the shape, defensive reaction, and movements of both teams.
8. "attacking_team_execution_rating": (1-10 scale)
9. "defending_team_execution_rating": (1-10 scale)
10. "key_tactical_insight": One sentence summarizing the core lesson or error for both teams.
11. "coach_actionable_advice": Direct, practical instructions for the coach.
12. "suggested_training_drill": A specific, named training ground drill."""


def text_report_prompt(csv_data: str, tactical_json: str) -> str:
    """Stage 4 — ask Gemini for a comprehensive Markdown coaching report."""
    return f"""\
You are the Head Coach's First Assistant.
You are analyzing the provided match video. You must also use the raw CSV timeline and the structured JSON tactical data we just extracted.

<csv_data>
{csv_data}
</csv_data>

<tactical_json>
{tactical_json}
</tactical_json>

Based strictly on your visual analysis combined with the CSV and JSON data, write a highly professional "Comprehensive Tactical Analysis" report in plain text (Markdown format). Use the video to add depth to the JSON findings.

Structure it EXACTLY like this template:

### Comprehensive Tactical Analysis ([Team A] vs. [Team B])
[Write a brief 2-sentence overarching summary of the match dynamics]

#### 1. [Title of First Tactical Observation based on the JSON and Video]
* **What the data says:** [Summarize start_timestamp, end_timestamp, event_type, and what happened using the CSV and Video]
* **Diagnosis:** [What went right/wrong based on the tactical_description and execution ratings]
* **Tactical Advice:** [Insert the coach_actionable_advice here, expanded slightly if the video provides more context]

[... repeat the above block for every phase found in the JSON ...]

---

### Training Tips for the Coach (Based on Data Analysis)

**1. Drill: "[Insert suggested_training_drill name]"**
* **Objective:** [What tactical flaw it fixes based on the key_tactical_insight]
* **The Drill:** [Explain how to run the drill]

[... repeat for all drills suggested in the JSON ...]

CRITICAL: Output ONLY the Markdown text. Do NOT wrap it in JSON. Be direct, authoritative, and analytical."""
