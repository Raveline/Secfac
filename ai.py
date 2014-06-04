from random import choice, randint
from constants import EmployeeType
import libtcodpy as libtcod

"""This module handle Artifical Intelligence stuff."""
class EmployeeBehaviour(object):
    WANDER = 0
    TASK_MOVE = 1
    TASK_DO = 2

    def __init__(self, locator, employeeType):
        # A reference to this employee localisation
        self.location = locator
        self.employeeType = employeeType
        self.currentTask = None
        self.currentPath = None
        self.set_behaviour(EmployeeBehaviour.WANDER)

    def set_behaviour(self, behaviour):
        self.behaviour = behaviour

    def is_idle(self):
        return self.behaviour == EmployeeBehaviour.WANDER

    def update(self, facility):
        potential_tasks = facility.get_task_for_type(self.employeeType)
        has_task = len(potential_tasks) > 0
        if self.is_idle() and has_task:
            task = potential_tasks[0]
            self.set_behaviour(EmployeeBehaviour.TASK_MOVE)
            self.moveToTask(task, facility)
        else:
            self.follow_behaviour(facility)

    def follow_behaviour(self, facility):
        self.tasks[self.behaviour](self, facility)

    def back_to_idleness(self):
        self.currentTask = None
        self.currentPath = None
        self.set_behaviour(EmployeeBehaviour.WANDER)

    def wander(self, facility):
        """Randomly move to a direction, stopping and changing
        direction in the meantime."""
        random_decision = randint(0,2)
        if random_decision == 1:
            potential_moves = [(1,0), (-1,0)]
            move = choice(potential_moves)
            self.location.moveTowards(move[0], move[1])
        elif random_decision == 2:
            self.location.moveTowards(0,0)

    def moveToTask(self, task, facility):
        """Compute a move to a given task. Called when taking a task."""
        taskX = task.location.getX()
        taskY = task.location.getY()
        close_tiles = facility.circulation.free_surrounding_tiles_of(taskX,
                                                                    taskY)
        closest = closest_tile_from(self.location.getX(),
                                    self.location.getY(),
                                    close_tiles)
        if closest is None:
            self.back_to_idleness()
            # Ideally, mark the task as "currently unreachable" to avoid
            # repeting this too often
        else:
            self.moveTo(closest[0], closest[1], facility)
            self.currentTask = task
            facility.consume_task(self.currentTask)

    def moveTo(self, x, y, facility):
        """Cancel the current path and take a general direction.
        If the move is illegal, do not change the current path."""
        self.currentPath = None
        print("Looking for a path between" +
                str(self.location.getX()) + "," +
                str(self.location.getY()) + " and " + str(x) + "," + str(y))
        self.currentPath =  facility.circulation.path_from_to(self.location.getX(),
                                        self.location.getY(),
                                        x,
                                        y)
        print("Length path : " +str(libtcod.path_size(self.currentPath)))

    def move(self, facility):
        """Follow the current path toward a given direction."""
        x,y = libtcod.path_walk(self.currentPath, False)
        if x is not None:
            self.location.moveTowards(x - self.location.x, y - self.location.y)
        else:
            # Path has been followed : delete it !
            libtcod.path_delete(self.currentPath)
            self.currentPath = None
            # STOP THE MOVEMENT !
            self.location.freeze()
            if self.currentTask is not None:
                self.set_behaviour(EmployeeBehaviour.TASK_DO)
            else:
                self.set_behaviour(EmployeeBehaviour.WANDER)

    def doTask(self, facility):
        pass

    # Class-level map to functions
    tasks = {WANDER : wander,
            TASK_MOVE : move,
            TASK_DO : doTask }

def manhattan(x1, y1, x2, y2):
    return abs(x1-x2) - abs(y1-y2)

def closest_tile_from(x, y, tiles):
    distances = [manhattan(x,y,tile[0], tile[1]) for tile in tiles]
    if len(distances) == 0:
        return None
    index_of_smallest_distance = distances.index(min(distances))
    return tiles[index_of_smallest_distance]

class DirectionCommand(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def execute(self, actor):
        actor.location.moveTowards(x,y)
