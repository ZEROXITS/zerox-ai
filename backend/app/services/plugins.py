"""
Plugin System - Tools and Extensions for ZeroX AI
"""
import httpx
import json
import re
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from datetime import datetime


class BasePlugin(ABC):
    """Base class for all plugins"""
    
    name: str = "base"
    display_name: str = "Base Plugin"
    description: str = ""
    icon: str = "🔧"
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the plugin with given parameters"""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Return the JSON schema for this plugin's parameters"""
        return {}


class WebSearchPlugin(BasePlugin):
    """Web search using DuckDuckGo (free, no API key needed)"""
    
    name = "web_search"
    display_name = "Web Search"
    description = "Search the web for current information"
    icon = "🔍"
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "")
        max_results = params.get("max_results", 5)
        
        if not query:
            return {"error": "Query is required"}
        
        try:
            # Using DuckDuckGo HTML search (no API key needed)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=10.0
                )
                
                # Parse results (simplified)
                results = []
                # Extract links and titles from HTML
                links = re.findall(r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>', response.text)
                snippets = re.findall(r'<a class="result__snippet"[^>]*>([^<]+)</a>', response.text)
                
                for i, (url, title) in enumerate(links[:max_results]):
                    result = {
                        "title": title.strip(),
                        "url": url,
                        "snippet": snippets[i].strip() if i < len(snippets) else ""
                    }
                    results.append(result)
                
                return {
                    "success": True,
                    "query": query,
                    "results": results,
                    "count": len(results)
                }
                
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "default": 5, "description": "Maximum results"}
            },
            "required": ["query"]
        }


class CalculatorPlugin(BasePlugin):
    """Safe mathematical calculator"""
    
    name = "calculator"
    display_name = "Calculator"
    description = "Perform mathematical calculations"
    icon = "🧮"
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        expression = params.get("expression", "")
        
        if not expression:
            return {"error": "Expression is required"}
        
        try:
            # Safe evaluation - only allow math operations
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                return {"error": "Invalid characters in expression"}
            
            result = eval(expression)
            return {
                "success": True,
                "expression": expression,
                "result": result
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Mathematical expression"}
            },
            "required": ["expression"]
        }


class WeatherPlugin(BasePlugin):
    """Weather information using wttr.in (free, no API key)"""
    
    name = "weather"
    display_name = "Weather"
    description = "Get current weather information"
    icon = "🌤️"
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        location = params.get("location", "")
        
        if not location:
            return {"error": "Location is required"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://wttr.in/{location}?format=j1",
                    timeout=10.0
                )
                data = response.json()
                
                current = data.get("current_condition", [{}])[0]
                
                return {
                    "success": True,
                    "location": location,
                    "temperature_c": current.get("temp_C"),
                    "temperature_f": current.get("temp_F"),
                    "condition": current.get("weatherDesc", [{}])[0].get("value"),
                    "humidity": current.get("humidity"),
                    "wind_kmph": current.get("windspeedKmph"),
                    "feels_like_c": current.get("FeelsLikeC")
                }
                
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name or location"}
            },
            "required": ["location"]
        }


class DateTimePlugin(BasePlugin):
    """Current date and time information"""
    
    name = "datetime"
    display_name = "Date & Time"
    description = "Get current date and time"
    icon = "📅"
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        timezone = params.get("timezone", "UTC")
        
        try:
            from datetime import datetime
            import pytz
            
            try:
                tz = pytz.timezone(timezone)
            except:
                tz = pytz.UTC
            
            now = datetime.now(tz)
            
            return {
                "success": True,
                "timezone": str(tz),
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "datetime": now.isoformat(),
                "day_of_week": now.strftime("%A"),
                "timestamp": int(now.timestamp())
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "timezone": {"type": "string", "default": "UTC", "description": "Timezone"}
            }
        }


class WikipediaPlugin(BasePlugin):
    """Wikipedia search and summary"""
    
    name = "wikipedia"
    display_name = "Wikipedia"
    description = "Search Wikipedia for information"
    icon = "📚"
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "")
        
        if not query:
            return {"error": "Query is required"}
        
        try:
            async with httpx.AsyncClient() as client:
                # Search Wikipedia
                search_response = await client.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "list": "search",
                        "srsearch": query,
                        "format": "json",
                        "srlimit": 1
                    },
                    timeout=10.0
                )
                search_data = search_response.json()
                
                results = search_data.get("query", {}).get("search", [])
                if not results:
                    return {"success": False, "error": "No results found"}
                
                page_title = results[0]["title"]
                
                # Get summary
                summary_response = await client.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "prop": "extracts",
                        "exintro": True,
                        "explaintext": True,
                        "titles": page_title,
                        "format": "json"
                    },
                    timeout=10.0
                )
                summary_data = summary_response.json()
                
                pages = summary_data.get("query", {}).get("pages", {})
                page = list(pages.values())[0]
                
                return {
                    "success": True,
                    "title": page.get("title"),
                    "summary": page.get("extract", "")[:1000],
                    "url": f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
                }
                
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        }


