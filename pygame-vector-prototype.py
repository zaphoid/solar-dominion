import pygame
import math
import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60
BG_COLOR = (0, 0, 0)
GRID_COLOR = (20, 20, 20)
TEXT_COLOR = (200, 200, 200)
ORBIT_COLORS = [(50, 50, 100), (50, 100, 50), (100, 50, 50), (100, 100, 50)]

# Astronomical constants (simplified)
AU = 100  # Astronomical Unit in pixels
EARTH_ORBITAL_PERIOD = 365  # Days
DAY_PER_SECOND = 1  # Game days per real second
GRAVITATIONAL_CONSTANT = 100  # Simplified for game purposes

# Factions
class Faction(Enum):
    EARTH = 1
    MARS = 2
    BELT = 3
    PROTOGEN = 4

# Resource types
class ResourceType(Enum):
    WATER = 1
    FOOD = 2
    FUEL = 3
    MATERIALS = 4
    POPULATION = 5

@dataclass
class Resource:
    type: ResourceType
    amount: float
    capacity: float
    production_rate: float
    consumption_rate: float

@dataclass
class CelestialBody:
    name: str
    mass: float
    radius: float  # Visual radius
    color: Tuple[int, int, int]
    orbital_radius: float  # Distance from parent (AU)
    orbital_period: float  # Days
    position: Tuple[float, float]  # Current position
    angle: float = 0.0  # Current orbital angle

@dataclass
class Ship:
    name: str
    faction: Faction
    position: Tuple[float, float]
    velocity: Tuple[float, float]
    fuel: float
    crew: int
    resources: Dict[ResourceType, Resource]
    destination: Optional[Tuple[float, float]] = None
    trajectory: List[Tuple[float, float]] = None
    
@dataclass
class Habitat:
    name: str
    faction: Faction
    position: Tuple[float, float]
    population: int
    resources: Dict[ResourceType, Resource]
    connected_to: List[str] = None  # Names of connected habitats

