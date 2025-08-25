class BenchmarkConfig:
    def __init__(self):
        self.games_per_session = 10
        self.llm_model = "gpt-4-vision-preview"  # or claude-3-opus, etc.
        self.api_key = "your-api-key"
        self.screenshot_region = (0, 0, 1920, 1080)  # Full screen or specific region
        self.move_delay = 5.0  # seconds between moves
        self.game_launch_path = "/Applications/Pocket Tanks.app/Contents/MacOS/Pocket Tanks"

config = BenchmarkConfig()