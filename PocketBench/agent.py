# agent.py
import base64, io, json, re, sys
from typing import Optional, Tuple, Literal, Dict, Any
from dataclasses import dataclass
from PIL import Image
from pydantic import BaseModel
import litellm

# --- Configuration ---
@dataclass
class ModelConfig:
    """Configuration for LiteLLM model calls."""
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 500
    timeout: int = 30
    extra_params: Optional[Dict[str, Any]] = None

# --- Data Structures ---
class MoveData:
    """Lightweight container for processed move info."""
    def __init__(self, angle_delta: int, power_delta: int, move_actions: Optional[Tuple[Literal["R","L"], int]]):
        self.angle_delta = angle_delta
        self.power_delta = power_delta
        self.move_actions = move_actions

class MoveActionSchema(BaseModel):
    direction: Literal["L","R"]
    count: int
    class Config: extra = "forbid"

class PocketTanksMoveSchema(BaseModel):
    angle_delta: int
    power_delta: int
    move_actions: Optional[MoveActionSchema]
    reasoning: str
    class Config: extra = "forbid"

# --- Main Agent Class ---
class PocketTanksAgent:
    """Agent class for analyzing Pocket Tanks screenshots using configurable LLMs."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self._setup_litellm()
    
    def _setup_litellm(self):
        """Configure LiteLLM with the provided config."""
        if self.config.api_key:
            # Set API key in environment or litellm config
            import os
            if "openai" in self.config.model.lower():
                os.environ["OPENAI_API_KEY"] = self.config.api_key
            elif "anthropic" in self.config.model.lower() or "claude" in self.config.model.lower():
                os.environ["ANTHROPIC_API_KEY"] = self.config.api_key
            elif "gemini" in self.config.model.lower() or "google" in self.config.model.lower():
                os.environ["GOOGLE_API_KEY"] = self.config.api_key
            # Add more providers as needed
        
        if self.config.base_url:
            litellm.api_base = self.config.base_url
        
        # Set timeout
        litellm.request_timeout = self.config.timeout
    
    @staticmethod
    def encode_image(img: Image.Image) -> str:
        """PIL → base64 PNG string."""
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    
    @staticmethod
    def clean_json(text: str) -> str:
        """Remove markdown fences and extract JSON object."""
        if not text: return ""
        s = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
        m = re.search(r"\{.*\}", s, flags=re.S)
        return m.group(0) if m else s
    
    @staticmethod
    def normalize_dir(d: Optional[str]) -> Optional[str]:
        """Normalize direction variants → 'L' or 'R'."""
        if not d: return None
        low = d.strip().lower()
        if low in ("r","right","rightwards","to the right"): return "R"
        if low in ("l","left","leftwards","to the left"): return "L"
        return low.upper() if low.upper() in ("L","R") else None
    
    def analyze_game(self, img: Image.Image) -> PocketTanksMoveSchema:
        """Send screenshot → model, parse into schema."""
        image_data = f"data:image/png;base64,{self.encode_image(img)}"
        
        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Analyze this Pocket Tanks screenshot.\n"
                        "Return JSON with: angle_delta, power_delta, move_actions({direction,count}|null), reasoning.\n"
                        "Constraints: angle 1-180, power 1-100, max 4 moves.\n"
                        "Output JSON ONLY."
                    )
                },
                {
                    "type": "image_url",
                    "image_url": {"url": image_data}
                }
            ]
        }]
        
        # Prepare call parameters
        call_params = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        
        # Add extra parameters if provided
        if self.config.extra_params:
            call_params.update(self.config.extra_params)
        
        # Try structured outputs for supported models, fall back to regular completion
        try:
            # Check if model supports structured outputs (mainly OpenAI models)
            if "gpt-4" in self.config.model or "gpt-3.5" in self.config.model:
                try:
                    call_params["response_format"] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "pocket_tanks_move",
                            "schema": PocketTanksMoveSchema.model_json_schema(),
                            "strict": True
                        }
                    }
                except: 
                    # Fallback if structured outputs not supported
                    call_params["response_format"] = {"type": "json_object"}
            
            response = litellm.completion(**call_params)
            
        except Exception as e:
            print(f"⚠️  Structured output failed, falling back to regular completion: {e}")
            # Remove response_format and try again
            call_params.pop("response_format", None)
            response = litellm.completion(**call_params)
        
        # Extract response text
        text = response.choices[0].message.content
        
        # Parse JSON
        try:
            data = json.loads(self.clean_json(text))
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"Raw response: {text}")
            raise
        
        # Normalize move direction
        if isinstance(data.get("move_actions"), dict):
            d = self.normalize_dir(data["move_actions"].get("direction"))
            data["move_actions"] = {"direction": d, "count": data["move_actions"]["count"]} if d else None
        
        # Validate via Pydantic
        try:
            return PocketTanksMoveSchema.model_validate(data)
        except AttributeError:
            return PocketTanksMoveSchema.parse_obj(data)
    
    def get_best_move(self, img: Image.Image) -> Optional[MoveData]:
        """Return cleaned MoveData with capped moves."""
        try:
            move = self.analyze_game(img)
            # Enforce ≤4 moves
            if move.move_actions and move.move_actions.count > 4:
                move.move_actions.count = 4
            return MoveData(
                move.angle_delta,
                move.power_delta,
                (move.move_actions.direction, move.move_actions.count) if move.move_actions else None
            )
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

# --- Convenience Functions for Common Configs ---
class ModelConfigs:
    """Pre-defined configurations for common models."""
    
    @staticmethod
    def openai_gpt4o(api_key: str, temperature: float = 0.1) -> ModelConfig:
        return ModelConfig(
            model="gpt-4o",
            api_key=api_key,
            temperature=temperature
        )
    
    @staticmethod
    def openai_gpt4_turbo(api_key: str, temperature: float = 0.1) -> ModelConfig:
        return ModelConfig(
            model="gpt-4-turbo",
            api_key=api_key,
            temperature=temperature
        )
    
    @staticmethod
    def anthropic_claude_3_5_sonnet(api_key: str, temperature: float = 0.1) -> ModelConfig:
        return ModelConfig(
            model="claude-3-5-sonnet-20241022",
            api_key=api_key,
            temperature=temperature
        )
    
    @staticmethod
    def google_gemini_pro(api_key: str, temperature: float = 0.1) -> ModelConfig:
        return ModelConfig(
            model="gemini-pro-vision",
            api_key=api_key,
            temperature=temperature
        )
    
    @staticmethod
    def custom_model(model_name: str, api_key: str = None, base_url: str = None, **kwargs) -> ModelConfig:
        return ModelConfig(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            **kwargs
        )

# --- CLI Entry ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 agent.py screenshot.png [model_name] [api_key]")
        sys.exit(1)
    
    # Default to GPT-4o if no model specified
    model_name = sys.argv[2] if len(sys.argv) > 2 else "gpt-4o"
    api_key = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Create config
    if model_name == "gpt-4o":
        config = ModelConfigs.openai_gpt4o(api_key)
    elif model_name == "claude-3-5-sonnet":
        config = ModelConfigs.anthropic_claude_3_5_sonnet(api_key)
    elif model_name == "gemini-pro":
        config = ModelConfigs.google_gemini_pro(api_key)
    else:
        config = ModelConfigs.custom_model(model_name, api_key)
    
    try:
        img = Image.open(sys.argv[1])
        agent = PocketTanksAgent(config)
        move = agent.get_best_move(img)
        
        if move:
            print(json.dumps({
                "model": config.model,
                "angle_delta": move.angle_delta,
                "power_delta": move.power_delta,
                "move_actions": move.move_actions
            }))
        else:
            print("❌ Failed to get move")
    except Exception as e:
        print(f"❌ {e}")