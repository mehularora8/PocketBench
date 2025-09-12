# agent.py
import base64, io, json, sys
from typing import Optional, Dict, Any, Union
from PIL import Image
import litellm
from config import BenchmarkConfig
from models import GameMove
import logging
from prompts.move_analysis import move_analysis_prompt
logger = logging.getLogger("PocketBench.agent")


# --- Main Agent Class ---
class PocketTanksAgent:
    """Agent class for analyzing Pocket Tanks screenshots using configurable LLMs."""
    
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.model = config.model
        self.move_schema = GameMove.model_json_schema()

        self._setup_litellm()
    
    def _setup_litellm(self):
        """Configure LiteLLM with the provided config."""
        model_provider = self.config.model_provider.lower()
        if "openai" == model_provider:
            litellm.openai_key = self.config.api_key
        elif "anthropic" == model_provider:
            litellm.anthropic_key = self.config.api_key
        elif "gemini" == model_provider:
            litellm.google_key = self.config.api_key
        else:
            raise ValueError(f"Invalid model provider: {model_provider}")
        
        logger.info(f"LLM Agent initialized with model: {self.config.model}")
    
    def encode_image(self, image: Union[str, Image.Image, bytes]) -> str:
        """
        Encode image to base64 string for API consumption.
        
        Args:
            image: Can be file path, PIL Image, or bytes
            
        Returns:
            Base64 encoded image string
        """
        try:
            if isinstance(image, str):
                # File path
                with open(image, "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode('utf-8')
            elif isinstance(image, Image.Image):
                # PIL Image
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
            elif isinstance(image, bytes):
                # Raw bytes
                return base64.b64encode(image).decode('utf-8')
            else:
                raise ValueError(f"Unsupported image type: {type(image)}")
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            raise
    
    def create_image_message(self, image: Union[str, Image.Image, bytes], 
                           text: str) -> Dict[str, Any]:
        """
        Create a message with both text and image content.
        
        Args:
            image: Image to include
            text: Text prompt
            
        Returns:
            Formatted message for LiteLLM
        """
        base64_image = self.encode_image(image)
        
        return {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": text
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                }
            ]
        }
    
    def get_structured_response(self, messages: list, 
                              response_format: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Get structured JSON response from LLM.
        
        Args:
            messages: List of messages for the conversation
            response_format: JSON schema for structured output
            
        Returns:
            Parsed JSON response
        """
        try:
            # Use response format if provided and model supports it
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1000
            }
            
            if response_format and "gpt" in self.model.lower():
                kwargs["response_format"] = {"type": "json_object"}
            
            response = litellm.completion(**kwargs)
            content = response.choices[0].message.content
            
            # Parse JSON response
            if isinstance(content, str):
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON, attempting extraction: {e}")
                    # Try to extract JSON from response
                    return self._extract_json_from_text(content)
            
            return content

        except Exception as e:
            logger.error(f"Error getting structured response: {e}")
            # Return fallback response
            return {
                "angle_delta": 0,
                "power_delta": 0,
                "move_actions": None,
                "reasoning": f"Error occurred: {str(e)}",
                "confidence": 0.1
            }
    

    def get_move(self, screenshot: Union[str, Image.Image, bytes], context: str) -> GameMove:
        """
        Analyze game screenshot and return next move.
        
        Args:
            screenshot: Game screenshot as file path, PIL Image, or bytes
            
        Returns:
            GameMove object with structured decision
        """
        base_prompt = move_analysis_prompt
        
        # Debug context
        if context and context.strip():
            enhanced_prompt = base_prompt + "\n\n" + context
        else:
            logger.info("Agent using base prompt (no context available)")
            enhanced_prompt = base_prompt

        try:
            # Create message with image and text
            message = self.create_image_message(screenshot, enhanced_prompt)
            messages = [message]
            
            # Get structured response
            response_data = self.get_structured_response(messages, self.move_schema)
            
            # Validate and create GameMove object
            move = GameMove(
                angle_delta=int(response_data.get("angle_delta", 0)),
                power_delta=int(response_data.get("power_delta", 0)),
                move_actions=response_data.get("move_actions"),
                reasoning=str(response_data.get("reasoning", "No reasoning provided")),
                confidence=float(response_data.get("confidence", 0.5))
            )
            
            logger.info(f"Move generated: angle_delta={move.angle_delta}, "
                       f"power_delta={move.power_delta}, move_actions={move.move_actions}, "
                       f"confidence={move.confidence}")
            logger.info(f"Reasoning: {move.reasoning}")
            
            return move
            
        except Exception as e:
            logger.error(f"Error generating move: {e}")
            # Return safe default move
            return GameMove(
                angle_delta=0,
                power_delta=0,
                move_actions=None,
                reasoning=f"Error occurred: {str(e)}",
                confidence=0.1
            )

    
    @staticmethod
    def clean_json(text: str) -> str:
        if not text: return ""

        try:
            # Look for JSON-like patterns
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)
        except:
            pass
        
        return {
            "angle_delta": 0,
            "power_delta": 0, 
            "move_actions": None,
            "reasoning": "Failed to parse response",
            "confidence": 0.1
        }
        
    