import logging

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pocketbench.log')
    ]
)

from controller import PocketTanksGameController
from config import config
from PocketBench.agent_backup import LLMAgent, GameMove
from controller import MoveData

logger = logging.getLogger(__name__)

def run():
    controller = PocketTanksGameController()
    agent = LLMAgent(config)

    controller.launch_and_setup_game()

    for _ in range(10):
        current_game_state = controller.take_game_screenshot()
        move: GameMove = agent.get_move(current_game_state)
        try:
            move_data = MoveData(angle_delta=move.angle_delta, power_delta=move.power_delta, move_actions=move.move_actions)
            controller.execute_turn(move_data)
        except Exception as e:
            logger.error(f"Error executing turn: {e}")
            continue


if __name__ == "__main__":
    run()