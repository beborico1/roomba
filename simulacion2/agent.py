from mesa import Agent
import networkx as nx

class RoombaAgent(Agent):
    def __init__(self, unique_id, model, x_inicial, y_inicial):
        super().__init__(unique_id, model)
        self.posicion_de_estacion_de_carga = (x_inicial, y_inicial)
        self.mis_celdas_vecinas = []
        self.vecinos_disponibles = []
        self.bateria = 100
        self.direccion = (1, 0)
        self.siguiente_celda = (0, 0)
        self.celdas_visitadas = set()
        self.celdas_no_visitadas = set()
        self.celdas_sucias = set()
        self.obstaculos = set()
        self.pasos_dados = 0
        self.cargando = False
        self.termine = False
        self.queue_de_movimientos_urgentes = []
        self.me_mori = False
        self.colchon = 25 # entre mas roombas tienes o mayor el grid probablemente quieras tener un colchon mas grande

    def rotate_to_face_cell(self, target_cell):
        if self.siguiente_celda == self.pos:
            self.direccion = (0, 0)
        elif self.siguiente_celda[0] == self.pos[0] + 1 and self.siguiente_celda[1] == self.pos[1]:
            self.direccion = (1, 0)
        elif self.siguiente_celda[0] == self.pos[0] - 1 and self.siguiente_celda[1] == self.pos[1]:
            self.direccion = (-1, 0)
        elif self.siguiente_celda[0] == self.pos[0] and self.siguiente_celda[1] == self.pos[1] + 1:
            self.direccion = (0, 1)
        elif self.siguiente_celda[0] == self.pos[0] and self.siguiente_celda[1] == self.pos[1] - 1:
            self.direccion = (0, -1)

    def calculate_route_to_cell_using_dijkstra(self, target_cell, visited_cells, obstacles, not_visited_cells):
        start = self.pos
        goal = target_cell

        G = nx.Graph()

        for cell in not_visited_cells.union(visited_cells).difference(obstacles):
            G.add_node(cell)
            for neighbor in self.get_neighbors_djikstra(cell, obstacles):
                if neighbor not in obstacles:
                    G.add_edge(cell, neighbor, weight=1)

        if start not in G or goal not in G:
            return []

        try:
            path = nx.shortest_path(
                G, source=start, target=goal, weight='weight')
            return path
        except nx.NetworkXNoPath:
            return []

    def get_neighbors_djikstra(self, cell, obstacles):
        neighbors = []
        for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            next_cell = (cell[0] + dx, cell[1] + dy)
            if not self.model.grid.out_of_bounds(next_cell) and next_cell not in obstacles:
                neighbors.append(next_cell)
        return neighbors

    def get_neighbors(self):
        neighbors = []
        for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            next_cell = (self.pos[0] + dx, self.pos[1] + dy)
            if not self.model.grid.out_of_bounds(next_cell) and next_cell not in self.visited:
                neighbors.append(next_cell)
        return neighbors

    def reconstruct_path(self, came_from, current):
        total_path = [current]
        while current in came_from:
            current = came_from[current]
            total_path.append(current)
        return total_path[::-1]

    def heuristic(self, cell, goal):
        return abs(cell[0] - goal[0]) + abs(cell[1] - goal[1])

    def obtener_celdas_vecinas(self):
        self.mis_celdas_vecinas = []
        # agregamos la celda de arriba la de abajo la izquierda y derecha
        self.mis_celdas_vecinas.append((self.pos[0], self.pos[1] + 1))
        self.mis_celdas_vecinas.append((self.pos[0], self.pos[1] - 1))
        self.mis_celdas_vecinas.append((self.pos[0] + 1, self.pos[1]))
        self.mis_celdas_vecinas.append((self.pos[0] - 1, self.pos[1]))
        vecinos_disponibles = []
        # appendear las celdas donde no haya ObstacleAgent ni Roomba Agent
        for vecino in self.mis_celdas_vecinas:
            # if vecino is out of bounds
            if self.model.grid.out_of_bounds(vecino):
                continue

            contenidos = self.model.grid.get_cell_list_contents(vecino)

            # agregar celdas no visitadas
            if not any(isinstance(obj, VisitedCellAgent) for obj in contenidos):
                self.celdas_no_visitadas.add(vecino)
            # agregar vecinos disponibles
            if not any(isinstance(obj, ObstacleAgent) for obj in contenidos) and not any(isinstance(obj, RoombaAgent) for obj in contenidos):
                vecinos_disponibles.append(vecino)
            # agregar obstaculos
            if any(isinstance(obj, ObstacleAgent) for obj in contenidos):
                self.obstaculos.add(vecino)
                self.celdas_no_visitadas.discard(vecino)
            # agregar celdas sucias
            if any(isinstance(obj, DirtyCellAgent) for obj in contenidos):
                self.celdas_sucias.add(vecino)
            # agregar celdas visitadas
            if any(isinstance(obj, VisitedCellAgent) for obj in contenidos):
                self.celdas_visitadas.add(vecino)
                self.celdas_no_visitadas.discard(vecino)
            # si hay una roomba vecina
            if any(isinstance(obj, RoombaAgent) for obj in contenidos):
                # vamos a obtener conocimiento de ella
                roomba_vecina = [roomba for roomba in contenidos if isinstance(roomba, RoombaAgent)][0]
                # print(f"Soy la Roomba {self.unique_id} y vamos a compartir conocimiento con Roomba {roomba_vecina.unique_id}")
                visitadas_previas = self.celdas_visitadas.copy()
                # imprimimos todo el conocimiento actual
                # print(f"Roomba {self.unique_id} tiene {self.celdas_visitadas} como celdas visitadas")
                # print(f"Roomba {roomba_vecina.unique_id} tiene {roomba_vecina.celdas_visitadas} como celdas visitadas")
                # print(f"Deberia aprender {roomba_vecina.celdas_visitadas.difference(self.celdas_visitadas)}")
                self.celdas_visitadas = self.celdas_visitadas.union(roomba_vecina.celdas_visitadas)
                self.celdas_no_visitadas = self.celdas_no_visitadas.union(roomba_vecina.celdas_no_visitadas)
                self.celdas_sucias = self.celdas_sucias.union(roomba_vecina.celdas_sucias)
                self.obstaculos = self.obstaculos.union(roomba_vecina.obstaculos)
                # quitamos de no visitados los que estan en visitados
                self.celdas_no_visitadas = self.celdas_no_visitadas.difference(self.celdas_visitadas)
                # quitamos de sucios los que estan en visitados
                self.celdas_sucias = self.celdas_sucias.difference(self.celdas_visitadas)
                # imprimir el conocimiento actualizado
                # print(f"Roomba {self.unique_id} tiene {self.celdas_visitadas} como celdas visitadas")
                # print lo que aprendi fue (la diferencia)
                # print(f"Roomba {self.unique_id} aprendio {self.celdas_visitadas.difference(visitadas_previas)}")
                # si la roomba termino o esta muerta la agregamos como obstaculo
                if roomba_vecina.termine or roomba_vecina.me_mori:
                    self.obstaculos.add(roomba_vecina.pos)                
 
        self.vecinos_disponibles = vecinos_disponibles

    def movernos(self):
        # volteamos a ver la celda
        self.rotate_to_face_cell(self.siguiente_celda)
        # quitamos la celda de la lista de celdas no visitadas
        self.celdas_no_visitadas.discard(self.pos)
        self.celdas_no_visitadas.discard(self.siguiente_celda)
        # si hay basura en la celda
        if self.siguiente_celda in self.celdas_sucias:
            # limpiamos la basura

            # llamar a model reduce_number_of_dirty_cells
            # si si hay basura en la celda
            contenidos = self.model.grid.get_cell_list_contents(self.siguiente_celda)
            if any(isinstance(obj, DirtyCellAgent) for obj in contenidos):
                self.model.reduce_number_of_dirty_cells()
                self.bateria -= 1 # esto nos quita 1 de bateria
            self.model.grid.remove_agent(self.model.grid.get_cell_list_contents(self.siguiente_celda)[0])
            self.celdas_sucias.remove(self.siguiente_celda)
            
            
        # nos movemos
        self.model.grid.move_agent(self, self.siguiente_celda)
        # quitamos uno de bateria
        self.bateria -= 1
        # agregamos uno a los pasos dados
        self.pasos_dados += 1
        # llamara a la funcion mark_cell_visited de model
        self.model.mark_cell_visited(self.pos)
        # place visited cell agent
        self.model.grid.place_agent(VisitedCellAgent(self.unique_id + 1000, self.model), self.pos)
    
    def step(self):
        # si ya termine
        if self.termine or self.me_mori:
            return
        # si tenemos alguna celda que no tiene un obstaculo o una roomba
        self.obtener_celdas_vecinas()
        if self.bateria <= 0:
            # print(f"Roomba {self.unique_id} se murio")
            self.me_mori = True
            return

        # si esta en la estacion de carga y tiene menos de 100 de bateria
        if self.pos == self.posicion_de_estacion_de_carga and self.bateria < 100:
            self.bateria += 5
            self.cargando = True
            if self.bateria >= 100:
                self.bateria = 100
                self.cargando = False
                if not self.celdas_no_visitadas:
                    self.termine = True
            return

        # si la longitud de la ruta mas corta a la estacion de carga es menor a la bateria que nos queda
        if len(self.calculate_route_to_cell_using_dijkstra(self.posicion_de_estacion_de_carga, self.celdas_visitadas, self.obstaculos, self.celdas_no_visitadas)) >= self.bateria - self.colchon and not self.queue_de_movimientos_urgentes: # agregamos aqui 25 de colchon por si se atora con otra rwmba
            # agregamos la ruta a la lista de emergencia
            nueva_ruta = self.calculate_route_to_cell_using_dijkstra(self.posicion_de_estacion_de_carga, self.celdas_visitadas, self.obstaculos, self.celdas_no_visitadas)
            if len(nueva_ruta) > 1:
                self.queue_de_movimientos_urgentes = nueva_ruta[1:]

        # si tenemos lista de emergencia
        if self.queue_de_movimientos_urgentes:
            # print(f"Roomba {self.unique_id} tiene una lista de emergencia que es {self.queue_de_movimientos_urgentes}")
            # si alguno de los movimientos de la lista de emergencia es un vecino disponible
            if any(movimiento in self.vecinos_disponibles for movimiento in self.queue_de_movimientos_urgentes):
                self.siguiente_celda = [movimiento for movimiento in self.queue_de_movimientos_urgentes if movimiento in self.vecinos_disponibles][0]
                self.queue_de_movimientos_urgentes.remove([movimiento for movimiento in self.queue_de_movimientos_urgentes if movimiento in self.vecinos_disponibles][0])
                self.movernos()
            else:
                # print(f"Soy Roomba {self.unique_id} y estoy en {self.pos} y no tengo vecinos disponibles en mi lista de emergencia")
                # calculamos de nuevo la lista mas corta a la estacion de carga tomando como un nuevo obstaculo la celda a la queriamos movernos
                roombas_vecinas = []
                vecinos = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False, radius=1)
                for vecino in vecinos:
                    contenidos = self.model.grid.get_cell_list_contents(vecino)
                    if any(isinstance(obj, RoombaAgent) for obj in contenidos):
                        # print(f"Roomba {self.unique_id} tiene una roomba vecina en {vecino}")
                        roombas_vecinas.append(vecino)

                nueva_ruta = self.calculate_route_to_cell_using_dijkstra(self.posicion_de_estacion_de_carga, self.celdas_visitadas, self.obstaculos.union(roombas_vecinas), self.celdas_no_visitadas)
                                                                         #self.obstaculos.union(self.queue_de_movimientos_urgentes[0]), self.celdas_no_visitadas)
                if len(nueva_ruta) > 1:
                    self.queue_de_movimientos_urgentes = nueva_ruta[1:]
                    # print(f"Roomba {self.unique_id} tiene una nueva lista de emergencia que es {self.queue_de_movimientos_urgentes}")
            return
        # elegir un vecino disponible al azar
        if self.vecinos_disponibles:
            # si hay suciedad en alguno de los vecinos disponibles nos movemos ahí
            if self.celdas_sucias.intersection(self.vecinos_disponibles):
                self.siguiente_celda = self.random.choice(list(self.celdas_sucias.intersection(self.vecinos_disponibles)))
            # si no si hay alguna celda que no hemos visitado nos movemos ahí
            elif self.celdas_no_visitadas.intersection(self.vecinos_disponibles):
                self.siguiente_celda = self.random.choice(list(self.celdas_no_visitadas.intersection(self.vecinos_disponibles)))
                # print(f"Roomba {self.unique_id} se ira a una celda no visitada que es {self.siguiente_celda}")
                
            # si no nos movemos a un vecino disponible al azar
            else:
                # si tenemos conocimiento de una celda sucia calculamos la ruta mas corta a esa celda
                if self.celdas_sucias:
                    ruta = self.calculate_route_to_cell_using_dijkstra(list(self.celdas_sucias)[0], self.celdas_visitadas, self.obstaculos, self.celdas_no_visitadas)
                    if len(ruta) > 1:
                        # print(f"Roomba {self.unique_id} se ira a una celda sucia que es {ruta[1]} con el objetivo de cumplir su ruta mas corta a una celda sucia que es {ruta}")
                        if ruta[1] in self.vecinos_disponibles:
                            self.siguiente_celda = ruta[1]
                        else:
                            roombas_vecinas = []
                            vecinos = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False, radius=1)
                            for vecino in vecinos:
                                contenidos = self.model.grid.get_cell_list_contents(vecino)
                                if any(isinstance(obj, RoombaAgent) for obj in contenidos):
                                    # print(f"Roomba {self.unique_id} tiene una roomba vecina en {vecino}")
                                    roombas_vecinas.append(vecino)
                            # volvemos a calcular la ruta mas corta tomando como obstaculos las roombas vecinas
                            ruta = self.calculate_route_to_cell_using_dijkstra(list(self.celdas_sucias)[0], self.celdas_visitadas, self.obstaculos.union(roombas_vecinas), self.celdas_no_visitadas)
                            if len(ruta) > 1:
                                # print(f"Roomba {self.unique_id} se ira a una celda sucia que es {ruta[1]} con el objetivo de cumplir su ruta mas corta a una celda sucia que es {ruta}")
                                self.siguiente_celda = ruta[1]
                    else:
                        # print(f"2. Roomba {self.unique_id} se ira a un vecino disponible al azar que es {self.random.choice(self.vecinos_disponibles)}")
                        self.siguiente_celda = self.random.choice(self.vecinos_disponibles)
                elif self.celdas_no_visitadas:
                    ruta = self.calculate_route_to_cell_using_dijkstra(list(self.celdas_no_visitadas)[0], self.celdas_visitadas, self.obstaculos, self.celdas_no_visitadas)
                    # print(f"1. Roomba {self.unique_id} tiene el objetivo de cumplir su ruta mas corta a una celda no visitada que es {ruta} la celda a la que se quiere llegar es {list(self.celdas_no_visitadas)[0]}")
                    if len(ruta) > 1:
                        # print(f"2. Roomba {self.unique_id} se ira a una celda no visitada que es {ruta[1]} con el objetivo de cumplir su ruta mas corta a una celda no visitada que es {ruta}")
                        if ruta[1] in self.vecinos_disponibles:
                            self.siguiente_celda = ruta[1]
                        else:
                            roombas_vecinas = []
                            vecinos = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False, radius=1)
                            for vecino in vecinos:
                                contenidos = self.model.grid.get_cell_list_contents(vecino)
                                if any(isinstance(obj, RoombaAgent) for obj in contenidos):
                                    # print(f"Roomba {self.unique_id} tiene una roomba vecina en {vecino}")
                                    roombas_vecinas.append(vecino)
                            # volvemos a calcular la ruta mas corta tomando como obstaculos las roombas vecinas
                            ruta = self.calculate_route_to_cell_using_dijkstra(list(self.celdas_no_visitadas)[0], self.celdas_visitadas, self.obstaculos.union(roombas_vecinas), self.celdas_no_visitadas)
                            if len(ruta) > 1:
                                # print(f"Roomba {self.unique_id} se ira a una celda sucia que es {ruta[1]} con el objetivo de cumplir su ruta mas corta a una celda sucia que es {ruta}")
                                self.siguiente_celda = ruta[1]
                    else:
                        # print(f"Roomba {self.unique_id} se ira a un vecino disponible al azar que es {self.random.choice(self.vecinos_disponibles)}")
                        self.siguiente_celda = self.random.choice(self.vecinos_disponibles)
                else:
                    # print(f"Roomba {self.unique_id} se ira a un vecino disponible al azar que es {self.random.choice(self.vecinos_disponibles)}")
                    self.siguiente_celda = self.random.choice(self.vecinos_disponibles)
        else:
            # print (f"Roomba {self.unique_id} no tiene vecinos disponibles")
            self.siguiente_celda = self.pos

        self.movernos()

        # print(f"Soy la Roomba {self.unique_id} y me movi a {self.pos} y me queda {self.bateria}% de bateria, y mi ruta mas corta a la estacion de carga es {self.calculate_route_to_cell_using_dijkstra(self.posicion_de_estacion_de_carga, self.celdas_visitadas, self.obstaculos, self.celdas_no_visitadas)}")
        return

class ObstacleAgent(Agent):  # Un agente que representa un obstáculo
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass  # Los obstáculos son estáticos, no hacen nada en cada paso


# Un agente que representa una estación de carga.
class ChargingStationAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass  # Las estaciones de carga son estáticas, no hacen nada en cada paso


class VisitedCellAgent(Agent):  # Un agente que representa una celda visitada
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass  # Las celdas visitadas son estáticas, no hacen nada en cada paso


class DirtyCellAgent(Agent):  # Un agente que representa una celda visitada
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass  # Las celdas visitadas son estáticas, no hacen nada en cada paso
