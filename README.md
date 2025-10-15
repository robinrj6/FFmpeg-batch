# FFmpeg Batch Video Processor

A production-ready, Docker-based batch video processing application powered by FFmpeg. Process multiple videos concurrently with predefined profiles, custom operations, and workflow automation.

## Features

- **Batch Processing**: Process multiple videos concurrently with configurable workers
- **Processing Profiles**: Pre-configured profiles for common tasks (web optimization, compression, social media, etc.)
- **Workflow Automation**: Chain multiple operations together
- **REST API**: Full-featured API for job management
- **CLI Tool**: Command-line interface for easy interaction
- **Progress Tracking**: Real-time progress monitoring for all jobs
- **Docker Ready**: Fully containerized application
- **Production Ready**: Logging, error handling, and queue management

## Supported Operations

- **Transcode**: Convert videos between formats/codecs
- **Compress**: Reduce video file size with quality control
- **Watermark**: Add image watermarks to videos
- **Thumbnails**: Generate video thumbnails
- **Audio Extraction**: Extract audio tracks in various formats
- **GIF Creation**: Create animated GIFs from video clips
- **Video Trimming**: Cut videos to specific durations
- **Concatenation**: Join multiple videos together

## Quick Start

### Using Docker Compose (Recommended)

1. **Start the application**:
```bash
docker-compose up -d
```

2. **Place your videos** in the `./data/input` directory

3. **Process videos** using the CLI:
```bash
# Using a profile
docker-compose exec video-processor python cli.py profile /data/input/video.mp4 web_optimized --output /data/output/video.mp4

# Using a workflow
docker-compose exec video-processor python cli.py workflow /data/input/video.mp4 social_media_package --output /data/output/video.mp4


# Check status
docker-compose exec video-processor python cli.py stats
```

4. **Find processed videos** in `./data/output`

### Using the API

The API is available at `http://localhost:8000`

**Interactive API docs**: http://localhost:8000/docs

## Usage Examples

### CLI Examples

#### Process with a Profile
```bash
# Web optimized video
python cli.py profile /data/input/video.mp4 web_optimized

# Social media ready
python cli.py profile /data/input/video.mp4 social_media

# Generate thumbnail
python cli.py profile /data/input/video.mp4 thumbnail

# Extract audio as MP3
python cli.py profile /data/input/video.mp4 audio_mp3
```

#### Execute a Workflow
```bash
# Complete social media package (video + thumbnail + GIF preview)
python cli.py workflow /data/input/video.mp4 social_media_package

# Multi-format delivery
python cli.py workflow /data/input/video.mp4 multi_format
```

#### Custom Operations
```bash
# Transcode with custom parameters
python cli.py create /data/input/video.mp4 transcode \
  --params '{"codec":"libx264","preset":"slow","crf":18}'

# Compress to specific size
python cli.py create /data/input/video.mp4 compress \
  --params '{"target_size_mb":50,"scale":"1280:720"}'

# Add watermark
python cli.py create /data/input/video.mp4 add_watermark \
  --params '{"watermark_path":"/data/input/logo.png","position":"bottom-right"}'
```

#### Monitor Jobs
```bash
# List all jobs
python cli.py list

# Filter by status
python cli.py list --status completed

# Watch job progress
python cli.py watch <job-id>

# Get job details
python cli.py status <job-id>

# View statistics
python cli.py stats
```

### API Examples

#### Create a Job from Profile
```bash
curl -X POST "http://localhost:8000/jobs/profile/" \
  -H "Content-Type: application/json" \
  -d '{
    "input_file": "/data/input/video.mp4",
    "profile": "web_optimized"
  }'
```

#### Create a Workflow
```bash
curl -X POST "http://localhost:8000/jobs/workflow/" \
  -H "Content-Type: application/json" \
  -d '{
    "input_file": "/data/input/video.mp4",
    "workflow": "social_media_package"
  }'
```

#### Check Job Status
```bash
curl "http://localhost:8000/jobs/{job-id}"
```

#### List All Jobs
```bash
curl "http://localhost:8000/jobs/"
```

#### Download Output
```bash
curl "http://localhost:8000/jobs/{job-id}/download" -o output.mp4
```

#### Upload a File
```bash
curl -X POST "http://localhost:8000/upload/" \
  -F "file=@video.mp4"
```

### Python SDK Example

```python
import requests

# Create client
BASE_URL = "http://localhost:8000"

# Upload video
with open("video.mp4", "rb") as f:
    response = requests.post(f"{BASE_URL}/upload/", files={"file": f})
    file_path = response.json()["file_path"]

# Create job from profile
response = requests.post(
    f"{BASE_URL}/jobs/profile/",
    json={
        "input_file": file_path,
        "profile": "web_optimized"
    }
)
job_id = response.json()["job_id"]

# Monitor progress
import time
while True:
    response = requests.get(f"{BASE_URL}/jobs/{job_id}")
    job = response.json()

    print(f"Status: {job['status']} - Progress: {job['progress']:.1f}%")

    if job['status'] in ['completed', 'failed']:
        break

    time.sleep(2)

# Download result
if job['status'] == 'completed':
    response = requests.get(f"{BASE_URL}/jobs/{job_id}/download")
    with open("output.mp4", "wb") as f:
        f.write(response.content)
```

## Available Profiles

