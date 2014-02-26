#!/usr/bin/python
# -- Content-Encoding: UTF-8 --
"""
Defines the basic probe component

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

# Local package
import core

# iPOPO
from pelix.ipopo.decorators import ComponentFactory, Validate, \
    Invalidate, Instantiate, Provides, Property, Requires
import pelix.framework
import pelix.remote
import pelix.services

# Standard library
import logging

# ------------------------------------------------------------------------------

BUNDLE_EVENT_PREFIX = "pelix/framework/BundleEvent"
""" Prefix to Bundle events """

SERVICE_EVENT_PREFIX = "pelix/framework/ServiceEvent"
""" Prefix to Service events """

_logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------

@ComponentFactory("basic-probe-factory")
@Provides(core.SVC_PROBE)
@Requires('_event', pelix.services.SERVICE_EVENT_ADMIN)
@Property('_export_config', pelix.remote.PROP_EXPORTED_CONFIGS, ["jsonrpc"])
@Property('_export_interface', pelix.remote.PROP_EXPORTED_INTERFACES,
          [core.SVC_PROBE])
@Instantiate('basic-probe')
class BasicProbe(object):
    """
    Basic probe
    """
    def __init__(self):
        """
        Sets up the probe
        """
        # Bundle context
        self._context = None

        # EventAdmin
        self._event = None

        # Export properties
        self._export_config = None
        self._export_interface = None


    def get_bundles(self):
        """
        Retrieves a dictionary: Bundle ID -> Bundle Name
        
        :return: A dictionary (ID -> Name)
        """
        result = {}
        for bundle in self._context.get_bundles():
            bid = bundle.get_bundle_id()
            result[bid] = bundle.get_symbolic_name()

        return result


    def get_bundle_state(self, bundle_id):
        """
        Retrieves the state (int) of the given bundle
        
        :param bundle_id: A bundle ID
        :return: The bundle status (int), -1 if unknown
        """
        try:
            return self._context.get_bundle(bundle_id).get_state()

        except pelix.framework.BundleException as ex:
            # Invalid bundle ID
            _logger.error("Error retrieving bundle state: %s", ex)
            return -1


    def get_services_info(self):
        """
        Retrieves the properties of all registered services in an array.
        
        :return: An array of properties
        """
        result = []
        references = self._context.get_all_service_references(None, None)
        for reference in references:
            # Only keep the properties of the service
            props = {}
            for key in reference.get_property_keys():
                props[key] = reference.get_property(key)

            result.append(props)

        return result


    def bundle_changed(self, event):
        """
        Notified by the framework of a bundle event
        """
        if self._event is None:
            # Late callback
            return

        bundle = event.get_bundle()
        kind = event.get_kind()

        # Handled events
        events = ("INSTALLED", "STARTING", "STARTED", "STOPPED", "STOPPING",
                  "STOPPING_PRECLEAN", "UNINSTALLED", "UPDATE_BEGIN",
                  "UPDATE_FAILED", "UPDATED")
        for event in events:
            if kind == getattr(pelix.framework.BundleEvent, event):
                event = "{0}/{1}".format(BUNDLE_EVENT_PREFIX, event)
                break
        else:
            # Unknown event
            return

        # Setup properties
        props = {}
        props['bundle.id'] = bundle.get_bundle_id()
        props['bundle.symbolicName'] = bundle.get_symbolic_name()
        props['bundle.state'] = bundle.get_state()

        # Post the event
        self._event.post(event, props)


    def service_changed(self, event):
        """
        Notified by the framework of a service event
        """
        if self._event is None:
            # Late callback
            return

        ref = event.get_service_reference()
        kind = event.get_kind()

        # Handled events
        events = ("REGISTERED", "MODIFIED", "UNREGISTERED")
        for event in events:
            if kind == getattr(pelix.framework.ServiceEvent, event):
                event = "{0}/{1}".format(SERVICE_EVENT_PREFIX, event)
                break

        else:
            # Unknown event
            return

        # Setup the event properties
        props = {}
        props["service.id"] = ref.get_property(pelix.framework.SERVICE_ID)
        props["service.properties"] = ref.get_properties()

        # Post the event
        self._event.post(event, props)


    @Validate
    def validate(self, context):
        """
        Component validated
        """
        self._context = context
        self._context.add_bundle_listener(self)

    @Invalidate
    def invalidate(self, context):
        """
        Component invalidated
        """
        self._context.remove_bundle_listener(self)
        self._context = None
