import base64
import io
import json
from openai import OpenAI
from typing import Optional, Tuple, Literal
from PIL import Image
from pydantic import BaseModel

client = OpenAI()

class MoveData:
    def __init__(self, angle_delta: int, power_delta: int, move_actions: Optional[Tuple[Literal['R', 'L'], int]]):
        self.angle_delta: int = angle_delta
        self.power_delta: int = power_delta
        self.move_actions: Optional[Tuple[Literal['R', 'L'], int]] = move_actions 

class MoveActionSchema(BaseModel):
    direction: Literal["L", "R"]
    count: int
    
    class Config:
        extra = "forbid"

class PocketTanksMoveSchema(BaseModel):
    angle_delta: int
    power_delta: int
    move_actions: Optional[MoveActionSchema]
    reasoning: str
    
    class Config:
        extra = "forbid"

def encode_image_to_base64(pil_image: Image.Image) -> str:
    buffer = io.BytesIO()
    pil_image.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def analyze_game_screenshot(screenshot: Image.Image) -> PocketTanksMoveSchema:
    base64_image = encode_image_to_base64(screenshot)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user", 
                "content": [
                    {
                        "type": "text",
                        "text": """Analyze this Pocket Tanks game screenshot and determine the optimal move.

Game Rules & Constraints:
- Angle range: 1-180 degrees
- Power range: 1-100
- Tank movement: Maximum 4 moves left or right per turn

Analysis Steps:
1. Identify your tank position (usually the active/highlighted tank)
2. Identify the enemy tank position
3. Analyze terrain, obstacles, and trajectory path
4. Calculate optimal angle and power adjustments needed
5. Determine if repositioning the tank would improve the shot

Provide incremental changes and brief reasoning."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "pocket_tanks_move",
                "schema": PocketTanksMoveSchema.model_json_schema(),
                "strict": True
            }
        },
        temperature=0.1,
        seed=42,
        max_tokens=500
    )
    
    # Show the raw JSON response
    raw_json = response.choices[0].message.content
    print("🔍 RAW JSON RESPONSE:")
    print(json.dumps(json.loads(raw_json), indent=2))
    print()
    
    # Parse and return structured data
    return PocketTanksMoveSchema.model_validate_json(raw_json)

def convert_to_move_data(structured_move: PocketTanksMoveSchema) -> MoveData:
    move_actions = None
    if structured_move.move_actions:
        move_actions = (structured_move.move_actions.direction, structured_move.move_actions.count)
    
    return MoveData(
        angle_delta=structured_move.angle_delta,
        power_delta=structured_move.power_delta,
        move_actions=move_actions
    )

def get_best_move(screenshot: Image.Image) -> Optional[MoveData]:
    try:
        print("🤖 Analyzing game screenshot with AI...")
        
        # Get structured AI analysis
        structured_move = analyze_game_screenshot(screenshot)
        
        print("📊 PARSED STRUCTURED DATA:")
        print(f"  Angle Delta: {structured_move.angle_delta}")
        print(f"  Power Delta: {structured_move.power_delta}")
        print(f"  Move Actions: {structured_move.move_actions}")
        print(f"  Reasoning: {structured_move.reasoning}")
        print()
        
        # Validate move count (1-4 per turn)
        if structured_move.move_actions and structured_move.move_actions.count > 4:
            print(f"⚠️ AI suggested {structured_move.move_actions.count} moves, capping at 4")
            structured_move.move_actions.count = 4
        
        # Convert to MoveData format for game controller
        move_data = convert_to_move_data(structured_move)
        
        print("🎯 FINAL MOVEDATA FOR CONTROLLER:")
        print(f"  angle_delta = {move_data.angle_delta}")
        print(f"  power_delta = {move_data.power_delta}")
        print(f"  move_actions = {move_data.move_actions}")
        print()
        
        return move_data
        
    except Exception as e:
        print(f"❌ Error analyzing screenshot: {e}")
        return None

def test_with_image_file(image_path: str):
    try:
        print(f"=== Testing Pocket Tanks AI with {image_path} ===")
        print()
        
        screenshot = Image.open(image_path)
        print(f"✅ Successfully loaded image: {screenshot.size} pixels")
        print()
        
        move_data = get_best_move(screenshot)
        
        if move_data:
            print("✅ SUCCESS! The AI agent is working correctly.")
            print("   - JSON response received and parsed")
            print("   - Structured data converted to MoveData")
            print("   - Ready for game controller integration")
        else:
            print("❌ Failed to get move data from AI")
            
    except FileNotFoundError:
        print(f"❌ Error: Could not find image file '{image_path}'")
    except Exception as e:
        print(f"❌ Error testing with image: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_with_image_file(sys.argv[1])
    else:
        print("💡 To test with an image file, run:")
        print("   python3 agent.py path/to/your/screenshot.png")