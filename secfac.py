#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Prototype code for SecFac

import libtcodpy as libtcod
from sys import argv
from messaging import Messenger, message_parser
from views import FacilityView
from facility import buildFacility
from constants import WIDTH, HEIGHT, MAP_WIDTH, MAP_HEIGHT

class Prompt(object):
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
    libtcod.console_init_root(WIDTH, HEIGHT, "FabSec", libtcod.RENDERER_SDL)
    libtcod.sys_set_fps(60)

# Global event system
messages = Messenger()

def read_command_file():
    """Debuggin' tool. Apply a series of commands."""
    with open('commands') as f:
        content = f.readlines()
    return content

if __name__ == "__main__":
    start_console()
    facility = buildFacility()
    view = FacilityView(facility)
    prompt = Prompt()
    map_console = libtcod.console_new(WIDTH, HEIGHT)
    prompt_console = libtcod.console_new(WIDTH,1)
    output_console = libtcod.console_new(WIDTH, 1)
    messages.focus = prompt
    now = libtcod.sys_elapsed_milli()

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
        messages.poll(prompt, facility)
