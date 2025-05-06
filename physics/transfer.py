"""
Transfer trajectory calculations for Solar Dominion.
Implements Hohmann transfers, bi-elliptic transfers, 
and other orbital maneuvers.
"""

import math
from typing import Tuple, Dict, List, Optional
import sys
import os

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import G, AU
from physics.orbital import calculate_orbital_velocity

def calculate_hohmann_transfer(r1: float, r2: float, central_mass: float) -> Dict[str, float]:
    """
    Calculate parameters for a Hohmann transfer orbit between two circular orbits.
    
    Args:
        r1: Radius of the starting orbit in AU
        r2: Radius of the destination orbit in AU
        central_mass: Mass of the central body
        
    Returns:
        Dictionary containing transfer parameters:
        - delta_v1: Delta-v for the first burn (departure)
        - delta_v2: Delta-v for the second burn (arrival)
        - total_delta_v: Total delta-v required
        - transfer_time: Time for the transfer in days
        - semi_major_axis: Semi-major axis of the transfer orbit in AU
    """
    # Convert AU to game units
    r1_units = r1 * AU
    r2_units = r2 * AU
    
    # Calculate semi-major axis of transfer orbit
    a_transfer = (r1_units + r2_units) / 2
    
    # Calculate velocities in the initial and final circular orbits
    v1_circular = calculate_orbital_velocity(central_mass, r1)
    v2_circular = calculate_orbital_velocity(central_mass, r2)
    
    # Calculate velocities at periapsis and apoapsis of the transfer orbit
    v1_transfer = math.sqrt(G * central_mass * (2/r1_units - 1/a_transfer))
    v2_transfer = math.sqrt(G * central_mass * (2/r2_units - 1/a_transfer))
    
    # Calculate delta-v for the first and second burns
    delta_v1 = abs(v1_transfer - v1_circular)
    delta_v2 = abs(v2_circular - v2_transfer)
    
    # Calculate transfer time (half the orbital period of the transfer orbit)
    transfer_time = math.pi * math.sqrt(a_transfer**3 / (G * central_mass))
    
    return {
        "delta_v1": delta_v1,
        "delta_v2": delta_v2,
        "total_delta_v": delta_v1 + delta_v2,
        "transfer_time": transfer_time,
        "semi_major_axis": a_transfer / AU  # Convert back to AU
    }

def calculate_bi_elliptic_transfer(r1: float, r2: float, r_intermediate: float, central_mass: float) -> Dict[str, float]:
    """
    Calculate parameters for a bi-elliptic transfer, which uses an intermediate
    high apoapsis to make the transfer more efficient for large orbit changes.
    
    Args:
        r1: Radius of the starting orbit in AU
        r2: Radius of the destination orbit in AU
        r_intermediate: Radius of the intermediate point (apoapsis) in AU
        central_mass: Mass of the central body
        
    Returns:
        Dictionary containing transfer parameters
    """
    # Convert AU to game units
    r1_units = r1 * AU
    r2_units = r2 * AU
    r_intermediate_units = r_intermediate * AU
    
    # Calculate velocities in the initial and final circular orbits
    v1_circular = calculate_orbital_velocity(central_mass, r1)
    v2_circular = calculate_orbital_velocity(central_mass, r2)
    
    # Calculate semi-major axes of the two transfer ellipses
    a1_transfer = (r1_units + r_intermediate_units) / 2
    a2_transfer = (r2_units + r_intermediate_units) / 2
    
    # Calculate velocities at key points
    v1_transfer = math.sqrt(G * central_mass * (2/r1_units - 1/a1_transfer))
    v_intermediate_1 = math.sqrt(G * central_mass * (2/r_intermediate_units - 1/a1_transfer))
    v_intermediate_2 = math.sqrt(G * central_mass * (2/r_intermediate_units - 1/a2_transfer))
    v2_transfer = math.sqrt(G * central_mass * (2/r2_units - 1/a2_transfer))
    
    # Calculate delta-v for each burn
    delta_v1 = abs(v1_transfer - v1_circular)
    delta_v2 = abs(v_intermediate_2 - v_intermediate_1)
    delta_v3 = abs(v2_circular - v2_transfer)
    
    # Calculate transfer times for each elliptical segment
    transfer_time1 = math.pi * math.sqrt(a1_transfer**3 / (G * central_mass))
    transfer_time2 = math.pi * math.sqrt(a2_transfer**3 / (G * central_mass))
    
    return {
        "delta_v1": delta_v1,
        "delta_v2": delta_v2,
        "delta_v3": delta_v3,
        "total_delta_v": delta_v1 + delta_v2 + delta_v3,
        "transfer_time1": transfer_time1,
        "transfer_time2": transfer_time2,
        "total_transfer_time": transfer_time1 + transfer_time2,
        "semi_major_axis1": a1_transfer / AU,
        "semi_major_axis2": a2_transfer / AU
    }

