# backend/utils/model_manager.py
"""
Ollama Model Manager - Dynamic Model Loading/Unloading

Manages multiple Ollama models with automatic loading/unloading
to optimize VRAM usage for dual-model architecture.
"""

import httpx
import asyncio
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from loguru import logger


class OllamaModelManager:
    """
    Manages dynamic loading and unloading of Ollama models
    
    Features:
    - Track loaded models
    - Auto-load models on demand
    - Auto-unload inactive models
    - VRAM optimization
    """
    
    def __init__(self, base_url: str, config: Dict):
        self.base_url = base_url
        self.config = config
        
        # Track model states
        self.loaded_models: Dict[str, datetime] = {}
        self._loading_locks: Dict[str, asyncio.Lock] = {}
        
        # Config settings
        self.auto_unload = config.get('model_management', {}).get('auto_unload', True)
        self.keep_both_loaded = config.get('model_management', {}).get('keep_both_loaded', False)
        self.unload_after_seconds = config.get('model_management', {}).get('unload_after_seconds', 300)
        
        logger.info(f"🤖 Model Manager initialized (auto_unload={self.auto_unload}, keep_both={self.keep_both_loaded})")
    
    async def ensure_model_loaded(self, model_name: str, model_type: str = "text") -> bool:
        """
        Ensure a model is loaded and ready to use
        
        Args:
            model_name: Name of the model to load
            model_type: Type of model ("text" or "vision")
            
        Returns:
            True if model is loaded and ready
        """
        # Check if already loaded
        if model_name in self.loaded_models:
            self.loaded_models[model_name] = datetime.now()
            logger.debug(f"✅ Model {model_name} already loaded")
            return True
        
        # Get or create lock for this model
        if model_name not in self._loading_locks:
            self._loading_locks[model_name] = asyncio.Lock()
        
        async with self._loading_locks[model_name]:
            # Double-check after acquiring lock
            if model_name in self.loaded_models:
                self.loaded_models[model_name] = datetime.now()
                return True
            
            logger.info(f"📥 Loading model: {model_name} ({model_type})")
            
            # If auto_unload and not keep_both, unload other models first
            if self.auto_unload and not self.keep_both_loaded:
                await self._unload_other_models(exclude=model_name)
            
            # Load the model by making a simple request
            success = await self._load_model(model_name)
            
            if success:
                self.loaded_models[model_name] = datetime.now()
                logger.info(f"✅ Model {model_name} loaded successfully")
                return True
            else:
                logger.error(f"❌ Failed to load model {model_name}")
                return False
    
    async def _load_model(self, model_name: str) -> bool:
        """
        Load a model by making a simple generation request
        
        This triggers Ollama to load the model into VRAM
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": "Hi",
                        "stream": False,
                        "options": {"num_predict": 1}
                    }
                )
                
                if response.status_code == 200:
                    return True
                else:
                    logger.error(f"Model load failed with status {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            return False
    
    async def _unload_other_models(self, exclude: str):
        """
        Unload all models except the excluded one
        
        Args:
            exclude: Model name to keep loaded
        """
        models_to_unload = [m for m in self.loaded_models.keys() if m != exclude]
        
        for model_name in models_to_unload:
            await self.unload_model(model_name)
    
    async def unload_model(self, model_name: str) -> bool:
        """
        Unload a model from VRAM
        
        Note: Ollama doesn't have explicit unload API,
        so we remove from tracking. Ollama will manage VRAM automatically.
        
        Args:
            model_name: Model to unload
            
        Returns:
            True if unloaded
        """
        if model_name in self.loaded_models:
            del self.loaded_models[model_name]
            logger.info(f"📤 Model {model_name} unloaded from tracking")
            return True
        return False
    
    async def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded models"""
        return list(self.loaded_models.keys())
    
    async def cleanup_inactive_models(self):
        """
        Unload models that have been inactive for too long
        
        This is called periodically if auto_unload is enabled
        """
        if not self.auto_unload or self.keep_both_loaded:
            return
        
        now = datetime.now()
        timeout = timedelta(seconds=self.unload_after_seconds)
        
        models_to_unload = []
        for model_name, last_used in self.loaded_models.items():
            if now - last_used > timeout:
                models_to_unload.append(model_name)
        
        for model_name in models_to_unload:
            logger.info(f"🧹 Auto-unloading inactive model: {model_name}")
            await self.unload_model(model_name)
    
    def update_last_used(self, model_name: str):
        """Update the last-used timestamp for a model"""
        if model_name in self.loaded_models:
            self.loaded_models[model_name] = datetime.now()


# Global singleton instance
_model_manager: Optional[OllamaModelManager] = None


def get_model_manager(base_url: str = None, config: Dict = None) -> OllamaModelManager:
    """
    Get or create the global model manager instance
    
    Args:
        base_url: Ollama base URL (required for first call)
        config: Configuration dict (required for first call)
        
    Returns:
        Model manager instance
    """
    global _model_manager
    
    if _model_manager is None:
        if base_url is None or config is None:
            raise ValueError("base_url and config required for first initialization")
        _model_manager = OllamaModelManager(base_url, config)
    
    return _model_manager
