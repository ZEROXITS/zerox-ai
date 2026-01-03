import httpx
from typing import AsyncGenerator, Optional, List, Dict
from app.config import settings
import json

class AIService:
    """Multi-provider AI Service supporting free models"""
    
    PROVIDERS = {
        "groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "models": [
                "llama-3.1-70b-versatile",
                "llama-3.1-8b-instant", 
                "mixtral-8x7b-32768",
                "gemma2-9b-it"
            ]
        },
        "huggingface": {
            "base_url": "https://api-inference.huggingface.co/models",
            "models": [
                "meta-llama/Llama-2-70b-chat-hf",
                "mistralai/Mixtral-8x7B-Instruct-v0.1",
                "google/gemma-7b-it"
            ]
        }
    }
    
    DEFAULT_MODEL = "llama-3.1-70b-versatile"
    DEFAULT_PROVIDER = "groq"
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "groq"):
        self.provider = provider
        self.api_key = api_key or getattr(settings, f"{provider.upper()}_API_KEY", "")
        self.base_url = self.PROVIDERS.get(provider, {}).get("base_url", "")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False
    ) -> AsyncGenerator[str, None] | Dict:
        """Generate chat completion using the configured provider"""
        
        model = model or self.DEFAULT_MODEL
        
        if self.provider == "groq":
            return await self._groq_completion(messages, model, temperature, max_tokens, stream)
        elif self.provider == "huggingface":
            return await self._huggingface_completion(messages, model, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def _groq_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        stream: bool
    ) -> AsyncGenerator[str, None] | Dict:
        """Groq API completion (OpenAI compatible)"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            if stream:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                if chunk["choices"][0]["delta"].get("content"):
                                    yield chunk["choices"][0]["delta"]["content"]
                            except json.JSONDecodeError:
                                continue
            else:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
    
    async def _huggingface_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict:
        """Hugging Face Inference API completion"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Format messages for HF
        prompt = self._format_messages_for_hf(messages)
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "return_full_text": False
            }
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/{model}",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            # Format response to match OpenAI format
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": result[0]["generated_text"] if isinstance(result, list) else result.get("generated_text", "")
                    }
                }],
                "model": model
            }
    
    def _format_messages_for_hf(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for Hugging Face models"""
        formatted = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                formatted += f"<|system|>\n{content}</s>\n"
            elif role == "user":
                formatted += f"<|user|>\n{content}</s>\n"
            elif role == "assistant":
                formatted += f"<|assistant|>\n{content}</s>\n"
        formatted += "<|assistant|>\n"
        return formatted
    
    @classmethod
    def get_available_models(cls, provider: str = None) -> List[str]:
        """Get list of available models for a provider"""
        if provider:
            return cls.PROVIDERS.get(provider, {}).get("models", [])
        
        all_models = []
        for p, config in cls.PROVIDERS.items():
            all_models.extend(config.get("models", []))
        return all_models
    
    @classmethod
    def get_providers(cls) -> List[str]:
        """Get list of available providers"""
        return list(cls.PROVIDERS.keys())


class FreeAIService(AIService):
    """AI Service using completely free tier APIs"""
    
    # Free API endpoints that don't require keys
    FREE_ENDPOINTS = {
        "ollama": "http://localhost:11434/api",  # Local Ollama
    }
    
    async def free_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama2"
    ) -> AsyncGenerator[str, None]:
        """Use local Ollama for completely free inference"""
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": model,
                "messages": messages,
                "stream": True
            }
            
            try:
                async with client.stream(
                    "POST",
                    f"{self.FREE_ENDPOINTS['ollama']}/chat",
                    json=payload
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if data.get("message", {}).get("content"):
                                    yield data["message"]["content"]
                            except json.JSONDecodeError:
                                continue
            except httpx.ConnectError:
                yield "Error: Ollama is not running. Please start Ollama locally or use a cloud provider."
