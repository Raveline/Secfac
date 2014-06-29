"""This module components handle events around SecFac."""

import libtcodpy as libtcod

class Focusable(object):
    def __init__(self):
        pass

    def clicked(self):
        pass

    def tab(self):
        pass

    def delete_char(self):
        pass

    def escape(self):
        pass

    def enter(self):
        pass

    def append_char(self, char):
        pass

    def pressedOn(self, x, y):
        pass

    def movedOn(self, x, y):
        pass

    def releasedOn(self, x, y):
        pass

class Message(object):
    """An event, most of the time a player input translated into game-logic."""
    PUT = "PUT"
    DIG = "DIG"
    TILE = "TILE"
    BUILD = "BUILD"
    DISPLAY = "DISPLAY"
    RECRUIT = "RECRUIT"
    VIEW = "VIEW"
    QUIT = "QUIT_GAME"
    verbs = [PUT, DIG, RECRUIT, QUIT]
    area_verbs = [PUT, DIG, BUILD]

    def __init__(self, verb, complement = None):
        self.verb = verb
        self.complements = []
        if complement is not None:
            self.complements.append(complement)

    def getVerb(self):
        """Serve the message's verb."""
        return self.verb

    def complement(self):
        """Serve the first available complement."""
        if len(self.complements) > 0:
            return self.complements[0]
        else:
            return None

    def add_complement(self, complement):
        self.complements.append(complement)

class Messenger(object):
    """A global object that will route messages. Currently fairly basic."""
    def __init__(self):
        self.quit = False
        self.messages = []
        # Just a clean-your-prompt signal
        self.must_clean = False
        # Flag for mouse left button drag
        self.current_lclick = False
        self.mouse = libtcod.Mouse()
        self.key = libtcod.Key()
        # Last position shall be cached here since libtcod is somewhat buggy
        # there
        self.lastX = 0
        self.lastY = 0

    def poll(self, focus, world):
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,self.key,self.mouse)
        self.poll_keys(focus)
        self.poll_mouse(focus)
        self.poll_events(world)

    def poll_mouse(self, focus):
        if self.mouse.lbutton:
            if not self.current_lclick:
                self.current_lclick = True
                focus.pressedOn(self.mouse.cx, self.mouse.cy)
            else:
                focus.movedOn(self.mouse.cx, self.mouse.cy)
        elif self.mouse.lbutton_pressed:
            focus.releasedOn(self.mouse.cx, self.mouse.cy)
            self.current_lclick = False
        else:
            mouse_move_x = self.mouse.cx - self.lastX
            mouse_move_y = self.mouse.cy - self.lastY
            self.lastX = self.mouse.cx
            self.lastY = self.mouse.cy
            focus.move_crosshair(mouse_move_x, mouse_move_y)

    def poll_keys(self,focus):
        if self.key.vk == libtcod.KEY_NONE:
            return
        elif self.key.vk == libtcod.KEY_ESCAPE:
            self.focus.escape()
        elif self.key.vk == libtcod.KEY_TAB:
            self.focus.tab()
        elif self.key.vk == libtcod.KEY_BACKSPACE:
            self.focus.delete_char()
        elif self.key.vk == libtcod.KEY_ENTER:
            self.focus.enter()
        elif self.key.c != 0:
            self.focus.append_char(chr(self.key.c))

        if self.has_quit_message():
            self.quit = True

    def poll_events(self, world):
        while self.has_world_message():
            message = self.consume_message()
            world.command(message)

    def receive(self, message):
        self.messages.append(message)

    def display(self, console):
        if self.must_clean:
            libtcod.console_clear(console)
            self.must_clean = False
        if self.has_display_message():
            message = self.consume_message()
            libtcod.console_clear(console)
            libtcod.console_print(console, 0,0,message.complement())

    def has_quit_message(self):
        return self.has_messages() and self.messages[0].getVerb() in [Message.QUIT]

    def has_display_message(self):
        return self.has_messages() and self.messages[0].getVerb() in [Message.DISPLAY]

    def has_world_message(self):
        return self.has_messages() and \
                self.messages[0].getVerb() in [Message.DIG, Message.RECRUIT, Message.BUILD]

    def has_messages(self):
        return len(self.messages)

    def consume_message(self):
        return self.messages.pop(0)

    def clean(self):
        self.must_clean = True

def message_parser(text):
    words = text.split(' ')
    verb = parseVerb(words[0])
    if verb is None:
        return Message(Message.DISPLAY, "Unknown verb : " + words[0] + " !")
    message = Message(verb)
    sentence = words[1:]
    while len(sentence) > 0:
        sentence, complement = parseComplement(sentence)
        if complement is None:
            return Message(Message.DISPLAY, "String is not parsable !")
        message.add_complement(complement)
    return message

def parseVerb(word):
    if word in Message.verbs:
        return word
    else:
        return None

def parseComplement(complement):
    index = 1
    element = None
    if complement[0] == Message.TILE:
        coords = complement[1].split(',')
        coords = map(int,coords)
        element = (tuple(coords))
        index = 2
    else:
        element = complement[0]
    return complement[index:], element

# Global event system
messages = Messenger()
