# AI Coaching Platform — Video Analysis Microservice SDD

**Version:** 1.2 (Focused Agent Architecture)
**Date:** April 2026
**Project:** Graduation Project — Computer Science

---

## 1. System Overview

This repository contains the **AI Video Analysis Agent (CoachAi)**, a standalone microservice that acts as the core intelligence engine for the broader AI Coaching Platform. 

It processes raw match footage, detects tactical events using state-of-the-art Computer Vision (`SoccerNet` / PyTorch), and generates professional coaching reports using large language models (`Google Gemini`).

### Microservice Responsibilities
* Accept video files (via S3 or local download).
* Run heavy GPU inference (T-DEED / Action Spotting).
* Group and structure bounding boxes and timestamps into tactical phases.
* Generate raw JSON tactical data and comprehensive plain-text Markdown reports.

---

## 2. Infrastructure & Architecture (Full AWS)

To handle the heavy compute requirements of PyTorch while keeping costs low for the graduation project, this specific microservice should be deployed in isolation on a GPU-enabled machine.

### 2.1 Infrastructure Map

| Component | AWS Resource | Purpose |
|-----------|-------------|---------|
| **AI Worker Compute** | EC2 `g4dn.xlarge` | Runs the PyTorch detection models using the NVIDIA T4 GPU. |
| **Object Storage** | S3 Bucket | Stores the raw `.mp4` videos waiting for processing, and the final `.json` and `.md` reports. |
| **LLM Provider** | Google Gemini API | Evaluates the detected events and video to generate final coaching tactical insights. |
| **Task Database** | RDS PostgreSQL | (Optional) Tracks the status of the video processing jobs (`pending`, `processing`, `done`). |

### 2.2 Cost Control Rule
Because the `g4dn.xlarge` instance is relatively expensive to run 24/7, this microservice should ideally be deployed behind a queue (like AWS SQS). 
* The GPU instance only wakes up/spins up when a video is deposited into the S3 bucket.
* It parses the video in 3-5 minutes.
* It powers down natively to save credits.

---

## 3. The Video Analysis Pipeline Workflow

When a main backend application sends a video to this microservice, it follows this strict 4-stage pipeline:

| Stage | Action | Technology Used |
|-------|--------|-----------------|
| **1. Data Ingestion** | Video is downloaded securely from AWS S3 (or YouTube via `yt-dlp`). | Python `boto3` / `yt-dlp` |
| **2. Computer Vision** | The `inference.py` script runs the SoccerNet models to detect precise tactical actions and ball movements across frames. | PyTorch, MPS/CUDA |
| **3. Data Engineering** | The backend merges the CSV outputs from the CV models, groups them by standard frame intervals, and assigns tactical phase tags. | `pandas` |
| **4. AI Generation** | Both the video file and the structured CSV are uploaded to the Gemini API. Gemini outputs a structured JSON analysis, followed by a human-readable Markdown report. | Google Gemini 3.1 Flash |

---

## 4. Integration Database Schema

If integrating this agent into the larger web platform, the main database should track the agent's progress using the following tables:

```sql
CREATE TABLE app_data.analysis_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id         TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','processing','done','failed')),
    video_s3_key    TEXT,
    events_s3_key   TEXT,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE app_data.tactical_reports (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id           UUID NOT NULL REFERENCES app_data.analysis_jobs(id),
    team_id          TEXT NOT NULL,
    report_content   TEXT,       -- raw Gemini output, always populated
    report_data      JSONB,      -- structured sections, null until Week 3
    report_s3_key    TEXT,
    created_at       TIMESTAMP DEFAULT NOW()
);

```

---

## 5. API Endpoint Reference (For Deployment)

To expose this script as a service, the codebase should be wrapped in FastAPI with the following endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analyze` | Receives an S3 URL for a video, creates a task ID, and triggers the background Celery worker to run the ML models. |
| GET | `/api/status/{task_id}` | Main app polls this to see if the video is `processing` or `done`. |
| GET | `/api/report/{task_id}` | Fetch the completed `.md` and `.json` tactical report. |

---

*This document is strictly scoped to the AI Video Analysis Microservice. For the broader frontend web portal, scouting features, and Snowflake database architecture, please refer to the Main App Repository SDD.*