class CodeExecutorPlugin(BasePlugin):
    """Safe Python code execution (sandboxed)"""
    
    name = "code_executor"
    display_name = "Code Executor"
    description = "Execute Python code safely"
    icon = "💻"
    
    ALLOWED_MODULES = {'math', 'random', 'datetime', 'json', 're', 'itertools', 'collections'}
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get("code", "")
        
        if not code:
            return {"error": "Code is required"}
        
        # Security checks
        dangerous_patterns = [
            'import os', 'import sys', 'import subprocess',
            '__import__', 'eval(', 'exec(', 'open(',
            'file(', 'input(', 'raw_input('
        ]
        
        for pattern in dangerous_patterns:
            if pattern in code:
                return {"error": f"Forbidden pattern: {pattern}", "success": False}
        
        try:
            # Create restricted globals
            restricted_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'range': range,
                    'str': str,
                    'int': int,
                    'float': float,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'bool': bool,
                    'sum': sum,
                    'min': min,
                    'max': max,
                    'abs': abs,
                    'round': round,
                    'sorted': sorted,
                    'enumerate': enumerate,
                    'zip': zip,
                    'map': map,
                    'filter': filter,
                }
            }
            
            # Import allowed modules
            import math
            import random
            restricted_globals['math'] = math
            restricted_globals['random'] = random
            
            # Capture output
            import io
            import sys
            
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            local_vars = {}
            exec(code, restricted_globals, local_vars)
            
            output = captured_output.getvalue()
            sys.stdout = old_stdout
            
            return {
                "success": True,
                "output": output,
                "variables": {k: str(v) for k, v in local_vars.items() if not k.startswith('_')}
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"}
            },
            "required": ["code"]
        }


class URLSummarizerPlugin(BasePlugin):
    """Fetch and summarize web page content"""
    
    name = "url_summarizer"
    display_name = "URL Summarizer"
    description = "Fetch and extract content from a URL"
    icon = "🔗"
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        url = params.get("url", "")
        
        if not url:
            return {"error": "URL is required"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=15.0,
                    follow_redirects=True
                )
                
                # Extract text content (simplified)
                html = response.text
                
                # Remove scripts and styles
                html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
                html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
                
                # Extract title
                title_match = re.search(r'<title[^>]*>([^<]+)</title>', html)
                title = title_match.group(1).strip() if title_match else ""
                
                # Extract text
                text = re.sub(r'<[^>]+>', ' ', html)
                text = re.sub(r'\s+', ' ', text).strip()
                
                return {
                    "success": True,
                    "url": url,
                    "title": title,
                    "content": text[:3000],
                    "length": len(text)
                }
                
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"}
            },
            "required": ["url"]
        }


class TranslatorPlugin(BasePlugin):
    """Text translation using LibreTranslate (free)"""
    
    name = "translator"
    display_name = "Translator"
    description = "Translate text between languages"
    icon = "🌐"
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        text = params.get("text", "")
        source = params.get("source", "auto")
        target = params.get("target", "en")
        
        if not text:
            return {"error": "Text is required"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://libretranslate.com/translate",
                    json={
                        "q": text,
                        "source": source,
                        "target": target
                    },
                    timeout=10.0
                )
                data = response.json()
                
                return {
                    "success": True,
                    "original": text,
                    "translated": data.get("translatedText", ""),
                    "source": source,
                    "target": target
                }
                
        except Exception as e:
            # Fallback - return original text
            return {
                "success": False,
                "error": str(e),
                "original": text
            }
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to translate"},
                "source": {"type": "string", "default": "auto", "description": "Source language"},
                "target": {"type": "string", "default": "en", "description": "Target language"}
            },
            "required": ["text"]
        }


# Plugin Registry
class PluginManager:
    """Manages all available plugins"""
    
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self._register_default_plugins()
    
    def _register_default_plugins(self):
        """Register all default plugins"""
        default_plugins = [
            WebSearchPlugin(),
            CalculatorPlugin(),
            WeatherPlugin(),
            DateTimePlugin(),
            WikipediaPlugin(),
            CodeExecutorPlugin(),
            URLSummarizerPlugin(),
            TranslatorPlugin(),
        ]
        
        for plugin in default_plugins:
            self.register(plugin)
    
    def register(self, plugin: BasePlugin):
        """Register a plugin"""
        self.plugins[plugin.name] = plugin
    
    def get(self, name: str) -> Optional[BasePlugin]:
        """Get a plugin by name"""
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all available plugins"""
        return [
            {
                "name": p.name,
                "display_name": p.display_name,
                "description": p.description,
                "icon": p.icon,
                "schema": p.get_schema()
            }
            for p in self.plugins.values()
        ]
    
    async def execute(self, plugin_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a plugin"""
        plugin = self.get(plugin_name)
        if not plugin:
            return {"error": f"Plugin '{plugin_name}' not found"}
        
        return await plugin.execute(params)


# Global plugin manager instance
plugin_manager = PluginManager()
