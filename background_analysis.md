# Bahamut Lagoon Background Analysis

Analysis of `setup_scene_background` parameters across 83 decompiled rooms.

## Background ID Frequency Analysis

| Background ID | Usage Count | Percentage | Category         |
|---------------|-------------|------------|------------------|
| 0x34          | 54          | 15.8%      | Common Indoor    |
| 0x33          | 35          | 10.3%      | Battle/Status UI |
| 0x35          | 26          | 7.6%       | Dialog Scenes    |
| 0x01          | 16          | 4.7%       | Sky Fortress     |
| 0x3B          | 9           | 2.6%       | Special Scenes   |
| 0x3A          | 8           | 2.3%       | Story Moments    |
| 0x3D          | 6           | 1.8%       | Rare Scenes      |
| 0x19          | 6           | 1.8%       | Rare Scenes      |
| 0x15          | 6           | 1.8%       | Kahna Castle     |
| 0x05          | 5           | 1.5%       | Unknown          |
| 0x39          | 5           | 1.5%       | Unknown          |
| 0x32          | 5           | 1.5%       | Town/Village     |
| 0x27          | 5           | 1.5%       | Fortress/Battle  |

## Background Categories

### Story/Cutscene Backgrounds

#### 0x15 - Kahna Castle Interior (6 uses)

- **Rooms**: 0 (prologue), 51, 250
- **Context**: Castle interior scenes, throne room, royal chambers
- **Common pattern**:
  ```assembly
  setup_scene_background(0x15)
  setup_scene_mask(0x0, 0xa)     ; or (0x0, 0x0)
  ; Often followed by royal dialog and actor setup
  ```

#### 0x32 - Town/Village Scenes (5 uses)

- **Rooms**: 0, 30, 49, 244, 248
- **Context**: Village and town backgrounds
- **Usage**: Civilian areas, shops, peaceful locations

#### 0x27 - Fortress/Battle Scenes (5 uses)

- **Rooms**: 0 (appears in battle sequence)
- **Context**: Military fortresses, battle preparations
- **Usage**: War scenes, strategic locations

#### 0x01 - Sky Fortress/Aerial (16 uses)

- **Rooms**: 0 (sky fortress scenes), multiple others
- **Context**: Aerial battles, sky fortresses, dragon flight
- **Common pattern**:
  ```assembly
  setup_scene_background(0x1)
  ; Often followed by:
  ; 0x73 __opcode(0xd)
  ; 0x7d __opcode(0xf0, 0x8)
  ```

### Gameplay Backgrounds

#### 0x34 - Common Indoor Scenes (54 uses - Most Frequent)

- **Rooms**: 12, 15 (heavily), and many others
- **Context**: Generic indoor locations, likely reusable
- **Usage**: Dialog scenes, shops, inns, generic buildings
- **Common pattern**:
  ```assembly
  setup_scene_background(0x34)
  setup_scene_mask(0x29, param)  ; Various mask parameters
  ```
- **Analysis**: High frequency suggests versatile background for many interactions

#### 0x33 - Battle/Status UI (35 uses - Second Most Common)

- **Context**: Battle preparation, status screens, strategic planning
- **Common pattern**: Often appears with opcode `0x73 __opcode(0xd)`
- **Usage**: Pre-battle scenes, army management, tactical displays

#### 0x35 - Dialog/Conversation Backgrounds (26 uses)

- **Context**: Character conversations, story exposition
- **Usage**: Dialog-heavy scenes, character interactions
- **Pattern**: Often in room 15 and other story-focused rooms

### Special Purpose Backgrounds

#### 0x3A - Story Moments (8 uses)

- **Rooms**: 1 (multiple uses), others
- **Context**: Specific narrative moments
- **Usage**: Key story beats, dramatic scenes

#### 0x3B - Special Scenes (9 uses)

- **Context**: Unique or special gameplay moments
- **Usage**: Boss encounters, special events, climactic scenes

#### 0x19 - Rare Scenes (6 uses)

- **Context**: Infrequently used background
- **Usage**: Specific story locations or special areas

## Room-Specific Background Usage

### Room 0 (Prologue) - Multi-Background Story

- **0x15**: Castle scenes (throne room, royal chambers)
- **0x01**: Sky fortress aerial battles
- **0x27**: Military fortress, battle preparations
- **0x32**: Town/village scenes
- **Pattern**: Story progression through different locations

### Room 15 (Chapter 15) - Heavy Indoor Usage

- **0x34**: Multiple uses throughout room
- **0x35**: Dialog scenes
- **Pattern**: Indoor-focused chapter with lots of character interaction

### Town/Village Rooms (244, 248, 30, 49)

- **0x32**: Consistent town background usage
- **Pattern**: Civilian locations, peaceful settings

### Castle Rooms (51, 250)

- **0x15**: Castle interior consistency
- **Pattern**: Royal/noble locations, important story beats

## Technical Implementation Patterns

### Common Setup Sequences

**Standard Scene Transition:**

```assembly
animate_brightness(0x0F, 0x00, 0x20, 0x00)  ; Fade out
pause(0x20)
set_screen_status(0x00)                      ; Turn off screen
setup_scene_background(bg_id)                ; Load background
setup_scene_mask(mask_id, param)             ; Set masking
set_screen_status(0x01)                      ; Turn on screen
animate_brightness(0x00, 0x0F, 0x20, 0x00)  ; Fade in
```

**Sky Fortress Pattern (0x01):**

```assembly
setup_scene_background(0x1)
0x73 __opcode(0xd)         ; Graphics mode setup
0x7d __opcode(0xf0, 0x8)   ; Color/palette setup  
0x7f __opcode(0x10, 0xff)  ; Display setup
setup_scene_mask(param, param)
```

**Castle Pattern (0x15):**

```assembly  
setup_scene_background(0x15)
setup_scene_mask(0x0, 0x0)  ; Clear mask
; Followed by actor setup and royal dialog
```

## Background ID Hypothesis

Based on usage patterns and context:

### Confirmed Categories

- **0x15**: Kahna Castle interior tileset
- **0x32**: Town/village tileset
- **0x01**: Sky/aerial combat tileset
- **0x34**: Generic indoor tileset (most versatile)
- **0x33**: Battle UI/preparation tileset

### Likely Categories

- **0x27**: Military fortress tileset
- **0x35**: Dialog/conversation tileset
- **0x3A/0x3B**: Special event tilesets
- **0x19**: Rare location tileset

### Usage Implications

1. **High frequency backgrounds** (0x34, 0x33, 0x35) are versatile, reusable tilesets
2. **Low frequency backgrounds** (0x15, 0x32, 0x27) are location-specific story tilesets
3. **Room-specific clustering** suggests backgrounds tied to narrative progression
4. **Technical patterns** indicate some backgrounds require special graphics mode setup

## Development Insights

### For Room Editors

- **0x34** is safe for testing generic indoor scenes
- **0x01** requires additional graphics setup opcodes
- **0x15** and **0x32** are story-specific, use carefully
- **Mask parameters** vary significantly by background type

### For Background System

- Background IDs map to specific graphics/tileset combinations
- Some backgrounds bundle graphics mode changes
- Masking system provides layering/overlay effects
- Scene transitions follow consistent fade patterns

This analysis provides the foundation for understanding Bahamut Lagoon's scene system and creating accurate room editors
with proper background handling.