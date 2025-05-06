"""
Gravity assist calculations for Solar Dominion.
Implements the physics of using planetary gravity to alter spacecraft trajectory.
"""

import math
from typing import Tuple, Dict, List, Optional
import sys
import os

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import G, AU

def calculate_gravity_assist(approach_velocity: Tuple[float, float], 
                           planet_velocity: Tuple[float, float],
                           planet_mass: float,
                           closest_approach: float) -> Tuple[float, float]:
    """
    Calculate the effect of a gravity assist maneuver.
    
    Args:
        approach_velocity: Initial velocity vector of the spacecraft (vx, vy)
        planet_velocity: Velocity vector of the assisting planet (vx, vy)
        planet_mass: Mass of the assisting planet
        closest_approach: Closest approach distance to the planet's center
        
    Returns:
        Post-encounter velocity vector (vx, vy)
    """
    # Convert spacecraft velocity to the planet's reference frame
    rel_vx = approach_velocity[0] - planet_velocity[0]
    rel_vy = approach_velocity[1] - planet_velocity[1]
    
    # Calculate magnitude of the relative velocity
    v_rel = math.sqrt(rel_vx**2 + rel_vy**2)
    
    # Calculate the impact parameter (perpendicular distance to the asymptote of the hyperbola)
    # Using b = r_min * sqrt(1 + 2*G*M/(r_min*v^2))
    # where r_min is the closest approach distance
    impact_parameter = closest_approach * math.sqrt(1 + 2 * G * planet_mass / (closest_approach * v_rel**2))
    
    # Calculate the deflection angle
    # Using sin(θ/2) = 1 / sqrt(1 + (b*v^2/(G*M))^2)
    deflection_angle = 2 * math.asin(1 / math.sqrt(1 + (impact_parameter * v_rel**2 / (G * planet_mass))**2))
    
    # Calculate direction of the incoming velocity
    rel_angle = math.atan2(rel_vy, rel_vx)
    
    # Calculate the new velocity direction after deflection
    # The magnitude stays the same in the planet's reference frame
    new_rel_angle = rel_angle + deflection_angle
    
    # Calculate the new velocity components in the planet's reference frame
    new_rel_vx = v_rel * math.cos(new_rel_angle)
    new_rel_vy = v_rel * math.sin(new_rel_angle)
    
    # Convert back to the solar system reference frame
    new_vx = new_rel_vx + planet_velocity[0]
    new_vy = new_rel_vy + planet_velocity[1]
    
    return (new_vx, new_vy)

def calculate_max_velocity_change(approach_velocity: Tuple[float, float],
                                 planet_velocity: Tuple[float, float],
                                 planet_mass: float) -> float:
    """
    Calculate the maximum possible velocity change from a gravity assist.
    
    Args:
        approach_velocity: Initial velocity vector of the spacecraft
        planet_velocity: Velocity vector of the assisting planet
        planet_mass: Mass of the assisting planet
        
    Returns:
        Maximum possible delta-v from the gravity assist
    """
    # Calculate the relative velocity
    rel_vx = approach_velocity[0] - planet_velocity[0]
    rel_vy = approach_velocity[1] - planet_velocity[1]
    v_rel = math.sqrt(rel_vx**2 + rel_vy**2)
    
    # Calculate the planet's escape velocity
    # This is the theoretical limit for velocity change in a gravity assist
    escape_velocity = math.sqrt(2 * G * planet_mass / (planet_mass * 0.1))  # Assuming minimum safe approach
    
    # The maximum delta-v is approximately 2 * v_planet for a perfect assist
    planet_speed = math.sqrt(planet_velocity[0]**2 + planet_velocity[1]**2)
    
    # Return the minimum of the two theoretical limits
    return min(2 * planet_speed, 2 * v_rel)