class GameState:
    def __init__(self):
        self.time = 0  # Current game time in days
        self.time_scale = 1  # Time acceleration factor
        self.selected_object = None
        self.celestial_bodies = []
        self.ships = []
        self.habitats = []
        self.player_faction = Faction.EARTH
        self.show_orbits = True
        self.show_grid = True
        self.show_trajectories = True
        self.camera_offset = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]
        self.zoom = 1.0
        
        # Initialize solar system
        self.initialize_solar_system()
        
    def initialize_solar_system(self):
        # Create the Sun
        sun = CelestialBody(
            name="Sun",
            mass=1000,
            radius=20,
            color=(255, 255, 0),
            orbital_radius=0,
            orbital_period=0,
            position=(0, 0)
        )
        self.celestial_bodies.append(sun)
        
        # Create planets
        earth = CelestialBody(
            name="Earth",
            mass=100,
            radius=10,
            color=(0, 100, 255),
            orbital_radius=1 * AU,
            orbital_period=EARTH_ORBITAL_PERIOD,
            position=(AU, 0)
        )
        self.celestial_bodies.append(earth)
        
        # Create Moon as Earth's satellite
        moon = CelestialBody(
            name="Luna",
            mass=10,
            radius=3,
            color=(200, 200, 200),
            orbital_radius=0.15 * AU,
            orbital_period=EARTH_ORBITAL_PERIOD / 12,
            position=(AU + 0.15 * AU, 0)
        )
        self.celestial_bodies.append(moon)
        
        mars = CelestialBody(
            name="Mars",
            mass=80,
            radius=8,
            color=(255, 100, 0),
            orbital_radius=1.5 * AU,
            orbital_period=EARTH_ORBITAL_PERIOD * 1.88,  # Mars orbital period in Earth days
            position=(1.5 * AU, 0)
        )
        self.celestial_bodies.append(mars)
        
        # Add a simple asteroid belt
        for i in range(10):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(2.2, 2.5) * AU
            asteroid = CelestialBody(
                name=f"Asteroid {i+1}",
                mass=1,
                radius=1,
                color=(150, 150, 150),
                orbital_radius=distance,
                orbital_period=EARTH_ORBITAL_PERIOD * math.sqrt(distance/AU)**3,  # Kepler's third law
                position=(distance * math.cos(angle), distance * math.sin(angle)),
                angle=angle
            )
            self.celestial_bodies.append(asteroid)
        
        # Add some initial ships and habitats
        earth_station = Habitat(
            name="Earth Station Alpha",
            faction=Faction.EARTH,
            position=(AU, 0),
            population=1000,
            resources={
                ResourceType.WATER: Resource(ResourceType.WATER, 1000, 2000, 10, 5),
                ResourceType.FOOD: Resource(ResourceType.FOOD, 800, 1000, 8, 7),
                ResourceType.FUEL: Resource(ResourceType.FUEL, 500, 1000, 5, 2),
                ResourceType.MATERIALS: Resource(ResourceType.MATERIALS, 1000, 5000, 20, 10),
                ResourceType.POPULATION: Resource(ResourceType.POPULATION, 1000, 2000, 0.1, 0)
            }
        )
        self.habitats.append(earth_station)
        
        mars_colony = Habitat(
            name="Mars Colony One",
            faction=Faction.MARS,
            position=(1.5 * AU, 0),
            population=500,
            resources={
                ResourceType.WATER: Resource(ResourceType.WATER, 500, 1000, 2, 3),
                ResourceType.FOOD: Resource(ResourceType.FOOD, 400, 600, 4, 3),
                ResourceType.FUEL: Resource(ResourceType.FUEL, 300, 800, 3, 1),
                ResourceType.MATERIALS: Resource(ResourceType.MATERIALS, 800, 2000, 15, 8),
                ResourceType.POPULATION: Resource(ResourceType.POPULATION, 500, 1000, 0.05, 0)
            }
        )
        self.habitats.append(mars_colony)
        
        # Create an Earth ship
        earth_ship = Ship(
            name="UNSS Explorer",
            faction=Faction.EARTH,
            position=(AU + 0.1 * AU, 0),
            velocity=(0, 0.01),
            fuel=100,
            crew=20,
            resources={
                ResourceType.WATER: Resource(ResourceType.WATER, 100, 200, 0, 0.5),
                ResourceType.FOOD: Resource(ResourceType.FOOD, 80, 100, 0, 0.4),
                ResourceType.FUEL: Resource(ResourceType.FUEL, 100, 100, 0, 0)
            }
        )
        self.ships.append(earth_ship)
        
    def update(self, dt):
        real_dt = dt * self.time_scale
        self.time += DAY_PER_SECOND * real_dt
        
        # Update positions of celestial bodies
        for body in self.celestial_bodies:
            if body.orbital_period > 0:
                # Calculate new angle based on orbital period
                angle_change = (2 * math.pi / body.orbital_period) * DAY_PER_SECOND * real_dt
                body.angle += angle_change
                
                # Update position
                body.position = (
                    body.orbital_radius * math.cos(body.angle),
                    body.orbital_radius * math.sin(body.angle)
                )
        
        # Update ships (simple physics)
        for ship in self.ships:
            # Apply velocity
            ship.position = (
                ship.position[0] + ship.velocity[0] * real_dt,
                ship.position[1] + ship.velocity[1] * real_dt
            )
            
            # If ship has a destination, update trajectory
            if ship.destination:
                # Very simple direct movement for now
                dx = ship.destination[0] - ship.position[0]
                dy = ship.destination[1] - ship.position[1]
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < 5:  # Reached destination
                    ship.destination = None
                    ship.velocity = (0, 0)
                else:
                    # Simplified acceleration towards destination
                    ship.velocity = (
                        dx / distance * 0.001,
                        dy / distance * 0.001
                    )
                    # Consume fuel
                    ship.fuel -= 0.01 * real_dt
        
        # Update habitats and resources
        for habitat in self.habitats:
            for resource in habitat.resources.values():
                # Production
                resource.amount += resource.production_rate * real_dt / 30  # per month
                # Consumption
                resource.amount -= resource.consumption_rate * real_dt / 30  # per month
                # Clamp to capacity
                resource.amount = max(0, min(resource.amount, resource.capacity))

