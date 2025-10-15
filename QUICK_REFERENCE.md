# Quick Reference Guide

## Starting the Application

```bash
# Quick start (builds and starts everything)
./quickstart.sh

# docker build
docker-compose build

# Manual start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f video-processor
```

## Common CLI Commands

```bash
# All commands run inside the container:
docker-compose exec video-processor python cli.py [command]

# List available profiles
python cli.py profiles

# List available workflows
python cli.py workflows

# Process with a profile
python cli.py profile /data/input/video.mp4 web_optimized

# Execute a workflow
python cli.py workflow /data/input/video.mp4 social_media_package

# Custom operation
python cli.py create /data/input/video.mp4 transcode --params '{"codec":"libx264","crf":23}'

# List all jobs
python cli.py list

# Watch job progress
python cli.py watch <job-id>

# Get statistics
python cli.py stats
```

## Popular Profiles

| Profile | Use Case |
|---------|----------|
| `web_optimized` | General web streaming |
| `social_media` | Social media posts (720p, 50MB) |
| `mobile_optimized` | Mobile devices (480p, 25MB) |
| `thumbnail` | Video preview image |
| `audio_mp3` | Extract audio as MP3 |
| `preview_gif` | 5-second GIF preview |
| `high_quality` | Archival quality video |

## Common API Calls

```bash
# Health check
curl http://localhost:8000/health

# List profiles
curl http://localhost:8000/profiles/

# Create job from profile
curl -X POST http://localhost:8000/jobs/profile/ \
  -H "Content-Type: application/json" \
  -d '{"input_file":"/data/input/video.mp4","profile":"web_optimized"}'

# Get job status
curl http://localhost:8000/jobs/<job-id>

# Download output
curl http://localhost:8000/jobs/<job-id>/download -o output.mp4
```

## File Locations

```
./data/input/    → Place your input videos here
./data/output/   → Find processed videos here
./data/logs/     → Application logs
```

## Quick Operations

### Generate Thumbnail
```bash
python cli.py profile /data/input/video.mp4 thumbnail
```

### Compress for Social Media
```bash
python cli.py profile /data/input/video.mp4 social_media
```

### Extract Audio
```bash
python cli.py profile /data/input/video.mp4 audio_mp3
```

### Create Preview GIF
```bash
python cli.py profile /data/input/video.mp4 preview_gif
```

### Full Social Media Package
```bash
python cli.py workflow /data/input/video.mp4 social_media_package
```

## Troubleshooting

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Restart service
docker-compose restart

# Check queue status
docker-compose exec video-processor python cli.py stats

# Check disk space
df -h ./data/output/
```

## Configuration

Edit `docker-compose.yml`:
```yaml
environment:
  - MAX_WORKERS=4    # Adjust concurrent workers
  - API_PORT=8000    # Change API port
```

## Documentation

- **README.md** - Complete documentation
- **EXAMPLES.md** - Real-world examples
- **PROJECT_SUMMARY.md** - Technical overview
- **http://localhost:8000/docs** - Interactive API docs
