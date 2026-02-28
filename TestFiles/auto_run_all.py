import os
import subprocess
import json
import pandas as pd
import sys
from datetime import datetime

# --- Basic Settings ---
VIDEO_PATH = "barcalonaMatchClip.mp4" 
FPS = 25  

# Dedicated output directories
CSV_OUT_DIR = "results_in_csv"
JSON_OUT_DIR = "inference_output"

# Models to run
MODELS_TO_RUN = [
    "SoccerNet_small",
    "SoccerNetBall_challenge1",
    "SoccerNet_big"  
]

# Create directories if they don't exist to prevent errors
os.makedirs(CSV_OUT_DIR, exist_ok=True)
os.makedirs(JSON_OUT_DIR, exist_ok=True)

def frame_to_time(frame, fps):
    total_seconds = int(frame) / fps
    return f"{int(total_seconds // 60):02d}:{int(total_seconds % 60):02d}"

def process_to_csv(model_name, json_path, run_timestamp):
    print(f"🔄 Converting {model_name} outputs to CSV...")
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        predictions = data.get('predictions', data)
        df = pd.DataFrame(predictions)
        
        if not df.empty:
            df['timestamp'] = df['frame'].apply(lambda x: frame_to_time(x, FPS))
            cols = ['frame', 'timestamp', 'label', 'confidence']
            df = df[[c for c in cols if c in df.columns]]
            
            # Save CSV with timestamp to prevent overwriting
            file_name = f"result_{model_name}_{run_timestamp}.csv"
            output_csv = os.path.join(CSV_OUT_DIR, file_name)
            
            df.to_csv(output_csv, index=False, encoding='utf-8-sig')
            print(f"✅ Successfully saved CSV: {output_csv}")
    except Exception as e:
        print(f"⚠️ Failed to convert for model {model_name}: {e}")

# Windows environment setup for RTX memory management
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.environ["WANDB_MODE"] = "offline"

print("🚀 Starting T-DEED comprehensive pipeline...")

for model in MODELS_TO_RUN:
    print(f"\n" + "="*50)
    print(f"📡 Running model: {model}")
    print("="*50)
    
    # Generate a unique timestamp for each model run (YYYYMMDD_HHMMSS)
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    cmd = [
        sys.executable, "inference.py",
        "--model", model,
        "--video_path", VIDEO_PATH,
        "--frame_width", "796",
        "--frame_height", "448",
        "--inference_threshold", "0.3"
    ]
    
    # Execute inference
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        # Read default output from inference_output folder
        potential_json = os.path.join(JSON_OUT_DIR, "results_inference.json")
        if os.path.exists(potential_json):
            
            # 1. Convert to CSV and send to designated folder
            process_to_csv(model, potential_json, run_timestamp)
            
            # 2. Rename raw JSON file and keep it as backup
            raw_save = os.path.join(JSON_OUT_DIR, f"raw_{model}_{run_timestamp}.json")
            os.rename(potential_json, raw_save)
            print(f"🗂️ Raw JSON saved at: {raw_save}")
    else:
        print(f"❌ Failed to run {model}. Check for errors above.")

print("\n🎉 All operations completed! Check your output directories (results_in_csv and inference_output).")