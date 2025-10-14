# FFmpeg Batch Processor - Real-World Examples

This document contains practical, real-world examples of using the FFmpeg Batch Processor.

## Table of Contents
1. [YouTube Video Preparation](#youtube-video-preparation)
2. [Social Media Content](#social-media-content)
3. [E-Learning Platform](#e-learning-platform)
4. [Podcast Production](#podcast-production)
5. [Video Surveillance](#video-surveillance)
6. [Marketing Campaigns](#marketing-campaigns)

---

## YouTube Video Preparation

### Scenario
You need to upload a video to YouTube and want to create multiple quality versions plus a thumbnail.

### Solution
```bash
# Upload your raw video
cp ~/Desktop/raw_video.mp4 ./data/input/

# Process for web (YouTube recommended settings)
docker-compose exec video-processor python cli.py create /data/input/raw_video.mp4 transcode \
  --params '{"codec":"libx264","preset":"slow","crf":18,"audio_codec":"aac"}' \
  --output /data/output/youtube_1080p.mp4

# Generate thumbnail at 3 seconds
docker-compose exec video-processor python cli.py create /data/input/raw_video.mp4 generate_thumbnail \
  --params '{"timestamp":"00:00:03","size":"1920x1080"}' \
  --output /data/output/thumbnail.jpg

# Create preview GIF for social media promotion
docker-compose exec video-processor python cli.py create /data/input/raw_video.mp4 create_gif \
  --params '{"start_time":"00:00:10","duration":3,"fps":15,"scale":640}' \
  --output /data/output/preview.gif
```

---

## Social Media Content

### Scenario
Convert a single video into multiple formats for different social media platforms.

### Platform Requirements
- Instagram Feed: 1080x1080 (square), max 60s, <100MB
- Instagram Stories: 1080x1920 (vertical), max 15s
- Twitter: 1280x720, max 2:20, <512MB
- Facebook: 1280x720, <240 minutes, <4GB

### Solution - Using Workflow
```bash
# Use the social media package workflow
docker-compose exec video-processor python cli.py workflow \
  /data/input/content.mp4 social_media_package
```

### Solution - Custom for Each Platform
```bash
# Instagram Feed (square crop)
docker-compose exec video-processor python cli.py create /data/input/content.mp4 transcode \
  --params '{"codec":"libx264","preset":"medium","crf":23}' \
  --output /data/output/instagram_feed.mp4

# Instagram Stories (vertical)
docker-compose exec video-processor python cli.py create /data/input/content.mp4 compress \
  --params '{"scale":"1080:1920","target_size_mb":90}' \
  --output /data/output/instagram_story.mp4

# Twitter (compressed)
docker-compose exec video-processor python cli.py create /data/input/content.mp4 compress \
  --params '{"scale":"1280:720","target_size_mb":450}' \
  --output /data/output/twitter.mp4

# Trim for Instagram Stories (15s)
docker-compose exec video-processor python cli.py create /data/output/instagram_story.mp4 trim_video \
  --params '{"start_time":"00:00:00","duration":15}' \
  --output /data/output/instagram_story_15s.mp4
```

---

## E-Learning Platform

### Scenario
Process uploaded course videos for streaming on an e-learning platform with multiple quality options.

### Requirements
- Multiple quality levels (1080p, 720p, 480p)
- Web-optimized for streaming
- Thumbnails for course listings
- Fast encoding for quick publishing

### Solution - Batch Script
Create a script `process_course_video.sh`:

```bash
#!/bin/bash

INPUT=$1
BASE_NAME=$(basename "$INPUT" .mp4)

# 1080p HD
docker-compose exec video-processor python cli.py create "$INPUT" transcode \
  --params '{"codec":"libx264","preset":"fast","crf":23,"audio_codec":"aac"}' \
  --output "/data/output/${BASE_NAME}_1080p.mp4" &

# 720p SD
docker-compose exec video-processor python cli.py create "$INPUT" compress \
  --params '{"scale":"1280:720","target_size_mb":null}' \
  --output "/data/output/${BASE_NAME}_720p.mp4" &

# 480p Mobile
docker-compose exec video-processor python cli.py create "$INPUT" compress \
  --params '{"scale":"854:480","target_size_mb":null}' \
  --output "/data/output/${BASE_NAME}_480p.mp4" &

# Thumbnail at 10% mark
docker-compose exec video-processor python cli.py create "$INPUT" generate_thumbnail \
  --params '{"timestamp":"00:00:10","size":"1280x720"}' \
  --output "/data/output/${BASE_NAME}_thumb.jpg" &

wait
echo "Processing complete for $BASE_NAME"
```

Usage:
```bash
chmod +x process_course_video.sh
./process_course_video.sh ./data/input/lecture_01.mp4
```

---

## Podcast Production

### Scenario
Extract audio from video recordings, create preview clips, and generate thumbnails.

### Solution
```bash
# Extract high-quality audio
docker-compose exec video-processor python cli.py profile \
  /data/input/podcast_episode_05.mp4 audio_aac

# Create 30-second preview clip
docker-compose exec video-processor python cli.py create /data/input/podcast_episode_05.mp4 trim_video \
  --params '{"start_time":"00:05:00","duration":30}' \
  --output /data/output/episode_05_preview.mp4

# Generate episode thumbnail
docker-compose exec video-processor python cli.py profile \
  /data/input/podcast_episode_05.mp4 thumbnail

# Extract multiple audio formats for distribution
docker-compose exec video-processor python cli.py profile \
  /data/input/podcast_episode_05.mp4 audio_mp3
```

### Batch Process Multiple Episodes
```python
#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

episodes_dir = Path("./data/input/podcast_episodes")

for episode in episodes_dir.glob("*.mp4"):
    print(f"Processing {episode.name}...")

    # Extract audio
    subprocess.run([
        "docker-compose", "exec", "video-processor",
        "python", "cli.py", "profile",
        str(episode), "audio_mp3"
    ])

    # Generate thumbnail
    subprocess.run([
        "docker-compose", "exec", "video-processor",
        "python", "cli.py", "profile",
        str(episode), "thumbnail"
    ])

print("Batch processing complete!")
```

---

## Video Surveillance

### Scenario
Process security camera footage - compress for storage, create time-lapse, extract key frames.

### Solution
```bash
# Compress for long-term storage (high compression)
docker-compose exec video-processor python cli.py create /data/input/camera_01_20240115.mp4 compress \
  --params '{"scale":"1280:720","target_size_mb":50}' \
  --output /data/output/camera_01_archived.mp4

# Create time-lapse (speed up 10x)
# Note: This would require adding a custom operation to video_processor.py

# Extract thumbnail every 60 seconds for review
# This could be done by creating a custom script
```

### Batch Archive Script
```bash
#!/bin/bash

# Archive all footage older than 7 days
find ./data/input/surveillance -name "*.mp4" -mtime +7 | while read file; do
    echo "Archiving: $file"
    docker-compose exec video-processor python cli.py profile "$file" social_media
done
```

---

## Marketing Campaigns

### Scenario
Create multiple ad variations from a single master video.

### Requirements
- Different lengths (6s, 15s, 30s bumper ads)
- Multiple aspect ratios (16:9, 1:1, 9:16)
- Add watermarks/branding
- Various quality levels for different platforms

### Solution
```bash
# Master video
MASTER="/data/input/ad_campaign_2024.mp4"
LOGO="/data/input/company_logo.png"

# 6-second bumper (YouTube)
docker-compose exec video-processor python cli.py create "$MASTER" trim_video \
  --params '{"start_time":"00:00:00","duration":6}' \
  --output /data/output/ad_6s.mp4

# 15-second spot
docker-compose exec video-processor python cli.py create "$MASTER" trim_video \
  --params '{"start_time":"00:00:00","duration":15}' \
  --output /data/output/ad_15s.mp4

# 30-second spot with watermark
docker-compose exec video-processor python cli.py create "$MASTER" trim_video \
  --params '{"start_time":"00:00:00","duration":30}' \
  --output /data/output/ad_30s_temp.mp4

docker-compose exec video-processor python cli.py create /data/output/ad_30s_temp.mp4 add_watermark \
  --params '{"watermark_path":"'"$LOGO"'","position":"bottom-right","opacity":0.8}' \
  --output /data/output/ad_30s_branded.mp4

# Square format for Instagram
docker-compose exec video-processor python cli.py create /data/output/ad_15s.mp4 compress \
  --params '{"scale":"1080:1080"}' \
  --output /data/output/ad_15s_square.mp4
```

---

## Advanced: Python Integration

### Building a Video Processing Pipeline

```python
#!/usr/bin/env python3
"""
Complete video processing pipeline example
"""

import requests
import time
from pathlib import Path

class VideoProcessor:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def upload_video(self, file_path):
        """Upload a video file"""
        with open(file_path, "rb") as f:
            response = requests.post(
                f"{self.base_url}/upload/",
                files={"file": f}
            )
        return response.json()["file_path"]

    def create_job(self, input_file, profile):
        """Create a processing job"""
        response = requests.post(
            f"{self.base_url}/jobs/profile/",
            json={"input_file": input_file, "profile": profile}
        )
        return response.json()["job_id"]

    def wait_for_job(self, job_id):
        """Wait for job to complete"""
        while True:
            response = requests.get(f"{self.base_url}/jobs/{job_id}")
            job = response.json()

            print(f"[{job_id[:8]}] {job['status']} - {job['progress']:.1f}%")

            if job['status'] in ['completed', 'failed']:
                return job

            time.sleep(2)

    def download_output(self, job_id, output_path):
        """Download processed video"""
        response = requests.get(f"{self.base_url}/jobs/{job_id}/download")
        with open(output_path, "wb") as f:
            f.write(response.content)

# Usage example
processor = VideoProcessor()

# Upload video
print("Uploading video...")
input_file = processor.upload_video("~/Desktop/my_video.mp4")

# Create multiple processing jobs
jobs = []
for profile in ["web_optimized", "mobile_optimized", "thumbnail"]:
    print(f"Creating job for profile: {profile}")
    job_id = processor.create_job(input_file, profile)
    jobs.append((job_id, profile))

# Wait for all jobs
for job_id, profile in jobs:
    print(f"\nProcessing {profile}...")
    job = processor.wait_for_job(job_id)

    if job['status'] == 'completed':
        output_file = f"output_{profile}.mp4"
        processor.download_output(job_id, output_file)
        print(f"✓ Downloaded: {output_file}")
    else:
        print(f"✗ Failed: {job.get('error')}")

print("\n✓ All processing complete!")
```

---

## Tips for Production Use

### 1. Error Handling
Always check job status and handle failures:
```python
job = processor.wait_for_job(job_id)
if job['status'] == 'failed':
    logger.error(f"Job failed: {job['error']}")
    # Retry logic here
```

### 2. Resource Management
Monitor queue size and adjust workers:
```bash
# Check stats
docker-compose exec video-processor python cli.py stats

# Adjust workers in docker-compose.yml
environment:
  - MAX_WORKERS=8  # Increase for more throughput
```

### 3. Batch Processing
Process multiple files efficiently:
```bash
# Process all MP4 files in a directory
for file in ./data/input/*.mp4; do
    docker-compose exec video-processor python cli.py profile "$file" web_optimized &
done
wait
```

### 4. Monitoring
Set up monitoring for long-running processes:
```bash
# Watch queue in real-time
watch -n 2 "docker-compose exec video-processor python cli.py stats"
```

---

## Need Help?

- Check the main [README.md](README.md) for detailed API documentation
- Visit http://localhost:8000/docs for interactive API docs
- Review logs: `tail -f ./data/logs/processor.log`
