"""
LLM client module for Ollama integration.
Handles communication with local Llama 3.1 model via Ollama.
"""

import logging
from typing import Optional, Generator
import ollama
from ollama import Client

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for interacting with Ollama-hosted LLM models.
    Supports both standard and streaming response generation.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:latest", timeout: int = 120):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Base URL for Ollama server
            model: Model name to use for generation
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        
        try:
            logger.info(f"Initializing Ollama client with model: {model}")
            self.client = Client(host=base_url)
            
            # Test connection
            self._test_connection()
            
            logger.info("Ollama client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {str(e)}")
            raise Exception(f"Ollama client initialization failed: {str(e)}")
    
    def _test_connection(self) -> bool:
        """
        Test connection to Ollama server.
        
        Returns:
            True if connection successful
            
        Raises:
            Exception: If connection fails
        """
        try:
            # Try to list models to verify connection
            models = self.client.list()
            
            # Handle different response formats
            if hasattr(models, 'models'):
                model_list = models.models
            elif isinstance(models, dict):
                model_list = models.get('models', [])
            else:
                model_list = []
            
            logger.info(f"Connected to Ollama. Available models: {len(model_list)}")
            
            # Check if our model is available
            model_names = []
            for m in model_list:
                if hasattr(m, 'model'):
                    model_names.append(m.model)
                elif isinstance(m, dict) and 'name' in m:
                    model_names.append(m['name'])
                elif hasattr(m, 'name'):
                    model_names.append(m.name)
            
            if model_names and self.model not in model_names:
                logger.warning(
                    f"Model {self.model} not found in available models. "
                    f"Available: {model_names}. "
                    f"You may need to run: ollama pull {self.model}"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Ollama connection test failed: {str(e)}")
            raise Exception(
                f"Cannot connect to Ollama at {self.base_url}. "
                f"Make sure Ollama is running. Error: {str(e)}"
            )
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text completion using the LLM.
        
        Args:
            prompt: User prompt/question
            system_prompt: Optional system prompt to set context
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        if not prompt or not prompt.strip():
            logger.warning("Attempted to generate with empty prompt")
            return ""
        
        try:
            logger.info(f"Generating response for prompt length: {len(prompt)}")
            
            # Build messages
            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Build options
            options = {
                "temperature": temperature,
            }
            if max_tokens:
                options["num_predict"] = max_tokens
            
            # Generate response
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options=options,
                stream=False
            )
            
            # Extract response text
            answer = response.get("message", {}).get("content", "")
            
            logger.info(f"Generated response length: {len(answer)}")
            return answer
            
        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            raise Exception(f"LLM generation failed: {str(e)}")
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Generator[str, None, None]:
        """
        Generate text completion with streaming response.
        
        Args:
            prompt: User prompt/question
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Yields:
            Chunks of generated text
        """
        if not prompt or not prompt.strip():
            logger.warning("Attempted to generate with empty prompt")
            return
        
        try:
            logger.info(f"Starting streaming generation for prompt length: {len(prompt)}")
            
            # Build messages
            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Build options
            options = {
                "temperature": temperature,
            }
            if max_tokens:
                options["num_predict"] = max_tokens
            
            # Stream response
            stream = self.client.chat(
                model=self.model,
                messages=messages,
                options=options,
                stream=True
            )
            
            for chunk in stream:
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content
            
            logger.info("Streaming generation completed")
            
        except Exception as e:
            logger.error(f"Failed to stream response: {str(e)}")
            raise Exception(f"LLM streaming failed: {str(e)}")
    
    def is_available(self) -> bool:
        """
        Check if Ollama server is available and responsive.
        
        Returns:
            True if available, False otherwise
        """
        try:
            self.client.list()
            return True
        except Exception:
            return False
    
    def get_model_info(self) -> dict:
        """
        Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        try:
            models = self.client.list()
            
            # Handle different response formats
            if hasattr(models, 'models'):
                model_list = models.models
            elif isinstance(models, dict):
                model_list = models.get('models', [])
            else:
                model_list = []
            
            for model in model_list:
                model_name = None
                if hasattr(model, 'model'):
                    model_name = model.model
                elif isinstance(model, dict) and 'name' in model:
                    model_name = model['name']
                elif hasattr(model, 'name'):
                    model_name = model.name
                
                if model_name == self.model:
                    return {
                        "name": model_name,
                        "size": getattr(model, 'size', 'unknown') if hasattr(model, 'size') else model.get('size', 'unknown'),
                        "modified": getattr(model, 'modified_at', 'unknown') if hasattr(model, 'modified_at') else model.get('modified_at', 'unknown')
                    }
            
            return {"name": self.model, "status": "not_found"}
            
        except Exception as e:
            logger.error(f"Failed to get model info: {str(e)}")
            return {"error": str(e)}
