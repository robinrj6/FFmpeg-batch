from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import logging
import shutil
from pathlib import Path

from video_processor import VideoProcessor
from job_queue import Job, JobQueue, JobStatus
from config_manager import ConfigManager

logger = logging.getLogger(__name__)

app = FastAPI(
    title="FFmpeg Batch Video Processor",
    description="Production-ready batch video processing API powered by FFmpeg",
    version="1.0.0"
)

# Global instances
processor = VideoProcessor()
job_queue = JobQueue(max_workers=4)
config_manager = ConfigManager()


class JobRequest(BaseModel):
    """Request model for creating a job."""
    input_file: str
    operation: str
    parameters: Dict = {}
    output_file: Optional[str] = None


class ProfileJobRequest(BaseModel):
    """Request model for creating a job from a profile."""
    input_file: str
    profile: str
    output_file: Optional[str] = None


class WorkflowJobRequest(BaseModel):
    """Request model for creating jobs from a workflow."""
    input_file: str
    workflow: str


class CustomOperationRequest(BaseModel):
    """Request model for custom FFmpeg operations."""
    input_file: str
    output_file: str
    ffmpeg_args: List[str]


@app.on_event("startup")
async def startup_event():
    """Initialize the application."""
    logger.info("Starting FFmpeg Batch Processor API")
    await job_queue.start(processor)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down FFmpeg Batch Processor API")
    await job_queue.stop()


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "FFmpeg Batch Video Processor",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "queue_stats": job_queue.get_stats()
    }


@app.post("/jobs/", response_model=dict)
async def create_job(request: JobRequest):
    """
    Create a new video processing job.

    Operations: transcode, compress, add_watermark, generate_thumbnail,
                extract_audio, create_gif, concatenate_videos, trim_video
    """
    try:
        # Validate input file exists
        if not Path(request.input_file).exists():
            raise HTTPException(status_code=404, detail="Input file not found")

        # Create job
        job = Job(
            input_file=request.input_file,
            operation=request.operation,
            parameters=request.parameters,
            output_file=request.output_file
        )

        job_id = job_queue.add_job(job)

        return {
            "job_id": job_id,
            "status": "queued",
            "message": f"Job created successfully"
        }

    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/jobs/profile/", response_model=dict)
async def create_job_from_profile(request: ProfileJobRequest):
    """
    Create a job using a predefined profile.

    Profiles: web_optimized, high_quality, social_media, mobile_optimized,
              thumbnail, audio_mp3, preview_gif, etc.
    """
    try:
        # Get profile
        profile = config_manager.get_profile(request.profile)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile '{request.profile}' not found")

        # Validate input file
        if not Path(request.input_file).exists():
            raise HTTPException(status_code=404, detail="Input file not found")

        # Create job from profile
        job = Job(
            input_file=request.input_file,
            operation=profile["operation"],
            parameters=profile["parameters"],
            output_file=request.output_file
        )

        job_id = job_queue.add_job(job)

        return {
            "job_id": job_id,
            "profile": request.profile,
            "status": "queued",
            "message": f"Job created from profile '{request.profile}'"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create job from profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/jobs/workflow/", response_model=dict)
async def create_jobs_from_workflow(request: WorkflowJobRequest):
    """
    Create multiple jobs from a workflow.

    Workflows: social_media_package, archive_package, multi_format
    """
    try:
        # Get workflow
        workflow = config_manager.get_workflow(request.workflow)
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow '{request.workflow}' not found")

        # Validate input file
        if not Path(request.input_file).exists():
            raise HTTPException(status_code=404, detail="Input file not found")

        # Create jobs from workflow
        job_ids = []
        for job_config in workflow["jobs"]:
            profile_name = job_config["profile"]
            profile = config_manager.get_profile(profile_name)

            if not profile:
                logger.warning(f"Skipping unknown profile: {profile_name}")
                continue

            job = Job(
                input_file=request.input_file,
                operation=profile["operation"],
                parameters=profile["parameters"]
            )

            job_id = job_queue.add_job(job)
            job_ids.append({"job_id": job_id, "profile": profile_name})

        return {
            "workflow": request.workflow,
            "jobs": job_ids,
            "total_jobs": len(job_ids),
            "message": f"Created {len(job_ids)} jobs from workflow"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create jobs from workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/", response_model=List[dict])
async def list_jobs(status: Optional[str] = None):
    """List all jobs, optionally filtered by status."""
    try:
        if status:
            try:
                status_enum = JobStatus(status)
                return job_queue.get_jobs_by_status(status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        else:
            return job_queue.get_all_jobs()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}", response_model=dict)
async def get_job(job_id: str):
    """Get job details by ID."""
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job.to_dict()


@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a pending job."""
    if job_queue.cancel_job(job_id):
        return {"message": f"Job {job_id} cancelled"}
    else:
        raise HTTPException(
            status_code=400,
            detail="Job not found or cannot be cancelled (already processing/completed)"
        )


@app.get("/jobs/{job_id}/download")
async def download_output(job_id: str):
    """Download the output file of a completed job."""
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")

    output_path = Path(job.output_file)
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output file not found")

    return FileResponse(
        path=output_path,
        filename=output_path.name,
        media_type="application/octet-stream"
    )


@app.get("/profiles/", response_model=List[dict])
async def list_profiles():
    """List all available processing profiles."""
    return config_manager.list_profiles()


@app.get("/profiles/{profile_name}", response_model=dict)
async def get_profile(profile_name: str):
    """Get details of a specific profile."""
    profile = config_manager.get_profile(profile_name)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {
        "name": profile_name,
        **profile
    }


@app.get("/workflows/", response_model=List[dict])
async def list_workflows():
    """List all available workflows."""
    return config_manager.list_workflows()


@app.get("/workflows/{workflow_name}", response_model=dict)
async def get_workflow(workflow_name: str):
    """Get details of a specific workflow."""
    workflow = config_manager.get_workflow(workflow_name)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {
        "name": workflow_name,
        **workflow
    }


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """Upload a video file for processing."""
    try:
        # Save uploaded file
        upload_dir = Path("/data/input")
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / file.filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "filename": file.filename,
            "file_path": str(file_path),
            "message": "File uploaded successfully"
        }

    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/")
async def get_stats():
    """Get processing statistics."""
    return {
        "queue": job_queue.get_stats(),
        "profiles": len(config_manager.profiles),
        "workflows": len(config_manager.workflows)
    }


@app.get("/video/info/{job_id}")
async def get_video_info(job_id: str):
    """Get video metadata for a job's input file."""
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        info = processor.get_video_info(job.input_file)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
