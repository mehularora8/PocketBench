import pyautogui
import time
import subprocess
from config import config

class PocketTanksGameController:
    def __init__(self, config):
        self.config = config
        self.game_process = None
        self.setup_pyautogui()
    
    def setup_pyautogui(self):
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
    
    def launch_and_setup_game(self):
        """Launch game and set it up for benchmarking"""
        print("🎮 Launching Pocket Tanks...")
        
        # Launch game
        subprocess.run(["open", "-a", "Pocket Tanks"])
        time.sleep(3)
        
        # Navigate to new game setup
        self.setup_new_game()
        
    def setup_new_game(self):
        """Set up game: LLM Agent as Player 1, Random weapons"""
        print("⚙️  Setting up new game...")
        
        # Navigate menu sequence (coordinates need calibration)
        menu_actions = [
            (400, 300, "New Game"),
            (350, 400, "Two Player Mode"),
            (500, 450, "Random Weapons"),  # Important: random weapons
            (400, 500, "Start Game")
        ]
        
        for x, y, description in menu_actions:
            print(f"   {description}")
            pyautogui.click(x, y)
            time.sleep(1.5)
    
    def take_game_screenshot(self):
        """Capture current game state"""
        screenshot = pyautogui.screenshot()
        return screenshot
    
    def execute_move(self, move_data):
        """Execute the move returned by LLM"""
        print(f"🎯 Executing move: {move_data}")
        
        # Parse move data from LLM response
        angle = move_data.get('angle', 45)
        power = move_data.get('power', 50)
        
        # Execute the move (coordinates need calibration)
        self.set_angle(angle)
        time.sleep(0.5)
        self.set_power(power)
        time.sleep(0.5)
        self.fire()
        
        # Wait for turn to complete
        time.sleep(self.config.move_delay)
    
    def set_angle(self, angle):
        """Set cannon angle (0-90 degrees)"""
        # This depends on your game's UI - needs calibration
        angle_control = (300, 400)
        pyautogui.click(*angle_control)
        pyautogui.drag(angle * 2, 0, duration=0.3)
    
    def set_power(self, power):
        """Set shot power (0-100)"""
        power_control = (500, 400)
        pyautogui.click(*power_control)
        pyautogui.drag(0, -power, duration=0.3)
    
    def fire(self):
        """Fire the shot"""
        fire_button = (600, 500)
        pyautogui.click(*fire_button)
    
    def is_llm_turn(self):
        """Check if it's the LLM agent's turn (Player 1)"""
        # Look for turn indicators, UI elements, etc.
        # For now, simple implementation
        return True  # Placeholder - implement turn detection
    
    def is_game_over(self):
        """Check if current game has ended"""
        # Look for game over screen, victory message, etc.
        return False  # Placeholder