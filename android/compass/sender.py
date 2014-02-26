#!/usr/bin/python
# -- Content-Encoding: UTF-8 --
"""
Compass event sender

Sends compass events via EventAdmin every second.

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

# Kivy
from kivy.clock import Clock
from kivy.vector import Vector

# Pelix
from pelix.ipopo.decorators import ComponentFactory, Requires, Provides, \
    Property, Validate, Invalidate
import pelix.remote
import pelix.services

# Standard library
import logging

# ------------------------------------------------------------------------------

ANGLE_TOPIC = "pelix/demo/compass/angle"
SVC_COMPASS = "pelix.demo.compass"

_logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------

@ComponentFactory("compass-event-sender-factory")
@Provides(SVC_COMPASS)
@Requires('_event', pelix.services.SERVICE_EVENT_ADMIN)
@Requires('_hardware', "android.hardware")
@Property('_tick', 'clock.tick', 1.0)
@Property('_export_config', pelix.remote.PROP_EXPORTED_CONFIGS, ["jsonrpc"])
@Property('_export_interface', pelix.remote.PROP_EXPORTED_INTERFACES,
          [SVC_COMPASS])
class CompassEventSender(object):
    """
    Compass event sender component
    """
    def __init__(self):
        """
        Sets up members
        """
        # EventAdmin
        self._event = None

        # Hardware
        self._hardware = None

        # Clock tick time
        self._tick = 1.0

        # Export properties
        self._export_config = None
        self._export_interface = None


    def _clock_tick(self, dt):
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
        return True


    def get_angle(self):
        """
        Retrieves the current angle of the telephone

        :return: A float angle in degrees
        """
        # Compute the angle (from the Kivy compass example)
        (x, y, _) = self._hardware.magneticFieldSensorReading()
        return Vector(x, y).angle((0, 1))


    @Validate
    def validate(self, context):
        """
        Component validated
        """
        # Start the sensor
        self._hardware.magneticFieldSensorEnable(True)

        # Schedule the Kivy clock
        Clock.schedule_interval(self._clock_tick, self._tick)


    @Invalidate
    def invalidate(self, context):
        """
        Component invalidated
        """
        # Stop the clock
        Clock.unschedule(self._clock_tick)

        # Stop the sensor
        self._hardware.magneticFieldSensorEnable(False)
