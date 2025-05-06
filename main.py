"""
Solar Dominion: The Faction Wars
Main game module
"""

import pygame
import sys
import math
from enum import Enum
from typing import Dict, List, Tuple, Optional

# Import our modules
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BG_COLOR, GRID_COLOR, TEXT_COLOR,
    AU, G, DAY_PER_SECOND, EARTH_YEAR,
    ORBITAL_PARAMETERS, MOON_PARAMETERS, SHIP_TYPES
)

from physics.orbital import (
    calculate_orbital_position,
    calculate_orbital_velocity,
    calculate_orbital_period
)

from physics.transfer import (
    calculate_hohmann_transfer,
    calculate_bi_elliptic_transfer,
    generate_hohmann_trajectory_points
)

from physics.gravity_assist import (
    calculate_gravity_assist,
    evaluate_gravity_assist_opportunities
)

from physics.delta_v import (
    calculate_delta_v_budget,
    calculate_fuel_consumption,
    calculate_transfer_costs
)

from ui.trajectory_plotter import TrajectoryPlotter

# Define game state class
class GameState:
    def __init__(self):
        self.time = 0.0  # Game time in days
        self.time_scale = 1.0  # Time acceleration
        self.celestial_bodies = []
        self.ships = []
        self.habitats = []
        self.transfers = []
        
        # Camera settings
        self.camera_offset = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]
        self.zoom = 0.5
        
        # UI state
        self.selected_object = None
        self.show_orbits = True
        self.show_grid = True
        self.show_trajectories = True
        self.show_transfer_planning = False
        self.transfer_origin = None
        self.transfer_destination = None
        
        # Initialize solar system
        self.initialize_solar_system()
    
    def initialize_solar_system(self):
        """Initialize the celestial bodies in the solar system."""
        # Create the Sun
        self.celestial_bodies.append({
            "name": "Sun",
            "mass": ORBITAL_PARAMETERS["SUN"]["mass"],
            "radius": ORBITAL_PARAMETERS["SUN"]["radius"],
            "color": ORBITAL_PARAMETERS["SUN"]["color"],
            "semi_major_axis": 0,
            "orbital_period": 0,
            "position": (0, 0),
            "velocity": (0, 0),
            "angle": 0
        })
        
        # Create planets
        for name, params in ORBITAL_PARAMETERS.items():
            if name == "SUN":
                continue
                
            # Calculate initial position
            position = calculate_orbital_position(params["semi_major_axis"], 0)
            
            # Calculate orbital velocity
            velocity = calculate_orbital_velocity(ORBITAL_PARAMETERS["SUN"]["mass"], params["semi_major_axis"])
            
            # Create planet
            self.celestial_bodies.append({
                "name": name,
                "mass": params["mass"],
                "radius": params["radius"],
                "color": params["color"],
                "semi_major_axis": params["semi_major_axis"],
                "orbital_period": params["period"],
                "position": position,
                "velocity": (0, velocity),  # Initial velocity is perpendicular to radius
                "angle": 0
            })
        
        # Create moons
        for name, params in MOON_PARAMETERS.items():
            # Find the parent planet
            parent = None
            for body in self.celestial_bodies:
                if body["name"] == params["parent"]:
                    parent = body
                    break
            
            if parent is None:
                continue
            
            # Calculate initial position relative to parent
            rel_position = calculate_orbital_position(params["semi_major_axis"], 0)
            position = (parent["position"][0] + rel_position[0], parent["position"][1] + rel_position[1])
            
            # Calculate orbital velocity
            velocity = calculate_orbital_velocity(parent["mass"], params["semi_major_axis"])
            
            # Create moon
            self.celestial_bodies.append({
                "name": name,
                "mass": params["mass"],
                "radius": params["radius"],
                "color": params["color"],
                "semi_major_axis": params["semi_major_axis"],
                "orbital_period": params["period"],
                "position": position,
                "velocity": (0, velocity),  # Initial velocity is perpendicular to radius
                "angle": 0,
                "parent": params["parent"]
            })
        
        # Calculate Earth orbit parameters for ships
        earth_orbit_radius = ORBITAL_PARAMETERS["EARTH"]["semi_major_axis"] * AU
        earth_orbital_velocity = calculate_orbital_velocity(ORBITAL_PARAMETERS["SUN"]["mass"], 
                                                    ORBITAL_PARAMETERS["EARTH"]["semi_major_axis"])
        
        # Create some initial ships
        # Earth ship
        earth_ship_angle = math.pi / 4  # 45 degrees offset from Earth
        earth_ship = {
            "name": "UNSS Explorer",
            "type": "SHUTTLE",
            "faction": "EARTH",
            "position": (earth_orbit_radius * math.cos(earth_ship_angle), 
                        earth_orbit_radius * math.sin(earth_ship_angle)),
            "velocity": (earth_orbital_velocity * math.cos(earth_ship_angle + math.pi/2),
                        earth_orbital_velocity * math.sin(earth_ship_angle + math.pi/2)),
            "mass": SHIP_TYPES["SHUTTLE"]["mass"],
            "fuel": 100.0,  # Percentage
            "crew": 5,
            "destination": None,
            "trajectory": None,
            "mission": None
        }
        self.ships.append(earth_ship)
        
        # Mars ship
        mars_ship = {
            "name": "MCR Tachi",
            "type": "MILITARY",
            "faction": "MARS",
            "position": (ORBITAL_PARAMETERS["MARS"]["semi_major_axis"] * AU * 0.9, 0),
            "velocity": (0, calculate_orbital_velocity(ORBITAL_PARAMETERS["SUN"]["mass"], 
                                                  ORBITAL_PARAMETERS["MARS"]["semi_major_axis"] * 0.9)),
            "mass": SHIP_TYPES["MILITARY"]["mass"],
            "fuel": 80.0,  # Percentage
            "crew": 10,
            "destination": None,
            "trajectory": None,
            "mission": None
        }
        self.ships.append(mars_ship)
    
    
    
    
    
    
    def update(self, dt: float):
        """
        Update the game state.
        
        Args:
            dt: Time delta in seconds
        """
        # Apply time scaling
        game_dt = dt * self.time_scale
        self.time += DAY_PER_SECOND * game_dt
        
        # Update positions of celestial bodies
        for body in self.celestial_bodies:
            # Skip the Sun
            if body["name"] == "SUN":
                continue
                
            # Skip bodies with zero orbital period
            if body["orbital_period"] == 0:
                continue
                
            if "parent" in body:
                # This is a moon, orbit around its parent
                parent = None
                for p in self.celestial_bodies:
                    if p["name"] == body["parent"]:
                        parent = p
                        break
                
                if parent:
                    # Update angle
                    angle_change = (2 * math.pi / body["orbital_period"]) * DAY_PER_SECOND * game_dt
                    body["angle"] += angle_change
                    
                    # Calculate new position relative to parent
                    rel_position = calculate_orbital_position(body["semi_major_axis"], body["angle"])
                    
                    # Update position
                    body["position"] = (
                        parent["position"][0] + rel_position[0],
                        parent["position"][1] + rel_position[1]
                    )
                    
                    # Update velocity (simplified)
                    orbit_vel = calculate_orbital_velocity(parent["mass"], body["semi_major_axis"])
                    vel_angle = body["angle"] + math.pi/2  # Velocity is perpendicular to radius
                    
                    body["velocity"] = (
                        orbit_vel * math.cos(vel_angle) + parent["velocity"][0],
                        orbit_vel * math.sin(vel_angle) + parent["velocity"][1]
                    )
            else:
                # This is a planet, orbit around the sun
                # Update angle
                angle_change = (2 * math.pi / body["orbital_period"]) * DAY_PER_SECOND * game_dt
                body["angle"] += angle_change
                
                # Update position
                body["position"] = calculate_orbital_position(body["semi_major_axis"], body["angle"])
                
                # Update velocity
                orbit_vel = calculate_orbital_velocity(ORBITAL_PARAMETERS["SUN"]["mass"], body["semi_major_axis"])
                vel_angle = body["angle"] + math.pi/2  # Velocity is perpendicular to radius
                
                body["velocity"] = (
                    orbit_vel * math.cos(vel_angle),
                    orbit_vel * math.sin(vel_angle)
                )
        
        # Update ships
        for ship in self.ships:
            # Check for active missions
            if ship["mission"] and ship["mission"]["type"] == "hohmann_transfer":
                mission = ship["mission"]
                
                # Check if it's time for the arrival burn
                if self.time >= mission["arrival_time"]:
                    # Calculate position relative to target orbit
                    target_radius = mission["target_orbit_radius"]
                    ship_pos = ship["position"]
                    ship_radius = math.sqrt(ship_pos[0]**2 + ship_pos[1]**2)
                    
                    # Only execute if we're close to the target radius
                    if abs(ship_radius - target_radius) / target_radius < 0.1:
                        # Calculate current angle
                        ship_angle = math.atan2(ship_pos[1], ship_pos[0])
                        
                        # Calculate velocity direction (perpendicular to position)
                        vel_angle = ship_angle + math.pi/2
                        
                        # Apply the arrival burn
                        delta_v = mission["delta_v2"]
                        
                        # Calculate fuel consumption
                        fuel_required = calculate_fuel_consumption(
                            delta_v,
                            ship["type"],
                            ship["mass"]
                        )
                        
                        if fuel_required <= ship["fuel"]:
                            # Consume fuel
                            ship["fuel"] -= fuel_required
                            
                            # Calculate orbit velocity at current radius
                            orbit_vel = calculate_orbital_velocity(ORBITAL_PARAMETERS["SUN"]["mass"], ship_radius / AU)
                            
                            # Set to proper circular orbit velocity
                            ship["velocity"] = (
                                orbit_vel * math.cos(vel_angle),
                                orbit_vel * math.sin(vel_angle)
                            )
                            
                            print(f"Transfer completed: {ship['name']} arrived at {mission['target_body']}")
                        else:
                            print(f"Not enough fuel for arrival burn! Required: {fuel_required:.1f}%, Available: {ship['fuel']:.1f}%")
                        
                        # Clear mission and trajectory
                        ship["mission"] = None
                        ship["trajectory"] = None
            
            # If ship is not on a transfer mission, perform station-keeping
            elif ship["destination"] is None and ship["trajectory"] is None and ship["fuel"] > 0:
                # Calculate current orbital elements
                position = ship["position"]
                velocity = ship["velocity"]
                
                # Calculate orbital parameters
                r = math.sqrt(position[0]**2 + position[1]**2)
                v = math.sqrt(velocity[0]**2 + velocity[1]**2)
                
                # Calculate current orbit parameters using the function from GameRenderer
                orbital_elements = self.calculate_orbital_elements(position, velocity)
                
                # Check if orbit is deteriorating
                if orbital_elements["eccentricity"] > 0.01:  # Allow slight elliptical orbits
                    # Calculate circular orbit velocity at current radius
                    angle = math.atan2(position[1], position[0])
                    ideal_velocity = calculate_orbital_velocity(ORBITAL_PARAMETERS["SUN"]["mass"], r/AU)
                    
                    # Calculate ideal velocity vector (perpendicular to position)
                    ideal_vel_x = ideal_velocity * math.cos(angle + math.pi/2)
                    ideal_vel_y = ideal_velocity * math.sin(angle + math.pi/2)
                    
                    # Calculate velocity correction needed
                    correction_x = ideal_vel_x - velocity[0]
                    correction_y = ideal_vel_y - velocity[1]
                    correction_magnitude = math.sqrt(correction_x**2 + correction_y**2)
                    
                    # Apply small correction if needed (station-keeping)
                    if correction_magnitude > 0.01:
                        # Use only a fraction of the correction to conserve fuel
                        correction_factor = min(0.1, correction_magnitude / 10)
                        
                        # Apply the correction
                        ship["velocity"] = (
                            velocity[0] + correction_x * correction_factor,
                            velocity[1] + correction_y * correction_factor
                        )
                        
                        # Consume a tiny amount of fuel for station-keeping
                        ship["fuel"] = max(0, ship["fuel"] - 0.01)
            
            # Apply gravitational forces from all bodies
            total_force_x = 0
            total_force_y = 0
            
            for body in self.celestial_bodies:
                dx = body["position"][0] - ship["position"][0]
                dy = body["position"][1] - ship["position"][1]
                distance_sq = dx*dx + dy*dy
                
                # Skip if too close (prevents division by zero)
                if distance_sq < 1:
                    continue
                
                distance = math.sqrt(distance_sq)
                
                # Calculate gravitational force
                force_magnitude = G * body["mass"] / distance_sq
                
                # Add to total force
                total_force_x += dx / distance * force_magnitude
                total_force_y += dy / distance * force_magnitude
            
            # Update velocity (F = ma, but we're working with acceleration directly)
            ship["velocity"] = (
                ship["velocity"][0] + total_force_x * game_dt,
                ship["velocity"][1] + total_force_y * game_dt
            )
            
            # Update position based on velocity
            ship["position"] = (
                ship["position"][0] + ship["velocity"][0] * game_dt,
                ship["position"][1] + ship["velocity"][1] * game_dt
            )
        
    # Calculate orbital elements for ships
    def calculate_orbital_elements(self, position, velocity):
        """Calculate orbital elements from position and velocity"""
        # Calculate distance and speed
        r = math.sqrt(position[0]**2 + position[1]**2)
        v = math.sqrt(velocity[0]**2 + velocity[1]**2)
        
        # Calculate specific energy
        energy = 0.5 * v**2 - G * ORBITAL_PARAMETERS["SUN"]["mass"] / r
        
        # Calculate specific angular momentum
        h = position[0] * velocity[1] - position[1] * velocity[0]
        
        # Calculate semi-major axis
        if energy >= 0:
            # Hyperbolic orbit
            semi_major_axis = -G * ORBITAL_PARAMETERS["SUN"]["mass"] / (2 * energy)
        else:
            # Elliptical orbit
            semi_major_axis = -G * ORBITAL_PARAMETERS["SUN"]["mass"] / (2 * energy)
        
        # Calculate eccentricity
        eccentricity = math.sqrt(1 + 2 * energy * h**2 / (G * ORBITAL_PARAMETERS["SUN"]["mass"])**2)
        
        # Calculate orbital period (only for elliptical orbits)
        period = None
        if eccentricity < 1:
            period = 2 * math.pi * math.sqrt(semi_major_axis**3 / (G * ORBITAL_PARAMETERS["SUN"]["mass"]))
        
        return {
            "semi_major_axis": semi_major_axis / AU,  # Convert to AU
            "eccentricity": eccentricity,
            "energy": energy,
            "angular_momentum": h,
            "period": period
        }




        
            
