# ==========================================
# 1. CONFIGURATION & SETTINGS
# ==========================================
import os
import subprocess
import json
import pandas as pd
import sys
import time
import glob
from datetime import datetime
from google import genai
from dotenv import load_dotenv
import yt_dlp  # يجب تثبيتها عبر: pip install yt-dlp

# --- YOUTUBE INPUT ---
YOUTUBE_URL = "https://youtu.be/3oxlvdNMJB0?si=YMsiiLgpYr1mnZq5" 

def download_youtube_video(url):
    print(f"\n📥 Downloading video from YouTube: {url}")
    output_filename = "downloaded_match_clip.mp4"
    
    # تحديد الجودة والصيغة بشكل صارم
    ydl_opts = {
        'format': 'best[height<=720][ext=mp4]',
        'outtmpl': output_filename,
        'quiet': False,
        'nocheckcertificate': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"✅ Video downloaded successfully: {output_filename}")
        return output_filename
    except Exception as e:
        print(f"❌ Failed to download video: {e}")
        sys.exit(1)

# Set VIDEO_PATH dynamically from the downloaded file
VIDEO_PATH = download_youtube_video(YOUTUBE_URL)
FPS = 25  

# Directories
CSV_OUT_DIR = "results_in_csv"
JSON_OUT_DIR = "inference_output"
FINAL_OUT_DIR = "final_output"  # Dedicated folder for final products

MODELS_TO_RUN = [
    "SoccerNet_small",
    "SoccerNetBall_challenge1"
]

for directory in [CSV_OUT_DIR, JSON_OUT_DIR, FINAL_OUT_DIR]:
    os.makedirs(directory, exist_ok=True)

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.environ["WANDB_MODE"] = "offline"


# ==========================================
# 2. INFERENCE & DATA EXTRACTION (STAGE 1)
# ==========================================
def frame_to_time(frame, fps):
    total_seconds = int(frame) / fps
    return f"{int(total_seconds // 60):02d}:{int(total_seconds % 60):02d}"

def process_to_csv(model_name, json_path, run_timestamp):
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        predictions = data.get('predictions', data)
        df = pd.DataFrame(predictions)
        
        if not df.empty:
            df['timestamp'] = df['frame'].apply(lambda x: frame_to_time(x, FPS))
            cols = ['frame', 'timestamp', 'label', 'confidence']
            df = df[[c for c in cols if c in df.columns]]
            
            file_name = f"result_{model_name}_{run_timestamp}.csv"
            output_csv = os.path.join(CSV_OUT_DIR, file_name)
            df.to_csv(output_csv, index=False, encoding='utf-8-sig')
            print(f"   [+] Saved CSV: {output_csv}")
    except Exception as e:
        print(f"   [!] Failed to convert for model {model_name}: {e}")

def run_vision_models(run_timestamp):
    print("\n" + "="*50)
    print("🎬 STAGE 1: RUNNING COMPUTER VISION MODELS")
    print("="*50)
    
    for model in MODELS_TO_RUN:
        print(f"\n📡 Running model: {model}")
        cmd = [
            sys.executable, "inference.py",
            "--model", model, "--video_path", VIDEO_PATH,
            "--frame_width", "796", "--frame_height", "448",
            "--inference_threshold", "0.3"
        ]
        
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            potential_json = os.path.join(JSON_OUT_DIR, "results_inference.json")
            if os.path.exists(potential_json):
                process_to_csv(model, potential_json, run_timestamp)
                raw_save = os.path.join(JSON_OUT_DIR, f"raw_{model}_{run_timestamp}.json")
                os.rename(potential_json, raw_save)
        else:
            print(f"❌ Failed to run {model}.")
            sys.exit(1)


# ==========================================
# 3. DATA ENGINEERING & CLEANING (STAGE 2)
# ==========================================
def get_latest_csv(model_name):
    search_pattern = os.path.join(CSV_OUT_DIR, f"result_{model_name}_*.csv")
    files = glob.glob(search_pattern)
    return max(files, key=os.path.getctime) if files else None

def merge_and_clean_data(run_timestamp):
    print("\n" + "="*50)
    print("🧹 STAGE 2: DATA CLEANING AND MERGING")
    print("="*50)
    
    file_small = get_latest_csv("SoccerNet_small")
    file_ball = get_latest_csv("SoccerNetBall_challenge1")

    if not file_small or not file_ball:
        print("❌ Error: Missing CSV files for merging.")
        sys.exit(1)

    df_small = pd.read_csv(file_small)
    df_small['Event_Type'] = 'Match Event'
    
    df_ball = pd.read_csv(file_ball)
    df_ball['Event_Type'] = 'Ball Action'

    df_combined = pd.concat([df_small, df_ball], ignore_index=True)
    df_combined = df_combined.sort_values(by=['label', 'frame'])
    
    FRAME_WINDOW = FPS * 3
    df_combined['frame_diff'] = df_combined.groupby('label')['frame'].diff()
    df_combined['event_block'] = (df_combined['frame_diff'].fillna(FRAME_WINDOW + 1) > FRAME_WINDOW).cumsum()
    best_event_indices = df_combined.groupby(['label', 'event_block'])['confidence'].idxmax()
    
    df_clean = df_combined.loc[best_event_indices].copy()
    df_clean = df_clean.sort_values(by='frame')
    df_clean = df_clean[['timestamp', 'frame', 'label', 'confidence', 'Event_Type']]
    df_clean['confidence'] = df_clean['confidence'].apply(lambda x: round(x, 2))
    
    output_filename = f"Final_Match_Timeline_{run_timestamp}.csv"
    output_file = os.path.join(FINAL_OUT_DIR, output_filename)
    df_clean.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"✅ Cleaned data saved to: {output_file}")
    return output_file


