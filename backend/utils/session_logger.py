# backend/utils/session_logger.py
"""
Session-based logging utility for capturing ingestion and query processing steps.
Creates a single consolidated daily log file for all sessions.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger


class SessionLogger:
    """
    Creates consolidated session log files capturing:
    - Step-by-step processing logs
    - LLM thinking/reasoning output
    - Timing information
    - Final results
    
    All logs are appended to a single daily TXT file for easy reading.
    """
    
    def __init__(self, session_type: str, session_name: str, base_dir: str = "logs"):
        """
        Initialize session logger.
        
        Args:
            session_type: Type of session (e.g., 'ingestion', 'query')
            session_name: Name/identifier for the session (e.g., filename, query hash)
            base_dir: Base directory for logs
        """
        self.session_type = session_type
        self.session_name = self._sanitize_name(session_name)
        self.base_dir = Path(base_dir)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.date_str = datetime.now().strftime("%Y%m%d")
        
        # Create logs directory
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Single consolidated daily log file (appends all sessions)
        self.log_file = self.base_dir / f"{session_type}_{self.date_str}.log"
        
        self.step_count = 0
        self.start_time = datetime.now()
        
        # Write session header (appends to daily log)
        self._write_session_header()
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize filename for use in file names"""
        invalid_chars = '<>:"/\\|?*'
        sanitized = name
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        return sanitized[:40]
    
    def _write(self, text: str):
        """Append text to log file"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(text)
    
    def _write_session_header(self):
        """Write session header (appends to daily log)"""
        header = f"""
{'='*80}
SESSION: {self.session_name}
{'='*80}
Type: {self.session_type.upper()} | Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
{'─'*80}
"""
        # Append instead of overwrite
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(header)
    
    def log_step(
        self,
        step_name: str,
        status: str = "started",
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None
    ):
        """Log a processing step"""
        self.step_count += 1
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Format step
        step_text = f"\n[{timestamp}] STEP {self.step_count}: {step_name.upper()}\n"
        step_text += f"{'─'*60}\n"
        step_text += f"Status: {status}\n"
        
        if duration_ms:
            step_text += f"Duration: {duration_ms:.0f}ms\n"
        
        if details:
            step_text += "Details:\n"
            for key, value in details.items():
                step_text += f"  • {key}: {value}\n"
        
        step_text += "\n"
        self._write(step_text)
        
        logger.debug(f"[{self.session_name}] Step {self.step_count}: {step_name}")
    
    def log_llm_call(
        self,
        step_name: str,
        prompt: str,
        response: str,
        thinking: Optional[str] = None,
        model: str = "",
        duration_ms: float = 0
    ):
        """Log an LLM call with thinking content"""
        self.step_count += 1
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Format LLM call
        llm_text = f"\n[{timestamp}] STEP {self.step_count}: LLM CALL - {step_name.upper()}\n"
        llm_text += f"{'─'*60}\n"
        llm_text += f"Model: {model}\n"
        llm_text += f"Duration: {duration_ms:.0f}ms\n\n"
        
        # Show thinking if present
        if thinking:
            llm_text += f"🧠 MODEL THINKING:\n"
            llm_text += f"{'─'*40}\n"
            llm_text += f"{thinking}\n"
            llm_text += f"{'─'*40}\n\n"
        
        # Show prompt (truncated)
        llm_text += f"📝 PROMPT (first 500 chars):\n"
        llm_text += f"{prompt[:500]}{'...' if len(prompt) > 500 else ''}\n\n"
        
        # Show response (truncated)
        llm_text += f"📤 RESPONSE (first 1000 chars):\n"
        llm_text += f"{response[:1000]}{'...' if len(response) > 1000 else ''}\n\n"
        
        self._write(llm_text)
        
        if thinking:
            logger.info(f"🧠 [{self.session_name}] Model thinking captured ({len(thinking)} chars)")
    
    def log_thinking(self, thinking_content: str, step_name: str = ""):
        """Log model thinking content separately"""
        if not thinking_content:
            return
            
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        thinking_text = f"\n[{timestamp}] 🧠 MODEL THINKING"
        if step_name:
            thinking_text += f" ({step_name})"
        thinking_text += f"\n{'─'*60}\n"
        thinking_text += f"{thinking_content}\n"
        thinking_text += f"{'─'*60}\n\n"
        
        self._write(thinking_text)
        logger.info(f"🧠 Thinking logged ({len(thinking_content)} chars)")
    
    def log_result(self, result: Dict[str, Any]):
        """Log final result"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        result_text = f"\n{'='*80}\n"
        result_text += f"[{timestamp}] SESSION COMPLETE\n"
        result_text += f"{'='*80}\n"
        result_text += f"Total Steps: {self.step_count}\n"
        result_text += f"Total Time: {elapsed:.2f} seconds\n"
        result_text += f"Status: {result.get('status', 'unknown')}\n\n"
        
        result_text += "Result Summary:\n"
        for key, value in result.items():
            if key != 'status':
                result_text += f"  • {key}: {value}\n"
        
        result_text += f"\n{'='*80}\n"
        
        self._write(result_text)
        logger.info(f"📁 [{self.session_name}] Session log complete: {self.log_file}")
    
    def log_error(self, error: Exception, step_name: str = "unknown"):
        """Log an error"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        error_text = f"\n[{timestamp}] ❌ ERROR in {step_name}\n"
        error_text += f"{'─'*60}\n"
        error_text += f"Type: {type(error).__name__}\n"
        error_text += f"Message: {str(error)}\n"
        error_text += f"{'─'*60}\n\n"
        
        self._write(error_text)
        logger.error(f"[{self.session_name}] Error in {step_name}: {error}")


def create_ingestion_logger(filename: str) -> SessionLogger:
    """Create a session logger for document ingestion"""
    return SessionLogger("ingestion", filename)


def create_query_logger(query: str) -> SessionLogger:
    """Create a session logger for query processing"""
    query_id = query[:30].replace(' ', '_')
    return SessionLogger("query", query_id)
