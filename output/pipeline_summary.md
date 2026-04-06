# Pipeline Run Summary
**Video:** downloaded_match_clip.mp4
**Total Duration:** 165.0 seconds

## Stage Timings

| Stage            | Duration  | Notes                            |
|------------------|-----------|----------------------------------|
| Download         | 0.3s      | Loaded from volume               |
| Inference        | 88.5s     | GPU (T4/L4/A10)                  |
| Cleaning         | 0.0s      | —                                |
| Gemini Analysis  | 76.2s     | Stages 3 & 4                     |

## Inference Results

| Model                     | Raw Events | After Cleaning |
|---------------------------|------------|----------------|
| SoccerNet_small           | 14         | —              |
| SoccerNetBall_challenge1  | 106        | —              |
| **Total**                 | **120**    | **93**         |

## Output Files

| File                      | Description                        |
|---------------------------|------------------------------------|
| `timeline.csv`            | Per-frame event timeline (93 rows) |
| `tactical_report.json`    | 5 tactical phases with ratings     |
| `comprehensive_analysis.md` | Full match analysis + 5 drills   |
