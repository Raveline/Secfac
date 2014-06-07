#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Prototype code for SecFac

import libtcodpy as libtcod
from sys import argv
from messaging import Focusable, Messenger, Message, message_parser, messages
from views import FacilityView
from facility import buildFacility
from constants import WIDTH, HEIGHT, MAP_WIDTH, MAP_HEIGHT

class FacilityMap(Focusable):
    def __init__(self):
        self.areaSelectionMode = False
        self.currentAction = Message.DIG
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
        self.endMessage()

    def endMessage(self):
        for x in range(self.selectionStart[0], self.selectionEnd[0] + 1):
            for y in range(self.selectionStart[1], self.selectionEnd[1] + 1):
                messages.receive(Message(self.currentAction, (x,y)))

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

if __name__ == "__main__":
    start_console()
    libtcod.mouse_show_cursor(True)
    facility = buildFacility()
    view = FacilityView(facility)
    prompt = Prompt()
    map_console = libtcod.console_new(WIDTH, HEIGHT)
    prompt_console = libtcod.console_new(WIDTH,1)
    output_console = libtcod.console_new(WIDTH, 1)
    messages.focus = prompt
    now = libtcod.sys_elapsed_milli()
    game_mode = FacilityMap()

    no_commands = len(argv) > 1 and argv[1] == "noc"
    if not no_commands:
        commands = read_command_file()
        for command in commands:
            # Remove the \n and make upper caps
            command = command[:-1].upper()
            messages.receive(message_parser(command))
    while not messages.quit:
        delta = libtcod.sys_elapsed_milli() - now
        now = libtcod.sys_elapsed_milli()
        facility.update(delta)
        view.display(map_console, 0,0,WIDTH, HEIGHT, delta)
        prompt.display(prompt_console)
        messages.display(output_console)
        libtcod.console_blit(map_console, 0,0,0,0,0,0,0)
        libtcod.console_blit(prompt_console, 0,0,0,0,0,0,HEIGHT-2)
        libtcod.console_blit(output_console, 0,0,0,0,0,0,HEIGHT-1)
        libtcod.console_flush()
        messages.poll(game_mode, facility)
