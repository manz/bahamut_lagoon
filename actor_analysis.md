# Bahamut Lagoon Actor System Analysis

Comprehensive analysis of actor usage patterns across 83 decompiled rooms.

## Actor ID Usage Frequency

| Actor ID | Show Count | Percentage | Role Category             |
|----------|------------|------------|---------------------------|
| 0x0      | 361        | 16.1%      | Main Character/Captain    |
| 0x1      | 231        | 10.3%      | Party Member              |
| 0x3      | 214        | 9.5%       | Princess/Key Character    |
| 0x2      | 197        | 8.8%       | Party Member              |
| 0x5      | 175        | 7.8%       | Player Character (Rush)   |
| 0x6      | 168        | 7.5%       | Party Member (Rush)       |
| 0x4      | 166        | 7.4%       | King/Authority Figure     |
| 0x9      | 165        | 7.4%       | Dragon Squad Member       |
| 0x7      | 146        | 6.5%       | Party Member (Truce)      |
| 0x8      | 135        | 6.0%       | Party Member (Bikkebakke) |
| 0xA      | 102        | 4.5%       | Dragon Squad Member       |
| 0xB      | 102        | 4.5%       | Dragon Squad Member       |
| 0xC      | 88         | 3.9%       | Dragon Squad Member       |
| 0xE      | 83         | 3.7%       | Dragon Squad Member       |
| 0xD      | 81         | 3.6%       | Dragon Squad Member       |
| 0xF      | 68         | 3.0%       | Dragon Squad Member       |
| 0x10     | 58         | 2.6%       | Extended Squad            |
| 0x11+    | <40 each   | <2% each   | NPCs/Special              |

## Player Character Analysis

### Primary Playable Characters

| Actor ID | Playable Count | Role                                       |
|----------|----------------|--------------------------------------------|
| 0x0      | 102            | **Main Character/Captain** (Most playable) |
| 0x5      | 9              | **Rush** (Secondary protagonist)           |
| 0x7      | 8              | **Truce** (Squad member)                   |
| 0x1      | 8              | **Party Member**                           |
| 0xB      | 5              | **Dragon Squad**                           |
| 0x8      | 5              | **Bikkebakke**                             |

### Character Role Identification

**0x0 - Main Character/Captain:**

- Most frequently shown (361 times)
- Most frequently playable (102 times)
- Often positioned at strategic locations (0x14, 0x9)
- Leadership role in cutscenes

**0x5 - Rush (Secondary Protagonist):**

- Common in early game scenes
- Often made playable after 0x0
- Pattern: `actor_show(0x5, x, y) → actor_playable(0x5)`
- Positioned for dialog and movement sequences

**0x3 - Princess Character:**

- High show frequency (214) but rarely playable (1 time)
- Important story character, not combat role
- Often in castle scenes with specific states

**0x4 - King/Authority Figure:**

- Moderate show frequency (166)
- Rarely playable (1 time)
- Authority figure giving orders and exposition

## Actor State Analysis

### Most Common States

| State ID | Frequency | Purpose                     |
|----------|-----------|-----------------------------|
| 0x4      | 478       | **Combat/Action State**     |
| 0xE      | 338       | **Dialog/Speaking State**   |
| 0x7      | 314       | **Movement/Active State**   |
| 0xA      | 264       | **Standby/Waiting State**   |
| 0xB      | 224       | **Special Animation State** |
| 0x8      | 203       | **Interaction State**       |
| 0x9      | 177       | **Alert/Ready State**       |
| 0xD      | 146       | **Default/Idle State**      |

### State Usage Patterns

**Combat States (0x4):**

- Most frequent state across all actors
- Used during battle sequences and action scenes
- Applied to multiple actors simultaneously

**Dialog States (0xE):**

- Second most common
- Used when characters are speaking
- Often followed by text display opcodes

**Movement States (0x7, 0x9):**

- Used during choreographed movement sequences
- Actors transition between movement and idle states

**Default State (0xD):**

- Standard idle/standing state
- Used for basic actor presence
- Common in dialog setup sequences

## Actor Speed Analysis

### Speed Value Distribution

| Speed | Frequency | Usage                                |
|-------|-----------|--------------------------------------|
| 0x40  | 248       | **Normal Speed** (most common)       |
| 0x20  | 241       | **Slow Speed** (deliberate movement) |
| 0x8   | 192       | **Very Slow** (careful/dramatic)     |
| 0x10  | 184       | **Moderate Speed**                   |
| 0x80  | 56        | **Fast Speed** (action sequences)    |
| 0x4   | 64        | **Crawling Speed**                   |

### Speed Categories

**Dramatic Speeds (0x8, 0x4):**

- Used for emotional scenes
- Slow, deliberate character movement
- Story emphasis and tension building

**Normal Gameplay (0x10, 0x20, 0x40):**

- Standard movement speeds
- Balanced between readability and pacing
- Most cutscene choreography

**Action Sequences (0x80):**

