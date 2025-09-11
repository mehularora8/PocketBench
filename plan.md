# PocketBench Reactive Controller Design

## Current State
- Hardcoded coordinates for all UI interactions
- Fixed timing delays between moves  
- Agent only sees current screenshot without context
- No feedback on move effectiveness

## Goal: Reactive Environment-Aware Controller

### 1. Optical Flow Turn Detection
Replace hardcoded delays with motion-based turn detection:

**How it works:**
- Capture frames continuously during opponent turn
- Calculate optical flow between consecutive frames
- Track motion magnitude over time
- Turn ends when motion stays below threshold for N consecutive frames

**Distance Analysis (overshoot/undershoot):**
- Find player tank position (bottom-left region, color detection)
- Find opponent tank position (bottom-right region, color detection) 
- Detect impact location (largest change area in frame diff)
- Calculate distance error:
  - Project impact vector onto player→opponent line
  - Positive distance = overshoot, negative = undershoot
  - Example: Shot lands 50px past opponent = +50 overshoot

**Implementation:**
```python
class TurnDetector:
    def calculate_motion(frame) -> float
    def is_turn_finished(frame) -> bool
    
class MoveAnalyzer:
    def analyze_move_outcome(pre_shot, post_shot) -> MoveOutcome
    def _calculate_distance_error(player_pos, opponent_pos, impact_pos) -> float
```

### 2. Move Outcome Tracking
Analyze each shot's effectiveness to provide context for next move:

**Data to Extract:**
- Hit/miss detection (changes near opponent position)
- Impact location coordinates
- Distance error (how far off horizontally)
- Terrain damage area
- Trajectory accuracy score

**Context for Agent:**
```
"Previous move: angle_delta=+5, power_delta=-10 → MISS (overshoot by 45px)
Last move: angle_delta=-2, power_delta=-5 → NEAR MISS (undershoot by 12px)  
Current move: [analyze screenshot with this context]"
```

### 3. Dynamic UI Detection
Replace hardcoded coordinates with computer vision:

**Priority Order:**
1. Turn detection (optical flow) - **START HERE**
2. Move outcome analysis 
3. UI element detection (buttons, controls)
4. Game state recognition (menu vs gameplay)

**UI Detection Approaches:**
- Template matching for buttons
- OCR for text elements
- Color-based region detection
- Contour analysis for UI shapes

### 4. Enhanced Agent Integration

**Context-Aware Prompting:**
- Include previous 2-3 move outcomes in prompt
- Specify shot patterns (consistently overshooting, etc.)
- Provide distance/accuracy feedback

**Structured Move History:**
```python
@dataclass
class MoveOutcome:
    hit_detected: bool
    impact_location: Tuple[int, int] 
    distance_error: float  # +overshoot, -undershoot
    terrain_change_area: int
    confidence: float

class ContextualAgent:
    move_history: List[GameMove]
    outcome_history: List[MoveOutcome]
    
    def get_move_with_context(screenshot) -> GameMove
```

## Implementation Plan

### Phase 1: Turn Detection (Week 1)
- [ ] Implement optical flow motion calculation
- [ ] Add turn finished detection logic
- [ ] Test with different weapon types (fast bullets vs slow mortars)
- [ ] Tune motion thresholds

### Phase 2: Move Analysis (Week 2) 
- [ ] Tank position detection (color-based)
- [ ] Impact location detection (frame differencing)
- [ ] Distance error calculation (vector projection)
- [ ] Hit/miss detection near opponent

### Phase 3: Context Integration (Week 3)
- [ ] Move outcome storage and retrieval  
- [ ] Enhanced agent prompting with history
- [ ] Performance tracking and metrics
- [ ] Adaptive learning from patterns

### Phase 4: UI Detection (Week 4)
- [ ] Dynamic button detection
- [ ] Menu state recognition
- [ ] Adaptive coordinate system
- [ ] Multi-resolution support

## Technical Details

**Tank Detection Strategy:**
1. Crop bottom 30% of screen (where tanks typically are)
2. Split left/right halves for player/opponent
3. Use HSV color range to find tank-colored pixels
4. Get centroid of largest contour as tank position
5. Fallback to corner positions if detection fails

**Distance Error Calculation:**
1. Vector from player to opponent = target line
2. Vector from player to impact = actual shot
3. Project impact vector onto target line
4. Distance beyond target = overshoot (+), before target = undershoot (-)
5. Normalize by screen size for consistent feedback

**Motion Threshold Tuning:**
- Fast weapons: lower threshold, shorter stable period
- Slow weapons: higher threshold, longer stable period  
- Explosions: expect motion spike then rapid decay
- Terrain settling: gradual motion decrease

## Benefits

1. **Adaptive Timing** - Works with any weapon speed/type
2. **Learning Agent** - Improves accuracy over time
3. **Robust Control** - Handles UI changes and lag
4. **Better Performance** - Context-aware decision making
5. **Scalable** - Easy to add new game state detection

## Risk Mitigation

- **Fallback Systems** - Default to hardcoded values if CV fails
- **Incremental Rollout** - Replace one hardcoded system at a time  
- **Extensive Testing** - Various weapons, screen sizes, conditions
- **Debug Visualization** - Show motion vectors, detected positions