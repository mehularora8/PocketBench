import cv2
import numpy as np
from collections import deque
from typing import Optional, Tuple
from models import MoveOutcome

class TurnDetector:
    """DEPRECATED - kept for compatibility. Use timeout instead."""
    
    def __init__(self, motion_threshold=1000, stable_frames=20, fps=5):
        # Keep parameters for compatibility
        pass
        
    def is_our_turn(self, frame_bgr):
        """DEPRECATED - always returns True"""
        return True
    
    def is_turn_finished(self, frame_bgr):
        """DEPRECATED - always returns True"""
        return True
    
    def reset(self):
        """DEPRECATED - no-op"""
        pass

class MoveAnalyzer:
    """Analyzes move outcomes using simple computer vision"""
    
    def __init__(self):
        pass
        
    def analyze_move_outcome(self, pre_shot_pil, post_shot_pil) -> MoveOutcome:
        """Simple v0 analysis: hit/miss and overshoot/undershoot"""
        
        # Convert PIL to OpenCV
        pre_cv = cv2.cvtColor(np.array(pre_shot_pil), cv2.COLOR_RGB2BGR)
        post_cv = cv2.cvtColor(np.array(post_shot_pil), cv2.COLOR_RGB2BGR)
        
        outcome = MoveOutcome()
        
        # Find impact location
        impact_pos = self._find_impact_location(pre_cv, post_cv)
        outcome.impact_location = impact_pos
        
        if impact_pos is None:
            return outcome
            
        # Rough opponent position (assume right side)
        height, width = pre_cv.shape[:2]
        opponent_x = int(width * 0.85)  # Assume opponent is at 85% across screen
        
        # Simple distance check
        impact_x = impact_pos[0]
        
        if impact_x > opponent_x + 50:  # 50px tolerance
            outcome.distance_result = "overshoot"
        elif impact_x < opponent_x - 50:
            outcome.distance_result = "undershoot" 
        else:
            # Close to opponent, check for hit
            outcome.hit_detected = self._check_hit_near_opponent(
                pre_cv, post_cv, (opponent_x, int(height * 0.8))
            )
            outcome.distance_result = "hit" if outcome.hit_detected else "near_miss"
            
        return outcome
    
    def _find_impact_location(self, pre_frame, post_frame) -> Optional[Tuple[int, int]]:
        """Find impact location using frame difference"""
        
        # Calculate difference
        diff = cv2.absdiff(pre_frame, post_frame)
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        # Threshold for significant changes
        _, thresh = cv2.threshold(gray_diff, 40, 255, cv2.THRESH_BINARY)
        
        # Find largest changed area
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
            
        # Get largest contour (likely explosion/impact)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Only consider significant changes
        if cv2.contourArea(largest_contour) < 100:
            return None
            
        # Get centroid
        M = cv2.moments(largest_contour)
        if M["m00"] == 0:
            return None
            
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        
        return (cx, cy)
    
    def _check_hit_near_opponent(self, pre_frame, post_frame, opponent_pos) -> bool:
        """Check if there's significant change near opponent position"""
        
        ox, oy = opponent_pos
        margin = 80  # Check 80px around opponent
        
        height, width = pre_frame.shape[:2]
        
        # Ensure bounds
        x1 = max(0, ox - margin)
        x2 = min(width, ox + margin)
        y1 = max(0, oy - margin)
        y2 = min(height, oy + margin)
        
        # Crop regions
        pre_crop = pre_frame[y1:y2, x1:x2]
        post_crop = post_frame[y1:y2, x1:x2]
        
        if pre_crop.size == 0 or post_crop.size == 0:
            return False
            
        # Calculate change in opponent area
        diff = cv2.absdiff(pre_crop, post_crop)
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        # Count changed pixels
        _, thresh = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)
        changed_pixels = cv2.countNonZero(thresh)
        
        # Hit if significant change (tune this threshold)
        return changed_pixels > 300

class GameContextManager:
    """Manages move history and provides context for agent"""
    
    def __init__(self, max_history=5):
        self.move_history = []
        self.outcome_history = []
        self.max_history = max_history
        
    def add_move_result(self, move_data, outcome: MoveOutcome):
        """Add a completed move and its outcome"""
        self.move_history.append(move_data)
        self.outcome_history.append(outcome)
        
        # Keep only recent history
        if len(self.move_history) > self.max_history:
            self.move_history.pop(0)
            self.outcome_history.pop(0)
            
    def get_context_string(self) -> str:
        """Get context string for agent prompt"""
        if not self.outcome_history:
            context = "No previous moves to reference."
            print(f"DEBUG: Context Manager - {context}")
            return context
            
        context_lines = []
        recent_moves = min(3, len(self.outcome_history))
        
        print(f"DEBUG: Context Manager - Building context from {recent_moves} recent moves")
        
        for i in range(recent_moves):
            move = self.move_history[-(i+1)]
            outcome = self.outcome_history[-(i+1)]
            
            # Format move description with absolute values if available
            if hasattr(move, 'absolute_angle') and hasattr(move, 'absolute_power'):
                move_desc = f"angle={move.absolute_angle} (Δ{move.angle_delta:+d}), power={move.absolute_power} (Δ{move.power_delta:+d})"
            else:
                move_desc = f"angle_delta={move.angle_delta}, power_delta={move.power_delta}"
                
            if hasattr(move, 'move_actions') and move.move_actions:
                move_desc += f", move={move.move_actions}"
                
            # Format result
            if outcome.hit_detected:
                result = "HIT"
            else:
                result = f"MISS ({outcome.distance_result})"
                
            context_line = f"Move {recent_moves-i}: {move_desc} → {result}"
            context_lines.append(context_line)
            print(f"DEBUG: Context Manager - Added: {context_line}")
            
        context = "Recent moves:\n" + "\n".join(context_lines)
        print(f"DEBUG: Context Manager - Final context:\n{context}")
        return context
    
    def clear_history(self):
        """Clear all history (e.g., for new game)"""
        self.move_history.clear()
        self.outcome_history.clear()

# Convenience function for easy usage
def create_motion_detector(sensitivity="medium"):
    """Create turn detector with preset sensitivity levels"""
    
    if sensitivity == "low":
        return TurnDetector(motion_threshold=2000, stable_frames=30, fps=3)
    elif sensitivity == "medium":
        return TurnDetector(motion_threshold=1000, stable_frames=20, fps=5)  
    elif sensitivity == "high":
        return TurnDetector(motion_threshold=500, stable_frames=15, fps=8)
    else:
        raise ValueError("Sensitivity must be 'low', 'medium', or 'high'")