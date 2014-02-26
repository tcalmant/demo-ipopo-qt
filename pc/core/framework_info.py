#!/usr/bin/python
# -- Content-Encoding: UTF-8 --
"""
Defines the Qt tab widget containing the informations of a framework

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
from pelix.ipopo.decorators import ComponentFactory, Requires, \
    Invalidate, Instantiate, Provides, Property, BindField, UnbindField
import pelix.ipopo.constants as constants
import pelix.remote

# PyQt4
import PyQt4.QtGui as QtGui

# Standard library
import logging

# ------------------------------------------------------------------------------

FRAMEWORK_INFO_FACTORY = "framework-instance-info-factory"

_logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------

@ComponentFactory("framework-instance-info-creator-factory")
@Requires('_ipopo', constants.IPOPO_SERVICE_SPECIFICATION)
@Provides(core.SVC_FRAMEWORK_INSTANCE_INFO_FACTORY)
@Instantiate("framework-instance-info-creator")
class FrameworkInstanceInfoCreator(object):
    """
    Service that instantiates FrameworkInstanceInfo components
    """
    def __init__(self):
        """
        Sets up the component
        """
        # Bundle context
        self._context = None

        # iPOPO
        self._ipopo = None

        # Instances
        self._instances = {}


    def __make_name(self, dispatcher_id):
        """
        Generates the component name, based on the dispatcher ID
        
        :param dispatcher_id: The ID of the dispatcher exporting the Probe
                              service
        :return: The component name
        """
        return "framework-instance-info-{0}".format(dispatcher_id or "local")


    def make(self, framework_uid):
        """
        Makes a FrameworkInstanceInfo component, using the probe service
        matching the given framework UID
        
        :param framework_uid: The UID of the framework exporting the Probe
                              service
        :return: The instantiated component
        :raise Exception: Something went wrong during the instantiation
        """
        if not framework_uid:
            framework_uid = None

        try:
            # Already created component
            return self._instances[framework_uid]

        except KeyError:
            # Generate a name
            name = self.__make_name(framework_uid)

            # Prepare the @Requires filter override
            properties = {}
            properties[core.PROP_PROBE_UID] = framework_uid
            if framework_uid:
                probe_filter = "({0}={1})" \
                               .format(pelix.remote.PROP_FRAMEWORK_UID,
                                       framework_uid)
                details_filter = "({0}={1})".format(core.PROP_PROBE_UID,
                                                    framework_uid)
            else:
                probe_filter = "(!({0}=*))" \
                               .format(pelix.remote.PROP_FRAMEWORK_UID)
                details_filter = "(!({0}=*))".format(core.PROP_PROBE_UID)

            properties[constants.IPOPO_REQUIRES_FILTERS] = {
                '_probe': probe_filter,
                '_details': details_filter,
                }

            # Instantiate the component
            component = self._ipopo.instantiate(FRAMEWORK_INFO_FACTORY,
                                                name, properties)

            self._instances[framework_uid] = component
            return component


    def delete(self, dispatcher_id):
        """
        Deletes the component associated to the given dispatcher
        
        :param dispatcher_id: The ID of the dispatcher exporting the Probe
                              service
        """
        if not dispatcher_id:
            dispatcher_id = None

        if dispatcher_id in self._instances:
            # Delete it
            del self._instances[dispatcher_id]
            self._ipopo.kill(self.__make_name(dispatcher_id))


    @Invalidate
    def invalidate(self, context):
        """
        Component invalidated
        
        :param context: Bundle context
        """
        # Clear all known instances
        for dispatcher_id in self._instances.keys():
            self.delete(dispatcher_id)

        self._instances.clear()

# ------------------------------------------------------------------------------

@ComponentFactory(FRAMEWORK_INFO_FACTORY)
@Requires('_details', core.SVC_DETAILS, aggregate=True, optional=True)
@Requires('_qt_loader', core.SVC_QT_LOADER)
@Provides(core.SVC_FRAMEWORK_INSTANCE_INFO)
@Property('_dispatcher_id', core.PROP_PROBE_UID)
class FrameworkInstanceInfo(object):
    """
    The framework instance info widget
    """
    def __init__(self):
        """
        Sets up the component
        """
        # The Qt service
        self._qt_loader = None

        # The details services
        self._details = None

        # Details service -> reference
        self._details_refs = {}

        # The remote service dispatcher ID
        self._dispatcher_id = None

        # Qt Tab widget
        self._widget = None

        # Details widgets
        self._details_widgets = {}


    def get_name(self):
        """
        Returns the dispatcher ID, or "Local"
        """
        return "{0}".format(self._dispatcher_id or "Local")


    def get_uid(self):
        """
        Returns the raw dispatcher ID
        """
        return self._dispatcher_id


    def get_widget(self, parent):
        """
        Makes the Qt widget that will show the framework instance information.
        
        This method must/will be be called from the UI thread.
        
        :return: A QWidget object
        """
        if self._widget:
            return self._widget

        # Make the tab bar
        self._widget = QtGui.QTabWidget(parent)

        # Add all known details
        for service, reference in self._details_refs.items():
            self.__add_tab(service, reference)

        return self._widget


    def clean(self, parent):
        """
        Cleans the UI elements.
        
        This method must/will be be called from the UI thread.
        """
        for detail_widget in self._details_widgets:
            try:
                detail_widget.clean()
            except:
                # Ignore errors
                pass

        # Clear references
        self._widget = None


    def __add_tab(self, service, reference):
        """
        Adds a tab to the UI
        
        This method must be be called from the UI thread.
        
        :param service: A details service
        :param reference: The service reference
        """
        # Prepare the widget
        widget = service.get_widget(self._widget)

        # Store it in cache
        self._details_widgets[reference] = widget

        # Add it to the UI
        self._widget.addTab(widget, service.get_name())


    def __remove_tab(self, service, reference):
        """
        Removes a tab from the UI.
        
        This method must be be called from the UI thread.
        
        :param service: A details service
        :param reference: The service reference
        """
        # Pop the widget from cache
        widget = self._details_widgets.pop(reference)

        # Look for it in the tab widget
        index = self._widget.indexOf(widget)

        if index > -1:
            # Found it
            self._widget.removeTab(index)


    @BindField('_details')
    def _bind_details(self, field, service, reference):
        """
        A details component has been bound
        """
        # Store the service reference
        self._details_refs[service] = reference

        # Use "is not None", Qt Widgets seem to be False
        if self._widget is not None:
            self._qt_loader.run_on_ui(self.__add_tab, service, reference)


    @UnbindField('_details')
    def _unbind_details(self, field, service, reference):
        """
        A details component has been unbound
        """
        try:
            if self._widget is not None:
                self._qt_loader.run_on_ui(self.__remove_tab, service,
                                          reference)
        finally:
            # Clear the service reference
            del self._details_refs[service]
