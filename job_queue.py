import asyncio
import uuid
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from enum import Enum
import json

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job:
    """Represents a video processing job."""

    def __init__(
        self,
        input_file: str,
        operation: str,
        parameters: Dict,
        output_file: Optional[str] = None
    ):
        self.id = str(uuid.uuid4())
        self.input_file = input_file
        self.output_file = output_file or self._generate_output_path(input_file, operation)
        self.operation = operation
        self.parameters = parameters
        self.status = JobStatus.PENDING
        self.progress = 0.0
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.error = None
        self.result = None

    def _generate_output_path(self, input_file: str, operation: str) -> str:
        """Generate output path based on input and operation."""
        input_path = Path(input_file)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if operation == "generate_thumbnail":
            return str(input_path.parent / f"{input_path.stem}_{operation}_{timestamp}.jpg")
        elif operation == "create_gif":
            return str(input_path.parent / f"{input_path.stem}_{operation}_{timestamp}.gif")
        elif operation == "extract_audio":
            audio_format = self.parameters.get("audio_format", "mp3")
            return str(input_path.parent / f"{input_path.stem}_{operation}_{timestamp}.{audio_format}")
        else:
            return str(input_path.parent / f"{input_path.stem}_{operation}_{timestamp}{input_path.suffix}")

    def to_dict(self) -> Dict:
        """Convert job to dictionary."""
        return {
            "id": self.id,
            "input_file": self.input_file,
            "output_file": self.output_file,
            "operation": self.operation,
            "parameters": self.parameters,
            "status": self.status.value,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "result": self.result
        }


class JobQueue:
    """Manages job queue and batch processing."""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.jobs: Dict[str, Job] = {}
        self.queue: asyncio.Queue = asyncio.Queue()
        self.workers: List[asyncio.Task] = []
        self.running = False
        self.stats = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "processing_jobs": 0
        }

    def add_job(self, job: Job) -> str:
        """Add a job to the queue."""
        self.jobs[job.id] = job
        self.queue.put_nowait(job)
        self.stats["total_jobs"] += 1
        logger.info(f"Job {job.id} added to queue: {job.operation} on {job.input_file}")
        return job.id

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self.jobs.get(job_id)

    def get_all_jobs(self) -> List[Dict]:
        """Get all jobs."""
        return [job.to_dict() for job in self.jobs.values()]

    def get_jobs_by_status(self, status: JobStatus) -> List[Dict]:
        """Get jobs filtered by status."""
        return [
            job.to_dict()
            for job in self.jobs.values()
            if job.status == status
        ]

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job."""
        job = self.jobs.get(job_id)
        if job and job.status == JobStatus.PENDING:
            job.status = JobStatus.CANCELLED
            logger.info(f"Job {job_id} cancelled")
            return True
        return False

    async def start(self, processor):
        """Start the job queue workers."""
        if self.running:
            logger.warning("Job queue is already running")
            return

        self.running = True
        logger.info(f"Starting job queue with {self.max_workers} workers")

        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i, processor))
            self.workers.append(worker)

    async def stop(self):
        """Stop the job queue workers."""
        if not self.running:
            return

        logger.info("Stopping job queue...")
        self.running = False

        # Wait for current jobs to complete
        for worker in self.workers:
            worker.cancel()

        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        logger.info("Job queue stopped")

    async def _worker(self, worker_id: int, processor):
        """Worker that processes jobs from the queue."""
        logger.info(f"Worker {worker_id} started")

        while self.running:
            try:
                # Get job from queue with timeout
                job = await asyncio.wait_for(self.queue.get(), timeout=1.0)

                # Check if job was cancelled
                if job.status == JobStatus.CANCELLED:
                    self.queue.task_done()
                    continue

                # Process the job
                await self._process_job(worker_id, job, processor)
                self.queue.task_done()

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")

        logger.info(f"Worker {worker_id} stopped")

    async def _process_job(self, worker_id: int, job: Job, processor):
        """Process a single job."""
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now()
        self.stats["processing_jobs"] += 1

        logger.info(f"Worker {worker_id} processing job {job.id}: {job.operation}")

        try:
            # Progress callback
            def update_progress(progress: float):
                job.progress = progress

            # Execute the operation
            operation_func = getattr(processor, job.operation, None)
            if not operation_func:
                raise ValueError(f"Unknown operation: {job.operation}")

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: operation_func(
                    job.input_file,
                    job.output_file,
                    **job.parameters,
                    progress_callback=update_progress
                )
            )

            if result.get("success"):
                job.status = JobStatus.COMPLETED
                job.progress = 100.0
                job.result = result
                self.stats["completed_jobs"] += 1
                logger.info(f"Job {job.id} completed successfully")
            else:
                raise Exception(result.get("error", "Unknown error"))

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            self.stats["failed_jobs"] += 1
            logger.error(f"Job {job.id} failed: {e}")

        finally:
            job.completed_at = datetime.now()
            self.stats["processing_jobs"] -= 1

    def get_stats(self) -> Dict:
        """Get queue statistics."""
        return {
            **self.stats,
            "queue_size": self.queue.qsize(),
            "active_workers": len(self.workers)
        }

    def save_state(self, filepath: str):
        """Save job queue state to file."""
        state = {
            "jobs": [job.to_dict() for job in self.jobs.values()],
            "stats": self.stats
        }

        with open(filepath, "w") as f:
            json.dump(state, f, indent=2)

        logger.info(f"Queue state saved to {filepath}")

    def load_state(self, filepath: str):
        """Load job queue state from file."""
        try:
            with open(filepath, "r") as f:
                state = json.load(f)

            # Note: This is a simplified restore - in production you'd want to
            # handle re-queuing pending jobs, etc.
            logger.info(f"Queue state loaded from {filepath}")

        except FileNotFoundError:
            logger.info("No saved state found")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
