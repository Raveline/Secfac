#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Prototype code for SecFac

import libtcodpy as libtcod
from sys import argv
from messaging import Focusable, Messenger, Message, message_parser, messages
from views import FacilityView, MenuDisplay
from facility import buildFacility
from constants import WIDTH, HEIGHT, MAP_WIDTH, MAP_HEIGHT, EmployeeType

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
                message_part, children = []):
        self.label = label
        self.message_type = message_type
        self.message_part = message_part
        self.children = children
        self.shortcut = shortcut

class FacilityMap(Focusable):
    """Handle the main gameplay state. Manage selection, move on map,
    and pane menu navigation."""
    def __init__(self, pane, screen):
        self.pane = pane
        self.screen = screen
        self.areaSelectionMode = False
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
        self.startSelection(x,y)

    def movedOn(self, x, y):
        self.extendSelectionTo(x,y)

    def releasedOn(self, x, y):
        self.extendSelectionTo(x,y)
        self.sendAreaMessage()

    def sendAreaMessage(self):
        for x in range(self.selectionStart[0], self.selectionEnd[0] + 1):
            for y in range(self.selectionStart[1], self.selectionEnd[1] + 1):
                messages.receive(Message(self.currentAction, (x,y)))

    def escape(self):
        if self.pane.can_go_back():
            self.pane.go_back()
        else:
            messages.receive(Message(Message.QUIT))

    def tab(self):
        if self.screen.consoles[Screen.PANE].visible:
            self.screen.hide_pane()
        else:
            self.screen.show_pane()

    def append_char(self, char):
        submenu = self.pane.shortcuts.get(char, None)
        if submenu is not None:
            if submenu.message_type == MenuItem.ITEM_VERB:
                self.currentAction = submenu.message_part
                self.currentComplement = None
            if submenu.message_type == MenuItem.ITEM_COMPLEMENT:
                # Ideally, here, we should divide between verbs with area
                # which will require some more work before sending message
                # and verbs without area, which will work now.
                if self.currentAction in Message.area_verbs:
                    self.currentComplement = submenu.message_part
            if len(submenu.children):
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


def start_console():
    libtcod.console_init_root(WIDTH, HEIGHT, "FabSec", False, libtcod.RENDERER_SDL)
    libtcod.sys_set_fps(60)


def read_command_file():
    """Debuggin' tool. Apply a series of commands."""
    with open('commands') as f:
        content = f.readlines()
    return content

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

class Screen(object):
    MAP = 0
    PANE = 1
    PROMPT = 2
    FEEDBACK = 3

    """This class that manages offscreen console and focus."""
    def __init__(self, facility, menu, prompt):
        self.facilityDisplay = FacilityView(facility)
        self.menuDisplay = MenuDisplay(menu)
        self.build_consoles()
        self.prompt = prompt
        self.map_area = (20,0,WIDTH-20, HEIGHT-1)

    def build_consoles(self):
        self.consoles = []
        self.consoles.append(Console(20,0,WIDTH-20,HEIGHT))
        self.consoles.append(Console(0,0,20,HEIGHT))
        self.consoles.append(Console(0,HEIGHT-2,WIDTH, 1))
        self.consoles.append(Console(0,HEIGHT-1,WIDTH, 1))

    def get_real_console(self, console_id):
        return self.consoles[console_id].console

    def display(self, delta):
        self.facilityDisplay.display(self.get_real_console(Screen.MAP)
                                    , 0,0,WIDTH, HEIGHT, delta)
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

    def blit(self):
        for console in self.consoles:
            if console.visible:
                libtcod.console_blit(console.console, 0,0,0,0,0,
                                        console.x, console.y)
        # End of display : flush the console
        libtcod.console_flush()

def handle_arguments():
    no_commands = len(argv) > 1 and argv[1] == "noc"
    if not no_commands:
        commands = read_command_file()
        for command in commands:
            # Remove the \n and make upper caps
            command = command[:-1].upper()
            messages.receive(message_parser(command))

def main_game_loop(facility, consoles):
    now = libtcod.sys_elapsed_milli()
    while not messages.quit:
        # Time computing
        delta = libtcod.sys_elapsed_milli() - now
        now = libtcod.sys_elapsed_milli()
        # Model update
        messages.poll(game_mode, facility)
        facility.update(delta)
        # Display !
        consoles.display(delta)

if __name__ == "__main__":
    start_console()
    libtcod.mouse_show_cursor(True)
    facility = buildFacility()

    # TODO : read all that from a config file
    tree = MenuItem("Main menu", '', MenuItem.ITEM_VERB, Message.VIEW, [
                MenuItem("(D)ig", 'd', MenuItem.ITEM_VERB, Message.DIG),
                MenuItem("(B)uild", 'b', MenuItem.ITEM_VERB, Message.BUILD, [
                    MenuItem("(E)levator", 'e', MenuItem.ITEM_COMPLEMENT, "")]),
                MenuItem("(R)ecruit", 'r', MenuItem.ITEM_VERB, Message.RECRUIT, [
                    MenuItem("(W)orker", 'w', MenuItem.ITEM_COMPLEMENT,
                                        EmployeeType.WORKER),
                    MenuItem("(S)ecurity guard", 's', MenuItem.ITEM_COMPLEMENT,
                                        EmployeeType.SECURITY),
                    MenuItem("(R)esearcher", 'r', MenuItem.ITEM_COMPLEMENT,
                                        EmployeeType.RESEARCH)])
                ])

    menu = MenuPane(tree)
    prompt = Prompt()
    screen = Screen(facility, menu, prompt)
    game_mode = FacilityMap(menu, screen)
    messages.focus = game_mode
    # Use for debugging only, TODO : hide this, make it optional, whatever
    main_game_loop(facility, screen)

