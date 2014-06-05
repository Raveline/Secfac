"""This module contains gameplay classes connected
to the facility the player has to manage."""

from constants import MAP_WIDTH, MAP_HEIGHT, EmployeeType
from messaging import Message
from ai import EmployeeBehaviour
import libtcodpy as libtcod

def walk_compute(xFrom, yFrom, xTo, yTo, user_data):
    """This function is used for pathfinding. It will need to be
    imrpoved to allow diagonal move ONLY for stairway patterns."""
    if user_data[xTo][yTo].solid:
        return 0
    else:
        return 1

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

    def path_from_to(self, ox, oy, dx, dy):
        path = libtcod.path_new_using_function(MAP_WIDTH,
                                        MAP_HEIGHT,
                                        walk_compute,
                                        self.tiles,
                                        1.41)
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

class Elevator(object):
    def __init__(self, location):
        self.location = location
        self.floors = [location.getY()]
        # Current position of the elevator
        self.cabin_position = location.getY()
        # Floors where the elevator is called
        self.call_at = []
        # Current destinations required by passengers
        self.destinations = []
        self.stopping = False

    def add_floor(self, depth):
        self.floors.append(depth)
        self.floors.sort()

    def call(self, depth):
        if not self.is_called_at(depth):
            self.call_at.append(depth)

    def can_go_to(self, depth):
        return depth in self.floors

    def arrives_at(self, depth):
        if depth in self.call_at:
            self.call_at.remove(depth)
        if depth in self.destinations:
            self.destinations.remove(depth)
        self.cabin_position = depth

    def is_called_at(self, depth):
        return depth in self.call_at

    def destination_or_call_in_current_direction(self):
        potentials = []
        call_and_dest = self.destinations + self.call_at
        if self.location.dirY > 0:
            potentials = [f for f in call_and_dest if f > self.cabin_position]
        elif self.location.diry < 0:
            potentials = [f for f in call_and_dest if f < self.cabin_position]
        return len(potentials) > 0

    def is_called_or_has_destination(self):
        return len(self.destinations) > 0 or len(self.call_at) > 0

    def decide_next_destination(self):
        if self.location.dirY != 0:
            if not self.destination_or_call_in_current_direction():
                if self.is_called_or_has_destination():
                    return self.location.dirY * (-1)
                else:
                    return 0 # Stop moving !
            else:
                return 1
        else: # The cabin doesn't move
            if not self.is_called_or_has_destination():
                return 0
            else: # Go up or go down ?
                return self.arbitrate_between_calls()

    def arbitrate_between_calls(self):
        goUp = len([f for f in self.call_at if f < self.cabin_position])
        goDown = len([f for f in self.call_at if f > self.cabin_position])
        if goUp > goDown:
            return -1
        else:
            return 1 # Note : means we go down if equality

class SecureFacility(object):
    def __init__(self, tiles):
        self.objects = [] # A dict of coord tuple and array of objects
        self.tiles = tiles
        self.employees = []
        self.todoList = []
        self.beingDoneList = []
        self.circulation = FacilityPath(self.tiles)
        self.tick = 0

    def add_object_on(self, x, y, obj):
        self.objects.append(obj)

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

    def done(self, task):
        self.beingDoneList.remove(task)

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

