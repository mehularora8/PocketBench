import os

class BenchmarkConfig:
    def __init__(
        self, 
        model_provider: str = "openai", 
        model: str = "gpt-4o-mini", 
        games_per_session: int = 10,  
        screenshot_region: tuple = (400, 100, 1000, 700),
        game_launch_path: str = "/Applications/Pocket Tanks.app/Contents/MacOS/Pocket Tanks"
    ):
        self.games_per_session = games_per_session
        self.model = model
        self.model_provider = model_provider
        self.screenshot_region = screenshot_region
        self.game_launch_path = game_launch_path
        if model_provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
        elif model_provider == "anthropic":
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
        elif model_provider == "gemini":
            self.api_key = os.getenv("GEMINI_API_KEY")
        else:
            raise ValueError(f"Invalid model provider: {model_provider}")

config = BenchmarkConfig()