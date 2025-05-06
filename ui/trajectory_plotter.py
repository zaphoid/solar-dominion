"""
Trajectory plotting and visualization tools for Solar Dominion.
"""

import pygame
import math
from typing import Tuple, Dict, List, Optional
import sys
import os

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, 
    TRAJECTORY_COLOR, TRANSFER_COLOR, GRAVITY_ASSIST_COLOR,
    AU
)

class TrajectoryPlotter:
    def __init__(self, screen, camera_offset, zoom):
        """
        Initialize the trajectory plotter.
        
        Args:
            screen: Pygame screen surface
            camera_offset: (x, y) camera offset in screen coordinates
            zoom: Current zoom level
        """
        self.screen = screen
        self.camera_offset = camera_offset
        self.zoom = zoom
    
    def world_to_screen(self, pos: Tuple[float, float]) -> Tuple[int, int]:
        """
        Convert world coordinates to screen coordinates.
        
        Args:
            pos: (x, y) position in world coordinates
            
        Returns:
            (x, y) position in screen coordinates
        """
        x = pos[0] * self.zoom + self.camera_offset[0]
        y = pos[1] * self.zoom + self.camera_offset[1]
        return int(x), int(y)
    
    def draw_orbit(self, center: Tuple[float, float], radius: float, color: Tuple[int, int, int], width: int = 1):
        """
        Draw a circular orbit.
        
        Args:
            center: (x, y) center position in world coordinates
            radius: Orbit radius in world units
            color: RGB color tuple
            width: Line width in pixels
        """
        center_screen = self.world_to_screen(center)
        radius_screen = int(radius * self.zoom)
        
        # Only draw if the orbit would be visible
        if (center_screen[0] + radius_screen > 0 or 
            center_screen[0] - radius_screen < SCREEN_WIDTH) and \
           (center_screen[1] + radius_screen > 0 or 
            center_screen[1] - radius_screen < SCREEN_HEIGHT):
            pygame.draw.circle(self.screen, color, center_screen, radius_screen, width)
    
    def draw_elliptical_orbit(self, 
                             center: Tuple[float, float], 
                             semi_major_axis: float, 
                             semi_minor_axis: float, 
                             rotation: float, 
                             color: Tuple[int, int, int], 
                             width: int = 1):
        """
        Draw an elliptical orbit.
        
        Args:
            center: (x, y) center position in world coordinates
            semi_major_axis: Semi-major axis length in world units
            semi_minor_axis: Semi-minor axis length in world units
            rotation: Rotation angle in radians
            color: RGB color tuple
            width: Line width in pixels
        """
        # Calculate screen coordinates for the ellipse
        center_screen = self.world_to_screen(center)
        a_screen = int(semi_major_axis * self.zoom)
        b_screen = int(semi_minor_axis * self.zoom)
        
        # Define the ellipse rectangle
        ellipse_rect = pygame.Rect(
            center_screen[0] - a_screen,
            center_screen[1] - b_screen,
            a_screen * 2,
            b_screen * 2
        )
        
        # Ellipse is simple if not rotated
        if rotation == 0:
            pygame.draw.ellipse(self.screen, color, ellipse_rect, width)
            return
        
        # For rotated ellipses, we need to draw point by point
        # This is more computationally expensive
        points = []
        num_points = 100  # More points for smoother ellipses
        
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            
            # Calculate point on unrotated ellipse
            x = semi_major_axis * math.cos(angle)
            y = semi_minor_axis * math.sin(angle)
            
            # Apply rotation
            rotated_x = x * math.cos(rotation) - y * math.sin(rotation)
            rotated_y = x * math.sin(rotation) + y * math.cos(rotation)
            
            # Add center offset
            world_x = center[0] + rotated_x
            world_y = center[1] + rotated_y
            
            # Convert to screen coordinates
            screen_pos = self.world_to_screen((world_x, world_y))
            points.append(screen_pos)
        
        # Draw the points as a polygon
        if len(points) > 1:
            pygame.draw.polygon(self.screen, color, points, width)
    
    def draw_trajectory(self, points: List[Tuple[float, float]], color: Tuple[int, int, int], width: int = 1):
        """
        Draw a trajectory from a list of points.
        
        Args:
            points: List of (x, y) positions in world coordinates
            color: RGB color tuple
            width: Line width in pixels
        """
        if not points or len(points) < 2:
            return
        
        # Convert all points to screen coordinates
        screen_points = [self.world_to_screen(p) for p in points]
        
        # Draw as a series of connected lines
        pygame.draw.lines(self.screen, color, False, screen_points, width)
    
    def draw_hohmann_transfer(self, 
                             start_orbit: float, 
                             end_orbit: float, 
                             start_angle: float = 0, 
                             color: Tuple[int, int, int] = TRANSFER_COLOR, 
                             width: int = 2):
        """
        Draw a Hohmann transfer orbit between two circular orbits.
        
        Args:
            start_orbit: Starting orbit radius in world units
            end_orbit: Ending orbit radius in world units
            start_angle: Starting angle in radians
            color: RGB color tuple
            width: Line width in pixels
        """
        # Calculate semi-major axis of the transfer orbit
        a = (start_orbit + end_orbit) / 2
        
        # Calculate eccentricity of the transfer orbit
        if start_orbit < end_orbit:
            # Outbound transfer
            e = (end_orbit - start_orbit) / (end_orbit + start_orbit)
        else:
            # Inbound transfer
            e = (start_orbit - end_orbit) / (start_orbit + end_orbit)
        
        # Calculate semi-minor axis
        b = a * math.sqrt(1 - e**2)
        
        # Draw the elliptical transfer orbit
        # The rotation angle depends on the starting angle
        self.draw_elliptical_orbit((0, 0), a, b, start_angle, color, width)
        
        # Draw the burn points
        start_pos = (start_orbit * math.cos(start_angle), start_orbit * math.sin(start_angle))
        end_pos = (end_orbit * math.cos(start_angle + math.pi), end_orbit * math.sin(start_angle + math.pi))
        
        start_screen = self.world_to_screen(start_pos)
        end_screen = self.world_to_screen(end_pos)
        
        # Draw burn points as small circles
        pygame.draw.circle(self.screen, color, start_screen, 3)
        pygame.draw.circle(self.screen, color, end_screen, 3)
    
    def draw_bi_elliptic_transfer(self, 
                                 start_orbit: float, 
                                 end_orbit: float, 
                                 intermediate_orbit: float, 
                                 start_angle: float = 0, 
                                 color: Tuple[int, int, int] = TRANSFER_COLOR, 
                                 width: int = 2):
        """
        Draw a bi-elliptic transfer orbit between two circular orbits.
        
        Args:
            start_orbit: Starting orbit radius in world units
            end_orbit: Ending orbit radius in world units
            intermediate_orbit: Intermediate orbit radius in world units
            start_angle: Starting angle in radians
            color: RGB color tuple
            width: Line width in pixels
        """
        # Calculate parameters for the first transfer orbit (start to intermediate)
        a1 = (start_orbit + intermediate_orbit) / 2
        if start_orbit < intermediate_orbit:
            e1 = (intermediate_orbit - start_orbit) / (intermediate_orbit + start_orbit)
        else:
            e1 = (start_orbit - intermediate_orbit) / (start_orbit + intermediate_orbit)
        b1 = a1 * math.sqrt(1 - e1**2)
        
        # Calculate parameters for the second transfer orbit (intermediate to end)
        a2 = (intermediate_orbit + end_orbit) / 2
        if intermediate_orbit < end_orbit:
            e2 = (end_orbit - intermediate_orbit) / (end_orbit + intermediate_orbit)
        else:
            e2 = (intermediate_orbit - end_orbit) / (intermediate_orbit + end_orbit)
        b2 = a2 * math.sqrt(1 - e2**2)
        
        # Draw the first elliptical transfer orbit
        self.draw_elliptical_orbit((0, 0), a1, b1, start_angle, color, width)
        
        # Draw the second elliptical transfer orbit
        self.draw_elliptical_orbit((0, 0), a2, b2, start_angle + math.pi, color, width)
        
        # Draw the burn points
        start_pos = (start_orbit * math.cos(start_angle), start_orbit * math.sin(start_angle))
        intermediate_pos = (intermediate_orbit * math.cos(start_angle + math.pi), 
                           intermediate_orbit * math.sin(start_angle + math.pi))
        end_pos = (end_orbit * math.cos(start_angle), end_orbit * math.sin(start_angle))
        
        start_screen = self.world_to_screen(start_pos)
        intermediate_screen = self.world_to_screen(intermediate_pos)
        end_screen = self.world_to_screen(end_pos)
        
        # Draw burn points as small circles
        pygame.draw.circle(self.screen, color, start_screen, 3)
        pygame.draw.circle(self.screen, color, intermediate_screen, 5)
        pygame.draw.circle(self.screen, color, end_screen, 3)
    
    def draw_gravity_assist(self, 
                          planet_position: Tuple[float, float], 
                          approach_angle: float, 
                          deflection_angle: float, 
                          approach_distance: float, 
                          color: Tuple[int, int, int] = GRAVITY_ASSIST_COLOR, 
                          width: int = 2):
        """
        Draw a gravity assist trajectory around a planet.
        
        Args:
            planet_position: (x, y) position of the planet in world coordinates
            approach_angle: Approach angle in radians
            deflection_angle: Deflection angle in radians
            approach_distance: Closest approach distance in world units
            color: RGB color tuple
            width: Line width in pixels
        """
        # Convert to screen coordinates
        planet_screen = self.world_to_screen(planet_position)
        
        # Calculate the approach and departure vectors
        approach_vector = (math.cos(approach_angle), math.sin(approach_angle))
        departure_angle = approach_angle + deflection_angle
        departure_vector = (math.cos(departure_angle), math.sin(departure_angle))
        
        # Calculate the approach and departure points far from the planet
        approach_distance_screen = 200  # Screen units
        approach_point = (
            planet_screen[0] - approach_vector[0] * approach_distance_screen,
            planet_screen[1] - approach_vector[1] * approach_distance_screen
        )
        departure_point = (
            planet_screen[0] + departure_vector[0] * approach_distance_screen,
            planet_screen[1] + departure_vector[1] * approach_distance_screen
        )
        
        # The hyperbolic trajectory is approximated by an arc for simplicity
        # Calculate the angle range for the arc
        start_angle = math.atan2(-approach_vector[1], -approach_vector[0])
        end_angle = math.atan2(departure_vector[1], departure_vector[0])
        
        # Ensure the arc follows the shorter path
        if end_angle - start_angle > math.pi:
            end_angle -= 2 * math.pi
        elif start_angle - end_angle > math.pi:
            start_angle -= 2 * math.pi
        
        # Convert angles to degrees for pygame
        start_angle_deg = math.degrees(start_angle)
        end_angle_deg = math.degrees(end_angle)
        
        # Calculate the angular range
        angle_range = end_angle_deg - start_angle_deg
        
        # Draw the approach and departure lines
        pygame.draw.line(self.screen, color, approach_point, planet_screen, width)
        pygame.draw.line(self.screen, color, planet_screen, departure_point, width)
        
        # Draw the hyperbolic arc around the planet
        approach_distance_screen = int(approach_distance * self.zoom)
        arc_rect = pygame.Rect(
            planet_screen[0] - approach_distance_screen,
            planet_screen[1] - approach_distance_screen,
            approach_distance_screen * 2,
            approach_distance_screen * 2
        )
        
        # Draw the arc
        # Note: pygame.draw.arc is not ideal for proper hyperbolic trajectories,
        # but serves as a reasonable approximation for visualization
        pygame.draw.arc(self.screen, color, arc_rect, math.radians(start_angle_deg), 
                        math.radians(end_angle_deg), width)
    
    def draw_transfer_window_indicator(self, 
                                      current_angle: float, 
                                      target_angle: float, 
                                      orbit_radius: float, 
                                      color: Tuple[int, int, int] = (255, 255, 0)):
        """
        Draw an indicator showing the optimal transfer window.
        
        Args:
            current_angle: Current orbital angle in radians
            target_angle: Target orbital angle for transfer in radians
            orbit_radius: Orbit radius in world units
            color: RGB color tuple
        """
        # Calculate positions
        current_pos = (
            orbit_radius * math.cos(current_angle),
            orbit_radius * math.sin(current_angle)
        )
        target_pos = (
            orbit_radius * math.cos(target_angle),
            orbit_radius * math.sin(target_angle)
        )
        
        # Convert to screen coordinates
        current_screen = self.world_to_screen(current_pos)
        target_screen = self.world_to_screen(target_pos)
        
        # Draw indicators
        pygame.draw.circle(self.screen, color, current_screen, 5, 1)
        pygame.draw.circle(self.screen, color, target_screen, 5)
        
        # Draw an arc on the orbit to show the angular distance
        center_screen = self.world_to_screen((0, 0))
        radius_screen = int(orbit_radius * self.zoom)
        
        # Ensure the angles are properly ordered for the arc
        start_angle = current_angle
        end_angle = target_angle
        
        if end_angle < start_angle:
            end_angle += 2 * math.pi
        
        # Create a rectangle for the arc
        arc_rect = pygame.Rect(
            center_screen[0] - radius_screen,
            center_screen[1] - radius_screen,
            radius_screen * 2,
            radius_screen * 2
        )
        
        # Draw the arc
        pygame.draw.arc(self.screen, color, arc_rect, start_angle, end_angle, 2)
    
    def draw_delta_v_indicator(self, 
                              position: Tuple[float, float], 
                              delta_v: float, 
                              color: Tuple[int, int, int] = (200, 100, 50), 
                              max_delta_v: float = 10.0):
        """
        Draw an indicator showing the delta-v requirement for a maneuver.
        
        Args:
            position: (x, y) position in world coordinates
            delta_v: Delta-v value in game units
            color: RGB color tuple
            max_delta_v: Maximum delta-v for scaling the bar
        """
        # Convert to screen coordinates
        pos_screen = self.world_to_screen(position)
        
        # Calculate bar dimensions based on delta-v
        bar_width = 40
        bar_height = 5
        fill_width = int(min(delta_v / max_delta_v, 1.0) * bar_width)
        
        # Draw the background bar
        bar_rect = pygame.Rect(
            pos_screen[0] - bar_width // 2,
            pos_screen[1] - 20,
            bar_width,
            bar_height
        )
        pygame.draw.rect(self.screen, (50, 50, 50), bar_rect)
        
        # Draw the filled portion
        fill_rect = pygame.Rect(
            pos_screen[0] - bar_width // 2,
            pos_screen[1] - 20,
            fill_width,
            bar_height
        )
        pygame.draw.rect(self.screen, color, fill_rect)
        
        # Draw a text label with the delta-v value
        font = pygame.font.SysFont("monospace", 12)
        text = font.render(f"{delta_v:.1f}", True, (200, 200, 200))
        text_rect = text.get_rect(center=(pos_screen[0], pos_screen[1] - 30))
        self.screen.blit(text, text_rect)
    
    def update_camera(self, camera_offset, zoom):
        """
        Update the camera parameters.
        
        Args:
            camera_offset: (x, y) camera offset in screen coordinates
            zoom: Current zoom level
        """
        self.camera_offset = camera_offset
        self.zoom = zoom
