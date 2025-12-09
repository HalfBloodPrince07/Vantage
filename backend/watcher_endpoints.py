# File Watcher Endpoints
# Add to backend/api.py

@app.post("/watcher/enable")
async def enable_watcher(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """Enable file watcher for a directory"""
    global watcher
    
    try:
        directory_path = request.get("directory_path")
        if not directory_path:
            # If no path provided, try to get from recent indexing
            directory_path = request.get("directory")
        
        if not directory_path:
            raise HTTPException(status_code=400, detail="directory_path required")
        
        path = Path(directory_path)
        if not path.exists() or not path.is_dir():
            raise HTTPException(status_code=404, detail=f"Directory not found: {directory_path}")
        
        # Stop existing watcher if any
        if watcher:
            watcher.stop()
        
        # Create and start new watcher
        watcher = FileWatcher(config, ingestion_pipeline, opensearch_client)
        background_tasks.add_task(watcher.start, path)
        
        logger.info(f"📂 File watcher enabled for: {directory_path}")
        
        return {
            "status": "success",
            "message": f"File watcher enabled for {directory_path}",
            "directory": str(directory_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable watcher: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/watcher/disable")
async def disable_watcher():
    """Disable file watcher"""
    global watcher
    
    try:
        if watcher:
            watcher.stop()
            watcher = None
            logger.info("📂 File watcher disabled")
            return {"status": "success", "message": "File watcher disabled"}
        else:
            return {"status": "success", "message": "File watcher was not running"}
            
    except Exception as e:
        logger.error(f"Failed to disable watcher: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/watcher/status")
async def get_watcher_status():
    """Get file watcher status"""
    global watcher
    
    is_running = watcher and watcher.is_running if watcher else False
    watched_dir = str(watcher.watched_directory) if watcher and hasattr(watcher, 'watched_directory') else None
    
    return {
        "status": "success",
        "watcher_enabled": is_running,
        "watching_directory": watched_dir
    }
