"""
Delta-v and fuel calculations for Solar Dominion.
Implements the rocket equation and fuel budgeting.
"""

import math
from typing import Tuple, Dict, List, Optional
import sys
import os

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import G, AU

def calculate_delta_v_budget(ship_type: str, fuel_percentage: float, ship_mass: float) -> float:
    """
    Calculate the total delta-v available based on fuel percentage and ship characteristics.
    Uses the Tsiolkovsky rocket equation.
    
    Args:
        ship_type: Type of ship determining engine efficiency
        fuel_percentage: Current fuel percentage (0-100)
        ship_mass: Total mass of the ship
        
    Returns:
        Available delta-v in game units
    """
    # Engine efficiency (exhaust velocity) depends on ship type
    exhaust_velocity = {
        "SHUTTLE": 5.0,
        "TRANSPORT": 4.0,
        "MILITARY": 6.0,
        "ADVANCED": 8.0
    }.get(ship_type, 5.0)
    
    # Calculate dry mass (ship without fuel)
    dry_mass = ship_mass * 0.7  # Assuming 30% of total mass is fuel at 100%
    
    # Calculate current fuel mass
    max_fuel_mass = ship_mass * 0.3
    current_fuel_mass = max_fuel_mass * (fuel_percentage / 100.0)
    
    # Calculate current total mass
    current_total_mass = dry_mass + current_fuel_mass
    
    # Apply rocket equation: delta-v = v_e * ln(m0/m1)
    # Where v_e is exhaust velocity, m0 is initial mass, m1 is final mass (dry mass)
    delta_v = exhaust_velocity * math.log(current_total_mass / dry_mass)
    
    return delta_v

def calculate_fuel_consumption(delta_v: float, ship_type: str, ship_mass: float) -> float:
    """
    Calculate fuel consumption for a given delta-v maneuver.
    
    Args:
        delta_v: Required velocity change
        ship_type: Type of ship determining engine efficiency
        ship_mass: Total mass of the ship
        
    Returns:
        Fuel percentage consumed (0-100)
    """
    # Engine efficiency (exhaust velocity) depends on ship type
    exhaust_velocity = {
        "SHUTTLE": 5.0,
        "TRANSPORT": 4.0,
        "MILITARY": 6.0,
        "ADVANCED": 8.0
    }.get(ship_type, 5.0)
    
    # Calculate dry mass (ship without fuel)
    dry_mass = ship_mass * 0.7  # Assuming 30% of total mass is fuel at 100%
    
    # Calculate mass ratio using the rocket equation
    # delta-v = v_e * ln(m0/m1)
    # Therefore, m0/m1 = e^(delta-v/v_e)
    mass_ratio = math.exp(delta_v / exhaust_velocity)
    
    # Calculate initial mass needed
    initial_mass = dry_mass * mass_ratio
    
    # Calculate fuel mass needed
    fuel_mass_needed = initial_mass - dry_mass
    
    # Convert to percentage of maximum fuel
    max_fuel_mass = ship_mass * 0.3
    fuel_percentage = (fuel_mass_needed / max_fuel_mass) * 100
    
    return fuel_percentage

def calculate_mission_fuel_requirements(maneuvers: List[Dict], ship_type: str, ship_mass: float) -> Dict:
    """
    Calculate the total fuel requirements for a multi-maneuver mission.
    
    Args:
        maneuvers: List of dictionaries, each with a 'delta_v' key
        ship_type: Type of ship determining engine efficiency
        ship_mass: Total mass of the ship
        
    Returns:
        Dictionary with fuel requirements
    """
    # Sum the total delta-v required
    total_delta_v = sum(maneuver["delta_v"] for maneuver in maneuvers)
    
    # Calculate fuel consumption
    fuel_percentage = calculate_fuel_consumption(total_delta_v, ship_type, ship_mass)
    
    # Calculate maximum delta-v available with full fuel
    max_delta_v = calculate_delta_v_budget(ship_type, 100.0, ship_mass)
    
    return {
        "total_delta_v": total_delta_v,
        "fuel_percentage_required": fuel_percentage,
        "max_delta_v": max_delta_v,
        "is_possible": fuel_percentage <= 100.0,
        "margin": 100.0 - fuel_percentage if fuel_percentage <= 100.0 else 0.0
    }