- Fast movement for battle scenes
- Chase sequences and urgency
- Limited usage for dramatic effect

## Actor Data Structure

From actors table analysis (Room 0 example):

### Actor Data Format (7 bytes each)

```
Byte 0: Sprite ID (character appearance)
Byte 1: 0xFF (constant marker)
Byte 2: X Position (0x80 = offscreen/hidden)
Byte 3: Y Position (0x80 = offscreen/hidden)  
Byte 4: Initial State (0x02 common default)
Byte 5: Speed (0x08, 0x10 common defaults)
Byte 6: Flags/Properties (0x00 common)
```

### Example Actor Definitions

```
Actor 0x1: 0x01 0xFF 0x80 0x80 0x02 0x10 0x00
Actor 0x5: 0x05 0xFF 0x80 0x80 0x02 0x08 0x00  
Actor 0x4: 0x04 0xFF 0x80 0x80 0x02 0x08 0x00
Actor 0x2: 0x02 0xFF 0x80 0x80 0x02 0x10 0x00
```

### Default Pattern Analysis

- **0x80, 0x80**: Default offscreen position (actors start hidden)
- **0x02**: Common initial state (idle/ready)
- **0x08/0x10**: Default speed values
- **0x00**: No special flags by default

## Actor Group Patterns

### Dragon Squad Formation (0x9-0xF)

- Actors 0x9 through 0xF form coordinated group
- Often shown together in formation scenes
- Similar state transitions (all set to state 0x4 simultaneously)
- Uniform movement patterns and speeds

### Party Core (0x0, 0x1, 0x2, 0x3, 0x5)

- Main story characters
- Highest usage frequency
- Most playable character assignments
- Central to dialog and cutscene systems

### Extended Squad (0x10-0x15)

- Lower frequency usage
- Supporting characters
- Specific scene appearances
- Background formation filling

## Character Movement Patterns

### Common Sequences

**Actor Introduction:**

```assembly
actor_show(actor_id, x, y)
actor_state(actor_id, 0xD)       ; Set to idle state
; Optional: actor_playable(actor_id)
```

**Dialog Setup:**

```assembly
actor_state(actor_id, 0xE)       ; Set to speaking state
; Text display follows
```

**Formation Movement:**

```assembly
; Multiple actors set to movement state 0x4
actor_state(0x9, 0x4)
actor_state(0xA, 0x4) 
actor_state(0xB, 0x4)
; Followed by coordinated movement
```

**Speed Transitions:**

```assembly
actor_speed(actor_id, 0x40)      ; Normal speed
actor_move(actor_id, directions)
actor_speed(actor_id, 0x80)      ; Fast speed  
actor_move(actor_id, directions)
```

## Position Analysis

### Common Positions

**Strategic Positions:**

- (0x14, 0x9): Leadership position (actor 0x0)
- (0x8, 0x12): Central dialog position
- (0x4, 0x7): Formation left flank
- (0x15, 0x8): Formation right flank

**Formation Patterns:**

- Dragon Squad: Coordinated positioning in military formation
- Party: Scattered positioning for natural conversation
- NPCs: Specific story-relevant positions

## Technical Implementation

### Actor System Architecture

**Actor Lifecycle:**

1. **Definition**: Actor data in actors table
2. **Show**: `actor_show` places actor at position
3. **State**: `actor_state` sets behavior/animation
4. **Control**: Optional `actor_playable` for player control
5. **Movement**: `actor_move` with speed settings
6. **Cleanup**: Actors can be hidden (0x80, 0x80 position)

**State Management:**

- States control animation and behavior
- State transitions create dramatic timing
- Multiple actors can share states for coordination

**Speed System:**

- Dynamic speed changes for pacing
- Speed affects movement duration and feel
- Consistent speed values across characters

## Development Insights

### For Room Editors

**Safe Actor IDs for Testing:**

- **0x5**: Well-established player character patterns
- **0x9-0xB**: Good for group testing
- **0x0**: Main character, most patterns available

**Common State Combinations:**

- **0xD**: Safe idle state for dialog setup
- **0xE**: Speaking state before text display
- **0x4**: Action state for movement sequences

**Speed Guidelines:**

- **0x8**: Dramatic/slow scenes
- **0x20**: Normal dialog movement
- **0x40**: Standard action speed
- **0x80**: Fast action sequences

### Character System Design

**Actor Roles:**

- **0x0-0x5**: Core party (high usage, story important)
- **0x6-0x8**: Secondary party (moderate usage)
- **0x9-0xF**: Dragon Squad (group coordination)
- **0x10+**: NPCs and special characters

**Playable Character System:**

- Primary: 0x0 (captain/leader role)
- Secondary: 0x5 (Rush, action character)
- Situational: 0x1, 0x7, 0x8 (party members)

This analysis reveals a sophisticated character management system with clear role hierarchies, state-based behavior, and
coordinated group mechanics essential for Bahamut Lagoon's strategic storytelling.