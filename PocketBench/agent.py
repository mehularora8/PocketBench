# agent.py
import base64, io, json, re, sys
from typing import Optional, Tuple, Literal
from openai import OpenAI
from PIL import Image
from pydantic import BaseModel

client = OpenAI()

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

# --- Helpers ---
def encode_image(img: Image.Image) -> str:
    """PIL → base64 PNG string."""
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def clean_json(text: str) -> str:
    """Remove markdown fences and extract JSON object."""
    if not text: return ""
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    m = re.search(r"\{.*\}", s, flags=re.S)
    return m.group(0) if m else s

def normalize_dir(d: Optional[str]) -> Optional[str]:
    """Normalize direction variants → 'L' or 'R'."""
    if not d: return None
    low = d.strip().lower()
    if low in ("r","right","rightwards","to the right"): return "R"
    if low in ("l","left","leftwards","to the left"): return "L"
    return low.upper() if low.upper() in ("L","R") else None

# --- Main AI Logic ---
def analyze_game(img: Image.Image, model="gpt-4o") -> PocketTanksMoveSchema:
    """Send screenshot → model, parse into schema."""
    payload = [{
        "role":"user","content":[
            {"type":"input_text","text":(
                "Analyze this Pocket Tanks screenshot.\n"
                "Return JSON with: angle_delta, power_delta, move_actions({direction,count}|null), reasoning.\n"
                "Constraints: angle 1-180, power 1-100, max 4 moves.\n"
                "Output JSON ONLY."
            )},
            {"type":"input_image","image_url":f"data:image/png;base64,{encode_image(img)}"}
        ]
    }]
    # Try structured outputs first; fall back to plain text
    try:
        resp = client.responses.create(
            model=model, input=payload, max_output_tokens=500,
            response_format={"type":"json_schema","json_schema":{
                "name":"pocket_tanks_move","schema":PocketTanksMoveSchema.model_json_schema(),"strict":True}}
        )
    except Exception:  
        resp = client.responses.create(model=model,input=payload,max_output_tokens=500)

    # Extract raw text safely
    text = getattr(resp,"output_text",None)
    if not text:
        text = "\n".join(c.get("text","") for o in getattr(resp,"output",[]) for c in o.get("content",[]))
    data = json.loads(clean_json(text or str(resp)))

    # Normalize move direction
    if isinstance(data.get("move_actions"),dict):
        d = normalize_dir(data["move_actions"].get("direction"))
        data["move_actions"] = {"direction":d,"count":data["move_actions"]["count"]} if d else None

    # Validate via Pydantic (v2 then v1)
    try: return PocketTanksMoveSchema.model_validate(data)
    except AttributeError: return PocketTanksMoveSchema.parse_obj(data)

def get_best_move(img: Image.Image) -> Optional[MoveData]:
    """Return cleaned MoveData with capped moves."""
    try:
        move = analyze_game(img)
        # enforce ≤4 moves
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

# --- CLI Entry ---
if __name__=="__main__":
    if len(sys.argv)<2:
        print("Usage: python3 agent.py screenshot.png"); sys.exit(1)
    try:
        img = Image.open(sys.argv[1])
        move = get_best_move(img)
        if move:
            print(json.dumps({
                "angle_delta": move.angle_delta,
                "power_delta": move.power_delta,
                "move_actions": move.move_actions
            }))
        else:
            print("❌ Failed to get move")
    except Exception as e:
        print(f"❌ {e}")