def calculate_transfer_costs(origin_orbit: float, destination_orbit: float, central_mass: float, ship_type: str, ship_mass: float) -> Dict:
    """
    Calculate the fuel costs for different transfer options between orbits.
    
    Args:
        origin_orbit: Radius of origin orbit in AU
        destination_orbit: Radius of destination orbit in AU
        central_mass: Mass of the central body
        ship_type: Type of ship determining engine efficiency
        ship_mass: Total mass of the ship
        
    Returns:
        Dictionary with costs for different transfer options
    """
    from physics.transfer import calculate_hohmann_transfer, calculate_bi_elliptic_transfer
    
    # Calculate Hohmann transfer
    hohmann = calculate_hohmann_transfer(origin_orbit, destination_orbit, central_mass)
    hohmann_fuel = calculate_fuel_consumption(hohmann["total_delta_v"], ship_type, ship_mass)
    
    # Calculate bi-elliptic transfer with various intermediate points
    bi_elliptic_results = []
    
    # Try a range of intermediate radii
    if origin_orbit < destination_orbit:
        # Outbound transfer
        max_radius = destination_orbit * 5
        intermediate_points = [destination_orbit * 2, destination_orbit * 3, destination_orbit * 4, max_radius]
    else:
        # Inbound transfer
        max_radius = origin_orbit * 5
        intermediate_points = [origin_orbit * 2, origin_orbit * 3, origin_orbit * 4, max_radius]
    
    for r_intermediate in intermediate_points:
        bi_elliptic = calculate_bi_elliptic_transfer(origin_orbit, destination_orbit, r_intermediate, central_mass)
        bi_fuel = calculate_fuel_consumption(bi_elliptic["total_delta_v"], ship_type, ship_mass)
        
        bi_elliptic_results.append({
            "intermediate_radius": r_intermediate,
            "total_delta_v": bi_elliptic["total_delta_v"],
            "fuel_percentage": bi_fuel,
            "transfer_time": bi_elliptic["total_transfer_time"],
            "is_possible": bi_fuel <= 100.0
        })
    
    # Find the optimal bi-elliptic transfer (if any are possible)
    possible_bi_elliptic = [b for b in bi_elliptic_results if b["is_possible"]]
    optimal_bi_elliptic = min(possible_bi_elliptic, key=lambda x: x["fuel_percentage"]) if possible_bi_elliptic else None
    
    # Compare Hohmann and bi-elliptic
    if not hohmann_fuel <= 100.0:
        # Hohmann is not possible
        if optimal_bi_elliptic:
            recommended = "bi_elliptic"
        else:
            recommended = "impossible"
    else:
        # Hohmann is possible
        if optimal_bi_elliptic and optimal_bi_elliptic["fuel_percentage"] < hohmann_fuel:
            # Bi-elliptic is better
            recommended = "bi_elliptic"
        else:
            # Hohmann is better or bi-elliptic is not possible
            recommended = "hohmann"
    
    return {
        "hohmann": {
            "total_delta_v": hohmann["total_delta_v"],
            "fuel_percentage": hohmann_fuel,
            "transfer_time": hohmann["transfer_time"],
            "is_possible": hohmann_fuel <= 100.0
        },
        "bi_elliptic_options": bi_elliptic_results,
        "optimal_bi_elliptic": optimal_bi_elliptic,
        "recommended_transfer": recommended
    }

def calculate_ejection_delta_v(origin_orbit: float, ejection_velocity: float, central_mass: float) -> float:
    """
    Calculate the delta-v required to achieve escape velocity from an orbit.
    
    Args:
        origin_orbit: Radius of origin orbit in AU
        ejection_velocity: Desired velocity at infinity (v_inf)
        central_mass: Mass of the central body
        
    Returns:
        Delta-v required for ejection
    """
    # Convert AU to game units
    r = origin_orbit * AU
    
    # Calculate circular orbit velocity
    v_circular = math.sqrt(G * central_mass / r)
    
    # Calculate escape velocity
    v_escape = math.sqrt(2 * G * central_mass / r)
    
    # Calculate required velocity for the desired v_inf
    v_required = math.sqrt(v_escape**2 + ejection_velocity**2)
    
    # Delta-v is the difference between required velocity and circular velocity
    delta_v = v_required - v_circular
    
    return delta_v

def calculate_orbital_insertion_delta_v(approach_velocity: float, target_orbit: float, central_mass: float) -> float:
    """
    Calculate the delta-v required for orbital insertion from a hyperbolic approach.
    
    Args:
        approach_velocity: Hyperbolic approach velocity at infinity (v_inf)
        target_orbit: Radius of target orbit in AU
        central_mass: Mass of the central body
        
    Returns:
        Delta-v required for insertion
    """
    # Convert AU to game units
    r = target_orbit * AU
    
    # Calculate circular orbit velocity
    v_circular = math.sqrt(G * central_mass / r)
    
    # Calculate velocity at periapsis of the hyperbolic trajectory
    v_periapsis = math.sqrt(approach_velocity**2 + 2 * G * central_mass / r)
    
    # Delta-v is the difference between hyperbolic velocity and circular velocity
    delta_v = v_periapsis - v_circular
    
    return delta_v
