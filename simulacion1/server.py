from mesa.visualization import CanvasGrid
from mesa.visualization import ModularServer
from mesa.visualization.modules import ChartModule
from mesa.visualization import Slider
from model import CleaningModel, RoombaAgent, ObstacleAgent, ChargingStationAgent, VisitedCellAgent, DirtyCellAgent


def agent_portrayal(agent):
    if isinstance(agent, RoombaAgent):
        dx, dy = agent.direccion
        if dx == 0 and dy == 0:
            portrayal = {"Shape": "circle",
                        "Filled": "true",
                        "Layer": 4,
                        "Color": "black",
                        "r": 0.5}
        else:
            portrayal = {"Shape": "arrowHead",
                        "Filled": "true",
                        "Layer": 4,
                        "Color": "black",
                        "scale": 0.5,
                        "heading_x": dx,
                        "heading_y": dy}
    elif isinstance(agent, ChargingStationAgent):
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 3,
                     "Color": "green",
                     "r": 0.8}
    elif isinstance(agent, ObstacleAgent):
        portrayal = {"Shape": "rect",
                     "Filled": "true",
                     "Layer": 2,
                     "Color": "black",
                     "w": 1,
                     "h": 1}
    elif isinstance(agent, DirtyCellAgent):
        portrayal = {"Shape": "rect",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": "#b8967d",
                     "w": 1,
                     "h": 1}
    elif isinstance(agent, VisitedCellAgent):
        portrayal = {"Shape": "rect",
                     "Filled": "true",
                     "Layer": 0,
                     "Color": "lightgray",
                     "w": 1,
                     "h": 1}
    return portrayal


def battery_level(model):
    battery_levels = [
        agent.bateria for agent in model.schedule.agents if isinstance(agent, RoombaAgent)]
    return sum(battery_levels) / len(battery_levels) if battery_levels else 0


battery_chart = ChartModule([{"Label": "BatteryLevel",
                              "Color": "Red"}],
                            data_collector_name='datacollector')

grid = CanvasGrid(agent_portrayal, 10, 10, 500, 500)

model_params = {
    #"n_agents": 1,
    "n_agents": Slider("Number of Agents", 1, 1, 10, 1),
    "obstacle_density": Slider("Obstacle Density", 0.1, 0.0, 0.99, 0.01),
    "dirty_cells_density": Slider("Dirty Cells Density", 0.1, 0.0, 0.99, 0.01),
    "width": 10,
    "height": 10
}

server = ModularServer(CleaningModel,
                       [grid, battery_chart],
                       "Room Cleaning Simulation",
                       model_params)

server.port = 8521
server.launch()
