#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest

import libtcodpy as tcod
from facility import *
from secfac import *

class ViewportTest(unittest.TestCase):
    MAP_SIZE_TEST_WIDTH = 200
    MAP_SIZE_TEST_HEIGHT = 100
    VIEWPORT_WIDTH = 80
    VIEWPORT_HEIGHT = 60

    def setUp(self):
        self.viewport = Viewport(self.VIEWPORT_WIDTH,
                                self.VIEWPORT_HEIGHT,
                                self.MAP_SIZE_TEST_WIDTH,
                                self.MAP_SIZE_TEST_HEIGHT)

    def testCenter(self):
        self.viewport.move(self.MAP_SIZE_TEST_WIDTH/2
                        , self.MAP_SIZE_TEST_HEIGHT/2)
        self.assertEquals(self.viewport.getX()
                , self.MAP_SIZE_TEST_WIDTH/2 - self.VIEWPORT_WIDTH/2)
        self.assertEquals(self.viewport.getX2()
                , self.MAP_SIZE_TEST_WIDTH/2 + self.VIEWPORT_WIDTH/2)
        self.assertEquals(self.viewport.getY()
                , self.MAP_SIZE_TEST_HEIGHT/2 - self.VIEWPORT_HEIGHT/2)
        self.assertEquals(self.viewport.getY2()
                , self.MAP_SIZE_TEST_HEIGHT/2 + self.VIEWPORT_HEIGHT/2)

    def testLeft(self):
        self.viewport.move(0, self.MAP_SIZE_TEST_HEIGHT/2)
        self.assertEquals(self.viewport.getX(), 0)
        self.assertEquals(self.viewport.getX2(), self.VIEWPORT_WIDTH)
        self.assertEquals(self.viewport.getY()
                , self.MAP_SIZE_TEST_HEIGHT/2 - self.VIEWPORT_HEIGHT/2)
        self.assertEquals(self.viewport.getY2()
                , self.MAP_SIZE_TEST_HEIGHT/2 + self.VIEWPORT_HEIGHT/2)

    def testRight(self):
        self.viewport.move(self.MAP_SIZE_TEST_WIDTH,
                        self.MAP_SIZE_TEST_HEIGHT/2)
        self.assertEquals(self.viewport.getX()
                        , self.MAP_SIZE_TEST_WIDTH - self.VIEWPORT_WIDTH)
        self.assertEquals(self.viewport.getX2(), self.MAP_SIZE_TEST_WIDTH)
        self.assertEquals(self.viewport.getY()
                , self.MAP_SIZE_TEST_HEIGHT/2 - self.VIEWPORT_HEIGHT/2)
        self.assertEquals(self.viewport.getY2()
                , self.MAP_SIZE_TEST_HEIGHT/2 + self.VIEWPORT_HEIGHT/2)

    def testTop(self):
        self.viewport.move(self.MAP_SIZE_TEST_WIDTH/2,
                        0)
        self.assertEquals(self.viewport.getX()
                , self.MAP_SIZE_TEST_WIDTH/2 - self.VIEWPORT_WIDTH/2)
        self.assertEquals(self.viewport.getX2()
                , self.MAP_SIZE_TEST_WIDTH/2 + self.VIEWPORT_WIDTH/2)
        self.assertEquals(self.viewport.getY(), 0)
        self.assertEquals(self.viewport.getY2() , self.VIEWPORT_HEIGHT)

    def testBottom(self):
        self.viewport.move(self.MAP_SIZE_TEST_WIDTH/2
                        , self.MAP_SIZE_TEST_HEIGHT)
        self.assertEquals(self.viewport.getX()
                , self.MAP_SIZE_TEST_WIDTH/2 - self.VIEWPORT_WIDTH/2)
        self.assertEquals(self.viewport.getX2()
                , self.MAP_SIZE_TEST_WIDTH/2 + self.VIEWPORT_WIDTH/2)
        self.assertEquals(self.viewport.getY(),
                        self.MAP_SIZE_TEST_HEIGHT - self.VIEWPORT_HEIGHT)
        self.assertEquals(self.viewport.getY2() , self.MAP_SIZE_TEST_HEIGHT)

