"""
Orbital mechanics calculations for Solar Dominion.
"""

import math
from typing import Tuple, Dict, Optional
import sys
import os

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import G, AU

def calculate_orbital_position(semi_major_axis: float, angle: float) -> Tuple[float, float]:
    """
    Calculate the position of an object in a circular orbit.
    
    Args:
        semi_major_axis: The orbital radius in AU
        angle: The current orbital angle in radians
        
    Returns:
        Tuple containing (x, y) position
    """
    # Convert AU to game units
    radius = semi_major_axis * AU
    
    # Calculate position
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    
    return (x, y)

def calculate_orbital_velocity(mass_central: float, semi_major_axis: float) -> float:
    """
    Calculate the orbital velocity for a circular orbit.
    
    Args:
        mass_central: Mass of the central body
        semi_major_axis: The semi-major axis of the orbit in AU
        
    Returns:
        Orbital velocity in game units per day
    """
    # Convert AU to game units
    radius = semi_major_axis * AU
    
    # Calculate velocity using v = sqrt(G*M/r)
    velocity = math.sqrt(G * mass_central / radius)
    
    return velocity

def calculate_orbital_period(mass_central: float, semi_major_axis: float) -> float:
    """
    Calculate the orbital period using Kepler's Third Law.
    
    Args:
        mass_central: Mass of the central body
        semi_major_axis: The semi-major axis of the orbit in AU
        
    Returns:
        Orbital period in days
    """
    # Convert AU to game units
    radius = semi_major_axis * AU
    
    # Calculate period using T = 2π * sqrt(r³/GM)
    period = 2 * math.pi * math.sqrt(radius**3 / (G * mass_central))
    
    return period

def calculate_phase_angle(r1: float, r2: float) -> float:
    """
    Calculate the phase angle for a Hohmann transfer.
    This is the angle between the departure and destination planets
    when the spacecraft should depart.
    
    Args:
        r1: Radius of the starting orbit in AU
        r2: Radius of the destination orbit in AU
        
    Returns:
        Phase angle in radians
    """
    # For a Hohmann transfer to an outer planet, the phase angle is given by:
    # θ = π(1 - (1/2)*(period_transfer/period_destination)^(2/3))
    
    # Calculate semi-major axis of transfer orbit
    a_transfer = (r1 + r2) / 2
    
    # Calculate period of transfer orbit (half of it is used)
    period_transfer = math.pi * math.sqrt(a_transfer**3)
    
    # Calculate period of destination orbit
    period_destination = 2 * math.pi * math.sqrt(r2**3)
    
    # Calculate phase angle
    if r2 > r1:
        # Transfer to outer planet
        phase_angle = math.pi * (1 - 0.5 * (period_transfer / period_destination)**(2/3))
    else:
        # Transfer to inner planet
        phase_angle = math.pi * (1 + 0.5 * (period_transfer / period_destination)**(2/3))
    
    return phase_angle

def calculate_orbital_elements_from_state_vectors(position: Tuple[float, float], 
                                                 velocity: Tuple[float, float], 
                                                 central_mass: float) -> Dict[str, float]:
    """
    Calculate orbital elements from position and velocity vectors.
    
    Args:
        position: (x, y) position vector in game units
        velocity: (vx, vy) velocity vector in game units per day
        central_mass: Mass of the central body
        
    Returns:
        Dictionary of orbital elements (semi-major axis, eccentricity, etc.)
    """
    # Calculate position and velocity magnitudes
    r = math.sqrt(position[0]**2 + position[1]**2)
    v = math.sqrt(velocity[0]**2 + velocity[1]**2)
    
    # Calculate specific angular momentum
    h_x = position[1] * velocity[2] - position[2] * velocity[1]
    h_y = position[2] * velocity[0] - position[0] * velocity[2]
    h_z = position[0] * velocity[1] - position[1] * velocity[0]
    h = math.sqrt(h_x**2 + h_y**2 + h_z**2)
    
    # Calculate specific energy
    energy = 0.5 * v**2 - G * central_mass / r
    
    # Calculate semi-major axis
    if energy >= 0:
        # Parabolic or hyperbolic orbit
        semi_major_axis = float('inf') if energy == 0 else -G * central_mass / (2 * energy)
    else:
        # Elliptical orbit
        semi_major_axis = -G * central_mass / (2 * energy)
    
    # Calculate eccentricity
    eccentricity_vector_x = (v**2 / (G * central_mass) - 1/r) * position[0] - (position[0]*velocity[0] + position[1]*velocity[1]) / (G * central_mass) * velocity[0]
    eccentricity_vector_y = (v**2 / (G * central_mass) - 1/r) * position[1] - (position[0]*velocity[0] + position[1]*velocity[1]) / (G * central_mass) * velocity[1]
    eccentricity = math.sqrt(eccentricity_vector_x**2 + eccentricity_vector_y**2)
    
    # Return orbital elements
    return {
        "semi_major_axis": semi_major_axis / AU,  # Convert to AU
        "eccentricity": eccentricity,
        "energy": energy,
        "angular_momentum": h
    }
