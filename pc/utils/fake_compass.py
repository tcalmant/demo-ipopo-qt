#!/usr/bin/python
# -- Content-Encoding: UTF-8 --
"""
Compass event sender

Sends fake compass events via EventAdmin every 10th of second.

:author: Thomas Calmant
:copyright: Copyright 2013, isandlaTech
:license: GPLv2
:version: 0.1
:status: Alpha
"""

# Module version
__version_info__ = (0, 1, 0)
__version__ = ".".join(map(str, __version_info__))

# Documentation strings format
__docformat__ = "restructuredtext en"

# ------------------------------------------------------------------------------

# Pelix
from pelix.ipopo.decorators import ComponentFactory, Requires, Provides, \
    Property, Instantiate, Validate, Invalidate
import pelix.remote
import pelix.services

# Standard library
import logging
import random
import threading

# ------------------------------------------------------------------------------

ANGLE_TOPIC = "pelix/demo/compass/angle"
SVC_COMPASS = "pelix.demo.compass"

_logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------

@ComponentFactory("fake-compass-event-sender-factory")
@Provides(SVC_COMPASS)
@Requires('_event', pelix.services.SERVICE_EVENT_ADMIN)
@Property('_tick', 'clock.tick', 1.0)
@Property('_export_config', pelix.remote.PROP_EXPORTED_CONFIGS, ["jsonrpc"])
@Property('_export_interface', pelix.remote.PROP_EXPORTED_INTERFACES,
          [SVC_COMPASS])
@Instantiate("fake-compass")
class FakeCompassEventSender(object):
    """
    Compass event sender component
    """
    def __init__(self):
        """
        Sets up members
        """
        # EventAdmin
        self._event = None

        # Previous value
        self._value = 0

        # The clock
        self._timer = None

        # Export properties
        self._export_config = None
        self._export_interface = None


    def _clock_tick(self, dt=0):
        """
        Notified of a clock tick
        """
        if self._event is None:
            # Late tick
            return False

        # Compute the angle
        angle = self.get_angle()

        # Post the event
        self._event.post(ANGLE_TOPIC, {"angle": angle})

        # Continue the ticks
        if self._timer is not None:
            self._timer = threading.Timer(.1, self._clock_tick)
            self._timer.start()

        return True


    def get_angle(self):
        """
        Retrieves the current angle of the telephone

        :return: A float angle in degrees
        """
        # Compute the angle (from the Kivy compass example)
        self._value += random.randint(-10, 10)
        return self._value


    @Validate
    def validate(self, context):
        """
        Component validated
        """
        # First value
        self._value = random.randint(0, 359)

        # Start the sensor
        self._timer = threading.Timer(.1, self._clock_tick)
        self._timer.start()


    @Invalidate
    def invalidate(self, context):
        """
        Component invalidated
        """
        # Stop the clock
        self._timer.cancel()
        self._timer = None
