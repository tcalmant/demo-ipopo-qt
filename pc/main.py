#!/usr/bin/python
# -- Content-Encoding: UTF-8 --
"""
Pelix/Qt application bootstrap.

Loads Qt in the main thread and starts a Pelix framework in a second one

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
from pelix.ipopo.constants import use_ipopo
import pelix.framework

# Standard library
import argparse
import logging
import sys
import threading

# ------------------------------------------------------------------------------

BUNDLES = ("pelix.ipopo.core",
           "pelix.shell.core",
           "pelix.shell.ipopo",
           "pelix.shell.console",
           "pelix.shell.eventadmin",
           "pelix.http.basic",
           "pelix.remote.dispatcher",
           "pelix.remote.registry",
           "pelix.remote.json_rpc",
           "pelix.remote.discovery.multicast",
           "pelix.services.eventadmin")
""" Bundles to install by default in the Pelix framework """

# ------------------------------------------------------------------------------

def run_framework(framework, http_port, on_stop):
    """
    Handles Pelix framework starting and main loop.
    Waits for the framework to stop before stopping Qt and returning.

    This method should be executed in a new thread.

    :param framework: The Pelix framework to run
    :param http_port: Port the HTTP server will listen on
    :param on_stop: Method to call once the framework has stopped
    """
    try:
        # Start the framework
        context = framework.get_bundle_context()
        framework.start()

        # Instantiate components...
        with use_ipopo(context) as ipopo:
            # EventAdmin
            ipopo.instantiate("pelix-services-eventadmin-factory",
                              "pelix-services-eventadmin", {})

            # HTTP Service
            ipopo.instantiate("pelix.http.service.basic.factory",
                              "pelix.http.service.basic",
                              {"pelix.http.port": http_port})

            # Remote services
            ipopo.instantiate("pelix-remote-dispatcher-servlet-factory",
                              "pelix-remote-dispatcher-servlet", {})
            ipopo.instantiate("pelix-jsonrpc-exporter-factory",
                              "pelix-jsonrpc-exporter", {})
            ipopo.instantiate("pelix-jsonrpc-importer-factory",
                              "pelix-jsonrpc-importer", {})
            ipopo.instantiate("pelix-remote-discovery-multicast-factory",
                              "pelix-remote-discovery-multicast", {})


            # Install other bundles
            context.install_bundle("core.bridges").start()
            context.install_bundle("core.frame").start()
            context.install_bundle('core.framework_info').start()
            context.install_bundle('core.probe').start()

        bundles, _ = context.install_package('./details')
        for bundle in bundles:
            bundle.start()

        # Wait for stop then delete the framework
        framework.wait_for_stop()

    finally:
        # Notify that the framework has stopped
        if on_stop is not None:
            on_stop()

# ------------------------------------------------------------------------------

def main(args=None):
    """
    Loads Qt and the framework.
    Blocks while Qt or the framework are running.
    """
    if args is None:
        args = sys.argv[1:]

    # Get arguments
    parser = argparse.ArgumentParser(description="Pelix-Qt demo")
    parser.add_argument("-p", "--port", type=int, dest="http_port",
                        default=8080, metavar="PORT",
                        help="Port of the HTTP server")
    options = parser.parse_args(args)
    http_port = options.http_port

    # Prepare Qt (import the package as late as possible)
    import core.qt
    qt_loader = core.qt.QtLoader()
    qt_loader.setup()

    # Prepare the framework + iPOPO + shell)
    framework = pelix.framework.create_framework(BUNDLES)

    # Register QtLoader as a service
    context = framework.get_bundle_context()
    context.register_service(core.SVC_QT_LOADER, qt_loader, {})

    # Run the framework in a new thread
    thread = threading.Thread(target=run_framework, args=(framework,
                                                          http_port,
                                                          qt_loader.stop))
    thread.start()

    # Run the Qt loop (blocking)
    qt_loader.loop()

    # Stop the framework (if still there)
    framework.stop()
    thread.join(1)

    thread = None
    framework = None
    qt_loader = None

# ------------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("PyQt5").setLevel(logging.INFO)
    main()
