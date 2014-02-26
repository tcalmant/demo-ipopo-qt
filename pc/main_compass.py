#!/usr/bin/python
# -- Content-Encoding: UTF-8 --
"""
Pelix remote framework test

Starts a framework with a fake compass service

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

# ------------------------------------------------------------------------------

BUNDLES = ("pelix.ipopo.core",
           "pelix.shell.core",
           "pelix.shell.ipopo",
           "pelix.shell.console",
           "pelix.http.basic",
           "pelix.remote.dispatcher",
           "pelix.remote.registry",
           "pelix.remote.json_rpc",
           "pelix.remote.discovery.multicast",
           "pelix.services.eventadmin")
""" Bundles to install by default in the Pelix framework """

# ------------------------------------------------------------------------------

def main(args=None):
    """
    Loads Qt and the framework.
    Blocks while Qt or the framework are running.
    """
    if args is None:
        args = sys.argv[1:]

    # Get arguments
    parser = argparse.ArgumentParser(description="Pelix-Qt demo - Fake Compass")
    parser.add_argument("-p", "--port", type=int, dest="http_port",
                        default=8081, metavar="PORT",
                        help="Port of the HTTP server")
    options = parser.parse_args(args)
    http_port = options.http_port

    # Prepare the framework + iPOPO + shell)
    framework = pelix.framework.create_framework(BUNDLES)
    context = framework.get_bundle_context()
    framework.start()

    # Instantiate components
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
    context.install_bundle('core.probe').start()
    context.install_bundle('utils.fake_compass').start()

    # Wait for stop then delete the framework
    framework.wait_for_stop()


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
