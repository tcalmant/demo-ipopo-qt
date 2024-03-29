#!/usr/bin/python
# -- Content-Encoding: UTF-8 --
"""
Services details component

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

# PyQt5
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

# iPOPO
from pelix.ipopo.decorators import ComponentFactory, Requires, Provides, \
    Property, Instantiate, Invalidate, Validate
import pelix.ipopo.constants as constants
import pelix.constants
import pelix.framework
import pelix.remote
import pelix.services

# Standard library
import logging

# ------------------------------------------------------------------------------

SERVICES_DETAILS_FACTORY = "services-details-factory"

_logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------

@ComponentFactory("services-details-creator-factory")
@Provides(core.SVC_DETAILS_CREATOR_FACTORY)
@Requires('_ipopo', constants.IPOPO_SERVICE_SPECIFICATION)
@Instantiate("services-details-creator")
class ServicesDetailsCreator(object):
    """
    Services details creator
    """
    def __init__(self):
        """
        Sets up the component
        """
        # iPOPO service
        self._ipopo = None

        # Instances
        self._instances = {}

        # Local framework UID
        self._local_uid = None


    def __make_name(self, uid):
        """
        Sets up a component name using the given UID

        :param uid: A framework information component UID
        :return: A component name
        """
        return "services-details-{0}".format(uid)


    def make(self, uid):
        """
        Sets up a services details component

        :param uid: A framework information component UID
        """
        if not uid:
            uid = None

        try:
            # Already created component
            return self._instances[uid]

        except KeyError:
            # Prepare the @Requires filter override, to select the associated
            # probe
            properties = {}
            properties[core.PROP_PROBE_UID] = uid

            if uid:
                probe_filter = "({0}={1})" \
                               .format(pelix.remote.PROP_ENDPOINT_FRAMEWORK_UUID, uid)

            else:
                probe_filter = "(!({0}=*))" \
                               .format(pelix.remote.PROP_ENDPOINT_FRAMEWORK_UUID)

            properties[constants.IPOPO_REQUIRES_FILTERS] = {'_probe':
                                                            probe_filter}

            # Prepare the EventAdmin handler filter
            properties[pelix.services.PROP_EVENT_FILTER] = \
                    "({0}={1})".format(pelix.services.EVENT_PROP_FRAMEWORK_UID,
                                       self._local_uid if uid is None else uid)

            # Make the component
            component = self._ipopo.instantiate(SERVICES_DETAILS_FACTORY,
                                                self.__make_name(uid),
                                                properties)
            self._instances[uid] = component
            return component


    def delete(self, uid):
        """
        Deletes a services details component

        :param uid: A framework information component UID
        """
        if not uid:
            uid = None

        if uid in self._instances:
            # Delete it
            del self._instances[uid]
            try:
                self._ipopo.kill(self.__make_name(uid))

            except ValueError:
                # The instance was already gone
                pass


    @Validate
    def validate(self, context):
        """
        Component validated

        :param context: Bundle context
        """
        self._local_uid = context.get_property(pelix.framework.FRAMEWORK_UID)


    @Invalidate
    def invalidate(self, context):
        """
        Component invalidated

        :param context: Bundle context
        """
        # Clear all known instances
        for framework_id in self._instances.keys():
            self.delete(framework_id)

        self._instances.clear()
        self._local_uid = None

# ------------------------------------------------------------------------------

@ComponentFactory(SERVICES_DETAILS_FACTORY)
@Requires('_probe', core.SVC_PROBE)
@Requires('_qt_loader', core.SVC_QT_LOADER)
@Provides((core.SVC_DETAILS, pelix.services.SERVICE_EVENT_HANDLER))
@Property('_event_handler_topic', pelix.services.PROP_EVENT_TOPICS,
          ["pelix/framework/ServiceEvent/*"])
@Property('_event_handler_filter', pelix.services.PROP_EVENT_FILTER)
@Property('_export_interface', pelix.remote.PROP_EXPORTED_INTERFACES,
          [pelix.services.SERVICE_EVENT_HANDLER])
@Property('_uid', core.PROP_PROBE_UID)
class ServicesDetails(object):
    """
    Services details
    """
    def __init__(self):
        """
        Sets up the component
        """
        # The associated probe
        self._probe = None

        # The Qt loader
        self._qt_loader = None

        # Associate framework information component UID
        self._uid = None

        # Event handler: topic & filter
        self._event_handler_topic = None
        self._event_handler_filter = None

        # Export property
        self._export_interface = None

        # Table widget
        self._table = None


    def get_uid(self):
        """
        Returns the UID of the associated information component

        :return: A UID
        """
        return self._uid


    def get_name(self):
        """
        Returns the name to show in the UI
        """
        return "Services"


    def handle_event(self, topic, properties):
        """
        Notification of an event by EventAdmin
        """
        if self._qt_loader is None:
            # Late call
            return

        # Get information from the event
        service_id = properties.get('service.id')
        svc_props = properties.get('service.properties')

        # Extract the ID and specifications
        _, specs = self.__extract_properties(svc_props)

        try:
            if topic.endswith('/UNREGISTERING'):
                self._qt_loader.run_on_ui(self.__remove_line, service_id)

            else:
                self._qt_loader.run_on_ui(self.__update_line,
                                          service_id, specs, svc_props)

        except ValueError:
            # Qt is gone
            pass


    def __extract_properties(self, properties):
        """
        Extracts (and removes) the service ID and specifications from the given
        properties.
        Modifies the given dictionary in-place

        :param properties: A dictionary
        :return: A (service ID, specifications) tuple
        """
        keys = (pelix.constants.SERVICE_ID, pelix.constants.OBJECTCLASS)
        result = []

        # Extract values
        for key in keys:
            result.append(properties.pop(key))

        # Freeze the result
        return tuple(result)


    def __set_line_content(self, line, ident, *values):
        """
        Sets the content of a line
        """
        # Add the identifier
        self._table.setItem(line, 0, QtWidgets.QTableWidgetItem(str(ident)))

        # Fill it
        for i, value in enumerate(values):
            if value is not None:
                item = QtWidgets.QTableWidgetItem(str(value))
                self._table.setItem(line, i + 1, item)

        # Update the columns size
        self._table.resizeColumnsToContents()


    def __find_row(self, ident):
        """
        Gets the index of row with the given identifier

        :param ident: A line identifier
        :return: The row number or -1
        """
        ident = str(ident)
        for item in self._table.findItems(ident, QtCore.Qt.MatchFixedString):
            if item.column() == 0:
                # ID match, return the row number
                return item.row()
        else:
            return -1


    def __update_line(self, ident, *values):
        """
        Updates the line with the given value.
        The first value is the identifier of the line.
        If the identifier is not found, a new line is created

        :param ident: A line identifier
        :param values: A set of values to update
        """
        # Find the row with the same first value
        row = self.__find_row(ident)
        if row > -1:
            # Found it, update its content
            self.__set_line_content(row, ident, *values)

        else:
            # Not found, append the line
            self.__append_line(ident, *values)


    def __append_line(self, ident, *values):
        """
        Appends a line to the table.
        The first value is the identifier of the line.

        :param ident: A line identifier
        :param values: A set of values to add
        """
        # Add the new row
        line = self._table.rowCount()
        self._table.insertRow(line)

        # Set its content
        self.__set_line_content(line, ident, *values)

        # Sort the lines
        self._table.sortItems(0)


    def __remove_line(self, ident):
        """
        Removes the line associated to the given identifier

        :param ident: A line identifier
        """
        row = self.__find_row(ident)
        if row > -1:
            self._table.removeRow(row)


    def get_widget(self, parent):
        """
        Returns the widget to be shown in the framework information panel

        :param parent: The parent UI container
        :return: A Qt widget
        """
        # Headers
        headers = ('ID', 'Specifications', 'Properties')

        # Make the table
        self._table = QtWidgets.QTableWidget(0, len(headers), parent)
        self._table.setHorizontalHeaderLabels(headers)
        self._table.verticalHeader().hide()

        # Fill it
        for properties in self._probe.get_services_info():
            # Extract the ID and specifications
            sid, specs = self.__extract_properties(properties)

            # Append the line
            self.__append_line(sid, specs, properties)

        return self._table
