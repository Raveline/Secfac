"""This module contains gameplay classes connected
to the facility the player has to manage."""

from constants import MAP_WIDTH, MAP_HEIGHT, EmployeeType
from messaging import Message
from ai import EmployeeBehaviour
import libtcodpy as libtcod

class Tile(object):
    def __init__(self, depth):
        self.depth = depth
        self.solid = self.depth > 3
        self.resistance = 5

    def dig(self):
        self.resistance = self.resistance - 1
        if self.resistance == 0:
            self.solid = False

class FacilityPath(object):
    def __init__(self, tiles):
        self.tiles = tiles
        self.build_path_map()

    def build_path_map(self):
        self.path_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
        for y in range(0, MAP_HEIGHT):
            for x in range (0, MAP_WIDTH):
                libtcod.map_set_properties(self.path_map
                                        , x
                                        , y
                                        , False
                                        , not self.tiles[x][y].solid)


    def path_from_to(self, ox, oy, dx, dy):
        path = libtcod.path_new_using_map(self.path_map, 0)
        libtcod.path_compute(path, ox, oy, dx, dy)
        return path

    def is_movement_possible(self, x,y):
        return self.is_tile_in_map(x,y) and not self.tiles[x][y].solid

    def is_tile_in_map(self, x,y):
        return x >= 0 and y >= 0 and x < MAP_WIDTH and y < MAP_HEIGHT

    def surrounding_tiles_of(self, x, y):
        return [(x-1, y-1), (x, y-1), (x+1, y-1),
               (x-1, y), (x+1, y),
               (x-1, y+1), (x, y+1), (x+1, y+1)]

    def free_surrounding_tiles_of(self,x,y):
        return [tile for tile in self.surrounding_tiles_of(x,y) if
            self.is_movement_possible(tile[0], tile[1])]

class SecureFacility(object):
    def __init__(self, tiles):
        self.objects = {} # A dict of coord tuple and array of objects
        self.tiles = tiles
        self.employees = []
        self.todoList = []
        self.beingDoneList = []
        self.circulation = FacilityPath(self.tiles)
        self.tick = 0

    def command(self, message):
        if message.complement() is not None:
            if message.getVerb() == Message.DIG:
                self.add_dig(message.complement())
            elif message.getVerb() == Message.RECRUIT:
                self.add_employee(message.complement())

    def add_employee(self, employeeType):
        if employeeType in Employee.jobs:
            employee = Employee(Employee.jobs[employeeType])
            self.employees.append(employee)

    def add_dig(self, location):
        # Cannot dig above ground !
        if location[1] >= 4:
            self.todoList.append(Task(Message.DIG, location))

    def extract_employees_in(self, x1, y1, x2, y2):
        return self.extract_location(x1,y1,x2,y2, self.employees)

    def extract_tasks_in(self, x1, y1, x2, y2):
        return self.extract_location(x1,y1,x2,y2, self.todoList)

    def extract_ongoing_tasks_in(self, x1, y1, x2, y2):
        return self.extract_location(x1,y1,x2,y2, self.beingDoneList)

    def extract_location(self, x1, y1, x2, y2, array):
        return [item for item in array
                if item.location.isIn(x1,y1,x2,y2)]

    def consume_task(self, task):
        self.todoList.remove(task)
        self.beingDoneList.append(task)

    def get_task_for_type(self, employeeType):
        tasks_searched = Task.employeesTasksType[employeeType]
        return [task for task in self.todoList
                    if task.taskType in tasks_searched]

    def update(self, time):
        self.tick += time
        if self.tick > 500:
            self.tick = 0
            self.update_employees()

    def update_employees(self):
        for employee in self.employees:
            employee.behaviour.update(self)
            employee.location.update(self)


class Location(object):
    """A simple container to provide cartesian coordinates."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dirX = 0
        self.dirY = 0

    def getX(self):
        return self.x

    def getY(self):
        return self.y

    def isIn(self, x1,y1,x2,y2):
        return self.x >= x1 and self.x <= x2 \
                and self.y >= y1 and self.y <= y2

    def freeze(self):
        self.moveTowards(0,0)

    def moveTowards(self, x, y):
        self.dirX = x
        self.dirY = y

    def update(self, facility):
        nextX = self.x + self.dirX
        nextY = self.y + self.dirY
        if facility.circulation.is_movement_possible(nextX, nextY):
            self.x = nextX
            self.y = nextY

class Employee(object):
    jobs = { 'WORKER' : EmployeeType.WORKER
            , 'SECURITY' : EmployeeType.SECURITY
            , 'RESEARCH' : EmployeeType.RESEARCH }

    def __init__(self, employeeType):
        self.employeeType = employeeType
        self.location = Location(0,3)
        self.behaviour = EmployeeBehaviour(self.location, self.employeeType)

class Task(object):
    employeesTasksType = { EmployeeType.WORKER : [Message.DIG],
                            EmployeeType.SECURITY : [],
                            EmployeeType.RESEARCH : [] }

    def __init__(self, taskType, location):
        self.taskType = taskType
        self.location = Location(location[0], location[1])

def buildFacility():
    """Build a new complex."""
    return SecureFacility(build_tiles())

def build_tiles():
    """Return the tile matrix for a new complex."""
    return [[ Tile(y)
                for y in range(MAP_HEIGHT) ]
                for x in range(MAP_WIDTH) ]
