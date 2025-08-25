#!/usr/bin/env python3
import pyautogui
import time

def find_coordinates():
    """Interactive coordinate finder"""
    print("Move mouse to UI element and press Ctrl+C to capture coordinates")
    try:
        while True:
            x, y = pyautogui.position()
            print(f"\rCurrent position: ({x}, {y})", end="", flush=True)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print(f"\nCaptured coordinates: ({x}, {y})")
        return x, y

def main():
    print(f"Screen size: {pyautogui.size()}")
    print("\nCapture Pocket Tanks UI coordinates:")
    
    coordinates = {}
    
    elements = [
        "angle_control",
        "power_control", 
        "fire_button",
        "new_game_button",
        "start_game_button"
    ]
    
    for element in elements:
        print(f"\n📍 Position mouse over {element} and press Ctrl+C:")
        coords = find_coordinates()
        coordinates[element] = coords
        time.sleep(1)
    
    # Save coordinates
    print(f"\n💾 Coordinates captured:")
    for name, coords in coordinates.items():
        print(f"{name}: {coords}")
    
    # Generate code snippet
    print(f"\n📋 Copy this into your game controller:")
    print("game_controls = {")
    for name, coords in coordinates.items():
        print(f"    '{name}': {coords},")
    print("}")

if __name__ == "__main__":
    main()