from typing import Optional, Tuple, Literal
from pydantic import BaseModel

class GameMove(BaseModel):
    """Structured output for game moves"""
    angle_delta: int 
    power_delta: int 
    move_actions: Optional[Tuple[Literal['R', 'L'], int]]  # direction and steps
    reasoning: str  # explanation of the move
    confidence: float  # 0.0 to 1.0