class ElevatorTest(unittest.TestCase):
    def setUp(self):
        self.elevator = Elevator(Location(0,4))
        self.elevator.add_floor(8)
        self.elevator.add_floor(16)
        self.elevator.add_floor(24)
        self.elevator.add_floor(32)

    def test_call(self):
        self.elevator.call(8)
        self.elevator.call(16)
        self.assertEquals(len(self.elevator.call_at), 2)
        self.assertTrue(self.elevator.is_called_or_has_destination())

    def test_can_go_to(self):
        self.assertTrue(self.elevator.can_go_to(8))
        self.assertFalse(self.elevator.can_go_to(9))

    def test_basic_destination(self):
        self.elevator.call(8)
        self.assertEquals(self.elevator.decide_next_destination(), 1)
        self.elevator.cabin_position = 8
        self.elevator.call(0)
        self.assertEquals(self.elevator.decide_next_destination(), -1)

    def test_move_continuity(self):
        # The elevator is going down, has 1 call down left, but has 2 call up.
        # It should keep going down.
        self.elevator.call(0)
        self.elevator.call(8)
        self.elevator.call(24)
        self.elevator.cabin_position = 16
        self.elevator.location.dirY = 1
        self.assertEquals(self.elevator.decide_next_destination(), 1)

    def test_move_discontinuity(self):
        # The elevator is going down, has 2 call up, but no call down anymore.
        # It should move up.
        self.elevator.call(0)
        self.elevator.call(8)
        self.elevator.cabin_position = 16
        self.elevator.location.dirY = 1
        self.assertEquals(self.elevator.decide_next_destination(), -1)

    def test_move_need_to_stop(self):
        # There is no call but the elevator is still moving. It should stop.
        self.elevator.location.dirY = 1
        self.assertEquals(self.elevator.decide_next_destination(), 0)

if __name__ == "__main__":
    unittest.main()
class ElevatorTest(unittest.TestCase):
    def setUp(self):
        self.elevator = Elevator(Location(0,4))
        self.elevator.add_floor(8)
        self.elevator.add_floor(16)
        self.elevator.add_floor(24)
        self.elevator.add_floor(32)

    def test_call(self):
        self.elevator.call(8)
        self.elevator.call(16)
        self.assertEquals(len(self.elevator.call_at), 2)
        self.assertTrue(self.elevator.is_called_or_has_destination())

    def test_can_go_to(self):
        self.assertTrue(self.elevator.can_go_to(8))
        self.assertFalse(self.elevator.can_go_to(9))

    def test_basic_destination(self):
        self.elevator.call(8)
        self.assertEquals(self.elevator.decide_next_destination(), 1)
        self.elevator.cabin_position = 8
        self.elevator.call(0)
        self.assertEquals(self.elevator.decide_next_destination(), -1)

    def test_move_continuity(self):
        # The elevator is going down, has 1 call down left, but has 2 call up.
        # It should keep going down.
        self.elevator.call(0)
        self.elevator.call(8)
        self.elevator.call(24)
        self.elevator.cabin_position = 16
        self.elevator.location.dirY = 1
        self.assertEquals(self.elevator.decide_next_destination(), 1)

    def test_move_discontinuity(self):
        # The elevator is going down, has 2 call up, but no call down anymore.
        # It should move up.
        self.elevator.call(0)
        self.elevator.call(8)
        self.elevator.cabin_position = 16
        self.elevator.location.dirY = 1
        self.assertEquals(self.elevator.decide_next_destination(), -1)

    def test_move_need_to_stop(self):
        # There is no call but the elevator is still moving. It should stop.
        self.elevator.location.dirY = 1
        self.assertEquals(self.elevator.decide_next_destination(), 0)

if __name__ == "__main__":
    unittest.main()