def plan_gravity_assist(start_position: Tuple[float, float],
                       start_velocity: Tuple[float, float],
                       target_position: Tuple[float, float],
                       assisting_planet: Dict,
                       current_time: float) -> Dict:
    """
    Plan a gravity assist maneuver to reach a target position.
    
    Args:
        start_position: Starting position of the spacecraft
        start_velocity: Starting velocity of the spacecraft
        target_position: Desired target position
        assisting_planet: Dictionary with planet parameters
        current_time: Current game time
        
    Returns:
        Dictionary with gravity assist parameters
    """
    # Calculate the required velocity change to reach the target
    dx = target_position[0] - start_position[0]
    dy = target_position[1] - start_position[1]
    distance = math.sqrt(dx**2 + dy**2)
    
    # Calculate the direction to the target
    target_angle = math.atan2(dy, dx)
    
    # Calculate the planet's position at the current time
    planet_angle = (current_time % assisting_planet["period"]) / assisting_planet["period"] * 2 * math.pi
    planet_position = (
        assisting_planet["semi_major_axis"] * AU * math.cos(planet_angle),
        assisting_planet["semi_major_axis"] * AU * math.sin(planet_angle)
    )
    
    # Calculate the planet's velocity
    planet_speed = 2 * math.pi * assisting_planet["semi_major_axis"] * AU / assisting_planet["period"]
    planet_velocity = (
        -planet_speed * math.sin(planet_angle),
        planet_speed * math.cos(planet_angle)
    )
    
    # Calculate the angle of approach to maximize velocity in the target direction
    # This is a simplified approach, in reality this would be a complex optimization problem
    approach_angle = target_angle - math.pi/2  # Approach perpendicular to target direction
    
    # Calculate closest approach distance (minimum safe altitude)
    planet_radius = assisting_planet["radius"]
    closest_approach = planet_radius * 1.2  # 20% safety margin
    
    # Calculate the approach velocity needed
    approach_speed = math.sqrt(G * assisting_planet["mass"] / closest_approach)
    approach_velocity = (
        approach_speed * math.cos(approach_angle),
        approach_speed * math.sin(approach_angle)
    )
    
    # Calculate the post-assist velocity
    post_assist_velocity = calculate_gravity_assist(
        approach_velocity, planet_velocity, assisting_planet["mass"], closest_approach
    )
    
    # Calculate the delta-v required for the approach
    delta_v_approach = math.sqrt(
        (approach_velocity[0] - start_velocity[0])**2 +
        (approach_velocity[1] - start_velocity[1])**2
    )
    
    # Calculate the estimated time to reach the assisting planet
    dx_planet = planet_position[0] - start_position[0]
    dy_planet = planet_position[1] - start_position[1]
    distance_to_planet = math.sqrt(dx_planet**2 + dy_planet**2)
    time_to_planet = distance_to_planet / approach_speed
    
    # Return the gravity assist plan
    return {
        "planet_name": assisting_planet["name"],
        "closest_approach": closest_approach / AU,  # Convert to AU
        "approach_velocity": approach_velocity,
        "post_assist_velocity": post_assist_velocity,
        "delta_v_approach": delta_v_approach,
        "estimated_time_to_planet": time_to_planet,
        "execution_time": current_time + time_to_planet
    }

def generate_gravity_assist_trajectory(spacecraft_position: Tuple[float, float],
                                      spacecraft_velocity: Tuple[float, float],
                                      planet_position: Tuple[float, float],
                                      planet_velocity: Tuple[float, float],
                                      planet_mass: float,
                                      closest_approach: float,
                                      num_points: int = 50) -> List[Tuple[float, float]]:
    """
    Generate points along a gravity assist trajectory for visualization.
    
    Args:
        spacecraft_position: Initial spacecraft position
        spacecraft_velocity: Initial spacecraft velocity
        planet_position: Planet position at encounter
        planet_velocity: Planet velocity at encounter
        planet_mass: Mass of the planet
        closest_approach: Closest approach distance
        num_points: Number of points to generate
        
    Returns:
        List of positions along the trajectory
    """
    # Convert to planet-centered coordinates
    rel_pos_x = spacecraft_position[0] - planet_position[0]
    rel_pos_y = spacecraft_position[1] - planet_position[1]
    
    # Convert velocity to planet's reference frame
    rel_vel_x = spacecraft_velocity[0] - planet_velocity[0]
    rel_vel_y = spacecraft_velocity[1] - planet_velocity[1]
    
    # Calculate relative velocity magnitude
    v_rel = math.sqrt(rel_vel_x**2 + rel_vel_y**2)
    
    # Calculate the energy and angular momentum of the hyperbolic orbit
    energy = 0.5 * v_rel**2 - G * planet_mass / math.sqrt(rel_pos_x**2 + rel_pos_y**2)
    h = rel_pos_x * rel_vel_y - rel_pos_y * rel_vel_x
    
    # Calculate the semi-major axis and eccentricity of the hyperbola
    a = -G * planet_mass / (2 * energy)  # Negative for hyperbola
    eccentricity = math.sqrt(1 + 2 * energy * h**2 / (G * planet_mass)**2)
    
    # Calculate the range of true anomaly for the hyperbolic encounter
    # For a hyperbola, true anomaly has a limit of arccos(-1/e)
    max_anomaly = math.acos(-1/eccentricity)
    
    # Generate points along the hyperbolic trajectory
    points = []
    
    for i in range(num_points):
        # Interpolate from -max_anomaly to +max_anomaly
        true_anomaly = -max_anomaly + 2 * max_anomaly * i / (num_points - 1)
        
        # Calculate radius at this true anomaly
        r = a * (1 - eccentricity**2) / (1 + eccentricity * math.cos(true_anomaly))
        
        # Calculate position in planet-centered coordinates
        x = r * math.cos(true_anomaly)
        y = r * math.sin(true_anomaly)
        
        # Convert back to solar system coordinates
        solar_x = x + planet_position[0]
        solar_y = y + planet_position[1]
        
        points.append((solar_x, solar_y))
    
    return points

