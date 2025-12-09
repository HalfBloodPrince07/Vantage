# File upload endpoint for SettingsPanel
# Add this BEFORE the shutdown event in api.py

from fastapi import File, UploadFile
import tempfile
import shutil

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and index a single file
    """
    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            # Save uploaded file
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = Path(tmp_file.name)
        
        logger.info(f"📤 Uploaded file: {file.filename}")
        
        # Process the file through ingestion pipeline
        result = await ingestion_pipeline.process_file(tmp_path)
        
        # Clean up temp file
        tmp_path.unlink()
        
        if result:
            return {
                "status": "success",
                "message": f"Successfully indexed {file.filename}",
                "filename": file.filename
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to index {file.filename}"
            }
            
    except Exception as e:
        logger.error(f"Upload error for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-batch")
async def upload_batch(files: List[UploadFile] = File(...), background_tasks: BackgroundTasks = None):
    """
    Upload and index multiple files at once
    Returns immediately and processes in background
    """
    try:
        task_id = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize status
        ingestion_status[task_id] = []
        ingestion_status[task_id].append({
            "task_id": task_id,
            "status": "started",
            "message": f"Starting upload of {len(files)} files",
            "total_files": len(files),
            "processed": 0
        })
        
        # Process files in background
        if background_tasks:
            background_tasks.add_task(process_uploaded_files, files, task_id)
        else:
            await process_uploaded_files(files, task_id)
        
        return {
            "status": "success",
            "message": f"Started processing {len(files)} files",
            "task_id": task_id,
            "file_count": len(files)
        }
        
    except Exception as e:
        logger.error(f"Batch upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_uploaded_files(files: List[UploadFile], task_id: str):
    """Process uploaded files and update status"""
    try:
        total = len(files)
        processed = 0
        
        for file in files:
            try:
                # Create temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
                    # Reset file pointer
                    await file.seek(0)
                    # Save uploaded file
                    shutil.copyfileobj(file.file, tmp_file)
                    tmp_path = Path(tmp_file.name)
                
                logger.info(f"📤 Processing uploaded file: {file.filename}")
                
                # Process through ingestion pipeline
                result = await ingestion_pipeline.process_file(tmp_path)
                
                # Clean up temp file
                tmp_path.unlink()
                
                processed += 1
                
                # Update status
                ingestion_status[task_id].append({
                    "task_id": task_id,
                    "status": "indexing",
                    "message": f"Processed {file.filename}",
                    "total_files": total,
                    "processed": processed
                })
                
            except Exception as e:
                logger.error(f"Failed to process {file.filename}: {e}")
                continue
        
        # Mark as complete
        ingestion_status[task_id].append({
            "task_id": task_id,
            "status": "completed",
            "message": f"Successfully processed {processed}/{total} files",
            "total_files": total,
            "processed": processed
        })
        
    except Exception as e:
        logger.error(f"Batch process error: {e}")
        ingestion_status[task_id].append({
            "task_id": task_id,
            "status": "error",
            "message": str(e)
        })
