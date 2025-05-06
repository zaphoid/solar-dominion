"""
Constants and settings for the Solar Dominion game.
"""

# Display settings
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Colors
BG_COLOR = (0, 0, 0)
GRID_COLOR = (20, 20, 20)
TEXT_COLOR = (200, 200, 200)
ORBIT_COLOR = (50, 50, 100)
TRAJECTORY_COLOR = (100, 150, 100)
TRANSFER_COLOR = (150, 150, 0)
GRAVITY_ASSIST_COLOR = (0, 150, 150)

# Faction colors
FACTION_COLORS = {
    "EARTH": (0, 100, 255),
    "MARS": (255, 100, 0),
    "BELT": (150, 150, 150),
    "PROTOGEN": (150, 0, 150),
}

# Astronomical constants
# We'll use a scaled version for the game
# 1 AU (Astronomical Unit) will be 100 pixels
AU = 100
# Gravitational constant (scaled for game purposes)
G = 100
# Scale for time: 1 day in game time per second of real time at 1x speed
DAY_PER_SECOND = 1
# Earth year in days
EARTH_YEAR = 365.25

# Mass values (scaled for game, approximate relative values)
SUN_MASS = 1000
EARTH_MASS = 1
MARS_MASS = 0.107
JUPITER_MASS = 317.8
SATURN_MASS = 95.2

# Orbital parameters (semi-major axis in AU, period in Earth days)
ORBITAL_PARAMETERS = {
    "SUN": {"mass": SUN_MASS, "radius": 20, "color": (255, 255, 0), "semi_major_axis": 0, "period": 0},
    "MERCURY": {"mass": 0.055, "radius": 3, "color": (180, 180, 180), "semi_major_axis": 0.387, "period": 88},
    "VENUS": {"mass": 0.815, "radius": 8, "color": (255, 198, 73), "semi_major_axis": 0.723, "period": 225},
    "EARTH": {"mass": EARTH_MASS, "radius": 10, "color": (0, 100, 255), "semi_major_axis": 1.0, "period": EARTH_YEAR},
    "MARS": {"mass": MARS_MASS, "radius": 5, "color": (255, 50, 0), "semi_major_axis": 1.524, "period": 687},
    "JUPITER": {"mass": JUPITER_MASS, "radius": 15, "color": (255, 200, 100), "semi_major_axis": 5.203, "period": 4333},
    "SATURN": {"mass": SATURN_MASS, "radius": 13, "color": (255, 220, 150), "semi_major_axis": 9.58, "period": 10759},
}

# Moon parameters (relative to parent planet)
MOON_PARAMETERS = {
    "LUNA": {"parent": "EARTH", "mass": 0.0123, "radius": 3, "color": (200, 200, 200), "semi_major_axis": 0.00257, "period": 27.3},
    "PHOBOS": {"parent": "MARS", "mass": 1.8e-9, "radius": 1, "color": (180, 180, 180), "semi_major_axis": 9.377e-5, "period": 0.32},
    "DEIMOS": {"parent": "MARS", "mass": 2.5e-10, "radius": 1, "color": (160, 160, 160), "semi_major_axis": 2.346e-4, "period": 1.26},
    "IO": {"parent": "JUPITER", "mass": 0.015, "radius": 2, "color": (255, 200, 0), "semi_major_axis": 0.0028, "period": 1.77},
    "EUROPA": {"parent": "JUPITER", "mass": 0.008, "radius": 2, "color": (200, 200, 255), "semi_major_axis": 0.0044, "period": 3.55},
    "GANYMEDE": {"parent": "JUPITER", "mass": 0.025, "radius": 3, "color": (150, 150, 150), "semi_major_axis": 0.0071, "period": 7.16},
    "CALLISTO": {"parent": "JUPITER", "mass": 0.018, "radius": 3, "color": (120, 120, 120), "semi_major_axis": 0.0125, "period": 16.69},
    "TITAN": {"parent": "SATURN", "mass": 0.0225, "radius": 3, "color": (255, 200, 50), "semi_major_axis": 0.0082, "period": 15.95},
}

# Ship parameters
SHIP_TYPES = {
    "SHUTTLE": {"delta_v": 5, "fuel_capacity": 100, "mass": 5, "crew_capacity": 10, "cargo_capacity": 20},
    "TRANSPORT": {"delta_v": 3, "fuel_capacity": 200, "mass": 20, "crew_capacity": 20, "cargo_capacity": 100},
    "MILITARY": {"delta_v": 8, "fuel_capacity": 150, "mass": 15, "crew_capacity": 30, "cargo_capacity": 50},
}

# Resource types and base values
RESOURCE_TYPES = {
    "WATER": {"base_value": 10, "mass_per_unit": 1.0},
    "FOOD": {"base_value": 15, "mass_per_unit": 0.5},
    "FUEL": {"base_value": 20, "mass_per_unit": 0.8},
    "MATERIALS": {"base_value": 5, "mass_per_unit": 2.0},
    "RARE_METALS": {"base_value": 50, "mass_per_unit": 1.5},
}

# UI Constants
BUTTON_COLOR = (50, 50, 70)
BUTTON_HOVER_COLOR = (70, 70, 100)
BUTTON_TEXT_COLOR = (220, 220, 220)
PANEL_BG_COLOR = (30, 30, 40, 200)  # With alpha for transparency
