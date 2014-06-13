import libtcodpy as libtcod
from messaging import Focusable, Message, messages
from views import FacilityView, MenuDisplay
from constants import WIDTH, HEIGHT, MAP_WIDTH, MAP_HEIGHT
from facility import Position

class MenuPane(object):
    def __init__(self, command_tree):
        """Take a tree of commands to be displayed."""
        self.branch_stack = []
        self.set_branch(command_tree)

    def enter_branch(self, branch):
        self.branch_stack.append(self.current_branch)
        self.set_branch(branch)

    def set_branch(self, branch):
        self.current_branch = branch
        self.shortcuts = dict([(elem.shortcut,elem) for elem in\
                                self.current_branch.children])

    def can_go_back(self):
        return self.branch_stack

    def go_back(self):
        self.set_branch(self.branch_stack.pop())

class MenuItem(object):
    ITEM_VERB = 0           # This item will carry a verb constant
    ITEM_COMPLEMENT = 1     # This item will carry a complement constant
    ITEM_NONE = 2           # This item carry no information, just children
    def __init__(self, label, shortcut, message_type,
                message_part, explaining_text = None, children = []):
        self.label = label
        self.message_type = message_type
        self.message_part = message_part
        self.children = children
        self.explaining_text = explaining_text
        self.shortcut = shortcut

class FacilityMap(Focusable):
    """Handle the main gameplay state. Manage selection, move on map,
    and pane menu navigation."""
    def __init__(self, pane, screen):
        self.pane = pane
        self.screen = screen
        self.areaSelectionMode = False
        self.currentAction = Message.VIEW
        self.selectionStart = None
        self.selectionEnd = None

    def startSelection(self, x, y):
        self.selectionStart = (x,y)

    def extendSelectionTo(self, x, y):
        if self.selectionStart[0] > x and self.selectionStart[1] > y:
            self.selectionEnd = self.selectionStart
            self.selectionStart = (x,y)
        else:
            self.selectionEnd = (x,y)

    def pressedOn(self, x, y):
        (x,y) = self.screen.local_to_global(x,y)
        if self.currentAction is not Message.VIEW:
            self.startSelection(x,y)
        else:
            self.screen.move_center(x,y)

    def movedOn(self, x, y):
        (x,y) = self.screen.local_to_global(x,y)
        if self.currentAction is not Message.VIEW:
            self.extendSelectionTo(x,y)
        else:
            self.screen.move_center(x,y)

    def releasedOn(self, x, y):
        (x,y) = self.screen.local_to_global(x,y)
        if self.currentAction is not Message.VIEW:
            self.extendSelectionTo(x,y)
            self.sendAreaMessage()

    def sendAreaMessage(self):
        if self.currentAction is not Message.VIEW:
            for x in range(self.selectionStart[0], self.selectionEnd[0] + 1):
                for y in range(self.selectionStart[1], self.selectionEnd[1] + 1):
                    messages.receive(Message(self.currentAction, (x,y)))

    def escape(self):
        if self.pane.can_go_back():
            self.pane.go_back()
            self.change_menu_action(self.pane.current_branch)
        else:
            messages.receive(Message(Message.QUIT))

    def tab(self):
        if self.screen.consoles[Screen.PANE].visible:
            self.screen.hide_pane()
        else:
            self.screen.show_pane()

    def change_menu_action(self, submenu):
        if submenu.message_type == MenuItem.ITEM_VERB:
            self.currentAction = submenu.message_part
            self.currentComplement = None
        if submenu.message_type == MenuItem.ITEM_COMPLEMENT:
            self.currentComplement = submenu.message_part

    def append_char(self, char):
        submenu = self.pane.shortcuts.get(char, None)
        if submenu is not None:
            self.change_menu_action(submenu)
            if submenu.children or submenu.explaining_text:
                self.pane.enter_branch(submenu)
            else:
                messages.receive(Message(self.currentAction, self.currentComplement))

class Prompt(Focusable):
    def __init__(self):
        self.content = ""

    def append_char(self,c):
        self.content += c

    def delete_char(self):
        self.content = self.content[:-1]

    def display(self, console):
        libtcod.console_clear(console)
        libtcod.console_print(console, 0,0, "> " + self.content)

    def enter(self):
        # Call to global. We'd like to avoid that.
        messages.clean()
        messages.receive(message_parser(self.content.upper()))
        self.content = ""

class Console(object):
    def __init__(self, x,y,w,h, visible = True):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.visible = visible
        self.create_console()

    def redraw(self, w, h):
        libtcod.console_delete(self.console)
        self.w = w
        self.h = h
        self.create_console()

    def create_console(self):
        self.console = libtcod.console_new(self.w, self.h)

