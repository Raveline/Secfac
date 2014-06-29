#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Prototype code for SecFac

import libtcodpy as libtcod
from secfacUI import FacilityMap, Screen, MenuItem, MenuPane, Prompt, Selection
from sys import argv
from messaging import Messenger, Message, message_parser, messages
from facility import buildFacility
from constants import WIDTH, HEIGHT, EmployeeType

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

    # TODO : read all that from a config file
    tree = MenuItem("Main menu", '', MenuItem.ITEM_VERB, Message.VIEW, "", [
                MenuItem("(D)ig", 'd', MenuItem.ITEM_VERB, Message.DIG,
                        "Select tiles to dig."),
                MenuItem("(B)uild", 'b', MenuItem.ITEM_VERB
                    , Message.BUILD, "", [
                    MenuItem("(E)levator", 'e', MenuItem.ITEM_COMPLEMENT, "")]),
                MenuItem("(R)ecruit", 'r', MenuItem.ITEM_VERB,
                        Message.RECRUIT, "", [
                    MenuItem("(W)orker", 'w', MenuItem.ITEM_COMPLEMENT,
                                        EmployeeType.WORKER),
                    MenuItem("(S)ecurity guard", 's', MenuItem.ITEM_COMPLEMENT,
                                        EmployeeType.SECURITY),
                    MenuItem("(R)esearcher", 'r', MenuItem.ITEM_COMPLEMENT,
                                        EmployeeType.RESEARCH)])
                ])

    menu = MenuPane(tree)
    prompt = Prompt()
    selection = Selection(0,0,0,0)
    screen = Screen(facility, menu, prompt, selection)
    game_mode = FacilityMap(menu, screen, selection)
    messages.focus = game_mode
    # Use for debugging only, TODO : hide this, make it optional, whatever
    main_game_loop(facility, screen)

