"""This module components handle events around SecFac."""

import libtcodpy as libtcod

class Message(object):
    """An event, most of the time a player input translated into game-logic."""
    PUT = "PUT"
    DIG = "DIG"
    TILE = "TILE"
    DISPLAY = "DISPLAY"
    RECRUIT = "RECRUIT"
    verbs = [PUT, DIG, RECRUIT]

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

    def poll(self, focus, world):
        self.poll_keys(focus)
        self.poll_events(world)

    def poll_keys(self,focus):
        key = libtcod.console_check_for_keypress()
        if key.vk == libtcod.KEY_NONE:
            return
        elif key.vk == libtcod.KEY_ESCAPE:
            self.quit = True
        elif key.vk == libtcod.KEY_BACKSPACE:
            self.focus.delete_char()
        elif key.vk == libtcod.KEY_ENTER:
            self.focus.enter()
        elif key.c != 0:
            self.focus.append_char(chr(key.c))
        return

    def poll_events(self, world):
        if self.has_world_message():
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

    def has_display_message(self):
        return self.has_messages() and self.messages[0].getVerb() == Message.DISPLAY

    def has_world_message(self):
        return self.has_messages() and \
                self.messages[0].getVerb() in [Message.DIG, Message.RECRUIT]

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
