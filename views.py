"""This module deals with display functions of SecFac."""

import libtcodpy as libtcod
from facility import Employee
from constants import GROUND, MAP_WIDTH, MAP_HEIGHT, EmployeeType

class MenuDisplay(object):
    def __init__(self, menu):
        self.menu = menu

    def display(self, console):
        libtcod.console_clear(console)
        self.display_string(console, 1, self.menu.current_branch.label)
        i = 3
        for item in self.menu.current_branch.children:
            i = i + 1
            self.display_string(console, i, item.label)

    def display_string(self, console, y, string):
        libtcod.console_print(console, 0,y,string)

class FacilityView(object):
    """An object that display the facility when asked to do so"""
    def __init__(self, facility):
        self.facility = facility
        self.allTradeDisplayer = DisplayCommand(libtcod.white)
        self.tileDisplayer = DisplayTileCommand(TilePainter())
        self.activeTaskDisplayer = DisplayBlinkingCommand(ord(' '), 250,
                                                    libtcod.white)
        self.inactiveTaskDisplayer = DisplayCommand()

    def display(self, console, fromx, fromy, tox, toy, delta):
        #print(fromx, fromy, tox, toy)
        libtcod.console_clear(console)
        self.display_tiles(console, fromx, fromy, tox, toy)
        self.display_employees(console, fromx, fromy, tox, toy)
        self.display_tasks(console, delta, fromx, fromy, tox, toy)

    def display_selection(self, console, crosshair, fromx, fromy, tox, toy):
        x = 0
        y = 0
        for lines in crosshair:
            for columns in lines:
                self.allTradeDisplayer.execute(fromx + x,fromy + y, 'X', console)
                x = x + 1
            y = y + 1
            x = 0

    def display_tiles(self, console, fromx, fromy, tox, toy):
        for y in range(fromy, toy):
            for x in range(fromx, tox):
                self.tileDisplayer.execute(self.facility.tiles[x][y],
                                        x-fromx, y-fromy, console)

    def display_tasks(self, console, tick, fromx, fromy, tox, toy):
        tasks = self.facility.extract_tasks_in(fromx, fromy, tox, toy)
        active_tasks = self.facility.extract_ongoing_tasks_in(fromx,
                                                                fromy,
                                                                tox, toy)
        # First, inactive tasks
        for task in tasks:
            self.allTradeDisplayer.execute(task.location.x - fromx,
                            task.location.y - fromy, ' ', console)
        # Then, active ones
        for task in active_tasks:
            self.activeTaskDisplayer.execute(tick
                                            , task.location.getX()
                                            , task.location.getY()
                                            , console)

    def display_employees(self, console, fromx, fromy, tox, toy):
        employees = self.facility.extract_employees_in(fromx, fromy, tox, toy)
        for employee in employees:
            self.print_employee(console, employee.employeeType,
                                employee.location.x, employee.location.y)

    def print_employee(self, console, employeeType, x, y):
        color = TilePainter.employeeToColor[employeeType]
        symbol = TilePainter.EMPLOYEE_SYMBOL
        libtcod.console_set_char_foreground(console,
                                            x,
                                            y,
                                            color)
        libtcod.console_set_char(console,x,y,symbol)

