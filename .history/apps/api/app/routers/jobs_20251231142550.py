"""
Jobs API endpoints.

Provides ability to trigger background tasks and check their status.
"""

import logging

from celery import Celery
from celery.result import AsyncResult
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Create Celery client (connects to broker)
celery_app = Celery("app-idea-miner", broker="redis://redis:6379/0", backend="redis://redis:6379/1")


class IngestJobRequest(BaseModel):
    """Request model for ingestion job."""

    source: str | None = None
    force: bool = False


class ReclusterJobRequest(BaseModel):
    """Request model for reclustering job."""

    min_quality: float = 0.3
    min_cluster_size: int = 2
    force: bool = True


@router.post("/ingest")
async def trigger_ingestion(request: IngestJobRequest = Body(default=IngestJobRequest())):
    """
    Trigger a new ingestion job.

    Fetches posts from configured sources and processes them.
    """
    logger.info(f"Triggering ingestion job (source={request.source}, force={request.force})")

    # Trigger the appropriate ingestion task
    if request.source:
        # Source-specific ingestion (not implemented yet)
        raise HTTPException(status_code=400, detail="Source-specific ingestion not yet implemented")
    else:
        # Trigger RSS feed fetching task by name
        task = celery_app.send_task("apps.worker.tasks.ingestion.fetch_rss_feeds")

    logger.info(f"Ingestion job queued: {task.id}")

    return {
        "job_id": task.id,
        "status": "queued",
        "estimated_duration": "30s",
        "message": "Ingestion job started successfully",
    }


@router.post("/recluster")
async def trigger_reclustering(request: ReclusterJobRequest = Body(default=ReclusterJobRequest())):
    """
    Trigger re-clustering of all ideas.

    Deletes existing clusters and re-runs clustering from scratch.
    """
    logger.info(
        f"Triggering reclustering job "
        f"(min_quality={request.min_quality}, min_cluster_size={request.min_cluster_size}, force={request.force})"
    )

    # Trigger clustering task by name with parameters
    task = celery_app.send_task(
        "apps.worker.tasks.clustering.run_clustering",
        kwargs={
            "min_quality": request.min_quality,
            "min_cluster_size": request.min_cluster_size,
            "recreate_clusters": request.force,
        },
    )

    logger.info(f"Reclustering job queued: {task.id}")

    return {
        "job_id": task.id,
        "status": "queued",
        "estimated_duration": "60s",
        "message": "Reclustering job started successfully",
    }


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    """
    Check the status of a background job.

    Returns job status, progress, and results (if completed).
    """
    try:
        # Get task result from Celery
        result = AsyncResult(job_id, app=celery_app)

        # Determine status
        if result.state == "PENDING":
            status = "pending"
            response = {
                "job_id": job_id,
                "status": status,
                "message": "Job is waiting to be executed",
            }
        elif result.state == "STARTED":
            status = "running"
            response = {"job_id": job_id, "status": status, "message": "Job is currently running"}
        elif result.state == "SUCCESS":
            status = "completed"
            response = {
                "job_id": job_id,
                "status": status,
                "result": result.result,
                "message": "Job completed successfully",
            }
        elif result.state == "FAILURE":
            status = "failed"
            response = {
                "job_id": job_id,
                "status": status,
                "error": str(result.info),
                "message": "Job failed with an error",
            }
        elif result.state == "RETRY":
            status = "retrying"
            response = {
                "job_id": job_id,
                "status": status,
                "message": "Job is being retried after a failure",
            }
        else:
            status = result.state.lower()
            response = {
                "job_id": job_id,
                "status": status,
                "message": f"Job status: {result.state}",
            }

        logger.info(f"Job {job_id} status: {status}")

        return response

    except Exception as e:
        logger.error(f"Error checking job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check job status: {str(e)}")


@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a running or pending job.

    Note: Some jobs may not be immediately cancellable if already started.
    """
    try:
        result = AsyncResult(job_id, app=celery_app)

        # Revoke the task
        result.revoke(terminate=True)

        logger.info(f"Job {job_id} cancelled")

        return {"job_id": job_id, "status": "cancelled", "message": "Job cancellation requested"}

    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")
