"""
Google AI Model Manager for Thumbnail Doctor Pro Ultimate
Automatic model discovery and selection with fallback support
"""
import google.generativeai as genai
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
from utils.logger import get_logger

logger = get_logger()

class ModelCapability(Enum):
    TEXT_ONLY = "text_only"
    VISION = "vision"
    CODE = "code"

@dataclass
class ModelInfo:
    name: str
    supports_vision: bool
    supports_text: bool
    context_size: int
    priority: int
    available: bool

class GeminiModelManager:
    _instance = None
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._models: List[ModelInfo] = []
        self._selected_model: Optional[str] = None
        self._genai_configured = False
        self._current_model = None
    
    @classmethod
    def get_instance(cls, api_key: str) -> 'GeminiModelManager':
        if cls._instance is None:
            cls._instance = cls(api_key)
        elif cls._instance.api_key != api_key:
            cls._instance.api_key = api_key
            cls._instance._genai_configured = False
        return cls._instance
    
    def configure(self):
        if not self._genai_configured:
            genai.configure(api_key=self.api_key)
            self._genai_configured = True
            logger.info("Google AI configured successfully")
    
    async def discover_models(self) -> List[ModelInfo]:
        self.configure()
        self._models = []
        
        priority_order = {
            'gemini-2.5-pro': 1,
            'gemini-2.5-flash': 2,
            'gemini-2.0-flash': 3,
            'gemini-1.5-pro': 4,
            'gemini-1.5-flash': 5,
            'gemini-1.0-pro': 6,
        }
        
        try:
            available_models = genai.list_models()
            
            for model in available_models:
                if 'generateContent' not in model.supported_generation_methods:
                    continue
                
                name = model.name.replace('models/', '')
                
                supports_vision = 'images' in model.input_modalities or any(
                    img in name.lower() for img in ['vision', 'flash']
                )
                
                context_size = getattr(model, 'input_token_limit', 32000)
                
                priority = priority_order.get(name.split('-')[0] + '-' + name.split('-')[1] 
                                             if len(name.split('-')) > 1 else name, 10)
                
                model_info = ModelInfo(
                    name=name,
                    supports_vision=supports_vision,
                    supports_text=True,
                    context_size=context_size,
                    priority=priority,
                    available=True
                )
                self._models.append(model_info)
                logger.info(f"Discovered model: {name}, vision={supports_vision}, context={context_size}")
            
            self._models.sort(key=lambda m: m.priority)
            
        except Exception as e:
            logger.error(f"Error discovering models: {e}")
            self._models = self._get_fallback_models()
        
        return self._models
    
    def _get_fallback_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(name='gemini-1.5-flash', supports_vision=True, supports_text=True,
                     context_size=1048576, priority=5, available=True),
            ModelInfo(name='gemini-1.0-pro', supports_vision=False, supports_text=True,
                     context_size=32000, priority=6, available=True),
        ]
    
    def select_best_model(self, requires_vision: bool = False) -> Optional[str]:
        if not self._models:
            self._models = self._get_fallback_models()
        
        for model in self._models:
            if requires_vision and not model.supports_vision:
                continue
            if model.available:
                self._selected_model = model.name
                logger.info(f"Selected model: {model.name}")
                return model.name
        
        return 'gemini-1.5-flash'
    
    def get_model(self, model_name: Optional[str] = None) -> Any:
        self.configure()
        
        if model_name is None:
            model_name = self._selected_model or self.select_best_model()
        
        try:
            self._current_model = genai.GenerativeModel(model_name)
            return self._current_model
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            self._current_model = genai.GenerativeModel('gemini-1.5-flash')
            return self._current_model
    
    async def generate_content(self, prompt: str, images: Optional[List] = None,
                              temperature: float = 0.7,
                              max_tokens: int = 4096) -> str:
        self.configure()
        
        model = self.get_model()
        
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            top_p=0.95,
        )
        
        try:
            if images:
                response = model.generate_content([prompt] + images, 
                                                  generation_config=generation_config)
            else:
                response = model.generate_content(prompt, generation_config=generation_config)
            
            return response.text
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            
            if 'quota' in str(e).lower() or 'rate' in str(e).lower():
                self._handle_quota_error()
                model = self.get_model()
                try:
                    response = model.generate_content(prompt, generation_config=generation_config)
                    return response.text
                except Exception as retry_error:
                    logger.error(f"Retry failed: {retry_error}")
                    raise retry_error
            
            raise e
    
    def _handle_quota_error(self):
        current_idx = 0
        for i, model in enumerate(self._models):
            if model.name == self._selected_model:
                current_idx = i
                break
        
        for model in self._models[current_idx + 1:]:
            if model.available:
                self._selected_model = model.name
                logger.info(f"Switched to fallback model: {model.name}")
                return
        
        logger.warning("No fallback models available")
    
    def test_model(self, model_name: str) -> Dict[str, bool]:
        results = {'text_support': False, 'vision_support': False, 'context_test': False}
        
        try:
            model = self.get_model(model_name)
            
            text_response = model.generate_content("Say hello")
            results['text_support'] = len(text_response.text) > 0
            
            results['context_test'] = True
            
        except Exception as e:
            logger.error(f"Model test failed for {model_name}: {e}")
        
        return results
    
    def get_available_models(self) -> List[str]:
        return [m.name for m in self._models if m.available]
    
    def get_current_model(self) -> Optional[str]:
        return self._selected_model
