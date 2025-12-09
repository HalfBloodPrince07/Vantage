# Add this to backend/api.py - Indexing endpoint

from fastapi import BackgroundTasks
from pathlib import Path

# Add after other endpoints (around line 1300)

@app.post("/index/directory")
async def index_directory(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Index a directory of documents
    
    Request body:
    {
        "directory_path": "/path/to/documents",
        "recursive": true
    }
    """
    try:
        directory_path = request.get("directory_path")
        recursive = request.get("recursive", True)
        
        if not directory_path:
            raise HTTPException(status_code=400, detail="directory_path is required")
        
        path = Path(directory_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Directory not found: {directory_path}")
        
        if not path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {directory_path}")
        
        # Generate task ID
        task_id = f"index_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start indexing in background
        background_tasks.add_task(
            ingestion_pipeline.process_directory,
            path,
            task_id
        )
        
        logger.info(f"Started indexing directory: {directory_path} (task_id: {task_id})")
        
        return {
            "status": "success",
            "message": f"Indexing started for {directory_path}",
            "task_id": task_id,
            "directory": str(directory_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start indexing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/index/status/{task_id}")
async def get_index_status(task_id: str):
    """Get status of an indexing task"""
    try:
        if task_id in ingestion_status:
            updates = ingestion_status[task_id]
            if updates:
                latest = updates[-1]
                return {
                    "status": "success",
                    "task_id": task_id,
                    "progress": latest,
                    "all_updates": updates
                }
        
        return {
            "status": "not_found",
            "task_id": task_id,
            "message": "Task not found or completed"
        }
    except Exception as e:
        logger.error(f"Failed to get index status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