def evaluate_gravity_assist_opportunities(spacecraft_position: Tuple[float, float],
                                        spacecraft_velocity: Tuple[float, float],
                                        target_position: Tuple[float, float],
                                        planets: List[Dict],
                                        current_time: float) -> List[Dict]:
    """
    Evaluate potential gravity assist opportunities to reach a target.
    
    Args:
        spacecraft_position: Current spacecraft position
        spacecraft_velocity: Current spacecraft velocity
        target_position: Desired target position
        planets: List of dictionaries with planet data
        current_time: Current game time
        
    Returns:
        List of dictionaries with gravity assist opportunities, sorted by efficiency
    """
    opportunities = []
    
    for planet in planets:
        # Skip planets that are too small for effective gravity assists
        if planet["mass"] < 10:  # Arbitrary threshold, adjust as needed
            continue
        
        # Calculate the planet's current position
        planet_angle = (current_time % planet["period"]) / planet["period"] * 2 * math.pi
        planet_position = (
            planet["semi_major_axis"] * AU * math.cos(planet_angle),
            planet["semi_major_axis"] * AU * math.sin(planet_angle)
        )
        
        # Calculate the planet's velocity
        planet_speed = 2 * math.pi * planet["semi_major_axis"] * AU / planet["period"]
        planet_velocity = (
            -planet_speed * math.sin(planet_angle),
            planet_speed * math.cos(planet_angle)
        )
        
        # Calculate potential gravity assist
        closest_approach = planet["radius"] * 1.2  # 20% safety margin
        
        # Simple check if planet is in a useful direction
        # This is a very simplified approach
        dx_planet = planet_position[0] - spacecraft_position[0]
        dy_planet = planet_position[1] - spacecraft_position[1]
        dx_target = target_position[0] - spacecraft_position[0]
        dy_target = target_position[1] - spacecraft_position[1]
        
        # Calculate angles
        planet_angle = math.atan2(dy_planet, dx_planet)
        target_angle = math.atan2(dy_target, dx_target)
        
        # Calculate angle difference
        angle_diff = abs(planet_angle - target_angle)
        while angle_diff > math.pi:
            angle_diff = 2 * math.pi - angle_diff
        
        # Skip planets that are in the completely wrong direction
        if angle_diff > math.pi * 0.75:
            continue
        
        # Calculate maximum velocity change possible
        max_delta_v = calculate_max_velocity_change(
            spacecraft_velocity, planet_velocity, planet["mass"]
        )
        
        # Calculate distance to planet
        distance_to_planet = math.sqrt(dx_planet**2 + dy_planet**2)
        
        # Simplified estimation of travel time to planet
        current_speed = math.sqrt(spacecraft_velocity[0]**2 + spacecraft_velocity[1]**2)
        estimated_time = distance_to_planet / current_speed
        
        # Add to opportunities list
        opportunities.append({
            "planet_name": planet["name"],
            "max_delta_v": max_delta_v,
            "distance": distance_to_planet / AU,  # Convert to AU
            "estimated_time": estimated_time,
            "angle_to_target": angle_diff,
            "position": planet_position,
            "velocity": planet_velocity,
            "mass": planet["mass"],
            "closest_approach": closest_approach
        })
    
    # Sort by a combination of maximum delta-v and angle to target
    # This is a simple heuristic, could be improved
    for opp in opportunities:
        opp["score"] = opp["max_delta_v"] * (1 - opp["angle_to_target"] / math.pi)
    
    opportunities.sort(key=lambda x: x["score"], reverse=True)
    
    return opportunities