# ==========================================
# 4. GEMINI TACTICAL ANALYSIS (STAGES 3 & 4)
# ==========================================
def run_gemini_analysis(video_path, csv_path, run_timestamp):
    print("\n" + "="*50)
    print("🧠 STAGE 3: GEMINI JSON TACTICAL ANALYSIS")
    print("="*50)
    
    if not API_KEY:
        print("❌ Error: GEMINI_API_KEY not found. Please set it in your .env file.")
        sys.exit(1)

    client = genai.Client(api_key=API_KEY)

    with open(csv_path, 'r', encoding='utf-8-sig') as file:
        csv_data = file.read()

    print(f"📤 Uploading video '{video_path}' to Gemini via File API...")
    try:
        video_file = client.files.upload(file=video_path)
    except Exception as e:
        print(f"❌ Failed to upload video: {e}")
        sys.exit(1)

    print("⏳ Processing video in the cloud...")
    while video_file.state.name == "PROCESSING":
        time.sleep(2)
        video_file = client.files.get(name=video_file.name)

    if video_file.state.name == "FAILED":
        print("❌ Video processing failed in the cloud.")
        sys.exit(1)

    print("✅ Video processed! Generating structured JSON report...")

    # --- PROMPT 1: THE JSON STRUCTURE ---
    json_prompt = f"""
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
8. "attacking_team_execution_rating": (1-10 scale rating the possession team's tactical execution and attacking efficiency)
9. "defending_team_execution_rating": (1-10 scale rating the out-of-possession team's defensive structure, tracking, and reaction)
10. "key_tactical_insight": One sentence summarizing the core lesson or error for both teams.
11. "coach_actionable_advice": Direct, practical instructions for the coach to either fix the exposed weakness or reinforce the successful tactic.
12. "suggested_training_drill": A specific, named training ground drill to improve the team's execution in this specific phase.
"""

    try:
        # Execute STAGE 3
        response_json = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=[video_file, json_prompt]
        ) 
        tactical_json = response_json.text
        
        report_filename_json = f"Tactical_Report_{run_timestamp}.json"
        report_path_json = os.path.join(FINAL_OUT_DIR, report_filename_json)
        with open(report_path_json, "w", encoding="utf-8") as f:
            f.write(tactical_json)
        print(f"💾 JSON Report saved to: {report_path_json}")

        # ==========================================
        # STAGE 4: COMPREHENSIVE TEXT ANALYSIS
        # ==========================================
        print("\n" + "="*50)
        print("📝 STAGE 4: GENERATING COMPREHENSIVE TEXT REPORT")
        print("="*50)
        
        # Safety valve to prevent 503 Rate Limit Error
        print("⏳ Pausing for 15 seconds to prevent Google API Rate Limit (503 Error) before the next heavy request...")
        time.sleep(15)
        
        text_prompt = f"""
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

CRITICAL: Output ONLY the Markdown text. Do NOT wrap it in JSON. Be direct, authoritative, and analytical.
"""
        print("⏳ Analyzing Video + JSON + CSV to write the final text report...")
        response_text = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=[video_file, text_prompt]
        )
        
        report_filename_txt = f"Comprehensive_Analysis_{run_timestamp}.md"
        report_path_txt = os.path.join(FINAL_OUT_DIR, report_filename_txt)
        with open(report_path_txt, "w", encoding="utf-8") as f:
            f.write(response_text.text)
        
        print(f"💾 Comprehensive Text Report saved to: {report_path_txt}")
        print("\n📋 FINAL TEXT PREVIEW:\n")
        print(response_text.text)

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
    finally:
        print("\n🗑️ Cleaning up: Deleting video from Google's servers and local storage...")
        # 1. Cloud cleanup
        try:
            client.files.delete(name=video_file.name)
            print("✅ Cloud cleanup complete.")
        except Exception as e:
            print(f"⚠️ Could not delete file from cloud: {e}")
            
        # 2. Local cleanup
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                print(f"✅ Local cleanup complete. Deleted {video_path}")
        except Exception as e:
            print(f"⚠️ Could not delete local file: {e}")

# ==========================================
# 5. MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    start_time = time.time()
    
    global_run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    run_vision_models(global_run_timestamp)
    final_csv_path = merge_and_clean_data(global_run_timestamp)
    run_gemini_analysis(VIDEO_PATH, final_csv_path, global_run_timestamp)
    
    elapsed = time.time() - start_time
    print("\n" + "="*50)
    print(f"🎉 PIPELINE COMPLETED SUCCESSFULLY IN {int(elapsed // 60)}m {int(elapsed % 60)}s!")
    print("="*50)