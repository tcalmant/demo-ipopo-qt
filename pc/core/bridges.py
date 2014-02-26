#!/usr/bin/python
# -- Content-Encoding: UTF-8 --
"""
Defines the bridges that instantiates info and detail components when needed

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
from pelix.ipopo.decorators import ComponentFactory, Requires, Validate, \
    Invalidate, Instantiate, BindField, UnbindField
import pelix.remote

# Standard library
import logging
import threading

# ------------------------------------------------------------------------------

_logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------

@ComponentFactory("probe-info-bridge-factory")
@Requires('_creator', core.SVC_FRAMEWORK_INSTANCE_INFO_FACTORY)
@Requires('_probes', core.SVC_PROBE, aggregate=True)
@Instantiate('probe-info-bridge')
class ProbeBridge(object):
    """
    Creates a Framework Instance Info component for each probe found
    """
    def __init__(self):
        """
        Sets up members
        """
        # Framework info creator
        self._creator = None

        # Injected probes
        self._probes = None

        # Framework UIDs -> probe service
        self._frameworks = {}


    @BindField('_probes')
    def bind_probe(self, field, service, reference):
        """
        A probe has been bound
        """
        framework_uid = reference.get_property(pelix.remote.PROP_FRAMEWORK_UID)

        # Store, using the framework UID
        self._frameworks[framework_uid] = service

        if self._creator:
            # Create the associated component
            self._creator.make(framework_uid)


    @UnbindField('_probes')
    def unbind_probe(self, field, service, reference):
        """
        A probe has gone
        """
        framework_uid = reference.get_property(pelix.remote.PROP_FRAMEWORK_UID)

        if framework_uid in self._frameworks:
            # Remove it from the local storage
            del self._frameworks[framework_uid]

            if self._creator:
                # Delete the component if possible
                self._creator.delete(framework_uid)


    @Validate
    def validate(self, context):
        """
        Component validated
        """
        for framework_uid in self._frameworks:
            # Make a component for all already known frameworks
            self._creator.make(framework_uid)


    @Invalidate
    def invalidate(self, context):
        """
        Component invalidated
        """
        for framework_uid in self._frameworks:
            # Delete all created components
            self._creator.delete(framework_uid)

# ------------------------------------------------------------------------------

@ComponentFactory("probe-details-bridge-factory")
@Requires('_creators', core.SVC_DETAILS_CREATOR_FACTORY,
          aggregate=True)
@Requires('_fwinfos', core.SVC_FRAMEWORK_INSTANCE_INFO, aggregate=True)
@Instantiate('probe-details-bridge')
class DetailsBridge(object):
    """
    Creates a Framework Instance Info component for each probe found
    """
    def __init__(self):
        """
        Sets up members
        """
        # Framework details creator
        self._creators = None

        # Framework info components
        self._fwinfos = None

        # Framework info -> [details]
        self._details = {}

        # Lock control
        self.__lock = threading.Lock()
        self.__validated = threading.Event()


    def __populate_info(self, info):
        """
        Creates the details components to be associated with the given framework
        information component
        
        :param info: The framework information component
        """
        uid = info.get_uid()
        for creator in self._creators:
            try:
                creator.make(uid)
            except Exception as ex:
                _logger.error("%s: %s", type(ex).__name__, ex)


    def __clear_info(self, info):
        """
        Deletes the details components associated to a framework information
        component
        
        :param info: The framework information component
        """
        if not self._creators:
            # No more creators
            return

        uid = info.get_uid()
        for creator in self._creators:
            try:
                creator.delete(uid)
            except Exception as ex:
                _logger.error("%s: %s", type(ex).__name__, ex)


    def __create_detail(self, creator):
        """
        Creates a detail component for all known framework information
        components
        
        :param creator: A detail component creator
        """
        for info in self._fwinfos:
            try:
                creator.make(info.get_uid())
            except Exception as ex:
                _logger.error("%s: %s", type(ex).__name__, ex)


    def __delete_detail(self, creator):
        """
        Creates a detail component for all known framework information
        components
        
        :param creator: A detail component creator
        """
        if not self._fwinfos:
            # No more framework information components
            return

        for info in self._fwinfos:
            try:
                creator.delete(info.get_uid())
            except Exception as ex:
                _logger.error("%s: %s", type(ex).__name__, ex)


    @BindField('_creators')
    def bind_detail(self, field, service, reference):
        """
        A detail creator has been bound
        """
        with self.__lock:
            if self.__validated.is_set():
                # Create a detail component for every known info
                self.__create_detail(service)


    @UnbindField('_creators')
    def unbind_detail(self, field, service, reference):
        """
        A detail creator has gone away
        """
        with self.__lock:
            # Remove the detail component for every known info
            self.__delete_detail(service)


    @BindField('_fwinfos')
    def bind_info(self, field, service, reference):
        """
        An information component has been bound
        """
        with self.__lock:
            if self.__validated.is_set():
                # Create the associated detail components
                self.__populate_info(service)


    @UnbindField('_fwinfos')
    def unbind_info(self, field, service, reference):
        """
        An information component has gone away
        """
        with self.__lock:
            # Kill all detail components for this info component
            self.__clear_info(service)


    @Validate
    def validate(self, context):
        """
        Component validated
        """
        # Setup all known components
        for info in self._fwinfos:
            self.__populate_info(info)

        # Activate un/bindings
        self.__validated.set()


    @Invalidate
    def invalidate(self, context):
        """
        Component invalidated
        """
        # Stop un/bindings
        self.__validated.clear()

        # Clear all known components
        for info in self._fwinfos:
            self.__clear_info(info)
