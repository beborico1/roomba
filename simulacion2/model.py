from mesa import Model, agent
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa import DataCollector
from agent import RoombaAgent, ObstacleAgent, ChargingStationAgent, VisitedCellAgent, DirtyCellAgent

def battery_level(model):
    # Calcula el nivel promedio de batería de todos los agentes RoombaAgent
    battery_levels = [agent.bateria for agent in model.schedule.agents if isinstance(agent, RoombaAgent)]
    return sum(battery_levels) / len(battery_levels) if battery_levels else 0

class CleaningModel(Model):
    """Un modelo con agentes que limpian un cuarto."""

    def __init__(self, width, height, n_agents, obstacle_density, dirty_cells_density):
        self.num_agents = n_agents
        self.grid = MultiGrid(width, height, torus=False)
        # RandomActivation is a scheduler that activates each agent once per step, in random order.
        self.schedule = RandomActivation(self)
        self.running = True
        self.datacollector = DataCollector(
            model_reporters={"BatteryLevel": battery_level}
        )
        self.visited_cells = set()

        # Crear agentes de limpieza
        if n_agents == 1:
            agent = RoombaAgent(0, self, 0, 0)
            self.schedule.add(agent)
            self.grid.place_agent(agent, (0, 0))
            chargin_station = ChargingStationAgent(1, self)
            self.schedule.add(chargin_station)
            self.grid.place_agent(chargin_station, (0, 0))
        else:
            for i in range(n_agents):
                # Añadir agentes a una celda aleatoria
                x = self.random.randrange(self.grid.width)
                y = self.random.randrange(self.grid.height)
                while (not self.grid.is_cell_empty((x, y))):
                    x = self.random.randrange(self.grid.width)
                    y = self.random.randrange(self.grid.height)
                
                agent = RoombaAgent(i, self, x, y)
                chargin_station = ChargingStationAgent(i+1000, self)
                self.schedule.add(agent)
                self.schedule.add(chargin_station)
                self.grid.place_agent(agent, (x, y))
                self.grid.place_agent(chargin_station, (x, y))

        # Generar obstaculos aleatorios
        for i in range(int(width * height * obstacle_density)):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            while (not self.grid.is_cell_empty((x, y))):
                x = self.random.randrange(self.grid.width)
                y = self.random.randrange(self.grid.height)
            obstacle = ObstacleAgent(i+2000, self)
            self.schedule.add(obstacle)
            self.grid.place_agent(obstacle, (x, y))

        # Generar celdas sucias aleatorias
        for i in range(int(width * height * dirty_cells_density)):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            while (not self.grid.is_cell_empty((x, y))):
                x = self.random.randrange(self.grid.width)
                y = self.random.randrange(self.grid.height)
            dirty_cell = DirtyCellAgent(i+3000, self)
            self.schedule.add(dirty_cell)
            self.grid.place_agent(dirty_cell, (x, y))
        

        self.datacollector.collect(self)

    def step(self):
        """Avanzar un paso en la simulación."""
        self.schedule.step()
        self.datacollector.collect(self)

    # Método para marcar las celdas como visitadas
    def mark_cell_visited(self, cell):
        self.visited_cells.add(cell)
