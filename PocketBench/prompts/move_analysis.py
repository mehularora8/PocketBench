move_analysis_prompt = """You are playing Pocket Tanks, a turn-based artillery game. Analyze the screenshot and decide your next move.

#Game Rules:
- You control a tank and need to hit the opponent's tank using 2-D projectile motion.
- You can adjust the angle and power for your shot.
- The maximum power is 100, and the angle is 0-360 degrees with 0 being straight right and 90 being straight up.
- You can move left/right before shooting, but you must produce a move action. I.e. you must shoot even if you choose to move left or right.
- Consider terrain and distance to target. Most weapons cannot go through hills, and operate under projectile physics.
- You get points for hitting the opponent's tank. 

# Steps:
1. Extract the current game state, i.e. Angle, and Power from the screenshot.
2. When provided, use visual feedback from the previous move to determine the best angle and power to hit the opponent's tank.
3. Determine the best move action to take.


Return your response as JSON with this exact structure:
{
    "angle_delta": <integer>,
    "power_delta": <integer>, 
    "move_actions": <null or ["R"|"L", <steps 1-5>]>,
    "reasoning": "<explanation of your strategy>",
    "confidence": <float from 0.0 to 1.0>
}

Analyze the current game state and make the best tactical decision."""