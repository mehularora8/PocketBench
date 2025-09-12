from typing import Optional, Tuple, Literal
from pydantic import BaseModel

class GameMove(BaseModel):
    """Structured output for game moves"""
    angle_delta: int 
    power_delta: int 
    move_actions: Optional[Tuple[Literal['R', 'L'], int]]  # direction and steps
    reasoning: str  # explanation of the move
    confidence: float  # 0.0 to 1.0

class MoveOutcome(BaseModel):
    """Simple move outcome for v0"""
    hit_detected: bool = False
    distance_result: str = "unknown"  # "overshoot", "undershoot", or "hit"
    impact_location: Optional[Tuple[int, int]] = None

class MoveData(BaseModel):
    angle_delta: int
    power_delta: int
    move_actions: Optional[Tuple[Literal['R', 'L'], int]]
    absolute_angle: Optional[int] = None
    absolute_power: Optional[int] = None