class TilePainter(object):
    employeeToColor = { EmployeeType.WORKER : libtcod.darker_yellow
                        , EmployeeType.SECURITY : libtcod.dark_blue
                        , EmployeeType.RESEARCH : libtcod.silver }
    EMPLOYEE_SYMBOL = 215

    def __init__(self):
        self.build_map()

    def build_map(self):
        upper = [libtcod.blue, libtcod.white, libtcod.grey,
        libtcod.lighter_grey, libtcod.blue, libtcod.blue,
        libtcod.blue, libtcod.blue, libtcod.blue, libtcod.green]
        colors = [libtcod.darker_grey, libtcod.black]
        index = [0, MAP_HEIGHT]
        gradient = libtcod.color_gen_map(colors, index)
        self.color_map = upper + list(gradient)

    def get_char(self, depth, solid):
        if depth > GROUND and solid:
            return libtcod.CHAR_BLOCK1
        else:
            return ord(' ')

    def get_foreground(self, depth, solid):
        if depth > GROUND and solid:
            return libtcod.black
        else:
            return None

    def get_background(self, depth, solid):
        if depth > GROUND and not solid:
            return libtcod.black
        else:
            return self.color_map[depth]

    def get_employee_color(self, employeeType):
        return self.employeeToColor[employeeType]

    def get_employee_symbol(self):
        return self.EMPLOYEE_SYMBOL


#####
# A series of basic implementations of the command pattern.
# Looking at it, I wonder if it's well done : we have repetition
# in the execute function, and at the same time, we cannot avoid
# different method signature for execute.
# Might be that we need some sort of decoration or sequence of steps
# to take to improve this.

class DisplayCommand(object):
    def __init__(self, background = None, foreground = None):
        self.background = background
        self.foreground = foreground

    def set_foreground(self, console, x, y):
        if self.foreground is not None:
            libtcod.console_set_char_foreground(console, x, y, self.foreground)

    def set_background(self, console, x, y):
        if self.background is not None:
            libtcod.console_set_char_background(console, x, y, self.background)

    def display_char(self, console, x, y, char):
        libtcod.console_set_char(console, x, y, char)

    def execute(self, x, y, char, console):
        self.set_foreground(console, x,y)
        self.set_background(console, x, y)
        self.display_char(console, x, y, char)

class DisplayTileCommand(DisplayCommand):
    def __init__(self, tileGetter):
        super(DisplayTileCommand, self).__init__(None, None)
        self.tileGetter = tileGetter

    def execute(self, tile, x, y, console):
        """For the tile painter, background and foreground properties
        will change each execution, after reading the proper information
        from the painter. Note : it could be worthwile to fuse the painter
        and this Command, here."""
        self.background = self.tileGetter.get_background(tile.depth, tile.solid)
        self.foreground = self.tileGetter.get_foreground(tile.depth, tile.solid)
        self.set_foreground(console, x, y)
        self.set_background(console, x, y)
        char = self.tileGetter.get_char(tile.depth, tile.solid)
        self.display_char(console, x, y, char)

class TimedDisplayCommand(DisplayCommand):
    def __init__(self, rythm, background = None, foreground = None):
        super(TimedDisplayCommand, self).__init__(background, foreground)
        self.rythm = rythm
        self.timer = 0

    def add_time(self, tick):
        self.timer = self.timer + tick
        if self.timer > self.rythm:
            self.timer = 0
            self.ticked()

    def ticked(self):
        pass

class DisplayAnimationCommand(TimedDisplayCommand):
    def __init__(self, chars, rythm, background = None, foreground = None):
        super(DisplayAnimationCommand, self).__init__(background, foreground)
        self.chars = chars
        self.index = 0

    def ticked(self):
        """Move the animation index."""
        self.index = self.index + 1
        if self.index == len(self.chars):
            self.index = 0

    def execute(self, tick, x, y, console):
        self.add_time(tick)
        self.set_foreground(console, x, y)
        self.set_background(console, x, y)
        self.display_char(console, x, y, self.chars[self.index])

class DisplayBlinkingCommand(TimedDisplayCommand):
    def __init__(self, char, rythm, background = None, foreground = None):
        super(DisplayBlinkingCommand, self).__init__(rythm, background, foreground)
        self.char = char
        self.visible = True

    def ticked(self):
        """Negate the current visible value."""
        self.visible = not self.visible

    def execute(self, tick, x, y, console):
        self.add_time(tick)
        if self.visible:
            self.set_foreground(console, x, y)
            self.set_background(console, x, y)
            self.display_char(console, x, y, self.char)