# Rendering class
class GameRenderer:
    def __init__(self, game_state):
        self.game_state = game_state
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Solar Dominion - Vector Prototype")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 15)
        self.large_font = pygame.font.SysFont("monospace", 24)
        
        # Create trajectory plotter
        self.trajectory_plotter = TrajectoryPlotter(
            self.screen, 
            self.game_state.camera_offset, 
            self.game_state.zoom
        )
    
    def world_to_screen(self, pos):
        """Convert world coordinates to screen coordinates"""
        x = pos[0] * self.game_state.zoom + self.game_state.camera_offset[0]
        y = pos[1] * self.game_state.zoom + self.game_state.camera_offset[1]
        return int(x), int(y)
        
    def screen_to_world(self, pos):
        """Convert screen coordinates to world coordinates"""
        x = (pos[0] - self.game_state.camera_offset[0]) / self.game_state.zoom
        y = (pos[1] - self.game_state.camera_offset[1]) / self.game_state.zoom
        return x, y
        
    def draw_grid(self):
        """Draw a reference grid"""
        if not self.game_state.show_grid:
            return
            
        grid_size = 50 * self.game_state.zoom
        
        # Calculate grid boundaries
        left = -self.game_state.camera_offset[0] / self.game_state.zoom
        right = (SCREEN_WIDTH - self.game_state.camera_offset[0]) / self.game_state.zoom
        top = -self.game_state.camera_offset[1] / self.game_state.zoom
        bottom = (SCREEN_HEIGHT - self.game_state.camera_offset[1]) / self.game_state.zoom
        
        # Calculate grid start and end points
        start_x = math.floor(left / grid_size) * grid_size
        end_x = math.ceil(right / grid_size) * grid_size
        start_y = math.floor(top / grid_size) * grid_size
        end_y = math.ceil(bottom / grid_size) * grid_size
        
        # Draw vertical lines
        x = start_x
        while x <= end_x:
            start_pos = self.world_to_screen((x, start_y))
            end_pos = self.world_to_screen((x, end_y))
            pygame.draw.line(self.screen, GRID_COLOR, start_pos, end_pos, 1)
            x += grid_size
            
        # Draw horizontal lines
        y = start_y
        while y <= end_y:
            start_pos = self.world_to_screen((start_x, y))
            end_pos = self.world_to_screen((end_x, y))
            pygame.draw.line(self.screen, GRID_COLOR, start_pos, end_pos, 1)
            y += grid_size
            
    def draw_celestial_bodies(self):
        """Draw planets, moons, etc."""
        for body in self.game_state.celestial_bodies:
            pos = self.world_to_screen(body["position"])
            # Only draw if on screen
            if 0 <= pos[0] <= SCREEN_WIDTH and 0 <= pos[1] <= SCREEN_HEIGHT:
                radius = max(1, int(body["radius"] * self.game_state.zoom))
                pygame.draw.circle(self.screen, body["color"], pos, radius)
                
                # Draw name if zoom level is sufficient
                if self.game_state.zoom > 0.5:
                    name_surface = self.font.render(body["name"], True, TEXT_COLOR)
                    name_rect = name_surface.get_rect(center=(pos[0], pos[1] - radius - 10))
                    self.screen.blit(name_surface, name_rect)
            
            # Draw orbit if this is a planet (not the Sun)
            if self.game_state.show_orbits and "semi_major_axis" in body and body["semi_major_axis"] > 0:
                # For moons, draw orbit around parent
                if "parent" in body:
                    parent = None
                    for p in self.game_state.celestial_bodies:
                        if p["name"] == body["parent"]:
                            parent = p
                            break
                    
                    if parent:
                        parent_pos = self.world_to_screen(parent["position"])
                        orbit_radius = int(body["semi_major_axis"] * self.game_state.zoom)
                        pygame.draw.circle(self.screen, GRID_COLOR, parent_pos, orbit_radius, 1)
                else:
                    # For planets, draw orbit around Sun
                    sun_pos = self.world_to_screen((0, 0))
                    orbit_radius = int(body["semi_major_axis"] * AU * self.game_state.zoom)
                    pygame.draw.circle(self.screen, GRID_COLOR, sun_pos, orbit_radius, 1)
                    
                    
                    
    
    def draw_ships(self):
        """Draw ships"""
        for ship in self.game_state.ships:
            pos = self.world_to_screen(ship["position"])
            
            # Only draw if on screen
            if 0 <= pos[0] <= SCREEN_WIDTH and 0 <= pos[1] <= SCREEN_HEIGHT:
                # Draw ship as a triangle
                size = max(3, int(5 * self.game_state.zoom))
                
                # Calculate direction based on velocity
                velocity = ship["velocity"]
                if velocity[0] != 0 or velocity[1] != 0:
                    angle = math.atan2(velocity[1], velocity[0])
                else:
                    angle = 0
                
                # Calculate triangle points
                points = [
                    (pos[0] + size * math.cos(angle), pos[1] + size * math.sin(angle)),
                    (pos[0] + size * math.cos(angle + 2.5), pos[1] + size * math.sin(angle + 2.5)),
                    (pos[0] + size * math.cos(angle - 2.5), pos[1] + size * math.sin(angle - 2.5))
                ]
                
                # Color based on faction
                if ship["faction"] == "EARTH":
                    color = (0, 100, 255)
                elif ship["faction"] == "MARS":
                    color = (255, 100, 0)
                else:
                    color = (150, 150, 150)
                
                pygame.draw.polygon(self.screen, color, points)
                
                # Draw ship name if selected or zoom level is high
                if self.game_state.selected_object == ship or self.game_state.zoom > 1.5:
                    name_surface = self.font.render(ship["name"], True, TEXT_COLOR)
                    name_rect = name_surface.get_rect(center=(pos[0], pos[1] - 15))
                    self.screen.blit(name_surface, name_rect)
                
                # Draw selection indicator if selected
                if self.game_state.selected_object == ship:
                    pygame.draw.polygon(self.screen, (255, 255, 255), points, 1)
                
                # Draw trajectory if planned
                if ship["trajectory"] and self.game_state.show_trajectories:
                    trajectory_points = [(p[0], p[1]) for p in ship["trajectory"]]
                    self.trajectory_plotter.draw_trajectory(trajectory_points, (100, 100, 200), 1)
    
    def draw_transfers(self):
        """Draw planned transfers"""
        # Update trajectory plotter with current camera settings
        self.trajectory_plotter.update_camera(
            self.game_state.camera_offset,
            self.game_state.zoom
        )
        
        # Draw any active transfers
        for transfer in self.game_state.transfers:
            if transfer["type"] == "hohmann":
                self.trajectory_plotter.draw_hohmann_transfer(
                    transfer["start_orbit"],
                    transfer["end_orbit"],
                    transfer["start_angle"],
                    (150, 200, 100)
                )
            elif transfer["type"] == "bi_elliptic":
                self.trajectory_plotter.draw_bi_elliptic_transfer(
                    transfer["start_orbit"],
                    transfer["end_orbit"],
                    transfer["intermediate_orbit"],
                    transfer["start_angle"],
                    (200, 150, 100)
                )
            elif transfer["type"] == "gravity_assist":
                self.trajectory_plotter.draw_gravity_assist(
                    transfer["planet_position"],
                    transfer["approach_angle"],
                    transfer["deflection_angle"],
                    transfer["approach_distance"],
                    (100, 200, 200)
                )
        
        # If in transfer planning mode, draw visualization
        if self.game_state.show_transfer_planning and self.game_state.transfer_origin and self.game_state.transfer_destination:
            origin = self.game_state.transfer_origin
            destination = self.game_state.transfer_destination
            
            # Find orbital radii
            origin_radius = math.sqrt(origin["position"][0]**2 + origin["position"][1]**2)
            dest_radius = math.sqrt(destination["position"][0]**2 + destination["position"][1]**2)
            
            # Calculate current angles
            origin_angle = math.atan2(origin["position"][1], origin["position"][0])
            dest_angle = math.atan2(destination["position"][1], destination["position"][0])
            
            # Draw Hohmann transfer
            self.trajectory_plotter.draw_hohmann_transfer(
                origin_radius,
                dest_radius,
                origin_angle,
                (150, 200, 100)
            )
            
            # Calculate and display delta-v requirements
            transfer_data = calculate_hohmann_transfer(
                origin_radius / AU, 
                dest_radius / AU, 
                ORBITAL_PARAMETERS["SUN"]["mass"]
            )
            
            # Draw delta-v indicators
            origin_screen = self.world_to_screen(origin["position"])
            dest_screen = self.world_to_screen(destination["position"])
            
            # Show delta-v requirements
            dv1_text = self.font.render(f"ΔV₁: {transfer_data['delta_v1']:.2f}", True, (150, 200, 100))
            dv2_text = self.font.render(f"ΔV₂: {transfer_data['delta_v2']:.2f}", True, (150, 200, 100))
            total_text = self.font.render(f"Total: {transfer_data['total_delta_v']:.2f}", True, (150, 200, 100))
            time_text = self.font.render(f"Time: {transfer_data['transfer_time']:.1f} days", True, (150, 200, 100))
            
            self.screen.blit(dv1_text, (origin_screen[0] + 20, origin_screen[1] - 30))
            self.screen.blit(dv2_text, (dest_screen[0] + 20, dest_screen[1] - 30))
            self.screen.blit(total_text, (SCREEN_WIDTH - 150, 60))
            self.screen.blit(time_text, (SCREEN_WIDTH - 150, 80))
            
            # If a ship is selected, show if transfer is possible
            if self.game_state.selected_object and "type" in self.game_state.selected_object:
                ship = self.game_state.selected_object
                
                # Calculate fuel consumption
                fuel_required = calculate_fuel_consumption(
                    transfer_data["total_delta_v"],
                    ship["type"],
                    ship["mass"]
                )
                
                fuel_text = self.font.render(
                    f"Fuel required: {fuel_required:.1f}% (Available: {ship['fuel']:.1f}%)",
                    True,
                    (150, 200, 100) if fuel_required <= ship["fuel"] else (200, 100, 100)
                )
                
                self.screen.blit(fuel_text, (SCREEN_WIDTH - 300, 100))
    
    def draw_ui(self):
        """Draw user interface elements"""
        # Draw time info
        days = int(self.game_state.time % 365)
        years = int(self.game_state.time // 365)
        time_text = f"Year {years}, Day {days} - Speed: {self.game_state.time_scale}x"
        time_surface = self.large_font.render(time_text, True, TEXT_COLOR)
        self.screen.blit(time_surface, (10, 10))
        
        # Draw fuel gauge for all ships in the top-right corner
        y_offset = 50
        for ship in self.game_state.ships:
            # Draw ship name
            name_surface = self.font.render(ship["name"], True, TEXT_COLOR)
            self.screen.blit(name_surface, (SCREEN_WIDTH - 200, y_offset))
            
            # Draw fuel bar
            bar_width = 150
            bar_height = 10
            bar_filled = int(bar_width * ship["fuel"] / 100.0)
            
            # Background bar
            bar_bg_rect = pygame.Rect(SCREEN_WIDTH - 200, y_offset + 20, bar_width, bar_height)
            pygame.draw.rect(self.screen, (50, 50, 50), bar_bg_rect)
            
            # Filled portion
            bar_fill_rect = pygame.Rect(SCREEN_WIDTH - 200, y_offset + 20, bar_filled, bar_height)
            
            # Color based on fuel level
            if ship["fuel"] > 50:
                color = (0, 200, 0)  # Green
            elif ship["fuel"] > 25:
                color = (200, 200, 0)  # Yellow
            else:
                color = (200, 0, 0)  # Red
                
            pygame.draw.rect(self.screen, color, bar_fill_rect)
            
            # Draw fuel percentage
            fuel_text = self.font.render(f"{ship['fuel']:.1f}%", True, TEXT_COLOR)
            self.screen.blit(fuel_text, (SCREEN_WIDTH - 40, y_offset + 15))
            
            # Calculate and show current orbit info
            position = ship["position"]
            velocity = ship["velocity"]
            r = math.sqrt(position[0]**2 + position[1]**2)
            
            # Show distance from Sun in AU
            distance_text = self.font.render(f"Dist: {r/AU:.2f} AU", True, TEXT_COLOR)
            self.screen.blit(distance_text, (SCREEN_WIDTH - 200, y_offset + 40))
            
            # Show if on mission
            if ship["mission"]:
                mission_text = self.font.render("On mission", True, (150, 200, 100))
                self.screen.blit(mission_text, (SCREEN_WIDTH - 100, y_offset + 40))
            
            y_offset += 70
        
        # Draw selected object info
        if self.game_state.selected_object:
            obj = self.game_state.selected_object
            info_text = []
            
            if "name" in obj:
                info_text.append(f"Name: {obj['name']}")
            
            if "type" in obj:
                # This is a ship
                info_text.append(f"Type: {obj['type']}")
                info_text.append(f"Faction: {obj['faction']}")
                info_text.append(f"Fuel: {obj['fuel']:.1f}%")
                info_text.append(f"Mass: {obj['mass']}")
                
                # Calculate current orbit parameters
                position = obj["position"]
                velocity = obj["velocity"]
                r = math.sqrt(position[0]**2 + position[1]**2)
                v = math.sqrt(velocity[0]**2 + velocity[1]**2)
                
                # Calculate orbital elements
                orbital_elements = self.calculate_orbital_elements(position, velocity)
                
                if orbital_elements["eccentricity"] < 1:
                    # Elliptical orbit
                    info_text.append(f"Orbit: {orbital_elements['semi_major_axis']:.2f} AU, e={orbital_elements['eccentricity']:.2f}")
                    info_text.append(f"Period: {orbital_elements['period']:.1f} days")
                else:
                    # Hyperbolic trajectory
                    info_text.append(f"Trajectory: Hyperbolic, e={orbital_elements['eccentricity']:.2f}")
                
                # Show available delta-v
                delta_v = calculate_delta_v_budget(obj["type"], obj["fuel"], obj["mass"])
                info_text.append(f"Available ΔV: {delta_v:.2f}")
                
                # Show mission info if on mission
                if obj["mission"]:
                    mission = obj["mission"]
                    info_text.append(f"Mission: {mission['type']}")
                    info_text.append(f"Target: {mission['target_body']}")
                    
                    # Time remaining
                    time_remaining = mission["arrival_time"] - self.game_state.time
                    info_text.append(f"Arrival in: {time_remaining:.1f} days")
            else:
                # This is a celestial body
                info_text.append(f"Mass: {obj['mass']}")
                
                if "semi_major_axis" in obj and obj["semi_major_axis"] > 0:
                    info_text.append(f"Orbit: {obj['semi_major_axis']:.2f} AU")
                    info_text.append(f"Period: {obj['orbital_period']:.1f} days")
            
            # Draw info box
            y_offset = 50
            for text in info_text:
                text_surface = self.font.render(text, True, TEXT_COLOR)
                self.screen.blit(text_surface, (10, y_offset))
                y_offset += 20
                
            # Draw transfer planning controls if a ship is selected
            if "type" in obj:
                # Transfer planning button
                plan_button = pygame.Rect(10, y_offset + 20, 200, 30)
                # Store for reference in input handler
                self.plan_button_rect = plan_button  
                pygame.draw.rect(
                    self.screen, 
                    (100, 100, 150) if self.game_state.show_transfer_planning else (50, 50, 100), 
                    plan_button
                )
                
                plan_text = self.font.render("Plan Transfer", True, TEXT_COLOR)
                plan_text_rect = plan_text.get_rect(center=plan_button.center)
                self.screen.blit(plan_text, plan_text_rect)
                
                # If in planning mode, show origin and destination
                if self.game_state.show_transfer_planning:
                    origin = self.game_state.transfer_origin
                    dest = self.game_state.transfer_destination
                    
                    origin_text = self.font.render(
                        f"Origin: {origin['name'] if origin else 'Not selected'}",
                        True, TEXT_COLOR
                    )
                    dest_text = self.font.render(
                        f"Destination: {dest['name'] if dest else 'Not selected'}",
                        True, TEXT_COLOR
                    )
                    
                    self.screen.blit(origin_text, (10, y_offset + 60))
                    self.screen.blit(dest_text, (10, y_offset + 80))
                    
                    # Execute button (only if both origin and destination are selected)
                    if origin and dest:
                        exec_button = pygame.Rect(10, y_offset + 100, 200, 30)
                        pygame.draw.rect(self.screen, (100, 150, 100), exec_button)
                        
                        exec_text = self.font.render("Execute Transfer", True, TEXT_COLOR)
                        exec_text_rect = exec_text.get_rect(center=exec_button.center)
                        self.screen.blit(exec_text, exec_text_rect)
                        
                        # Calculate and show optimal transfer window
                        origin_pos = origin["position"]
                        dest_pos = dest["position"]
                        origin_angle = math.atan2(origin_pos[1], origin_pos[0])
                        dest_angle = math.atan2(dest_pos[1], dest_pos[0])
                        
                        angle_diff = dest_angle - origin_angle
                        # Normalize to -π to +π
                        while angle_diff > math.pi:
                            angle_diff -= 2 * math.pi
                        while angle_diff < -math.pi:
                            angle_diff += 2 * math.pi
                        
                        # Check if we're close to ideal transfer angle
                        ideal_window = False
                        if abs(angle_diff - math.pi) < 0.2:  # Within ~11 degrees of optimal
                            ideal_window = True
                        
                        window_text = self.font.render(
                            "Transfer Window: " + ("OPTIMAL" if ideal_window else "Suboptimal"),
                            True, (100, 200, 100) if ideal_window else (200, 100, 100)
                        )
                        self.screen.blit(window_text, (10, y_offset + 140))                       
                            
                        
    
    def calculate_orbital_elements(self, position, velocity):
        """Calculate orbital elements from position and velocity"""
        # Calculate distance and speed
        r = math.sqrt(position[0]**2 + position[1]**2)
        v = math.sqrt(velocity[0]**2 + velocity[1]**2)
        
        # Calculate specific energy
        energy = 0.5 * v**2 - G * ORBITAL_PARAMETERS["SUN"]["mass"] / r
        
        # Calculate specific angular momentum
        h = position[0] * velocity[1] - position[1] * velocity[0]
        
        # Calculate semi-major axis
        if energy >= 0:
            # Hyperbolic orbit
            semi_major_axis = -G * ORBITAL_PARAMETERS["SUN"]["mass"] / (2 * energy)
        else:
            # Elliptical orbit
            semi_major_axis = -G * ORBITAL_PARAMETERS["SUN"]["mass"] / (2 * energy)
        
        # Calculate eccentricity
        eccentricity = math.sqrt(1 + 2 * energy * h**2 / (G * ORBITAL_PARAMETERS["SUN"]["mass"])**2)
        
        # Calculate orbital period (only for elliptical orbits)
        period = None
        if eccentricity < 1:
            period = 2 * math.pi * math.sqrt(semi_major_axis**3 / (G * ORBITAL_PARAMETERS["SUN"]["mass"]))
        
        return {
            "semi_major_axis": semi_major_axis / AU,  # Convert to AU
            "eccentricity": eccentricity,
            "energy": energy,
            "angular_momentum": h,
            "period": period
        }
    
    def render(self):
        """Render the entire game state"""
        self.screen.fill(BG_COLOR)
        
        self.draw_grid()
        self.draw_celestial_bodies()
        self.draw_ships()
        self.draw_transfers()
        self.draw_ui()
        
        pygame.display.flip()

class GameInputHandler:
    def __init__(self, game_state, renderer):
        self.game_state = game_state
        self.renderer = renderer
        self.dragging = False
        self.drag_start = None
        self.selecting = False
        self.select_start = None
        
        # UI interaction state
        self.plan_button_rect = pygame.Rect(10, 230, 200, 30)
        self.execute_button_rect = pygame.Rect(10, 310, 200, 30)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            elif event.type == pygame.KEYDOWN:
                self.handle_keydown(event)
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mousedown(event)
                
            elif event.type == pygame.MOUSEBUTTONUP:
                self.handle_mouseup(event)
                
            elif event.type == pygame.MOUSEMOTION:
                self.handle_mousemotion(event)
                
            elif event.type == pygame.MOUSEWHEEL:
                self.handle_mousewheel(event)
                
        return True
    
    def handle_keydown(self, event):
        if event.key == pygame.K_ESCAPE:
            self.game_state.selected_object = None
            self.game_state.show_transfer_planning = False
            self.game_state.transfer_origin = None
            self.game_state.transfer_destination = None
            
        elif event.key == pygame.K_SPACE:
            # Toggle pause/play
            if self.game_state.time_scale > 0:
                self.game_state.time_scale = 0
            else:
                self.game_state.time_scale = 1
                
        elif event.key == pygame.K_1:
            self.game_state.time_scale = 1
        elif event.key == pygame.K_2:
            self.game_state.time_scale = 10
        elif event.key == pygame.K_3:
            self.game_state.time_scale = 100
        elif event.key == pygame.K_4:
            self.game_state.time_scale = 1000
            
        elif event.key == pygame.K_g:
            self.game_state.show_grid = not self.game_state.show_grid
            
        elif event.key == pygame.K_o:
            self.game_state.show_orbits = not self.game_state.show_orbits
            
        elif event.key == pygame.K_t:
            self.game_state.show_trajectories = not self.game_state.show_trajectories
            
        elif event.key == pygame.K_r:
            # Reset view
            self.game_state.camera_offset = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]
            self.game_state.zoom = 0.5
    
    def handle_mousedown(self, event):
        if event.button == 1:  # Left click
            # Check if we're clicking UI elements first
            if self.game_state.selected_object and "type" in self.game_state.selected_object:
                # Get updated button rects based on the info panel
                info_height = 50 + (7 * 20)  # Base + number of info lines
                plan_button_rect = pygame.Rect(10, info_height + 20, 200, 30)
                
                if plan_button_rect.collidepoint(event.pos):
                    self.game_state.show_transfer_planning = not self.game_state.show_transfer_planning
                    if self.game_state.show_transfer_planning:
                        self.game_state.transfer_origin = self.game_state.selected_object
                        self.game_state.transfer_destination = None
                    return
                
                # Check execute button if in planning mode with origin and destination
                if (self.game_state.show_transfer_planning and 
                    self.game_state.transfer_origin and 
                    self.game_state.transfer_destination):
                    
                    exec_button_rect = pygame.Rect(10, info_height + 100, 200, 30)
                    if exec_button_rect.collidepoint(event.pos):
                        self.execute_transfer()
                        return
            
            # Check if planning a transfer
            if self.game_state.show_transfer_planning:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    # Start dragging (pan the view)
                    self.dragging = True
                    self.drag_start = event.pos
                else:
                    # Try to select a celestial body as destination
                    self.selecting = True
                    self.select_start = event.pos
                return
            
            # Normal interaction
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                # Start dragging (pan the view)
                self.dragging = True
                self.drag_start = event.pos
            else:
                # Start selection process
                self.selecting = True
                self.select_start = event.pos
                
        elif event.button == 3:  # Right click
            # Cancel transfer planning if active
            if self.game_state.show_transfer_planning:
                self.game_state.show_transfer_planning = False
                self.game_state.transfer_origin = None
                self.game_state.transfer_destination = None
    
    def handle_mouseup(self, event):
        if event.button == 1:  # Left click
            if self.dragging:
                self.dragging = False
            
            if self.selecting:
                self.selecting = False
                
                # Find clicked object
                world_pos = self.renderer.screen_to_world(event.pos)
                clicked_object = self.find_object_at_position(world_pos)
                
                if self.game_state.show_transfer_planning:
                    # In transfer planning mode, set destination
                    if clicked_object and "type" not in clicked_object:
                        self.game_state.transfer_destination = clicked_object
                else:
                    # Normal selection
                    self.game_state.selected_object = clicked_object
    
    def handle_mousemotion(self, event):
        if self.dragging:
            # Pan the view
            dx = event.pos[0] - self.drag_start[0]
            dy = event.pos[1] - self.drag_start[1]
            
            self.game_state.camera_offset[0] += dx
            self.game_state.camera_offset[1] += dy
            
            self.drag_start = event.pos
    
    def handle_mousewheel(self, event):
        # Zoom in/out
        zoom_factor = 1.1 if event.y > 0 else 0.9
        
        # Get mouse position in world coordinates before zoom
        mouse_pos = pygame.mouse.get_pos()
        mouse_world_pos = self.renderer.screen_to_world(mouse_pos)
        
        # Apply zoom
        self.game_state.zoom *= zoom_factor
        
        # Limit zoom
        self.game_state.zoom = max(0.1, min(10.0, self.game_state.zoom))
        
        # Get new mouse world position and adjust camera to maintain mouse position
        new_mouse_screen_pos = (
            mouse_world_pos[0] * self.game_state.zoom + self.game_state.camera_offset[0],
            mouse_world_pos[1] * self.game_state.zoom + self.game_state.camera_offset[1]
        )
        
        self.game_state.camera_offset[0] += mouse_pos[0] - new_mouse_screen_pos[0]
        self.game_state.camera_offset[1] += mouse_pos[1] - new_mouse_screen_pos[1]
    
    def find_object_at_position(self, world_pos):
        """Find the closest object to the given position"""
        closest_obj = None
        closest_distance = float('inf')
        
        # Check celestial bodies
        for body in self.game_state.celestial_bodies:
            dx = body["position"][0] - world_pos[0]
            dy = body["position"][1] - world_pos[1]
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Scale selection radius by the zoom level
            selection_radius = body["radius"] / self.game_state.zoom
            
            if distance < selection_radius and distance < closest_distance:
                closest_obj = body
                closest_distance = distance
        
        # Check ships
        for ship in self.game_state.ships:
            dx = ship["position"][0] - world_pos[0]
            dy = ship["position"][1] - world_pos[1]
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Use a fixed selection radius for ships
            selection_radius = 10 / self.game_state.zoom
            
            if distance < selection_radius and distance < closest_distance:
                closest_obj = ship
                closest_distance = distance
        
        return closest_obj
    
    def execute_transfer(self):
        """Execute the planned transfer"""
        if not self.game_state.transfer_origin or not self.game_state.transfer_destination:
            return
        
        ship = self.game_state.transfer_origin
        destination = self.game_state.transfer_destination
        
        # Calculate orbit parameters
        ship_pos = ship["position"]
        ship_vel = ship["velocity"]
        ship_radius = math.sqrt(ship_pos[0]**2 + ship_pos[1]**2)
        
        dest_pos = destination["position"]
        dest_radius = math.sqrt(dest_pos[0]**2 + dest_pos[1]**2)
        
        # Calculate current angles
        ship_angle = math.atan2(ship_pos[1], ship_pos[0])
        
        # Calculate Hohmann transfer
        transfer_data = calculate_hohmann_transfer(
            ship_radius / AU, 
            dest_radius / AU, 
            ORBITAL_PARAMETERS["SUN"]["mass"]
        )
        
        # Check if we have enough fuel
        fuel_required = calculate_fuel_consumption(
            transfer_data["delta_v1"],  # Just the first burn for now
            ship["type"],
            ship["mass"]
        )
        
        if fuel_required > ship["fuel"]:
            print(f"Not enough fuel! Required: {fuel_required:.1f}%, Available: {ship['fuel']:.1f}%")
            return
        
        # Consume fuel for the first burn
        ship["fuel"] -= fuel_required
        
        # Calculate new velocity after the burn
        if ship_radius < dest_radius:
            # Outbound transfer
            # The burn increases velocity in the current direction of travel
            speed_increment = transfer_data["delta_v1"]
            
            # Calculate the direction of velocity (perpendicular to position)
            vel_angle = ship_angle + math.pi/2
            
            # Apply the burn
            new_velocity = (
                ship_vel[0] + speed_increment * math.cos(vel_angle),
                ship_vel[1] + speed_increment * math.sin(vel_angle)
            )
        else:
            # Inbound transfer
            # The burn decreases velocity in the current direction of travel
            speed_decrement = transfer_data["delta_v1"]
            
            # Calculate the direction of velocity (perpendicular to position)
            vel_angle = ship_angle + math.pi/2
            
            # Apply the burn
            new_velocity = (
                ship_vel[0] - speed_decrement * math.cos(vel_angle),
                ship_vel[1] - speed_decrement * math.sin(vel_angle)
            )
        
        # Update ship's velocity
        ship["velocity"] = new_velocity
        
        # Generate trajectory points
        trajectory_points = generate_hohmann_trajectory_points(
            ship_pos,
            new_velocity,
            (dest_radius * math.cos(ship_angle + math.pi), dest_radius * math.sin(ship_angle + math.pi)),
            ORBITAL_PARAMETERS["SUN"]["mass"],
            50
        )
        
        # Set the trajectory
        ship["trajectory"] = trajectory_points
        
        # Create a transfer record
        transfer = {
            "type": "hohmann",
            "ship": ship["name"],
            "start_orbit": ship_radius,
            "end_orbit": dest_radius,
            "start_angle": ship_angle,
            "start_time": self.game_state.time,
            "end_time": self.game_state.time + transfer_data["transfer_time"],
            "delta_v1": transfer_data["delta_v1"],
            "delta_v2": transfer_data["delta_v2"]
        }
        
        self.game_state.transfers.append(transfer)
        
        # Reset transfer planning mode
        # Reset transfer planning mode
        self.game_state.show_transfer_planning = False
        self.game_state.transfer_origin = None
        self.game_state.transfer_destination = None
        
        # Create a mission that will execute the second burn automatically
        mission = {
            "type": "hohmann_transfer",
            "target_body": destination["name"],
            "start_time": self.game_state.time,
            "arrival_time": self.game_state.time + transfer_data["transfer_time"],
            "delta_v2": transfer_data["delta_v2"],
            "target_orbit_radius": dest_radius,
            "target_orbit_angle": ship_angle + math.pi  # Opposite side of orbit
        }
        
        # Assign mission to ship
        ship["mission"] = mission
        
        
def main():
    # Initialize pygame
    pygame.init()
    
    # Initialize the font module specifically
    pygame.font.init()
    
    game_state = GameState()
    renderer = GameRenderer(game_state)
    input_handler = GameInputHandler(game_state, renderer)
    
    running = True
    while running:
        # Handle events
        running = input_handler.handle_events()
        
        # Update game state
        dt = renderer.clock.tick(FPS) / 1000.0  # Time since last frame in seconds
        game_state.update(dt)
        
        # Render
        renderer.render()
    
    pygame.quit()

if __name__ == "__main__":
    main()