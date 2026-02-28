import pandas as pd
import os
import glob

# --- Settings ---
CSV_DIR = "results_in_csv"
OUTPUT_FILE = "Final_Match_Timeline.csv"
FPS = 25
TIME_WINDOW_SECONDS = 3  # Merge similar events happening within a 3-second window
FRAME_WINDOW = FPS * TIME_WINDOW_SECONDS

def get_latest_csv(model_name):
    """Fetches the most recently generated CSV file for a given model."""
    search_pattern = os.path.join(CSV_DIR, f"result_{model_name}_*.csv")
    files = glob.glob(search_pattern)
    if not files:
        return None
    # Return the latest file based on creation time
    return max(files, key=os.path.getctime)

print("🚀 Starting Data Pipeline (Merging and Cleaning)...")

# 1. Fetch the latest files
file_small = get_latest_csv("SoccerNet_small")
file_ball = get_latest_csv("SoccerNetBall_challenge1")

if not file_small or not file_ball:
    print("❌ Error: Could not find the required CSV files in the 'results_in_csv' directory.")
    exit()

print(f"📥 Reading files:\n1. {os.path.basename(file_small)}\n2. {os.path.basename(file_ball)}")

# 2. Read data and add Event_Type column
df_small = pd.read_csv(file_small)
df_small['Event_Type'] = 'Match Event'  # Macro events (Goals, Cards, etc.)

df_ball = pd.read_csv(file_ball)
df_ball['Event_Type'] = 'Ball Action'   # Micro events (Passes, Shots, etc.)

# Initial merge of both dataframes
df_combined = pd.concat([df_small, df_ball], ignore_index=True)

# 3. Temporal Deduplication Algorithm (Time-based NMS)
print("🧹 Removing temporal duplicates (keeping highest confidence events)...")

# Sort by label and frame to group similar events together chronologically
df_combined = df_combined.sort_values(by=['label', 'frame'])

# Calculate the frame difference between consecutive events of the same label
df_combined['frame_diff'] = df_combined.groupby('label')['frame'].diff()

# Define "event blocks" (if the gap is larger than 75 frames, it's a new independent event)
df_combined['event_block'] = (df_combined['frame_diff'].fillna(FRAME_WINDOW + 1) > FRAME_WINDOW).cumsum()

# Extract the index of the event with the highest confidence within each block
best_event_indices = df_combined.groupby(['label', 'event_block'])['confidence'].idxmax()

# Filter the dataframe to keep only the best events
df_clean = df_combined.loc[best_event_indices].copy()

# 4. Final Formatting and Sorting
# Sort chronologically from the start of the match to the end
df_clean = df_clean.sort_values(by='frame')

# Rearrange columns for a professional layout
final_columns = ['timestamp', 'frame', 'label', 'confidence', 'Event_Type']
df_clean = df_clean[final_columns]

# Round confidence to 2 decimal places for better readability
df_clean['confidence'] = df_clean['confidence'].apply(lambda x: round(x, 2))

# 5. Save the final dataset
df_clean.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

print("-" * 50)
print(f"✅ Process completed successfully!")
print(f"📉 Total raw events: {len(df_combined)}")
print(f"📈 Total events after cleaning: {len(df_clean)} golden events.")
print(f"🗂️ Final file is ready: {OUTPUT_FILE}")
print("-" * 50)