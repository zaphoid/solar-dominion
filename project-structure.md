# Solar Dominion Project Structure

```
solar_dominion/
├── main.py                  # Entry point, game loop
├── constants.py             # Game constants and settings
├── models/                  # Data models
│   ├── __init__.py
│   ├── celestial_body.py    # Planet, moon, asteroid classes
│   ├── faction.py           # Faction definitions
│   ├── habitat.py           # Space station, colony classes
│   ├── resource.py          # Resource types and management
│   └── ship.py              # Spacecraft classes
├── physics/                 # Physics simulation
│   ├── __init__.py
│   ├── orbital.py           # Orbital mechanics calculations
│   ├── transfer.py          # Transfer trajectories (Hohmann, bi-elliptic)
│   ├── gravity_assist.py    # Gravity assist calculations
│   └── delta_v.py           # Delta-v and fuel calculations
├── ui/                      # User interface
│   ├── __init__.py
│   ├── renderer.py          # Main rendering engine
│   ├── trajectory_plotter.py # Trajectory visualization
│   ├── resource_display.py  # Resource management UI
│   └── mission_planner.py   # Mission planning interface
├── game/                    # Game state and logic
│   ├── __init__.py
│   ├── game_state.py        # Main game state class
│   ├── input_handler.py     # User input processing
│   └── mission.py           # Mission planning and execution
└── utils/                   # Utility functions
    ├── __init__.py
    ├── vector.py            # Vector operations
    └── conversions.py       # Unit conversions and formatters
```
