import logging
import pyautogui
import time
import subprocess
import os
import cv2
import numpy as np
from datetime import datetime
from config import config
from typing import Tuple, Literal, Optional
from turn_detection import TurnDetector, MoveAnalyzer, GameContextManager
from models import MoveData

logger = logging.getLogger(__name__)

class PocketTanksGameController:

    SCAFFOLDING_COORDINATES = {
        "maybe_later": (1101, 674),
        "start_game": (1063, 720),
        "one_player_mode": (867, 269),
        "player_name_continue": (861, 548),
        "difficulty_continue": (861, 548),
        "random_weapons": (862, 577),
    }

    CONTROLS_COORDINATES = {
        "fire": (866, 650),
        "angle_decrease": (1017, 662),
        "angle_increase": (955, 662),
        "power_increase": (1017, 730),
        "power_decrease": (955, 730),
        "move_right": (781, 650),
        "move_left": (710, 650),
        "previous_weapon": (860, 713),
        "next_weapon": (860, 732)
    }

    def __init__(self):
        self.game_process = None
        self.setup_pyautogui()
        
        # Add state management  
        self.turn_detector = TurnDetector(motion_threshold=15000000, stable_frames=20, fps=5)
        self.move_analyzer = MoveAnalyzer()
        self.context_manager = GameContextManager()
        
        # Track absolute angle and power values
        self.current_angle = 60  # Starting angle
        self.current_power = 20  # Starting power
        
        # Move counter and debugging
        self.move_count = 0
        self.debug_folder = "debugging_photos"
        os.makedirs(self.debug_folder, exist_ok=True)
    
    def setup_pyautogui(self):
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

    def force_click(self, x, y, description=""):
        """Force focus then use pyautogui"""
        
        # Force app to front
        subprocess.run(["osascript", "-e", 'tell application "Pocket Tanks" to activate'])
        time.sleep(2)
        
        # Move and click with pyautogui
        pyautogui.moveTo(x, y)
        pyautogui.mouseDown(button='left')
        time.sleep(0.001)
        pyautogui.mouseUp(button='left')

    def force_click_multiple(self, x, y, times, description=""):
        """Force focus then use pyautogui to click multiple times"""
        subprocess.run(["osascript", "-e", 'tell application "Pocket Tanks" to activate'])
        time.sleep(2)
        for _ in range(times):
            pyautogui.moveTo(x, y)
            pyautogui.mouseDown(button='left')
            time.sleep(0.001)
            pyautogui.mouseUp(button='left')
    
    def launch_and_setup_game(self):
        """Launch game and set it up for benchmarking"""
        logger.info("Launching Pocket Tanks...")
        
        # Launch game
        subprocess.run(["open", "-a", "Pocket Tanks"])
        logger.info("Game launched, waiting for 6 seconds to load...")
        time.sleep(3)
        # Navigate to new game setup
        self.setup_new_game()
        
    def setup_new_game(self):
        """Set up game: LLM Agent as Player 1, Random weapons"""
        logger.info("Setting up new game...")

        for key, value in self.SCAFFOLDING_COORDINATES.items():
            logger.info(f"Clicking {key} at {value[0], value[1]}")
            self.force_click(value[0], value[1])
            time.sleep(4)
    
    def take_game_screenshot(self):
        """Capture current game state"""
        screenshot = pyautogui.screenshot(region=config.screenshot_region)
        return screenshot

        
    def execute_turn_with_analysis(self, move_data: MoveData):
        """Enhanced execute_turn that tracks outcomes"""
        self.move_count += 1
        
        # Calculate absolute values before executing
        new_angle = self.current_angle + move_data.angle_delta
        new_power = self.current_power + move_data.power_delta
        
        # Add absolute values to move_data for context
        move_data.absolute_angle = new_angle
        move_data.absolute_power = new_power
        
        logger.info(f"Executing turn {self.move_count}: angle={new_angle} (Δ{move_data.angle_delta:+d}), power={new_power} (Δ{move_data.power_delta:+d})")
        
        # Take pre-shot screenshot
        pre_shot = self.take_game_screenshot()
        self.save_debug_photo(pre_shot, f"move_{self.move_count}_pre_shot")
        
        # Execute the move (existing logic)
        self.set_angle(move_data.angle_delta)
        self.set_power(move_data.power_delta)
        self.perform_move_actions(move_data.move_actions)
        self.fire()
        
        # Update current state
        self.current_angle = new_angle
        self.current_power = new_power
        
        self.wait_for_turn_end()
        
        # Take post-shot screenshot
        post_shot = self.take_game_screenshot()
        self.save_debug_photo(post_shot, f"move_{self.move_count}_post_shot")
        
        # Analyze outcome
        outcome = self.move_analyzer.analyze_move_outcome(pre_shot, post_shot)
        
        # Store for next move
        self.context_manager.add_move_result(move_data, outcome)
        
        logger.info(f"Move {self.move_count} result: {outcome.distance_result}")
        if outcome.hit_detected:
            logger.info("HIT DETECTED!")
        
    def wait_for_turn_end(self):
        """Wait for turn cycle to complete using timeout"""
        logger.info("Waiting 12 seconds for turn cycle to complete...")
        time.sleep(18)
        logger.info("Turn cycle complete - ready for next move!")
        
    def wait_for_turn_end_deprecated(self):
        """DEPRECATED - old turn detection logic kept for reference"""
        logger.info("Waiting for complete turn cycle: our shot → opponent turn → our turn again")
        
        # Step 1: Wait for our underline to disappear (our turn ends)
        logger.info("Waiting for our turn to end...")
        while True:
            screenshot = pyautogui.screenshot(region=config.screenshot_region) 
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            if not self.turn_detector.is_our_turn(screenshot_cv):
                break
            
            time.sleep(0.3)
            
        logger.info("Our turn ended, opponent's turn active...")
        
        # Step 2: Wait for our underline to reappear (our turn starts again)
        logger.info("Waiting for our turn to return...")
        while True:
            screenshot = pyautogui.screenshot(region=config.screenshot_region) 
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            if self.turn_detector.is_our_turn(screenshot_cv):
                break
            
            time.sleep(0.3)
            
        logger.info("Our turn returned - ready for next move!")
        
    def get_context_for_agent(self) -> str:
        """Get context string to pass to agent"""
        context = self.context_manager.get_context_string()
        logger.info(f"Context for agent:\n{context}")
        return context
        
    def save_debug_photo(self, image, name):
        """Save screenshot with timestamp for debugging"""
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = os.path.join(self.debug_folder, filename)
        image.save(filepath)
        logger.info(f"Saved debug photo: {filepath}")
        
    def clear_game_context(self):
        """Clear context for new game"""
        self.context_manager.clear_history()
        self.move_count = 0
        # Reset to starting values
        self.current_angle = 60
        self.current_power = 20
        logger.info("Game context cleared")
    
    def set_angle(self, angle_delta: int):
        """Set cannon angle (0-90 degrees)"""
        # This depends on your game's UI - needs calibration
        if angle_delta > 0:
            self.force_click_multiple(self.CONTROLS_COORDINATES["angle_increase"][0], self.CONTROLS_COORDINATES["angle_increase"][1], angle_delta)
        elif angle_delta < 0:
            self.force_click_multiple(self.CONTROLS_COORDINATES["angle_decrease"][0], self.CONTROLS_COORDINATES["angle_decrease"][1], -angle_delta)
    
    def set_power(self, power_delta: int):
        """Set shot power (0-100)"""
        if power_delta > 0:
            self.force_click_multiple(self.CONTROLS_COORDINATES["power_increase"][0], self.CONTROLS_COORDINATES["power_increase"][1], power_delta)
        elif power_delta < 0:
            self.force_click_multiple(self.CONTROLS_COORDINATES["power_decrease"][0], self.CONTROLS_COORDINATES["power_decrease"][1], -power_delta)

    def perform_move_actions(self, move_actions: Optional[Tuple[Literal['R', 'L'], int]]):
        """Perform move actions, if any."""
        if move_actions:
            if move_actions[0] == "R":
                for _ in range(move_actions[1]):
                    self.force_click(self.CONTROLS_COORDINATES["move_right"][0], self.CONTROLS_COORDINATES["move_right"][1])
                    time.sleep(1)
            elif move_actions[0] == "L":
                for _ in range(move_actions[1]):
                    self.force_click(self.CONTROLS_COORDINATES["move_left"][0], self.CONTROLS_COORDINATES["move_left"][1])
                    time.sleep(1)
    
    def fire(self):
        """Fire the shot"""
        self.force_click(self.CONTROLS_COORDINATES["fire"][0], self.CONTROLS_COORDINATES["fire"][1])
    
    def is_llm_turn(self):
        """Check if it's the LLM agent's turn (Player 1)"""
        # Look for turn indicators, UI elements, etc.
        # For now, simple implementation
        return True  # Placeholder - implement turn detection
    
    def is_game_over(self):
        """Check if current game has ended"""
        # Look for game over screen, victory message, etc.
        return False  # 