class Viewport(object):
    def __init__(self, w, h, worldW, worldH):
        self.position = Position(0,0)
        self.worldW = worldW
        self.worldH = worldH
        self.redraw(w,h)

    def getX(self):
        return self.position.getX()

    def getY(self):
        return self.position.getY()

    def getX2(self):
        return self.position.getX() + self.w

    def getY2(self):
        return self.position.getY() + self.h

    def redraw(self, w, h):
        self.w = w
        self.h = h
        self.focusX = w/2
        self.focusY = h/2
        self.maxX = self.worldW - self.w
        self.maxY = self.worldH - self.h

    def move(self, centerx, centery):
        minx = self.position.x + self.focusX
        miny = self.position.y + self.focusY
        if centerx < minx:
            self.position.x = self.position.x - (minx-centerx)
        if centery < miny:
            self.position.y = self.position.y - (miny-centery)
        if centerx > minx:
            self.position.x = self.position.x + (centerx - minx)
        if centery > miny:
            self.position.y = self.position.y + (centery - miny)
        self.clamp()

    def clamp(self):
        if self.position.x < 0:
            self.position.x = 0
        if self.position.y < 0:
            self.position.y = 0
        if self.position.x > self.maxX:
            self.position.x = self.maxX
        if self.position.y > self.maxY:
            self.position.y = self.maxY

class MapConsole(Console):
    """Just a console with a viewport."""
    def __init__(self, x, y, w, h, visible, viewport):
        super(MapConsole, self).__init__(x,y,w,h,visible)
        self.viewport = viewport

    def redraw(self, w, h):
        super(MapConsole, self).redraw(w, h)
        self.viewport.redraw(w, h)

    def local_to_global(self, x, y):
        return (x + self.viewport.position.x - self.x
               ,y + self.viewport.position.y - self.y)

class Screen(object):
    MAP = 0
    PANE = 1
    PROMPT = 2
    FEEDBACK = 3

    """This class that manages offscreen console and focus."""
    def __init__(self, facility, menu, prompt):
        self.facilityDisplay = FacilityView(facility)
        self.menuDisplay = MenuDisplay(menu)
        self.prompt = prompt
        self.map_area = (20,0,WIDTH-20, HEIGHT-1)
        self.viewport = Viewport(WIDTH-20, HEIGHT, MAP_WIDTH, MAP_HEIGHT)
        self.build_consoles()

    def build_consoles(self):
        self.consoles = []
        self.consoles.append(MapConsole(20,0,WIDTH-20,HEIGHT, True, self.viewport))
        self.consoles.append(Console(0,0,20,HEIGHT))
        self.consoles.append(Console(0,HEIGHT-2,WIDTH, 1))
        self.consoles.append(Console(0,HEIGHT-1,WIDTH, 1))

    def get_real_console(self, console_id):
        return self.consoles[console_id].console

    def display(self, delta):
        map_console = self.consoles[self.MAP]
        self.facilityDisplay.display(map_console.console
                                    ,map_console.viewport.getX()
                                    ,map_console.viewport.getY()
                                    ,map_console.viewport.getX2()
                                    ,map_console.viewport.getY2()
                                    ,delta)
        if self.consoles[Screen.PANE].visible:
            self.menuDisplay.display(self.get_real_console(Screen.PANE))
        if self.consoles[Screen.PROMPT].visible:
            self.prompt.display(self.get_real_console(Screen.PROMPT))
        # Global call to the display, will need to get this out
        messages.display(self.get_real_console(Screen.FEEDBACK))
        # Display chain is done : let's blit
        self.blit()

    def hide_pane(self):
        self.consoles[Screen.PANE].visible = False
        map_console = self.consoles[Screen.MAP]
        map_console.x = 0
        map_console.redraw(map_console.w + self.consoles[Screen.PANE].w
                        , map_console.h)

    def show_pane(self):
        self.consoles[Screen.PANE].visible = True
        map_console = self.consoles[Screen.MAP]
        map_console.x = self.consoles[Screen.PANE].w
        map_console.redraw(map_console.w + self.consoles[Screen.PANE].w
                        , map_console.h)

    def hide_prompt(self):
        self.consoles[Screen.PROMPT].visible = False
        map_console = self.consoles[Screen.MAP]
        map_console.redraw(map_console.w,
                        map_console.h + self.consoles[Screen.PROMPT].h)

    def show_prompt(self):
        self.consoles[Screen.PROMPT].visible = True
        map_console = self.consoles[Screen.MAP]
        map_console.redraw(map_console.h,
                        map_console.h - self.consoles[PROMPT].h)

    def move_center(self, x, y):
        self.consoles[Screen.MAP].viewport.move(x,y)

    def blit(self):
        for console in self.consoles:
            if console.visible:
                libtcod.console_blit(console.console, 0,0,0,0,0,
                                        console.x, console.y)
        # End of display : flush the console
        libtcod.console_flush()

    def local_to_global(self, x, y):
        return self.consoles[Screen.MAP].local_to_global(x,y)
