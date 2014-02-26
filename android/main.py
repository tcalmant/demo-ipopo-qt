#!/usr/bin/python
# -- Content-Encoding: UTF-8 --
"""
Pelix demo: Android Compass, using Kivy

Based on the "compass" example of the Kivy project.

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
import kivy
kivy.require('1.0.9')
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.app import App

# PyJnius
from jnius import autoclass

# Pelix
import pelix.framework
from pelix.ipopo.constants import get_ipopo_svc_ref

# Logging trick
import logging
import sys
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

# ------------------------------------------------------------------------------

# Pelix Bundles
BUNDLES = ("pelix.ipopo.core",
           "pelix.shell.core",
           "pelix.shell.ipopo",
           "pelix.shell.eventadmin",
           "pelix.shell.remote",
           "pelix.http.basic",
           "pelix.remote.dispatcher",
           "pelix.remote.registry",
           "pelix.remote.json_rpc",
           "pelix.remote.discovery.multicast",
           "pelix.services.eventadmin")

# ------------------------------------------------------------------------------

class PelixScreen(GridLayout):
    """
    Main screen
    """
    def __init__(self, hardware, **kwargs):
        """
        Sets up the main screen
        """
        super(PelixScreen, self).__init__(**kwargs)

        # Declare members
        self._framework = None
        self._hardware = hardware

        # Setup the UI
        self.cols = 1
        self.add_widget(Label(text='Compass Demo'))
        self.add_widget(Button(text='Start Pelix',
                        on_release=self.on_pelix_btn))


    def __setup_components(self):
        """
        Instantiates iPOPO components
        """
        # Get the iPOPO service
        context = self._framework.get_bundle_context()
        ipopo = get_ipopo_svc_ref(context)[1]

        # Remote Shell
        ipopo.instantiate("ipopo-remote-shell-factory", "remote-shell",
                          {"pelix.shell.address": "0.0.0.0",
                           "pelix.shell.port": 9001})

        # EventAdmin (with 2 threads only)
        ipopo.instantiate("pelix-services-eventadmin-factory",
                          "pelix-services-eventadmin",
                          {"pool.threads": 2})

        # HTTP Service
        ipopo.instantiate("pelix.http.service.basic.factory",
                          "pelix.http.service.basic",
                          {"pelix.http.port": 9000})

        # Remote services
        ipopo.instantiate("pelix-remote-dispatcher-factory",
                          "pelix-remote-dispatcher", {})
        ipopo.instantiate("pelix-remote-dispatcher-servlet-factory",
                          "pelix-remote-dispatcher-servlet", {})
        ipopo.instantiate("pelix-remote-imports-registry-factory",
                          "pelix-remote-imports-registry", {})
        ipopo.instantiate("pelix-jsonrpc-exporter-factory",
                          "pelix-jsonrpc-exporter", {})
        ipopo.instantiate("pelix-jsonrpc-importer-factory",
                          "pelix-jsonrpc-importer", {})
        ipopo.instantiate("pelix-remote-discovery-multicast-factory",
                          "pelix-remote-discovery-multicast", {})

        # Compass
        ipopo.instantiate("compass-event-sender-factory",
                          "compass-event-sender",
                          {"clock.tick": .1})


    def on_pelix_btn(self, instance, *args):
        """
        Called when the Pelix button is clicked
        """
        if self._framework is None:
            # Setup the framework
            self._framework = pelix.framework.create_framework(BUNDLES)
            context = self._framework.get_bundle_context()

            # Start the framework
            self._framework.start()

            # Register the Hardware object as a service
            context.register_service("android.hardware", self._hardware, {})

            # Install the probe
            context.install_bundle('core.probe').start()

            # Install the "compass" package
            bundles, _ = context.install_package('./compass')
            for bundle in bundles:
                bundle.start()

            # Instantiate components
            self.__setup_components()

            # Change the button text
            instance.text = "Stop Pelix"

        else:
            # Stop the framework
            self.stop()

            # Change the button text
            instance.text = "Start Pelix"


    def stop(self):
        """
        The application is stopping
        """
        # Stop the framework
        pelix.framework.FrameworkFactory.delete_framework(self._framework)
        self._framework = None


# ------------------------------------------------------------------------------

class CompassApp(App):
    """
    Main application
    """
    def __init__(self, **kwargs):
        """
        Sets up members
        """
        App.__init__(self, **kwargs)
        self._screen = None

        # Load the Hardware class
        self.Hardware = autoclass('org.renpy.android.Hardware')

        # Load the Context class
        self.Context = autoclass('android.content.Context')

        # Load the activity class
        PythonActivity = autoclass('org.renpy.android.PythonActivity')
        # Get the current activity instance
        self.__activity = PythonActivity.mActivity

        # The Wifi multicast lock
        self.__multicast_lock = None


    def build(self):
        """
        Builds the application content
        """
        # Get a Wifi lock
        wifi = self.__activity.getSystemService(self.Context.WIFI_SERVICE)
        self.__multicast_lock = wifi.createMulticastLock("Pelix-RS-Multicast")
        self.__multicast_lock.acquire()

        # Setup the main screen
        self._screen = PelixScreen(self.Hardware())
        return self._screen


    def on_stop(self):
        """
        The application is stopping
        """
        # Stop the framework if needed
        if self._screen is not None:
            self._screen.stop()
            self._screen = None

        # Release the Wifi
        if self.__multicast_lock is not None:
            self.__multicast_lock.release()
            self.__multicast_lock = None


# ------------------------------------------------------------------------------

if __name__ in '__main__':
    # Entry point
    CompassApp().run()
