# ⚽ Video-Analysis-Agent-CoachAi

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-Deep%20Learning-ee4c2c)
![Gemini](https://img.shields.io/badge/Google%20Gemini-AI%20Analysis-1a73e8)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac-lightgrey)

**An AI-Powered Football Tactical Analysis System** *Graduation Project - College of Computer and Information Sciences, Al Imam Mohammad Ibn Saud Islamic University.*

## 📖 Overview
CoachAi is an automated, end-to-end pipeline designed to act as an elite football tactical analyst. It extracts gameplay footage directly from YouTube, processes it through state-of-the-art Computer Vision models to detect complex tactical events, and utilizes Large Language Models (LLMs) to generate professional, coach-ready tactical reports and training recommendations.

## 🏗️ System Architecture
The pipeline operates in 4 distinct stages:
1. **Data Ingestion:** Automated downloading of match clips via `yt-dlp`.
2. **Computer Vision (Stage 1):** Running `SoccerNet` models to detect actions and ball movements (Device-Agnostic: supports CUDA and MPS).
3. **Data Engineering (Stage 2):** Cleaning, merging, and grouping frames into distinct tactical phases using `pandas`.
4. **LLM Analysis (Stages 3 & 4):** Uploading the video and structured CSV to Google Gemini 3.1 Flash to generate a detailed JSON tactical breakdown and a final Markdown comprehensive report.

## ⚙️ Installation & Setup (For Developers)

We enforce strict environment isolation. Please follow the instructions specific to your operating system.

### 1. Clone the Repository
```bash
git clone [https://github.com/Marwan915/Video-Analysis-Agent-CoachAi.git](https://github.com/Marwan915/Video-Analysis-Agent-CoachAi.git)
cd Video-Analysis-Agent-CoachAi

```

### 2. Create a Virtual Environment

```bash
python -m venv venv

```

### 3. Activate the Environment

* **Windows:** `.\venv\Scripts\activate`
* **Mac/Linux:** `source venv/bin/activate`

### 4. Install Dependencies (OS Specific)

Due to hardware acceleration differences (NVIDIA CUDA vs. Apple MPS), install the correct requirements file:

* **For Windows (NVIDIA GPU):**
```bash
pip install -r requirements.txt

```


* **For Mac (Apple Silicon / Intel):**
```bash
pip install -r requirements-mac.txt

```



### 5. Environment Variables

Create a file named `.env` in the root directory and add your Google Gemini API Key:

```env
GEMINI_API_KEY="your_api_key_here"

```

*(Note: Do not commit the `.env` file to version control. It is already ignored in `.gitignore`).*

## 🚀 Usage

To run the complete analysis pipeline:

1. Open `run_but_youtube.py` .
2. Replace the `YOUTUBE_URL` variable with your target match clip.
3. Execute the script:

```bash
python run_but_youtube.py

```

or use the video path code in 
```bash
python run_pipeline.py

```

The system will automatically download the video, run the inference, and place the final reports in the `final_output/` directory.

## 👥 Author

* **Marwan** 




using :

# T-DEED
### T-DEED: Temporal-Discriminability Enhancer Encoder-Decoder for Precise Event Spotting in Sports Videos (CVsports '24)
<a href="https://pytorch.org/get-started/locally/"><img alt="PyTorch" src="https://img.shields.io/badge/PyTorch-ee4c2c?logo=pytorch&logoColor=white"></a>
[![arXiv](https://img.shields.io/badge/arXiv-2404.05392-red)](https://arxiv.org/abs/2404.05392)
[![ProjectPage](https://img.shields.io/badge/Project%20Page-green)](https://arturxe2.github.io/projects/T-DEED/)
[![ExtendedPaper](https://img.shields.io/badge/ExtendedPaper-green)](https://arturxe2.github.io/files/TDEED_Revisited.pdf)

This repository contains the PyTorch implementation of the paper:

**T-DEED: Temporal-Discriminability Enhancer Encoder-Decoder for Precise Event Spotting in Sports Videos**<br>
*Artur Xarles, Sergio Escalera, Thomas B. Moeslund, and Albert Clapés*<br>
**10th International Workshop on Computer Vision in Sports (CVsports) at CVPR 2024**<br>

An extension of the paper with additional results can be found in the provided button above (ExtendedPaper).


## Overview

This repository builds upon the original [T-DEED implementation](https://github.com/arturxe2/T-DEED) to evaluate the model across additional PES datasets and the broader Action Spotting task, including SoccerNet Action Spotting (SNAS) and SoccerNet Ball Action Spotting (SNBAS). Notably, this implementation was also used to achieve the 1st place in the 2024 SNBAS Challenge.

It contains two distinct releases: the first corresponds to the initial release for the paper, and the second includes an extended evaluation on additional PES datasets along with adaptations for the broader Action Spotting task in SoccerNet.


## Environment

You can install the required packages for the project using the following command, with `requirements.txt` specifying the versions of the various packages:

```
pip install -r requirements.txt
```

## Perform inference

You can perform inference on a single video using the `inference.py` script. Run it from the command line as follows:

```
python3 inference.py --model <model_name> --video_path <video_path> --frame_width <frame_width> --frame_height <frame_height> --inference_threshold <inference_threshold>
```

For example, to use a pre-trained SoccerNetBall model:

```
python3 inference.py --model SoccerNetBall_challenge1 --video_path /videos/inference_video.mp4 --frame_width 796 --frame_height 448 --inference_threshold 0.3
```

Ensure that the specified trained model is accessible. The frame width and height must match the resolution used during model training. The inference threshold can be adjusted according to your preference. 

## Contact

If you have any questions related to the code, feel free to contact arturxe@gmail.com.

## References

If you find our work useful, please consider citing our paper.
```
@inproceedings{xarles2024t,
  title={T-DEED: Temporal-Discriminability Enhancer Encoder-Decoder for Precise Event Spotting in Sports Videos},
  author={Xarles, Artur and Escalera, Sergio and Moeslund, Thomas B and Clap{\'e}s, Albert},
  booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition},
  pages={3410--3419},
  year={2024}
}
```