class GameRenderer:
    def __init__(self, game_state):
        self.game_state = game_state
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Solar Dominion - Vector Prototype")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 15)
        self.large_font = pygame.font.SysFont("monospace", 24)
        
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
            
    def draw_orbits(self):
        """Draw orbital paths"""
        if not self.game_state.show_orbits:
            return
            
        for body in self.game_state.celestial_bodies:
            if body.orbital_radius > 0:
                # Draw orbit as a circle
                center = self.world_to_screen((0, 0))  # Center of the system
                radius = int(body.orbital_radius * self.game_state.zoom)
                
                # Only draw if orbit would be visible
                if (center[0] + radius > 0 or center[0] - radius < SCREEN_WIDTH) and \
                   (center[1] + radius > 0 or center[1] - radius < SCREEN_HEIGHT):
                    pygame.draw.circle(self.screen, ORBIT_COLORS[0], center, radius, 1)
    
    def draw_celestial_bodies(self):
        """Draw planets, moons, etc."""
        for body in self.game_state.celestial_bodies:
            pos = self.world_to_screen(body.position)
            # Only draw if on screen
            if 0 <= pos[0] <= SCREEN_WIDTH and 0 <= pos[1] <= SCREEN_HEIGHT:
                radius = max(1, int(body.radius * self.game_state.zoom))
                pygame.draw.circle(self.screen, body.color, pos, radius)
                
                # Draw name if zoom level is sufficient
                if self.game_state.zoom > 0.5:
                    name_surface = self.font.render(body.name, True, TEXT_COLOR)
                    name_rect = name_surface.get_rect(center=(pos[0], pos[1] - radius - 10))
                    self.screen.blit(name_surface, name_rect)
    
    def draw_ships(self):
        """Draw ships"""
        for ship in self.game_state.ships:
            pos = self.world_to_screen(ship.position)
            
            # Only draw if on screen
            if 0 <= pos[0] <= SCREEN_WIDTH and 0 <= pos[1] <= SCREEN_HEIGHT:
                # Draw ship as a triangle
                size = max(3, int(5 * self.game_state.zoom))
                
                # Calculate direction (simple version, always facing right)
                points = [
                    (pos[0] + size, pos[1]),
                    (pos[0] - size, pos[1] - size),
                    (pos[0] - size, pos[1] + size)
                ]
                
                # Color based on faction
                color = (0, 0, 255)  # Default to Earth
                if ship.faction == Faction.MARS:
                    color = (255, 0, 0)
                elif ship.faction == Faction.BELT:
                    color = (100, 100, 100)
                elif ship.faction == Faction.PROTOGEN:
                    color = (150, 0, 150)
                
                pygame.draw.polygon(self.screen, color, points)
                
                # Draw ship name and stats if selected
                if self.game_state.selected_object == ship:
                    pygame.draw.polygon(self.screen, (255, 255, 255), points, 1)
                    
                # Draw trajectory if ship has a destination
                if ship.destination and self.game_state.show_trajectories:
                    dest_pos = self.world_to_screen(ship.destination)
                    pygame.draw.line(self.screen, color, pos, dest_pos, 1)
    
    def draw_habitats(self):
        """Draw habitats"""
        for habitat in self.game_state.habitats:
            pos = self.world_to_screen(habitat.position)
            
            # Only draw if on screen
            if 0 <= pos[0] <= SCREEN_WIDTH and 0 <= pos[1] <= SCREEN_HEIGHT:
                # Draw habitat as a square
                size = max(4, int(6 * self.game_state.zoom))
                rect = pygame.Rect(pos[0] - size, pos[1] - size, size * 2, size * 2)
                
                # Color based on faction
                color = (0, 0, 255)  # Default to Earth
                if habitat.faction == Faction.MARS:
                    color = (255, 0, 0)
                elif habitat.faction == Faction.BELT:
                    color = (100, 100, 100)
                elif habitat.faction == Faction.PROTOGEN:
                    color = (150, 0, 150)
                
                pygame.draw.rect(self.screen, color, rect)
                
                # Draw habitat name if zoom level is sufficient
                if self.game_state.zoom > 0.5:
                    name_surface = self.font.render(habitat.name, True, TEXT_COLOR)
                    name_rect = name_surface.get_rect(center=(pos[0], pos[1] - size - 10))
                    self.screen.blit(name_surface, name_rect)
                    
                # Draw selection indicator if selected
                if self.game_state.selected_object == habitat:
                    pygame.draw.rect(self.screen, (255, 255, 255), rect, 1)
    
    def draw_ui(self):
        """Draw user interface elements"""
        # Draw time info
        days = int(self.game_state.time % 365)
        years = int(self.game_state.time // 365)
        time_text = f"Year {years}, Day {days} - Speed: {self.game_state.time_scale}x"
        time_surface = self.large_font.render(time_text, True, TEXT_COLOR)
        self.screen.blit(time_surface, (10, 10))
        
        # Draw selected object info
        if self.game_state.selected_object:
            obj = self.game_state.selected_object
            info_text = []
            info_text.append(f"Name: {obj.name}")
            
            if isinstance(obj, Ship):
                info_text.append(f"Faction: {obj.faction.name}")
                info_text.append(f"Fuel: {obj.fuel:.1f}%")
                info_text.append(f"Crew: {obj.crew}")
                
                # Add resource info
                for res_type, resource in obj.resources.items():
                    info_text.append(f"{res_type.name}: {resource.amount:.1f}/{resource.capacity:.1f}")
            
            elif isinstance(obj, Habitat):
                info_text.append(f"Faction: {obj.faction.name}")
                info_text.append(f"Population: {obj.population}")
                
                # Add resource info
                for res_type, resource in obj.resources.items():
                    info_text.append(f"{res_type.name}: {resource.amount:.1f}/{resource.capacity:.1f}")
                    info_text.append(f"  Prod: {resource.production_rate:.1f}/mo, Cons: {resource.consumption_rate:.1f}/mo")
            
            # Draw info box
            y_offset = 60
            for text in info_text:
                text_surface = self.font.render(text, True, TEXT_COLOR)
                self.screen.blit(text_surface, (10, y_offset))
                y_offset += 20
    
    def render(self):
        """Render the entire game state"""
        self.screen.fill(BG_COLOR)
        
        self.draw_grid()
        self.draw_orbits()
        self.draw_celestial_bodies()
        self.draw_ships()
        self.draw_habitats()
        self.draw_ui()
        
        pygame.display.flip()

class GameInputHandler:
    def __init__(self, game_state):
        self.game_state = game_state
        self.dragging = False
        self.drag_start = None
        self.selecting = False
        self.select_start = None
        
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
            self.game_state.zoom = 1.0
    
    def handle_mousedown(self, event):
        if event.button == 1:  # Left click
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                # Start dragging (pan the view)
                self.dragging = True
                self.drag_start = event.pos
            else:
                # Start selection process
                self.selecting = True
                self.select_start = event.pos
                
        elif event.button == 3:  # Right click
            if self.game_state.selected_object and isinstance(self.game_state.selected_object, Ship):
                # Set destination for selected ship
                world_pos = self.screen_to_world(event.pos)
                self.game_state.selected_object.destination = world_pos
                
                # Calculate simple trajectory (direct line for now)
                ship = self.game_state.selected_object
                ship.trajectory = [ship.position, world_pos]
    
    def handle_mouseup(self, event):
        if event.button == 1:  # Left click
            if self.dragging:
                self.dragging = False
            
            if self.selecting:
                self.selecting = False
                
                # Find clicked object
                world_pos = self.screen_to_world(event.pos)
                closest_obj = None
                closest_distance = float('inf')
                
                # Check celestial bodies
                for body in self.game_state.celestial_bodies:
                    dx = body.position[0] - world_pos[0]
                    dy = body.position[1] - world_pos[1]
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance < body.radius / self.game_state.zoom and distance < closest_distance:
                        closest_obj = body
                        closest_distance = distance
                
                # Check ships
                for ship in self.game_state.ships:
                    dx = ship.position[0] - world_pos[0]
                    dy = ship.position[1] - world_pos[1]
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance < 5 / self.game_state.zoom and distance < closest_distance:
                        closest_obj = ship
                        closest_distance = distance
                
                # Check habitats
                for habitat in self.game_state.habitats:
                    dx = habitat.position[0] - world_pos[0]
                    dy = habitat.position[1] - world_pos[1]
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance < 6 / self.game_state.zoom and distance < closest_distance:
                        closest_obj = habitat
                        closest_distance = distance
                
                self.game_state.selected_object = closest_obj
    
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
        mouse_world_pos = self.screen_to_world(mouse_pos)
        
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
    
    def screen_to_world(self, pos):
        """Convert screen coordinates to world coordinates"""
        x = (pos[0] - self.game_state.camera_offset[0]) / self.game_state.zoom
        y = (pos[1] - self.game_state.camera_offset[1]) / self.game_state.zoom
        return x, y

def main():
    game_state = GameState()
    renderer = GameRenderer(game_state)
    input_handler = GameInputHandler(game_state)
    
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
