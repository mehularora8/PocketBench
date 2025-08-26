import pyautogui
import time
import subprocess
from config import config
from typing import Tuple, Literal, Optional

class MoveData:
    def __init__(self, angle_delta: int, power_delta: int, move_actions: Optional[Tuple[Literal['R', 'L'], int]]):
        self.angle_delta: int = angle_delta
        self.power_delta: int = power_delta
        # R = move right, L = move left
        self.move_actions: Optional[Tuple[Literal['R', 'L'], int]] = move_actions 

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
        "angle_increase": (1017, 662),
        "angle_decrease": (955, 662),
        "power_increase": (1017, 730),
        "power_decrease": (955, 730),
        "move_right": (781, 650),
        "move_left": (710, 650),
        "previous_weapon": (860, 713),
        "next_weapon": (860, 732)
    }

    def __init__(self, config):
        self.config = config
        self.game_process = None
        self.setup_pyautogui()
    
    def setup_pyautogui(self):
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

    def force_click(self, x, y, description=""):
        """Force focus then use pyautogui"""
        print(f"Forcing focus click for {description} at ({x}, {y})")
        
        # Force app to front
        subprocess.run(["osascript", "-e", 'tell application "Pocket Tanks" to activate'])
        time.sleep(2)
        
        # Move and click with pyautogui
        pyautogui.moveTo(x, y)
        time.sleep(0.1)
        pyautogui.mouseDown(button='left')
        time.sleep(0.05)
        pyautogui.mouseUp(button='left')
    
    def launch_and_setup_game(self):
        """Launch game and set it up for benchmarking"""
        print("Launching Pocket Tanks...")
        
        # Launch game
        subprocess.run(["open", "-a", "Pocket Tanks"])
        print("Game launched, waiting for 6 seconds to load...")
        time.sleep(6)
        # Navigate to new game setup
        self.setup_new_game()
        
    def setup_new_game(self):
        """Set up game: LLM Agent as Player 1, Random weapons"""
        print("Setting up new game...")

        for key, value in self.SCAFFOLDING_COORDINATES.items():
            print(f"Clicking {key} at {value[0], value[1]}")
            self.force_click(value[0], value[1])
            time.sleep(5)
    
    def take_game_screenshot(self):
        """Capture current game state"""
        screenshot = pyautogui.screenshot()
        return screenshot
    
    def execute_turn(self, move_data: MoveData):
        """Execute the move returned by LLM"""
        print(f"Executing turn: {move_data}")

        self.set_angle(move_data.angle_delta)
        self.set_power(move_data.power_delta)
        self.perform_move_actions(move_data.move_actions)
        self.fire()
        time.sleep(1)
    
    def set_angle(self, angle_delta: int):
        """Set cannon angle (0-90 degrees)"""
        # This depends on your game's UI - needs calibration
        if angle_delta > 0:
            for _ in range(angle_delta):
                self.force_click(self.CONTROLS_COORDINATES["angle_increase"])
        elif angle_delta < 0:
            for _ in range(-angle_delta):
                self.force_click(self.CONTROLS_COORDINATES["angle_decrease"])
    
    def set_power(self, power_delta: int):
        """Set shot power (0-100)"""
        if power_delta > 0:
            for _ in range(power_delta):
                self.force_click(self.CONTROLS_COORDINATES["power_increase"])
        elif power_delta < 0:
            for _ in range(-power_delta):
                self.force_click(self.CONTROLS_COORDINATES["power_decrease"])

    def perform_move_actions(self, move_actions: Optional[Tuple[Literal['R', 'L'], int]]):
        """Perform move actions, if any."""
        if move_actions:
            if move_actions[0] == "R":
                for _ in range(move_actions[1]):
                    self.force_click(self.CONTROLS_COORDINATES["move_right"])
                    time.sleep(1)
            elif move_actions[0] == "L":
                for _ in range(move_actions[1]):
                    self.force_click(self.CONTROLS_COORDINATES["move_left"])
                    time.sleep(1)
    
    def fire(self):
        """Fire the shot"""
        self.force_click(self.CONTROLS_COORDINATES["fire"])
    
    def is_llm_turn(self):
        """Check if it's the LLM agent's turn (Player 1)"""
        # Look for turn indicators, UI elements, etc.
        # For now, simple implementation
        return True  # Placeholder - implement turn detection
    
    def is_game_over(self):
        """Check if current game has ended"""
        # Look for game over screen, victory message, etc.
        return False  # 
    

if __name__ == "__main__":
    controller = PocketTanksGameController(config)
    controller.launch_and_setup_game()
    controller.execute_turn(MoveData(angle_delta=10, power_delta=10, move_actions=("R", 10)))