def generate_hohmann_trajectory_points(start_position: Tuple[float, float], 
                                      start_velocity: Tuple[float, float],
                                      end_position: Tuple[float, float],
                                      central_mass: float,
                                      num_points: int = 50) -> List[Tuple[float, float]]:
    """
    Generate points along a Hohmann transfer trajectory for visualization.
    
    Args:
        start_position: Starting position (x, y) in game units
        start_velocity: Starting velocity (vx, vy) in game units/day
        end_position: Ending position (x, y) in game units
        central_mass: Mass of the central body
        num_points: Number of points to generate along the trajectory
        
    Returns:
        List of (x, y) positions along the trajectory
    """
    # Calculate distance from central body
    r1 = math.sqrt(start_position[0]**2 + start_position[1]**2)
    r2 = math.sqrt(end_position[0]**2 + end_position[1]**2)
    
    # Calculate semi-major axis of transfer orbit
    a_transfer = (r1 + r2) / 2
    
    # Calculate eccentricity based on the periapsis and apoapsis
    if r1 < r2:
        # Outbound transfer
        periapsis = r1
        apoapsis = r2
    else:
        # Inbound transfer
        periapsis = r2
        apoapsis = r1
    
    eccentricity = (apoapsis - periapsis) / (apoapsis + periapsis)
    
    # Calculate transfer time
    transfer_time = math.pi * math.sqrt(a_transfer**3 / (G * central_mass))
    
    # Generate points along the elliptical orbit
    points = []
    
    # For a Hohmann transfer, we only need half of the elliptical orbit
    max_angle = math.pi
    
    for i in range(num_points):
        # Calculate true anomaly (angle around the orbit)
        if r1 < r2:
            # Outbound transfer
            true_anomaly = i * max_angle / (num_points - 1)
        else:
            # Inbound transfer
            true_anomaly = math.pi + i * max_angle / (num_points - 1)
        
        # Calculate radius at this point in the orbit
        radius = a_transfer * (1 - eccentricity**2) / (1 + eccentricity * math.cos(true_anomaly))
        
        # Calculate position
        x = radius * math.cos(true_anomaly)
        y = radius * math.sin(true_anomaly)
        
        # Add to points list
        points.append((x, y))
    
    return points

def calculate_fuel_consumption(delta_v: float, ship_mass: float, engine_efficiency: float) -> float:
    """
    Calculate fuel consumption for a given delta-v and ship mass.
    Uses the rocket equation: delta-v = Ve * ln(m0/m1)
    
    Args:
        delta_v: Change in velocity required
        ship_mass: Total mass of the ship (including fuel)
        engine_efficiency: Exhaust velocity of the engine
        
    Returns:
        Amount of fuel consumed
    """
    # Calculate mass ratio
    mass_ratio = math.exp(delta_v / engine_efficiency)
    
    # Calculate fuel consumption
    fuel_consumed = ship_mass * (1 - 1/mass_ratio)
    
    return fuel_consumed

def calculate_optimal_transfer_window(origin_orbit: Dict[str, float], 
                                     destination_orbit: Dict[str, float],
                                     current_time: float) -> float:
    """
    Calculate the optimal time for a transfer window.
    
    Args:
        origin_orbit: Dictionary with orbital parameters of the origin
        destination_orbit: Dictionary with orbital parameters of the destination
        current_time: Current game time in days
        
    Returns:
        Time in days until the next optimal transfer window
    """
    # Get orbital periods
    origin_period = origin_orbit["period"]
    destination_period = destination_orbit["period"]
    
    # Get current phases
    origin_phase = (current_time % origin_period) / origin_period * 2 * math.pi
    destination_phase = (current_time % destination_period) / destination_period * 2 * math.pi
    
    # Calculate phase angle needed for Hohmann transfer
    r1 = origin_orbit["semi_major_axis"]
    r2 = destination_orbit["semi_major_axis"]
    
    # This is different depending on whether we're going outward or inward
    if r2 > r1:
        # Outbound transfer
        # Calculate semi-major axis of transfer orbit
        a_transfer = (r1 + r2) / 2
        
        # Calculate time for half of transfer orbit
        transfer_time = math.pi * math.sqrt(a_transfer**3)
        
        # Calculate angular distance traveled by destination during transfer
        angular_distance = transfer_time / destination_period * 2 * math.pi
        
        # Phase angle needed
        phase_needed = math.pi - angular_distance
    else:
        # Inbound transfer
        a_transfer = (r1 + r2) / 2
        transfer_time = math.pi * math.sqrt(a_transfer**3)
        angular_distance = transfer_time / origin_period * 2 * math.pi
        phase_needed = math.pi + angular_distance
    
    # Current phase difference
    current_phase_diff = destination_phase - origin_phase
    
    # Normalize to [0, 2π]
    while current_phase_diff < 0:
        current_phase_diff += 2 * math.pi
    while current_phase_diff >= 2 * math.pi:
        current_phase_diff -= 2 * math.pi
    
    # Calculate how much more phase difference is needed
    phase_diff_needed = phase_needed - current_phase_diff
    
    # Normalize to [0, 2π]
    while phase_diff_needed < 0:
        phase_diff_needed += 2 * math.pi
        
    # Calculate relative angular velocity
    relative_angular_velocity = 2 * math.pi * (1/destination_period - 1/origin_period)
    
    # Calculate time until window
    time_to_window = phase_diff_needed / relative_angular_velocity
    
    return time_to_window