| Profile | Description | Use Case |
|---------|-------------|----------|
| `web_optimized` | H.264, medium preset, CRF 23 | General web streaming |
| `high_quality` | H.264, slow preset, CRF 18 | Archival/high quality |
| `social_media` | 720p, target 50MB | Instagram, Facebook |
| `mobile_optimized` | 480p, target 25MB | Mobile devices |
| `thumbnail` | Generate thumbnail at 1s | Video previews |
| `audio_mp3` | Extract MP3 @ 192kbps | Audio podcasts |
| `audio_aac` | Extract AAC @ 256kbps | High quality audio |
| `preview_gif` | 5s GIF preview | Social media previews |
| `downscale_1080p` | 4K to 1080p | Reduce resolution |
| `trim_30s` | First 30 seconds | Quick previews |

## Available Workflows

| Workflow | Description | Includes |
|----------|-------------|----------|
| `social_media_package` | Complete social media assets | Video, thumbnail, GIF preview |
| `archive_package` | Archival package | High quality video, audio, thumbnail |
| `multi_format` | Multi-format delivery | Web, mobile, audio, thumbnail |

## Configuration

### Environment Variables

Edit `docker-compose.yml` to configure:

```yaml
environment:
  - MAX_WORKERS=4        # Number of concurrent processing workers
  - API_HOST=0.0.0.0    # API host
  - API_PORT=8000       # API port
```

### Custom Profiles

Edit `config/profiles.yaml` to add custom profiles:

```yaml
profiles:
  my_custom_profile:
    operation: transcode
    description: "My custom transcoding profile"
    parameters:
      codec: libx264
      preset: medium
      crf: 23
      audio_codec: aac
```

### Custom Workflows

Add workflows in `config/profiles.yaml`:

```yaml
workflows:
  my_workflow:
    description: "My custom workflow"
    jobs:
      - profile: web_optimized
      - profile: thumbnail
      - profile: audio_mp3
```

## Project Structure

```
FFmpeg-batch/
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
├── main.py                 # Application entry point
├── api.py                  # FastAPI REST API
├── cli.py                  # Command-line interface
├── video_processor.py      # FFmpeg video processing logic
├── job_queue.py            # Job queue and worker management
├── config_manager.py       # Configuration management
├── config/
│   └── profiles.yaml       # Processing profiles and workflows
└── data/
    ├── input/              # Place input videos here
    ├── output/             # Processed videos output here
    └── logs/               # Application logs
```

## API Reference

### Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /jobs/` - Create a job
- `POST /jobs/profile/` - Create job from profile
- `POST /jobs/workflow/` - Create jobs from workflow
- `GET /jobs/` - List all jobs
- `GET /jobs/{job_id}` - Get job details
- `DELETE /jobs/{job_id}` - Cancel a job
- `GET /jobs/{job_id}/download` - Download output file
- `GET /profiles/` - List profiles
- `GET /workflows/` - List workflows
- `POST /upload/` - Upload a file
- `GET /stats/` - Get statistics

Full API documentation: http://localhost:8000/docs

## Performance Tuning

### Worker Configuration

Adjust concurrent workers based on your system:

```yaml
environment:
  - MAX_WORKERS=4  # Increase for more concurrent processing
```

**Guidelines**:
- CPU-bound: Set to number of CPU cores
- IO-bound: Can exceed CPU cores
- Memory: Ensure sufficient RAM (2-4GB per worker)

### FFmpeg Presets

Balance speed vs. quality:

- `ultrafast` - Fastest, lower quality
- `fast` - Good speed, decent quality
- `medium` - Balanced (default)
- `slow` - Better quality, slower
- `veryslow` - Best quality, very slow

## Troubleshooting

### Check Logs
```bash
# View application logs
docker-compose logs -f video-processor

# Check log files
tail -f ./data/logs/processor.log
```

### Common Issues

**No space left on device**:
- Clear old output files from `./data/output`
- Increase Docker disk space allocation

**Processing too slow**:
- Reduce `MAX_WORKERS`
- Use faster FFmpeg presets
- Enable hardware acceleration (requires GPU support)

**Jobs stuck in queue**:
- Check worker status: `python cli.py stats`
- Restart the service: `docker-compose restart`

## Real-World Use Cases

### 1. Content Publishing Platform
```bash
# Process uploaded videos for multi-device delivery
python cli.py workflow /data/input/uploaded_video.mp4 multi_format
```

### 2. Social Media Management
```bash
# Create social media ready package
python cli.py workflow /data/input/content.mp4 social_media_package
```

### 3. Video Archive
```bash
# Archive with high quality and metadata
python cli.py workflow /data/input/original.mp4 archive_package
```

### 4. Podcast Production
```bash
# Extract audio and create preview
python cli.py profile /data/input/episode.mp4 audio_mp3
python cli.py profile /data/input/episode.mp4 thumbnail
```

## Development

### Run without Docker
```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py

# Use CLI
python cli.py profiles
```

### Add New Operations

1. Add method to `VideoProcessor` class in `video_processor.py`
2. Create profile in `config/profiles.yaml`
3. Test using CLI or API

## License

MIT License - feel free to use in your projects!

## Support

- GitHub Issues: Report bugs and request features
- API Documentation: http://localhost:8000/docs
- FFmpeg Documentation: https://ffmpeg.org/documentation.html

## Credits

Built with:
- FFmpeg - Video processing engine
- FastAPI - Modern web framework
- Docker - Containerization
- Python 3.11 - Programming language
