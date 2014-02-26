#!/usr/bin/python
# -- Content-Encoding: UTF-8 --
"""
Defines the Qt main frame component

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

# PyQt4
import PyQt4.QtGui as QtGui
import PyQt4.uic as uic

# iPOPO
from pelix.ipopo.decorators import ComponentFactory, Requires, Validate, \
    Invalidate, Instantiate, Provides, BindField, UnbindField

# Standard library
import os
import logging

# ------------------------------------------------------------------------------

_logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------

class _QtMainFrame(QtGui.QMainWindow):
    """
    Represents the UI, loaded from a UI file
    """
    def __init__(self, controller, ui_file):
        """
        Sets up the frame
        """
        # Parent constructor
        QtGui.QMainWindow.__init__(self)

        # Store the controller
        self.__controller = controller

        # Load the frame UI
        uic.loadUi(ui_file, self)

        # Connect to signals
        self.action_quit.triggered.connect(controller.quit)
        self.action_about.triggered.connect(self.__about)
        self.action_about_qt.triggered.connect(self.__about_qt)


    def __about(self):
        """
        About signal handler
        """
        QtGui.QMessageBox.about(self, "About...", "Some text here")


    def __about_qt(self):
        """
        About Qt signal handler
        """
        QtGui.QMessageBox.aboutQt(self)

# ------------------------------------------------------------------------------

@ComponentFactory("MainFrameFactory")
@Requires("_qt_loader", core.SVC_QT_LOADER)
@Requires('_frameworks_info', core.SVC_FRAMEWORK_INSTANCE_INFO,
          aggregate=True, optional=True)
@Provides(core.QT_MAIN_FRAME)
@Instantiate("MainFrame")
class MainFrame(object):
    """
    The main frame component
    """
    def __init__(self):
        """
        Sets up the component
        """
        # Bundle context
        self._context = None

        # Valid state flag
        self.__validated = False

        # Main frame
        self._frame = None

        # Qt Loader service
        self._qt_loader = None

        # Frameworks
        self._frameworks_info = None

        # Tabs
        self._frameworks_tabs = {}


    def __make_ui(self):
        """
        Sets up the frame. Must be called from the UI thread
        """
        # Load the UI file
        ui_path = os.path.join(os.getcwd(), "ui", "main.ui")
        self._frame = _QtMainFrame(self, ui_path)

        # Show the frame
        self._frame.show()


    def __clear_ui(self):
        """
        Clears the UI. Must be called from the UI thread
        """
        # Close the window
        self._frame.hide()
        self._frame = None


    def get_frame(self):
        """
        Retrieves the main frame object
        """
        return self._frame


    def quit(self):
        """
        Stops the framework
        """
        self._context.get_bundle(0).stop()


    def __add_info_tab(self, framework_info):
        """
        Adds a tab representing a framework information
        
        To run in the UI thread.
        """
        # Prepare the content
        name = framework_info.get_name()
        uid = framework_info.get_uid()
        widget = framework_info.get_widget(self._frame)

        # Add the tab
        tab_bar = self._frame.frameworks_bar
        tab_bar.addTab(widget, name)

        # Store its widget
        self._frameworks_tabs[uid] = widget


    def __remove_info_tab(self, framework_info):
        """
        Removes a tab representing a framework information
        
        To run in the UI thread.
        """
        # Get framework ID
        uid = framework_info.get_uid()

        # Pop its widget
        widget = self._frameworks_tabs.pop(uid)

        # Remove the tab
        tab_bar = self._frame.frameworks_bar
        index = tab_bar.indexOf(widget)
        if index > -1:
            # Found it
            tab_bar.removeTab(index)

        # Clean the component
        framework_info.clean(self._frame)


    @BindField('_frameworks_info')
    def bind_info(self, field, service, reference):
        """
        Framework info service bound
        """
        if self.__validated:
            self._qt_loader.run_on_ui(self.__add_info_tab, service)


    @UnbindField('_frameworks_info')
    def unbind_info(self, field, service, reference):
        """
        Framework info service gone
        """
        if self.__validated:
            self._qt_loader.run_on_ui(self.__remove_info_tab, service)


    @Validate
    def validate(self, context):
        """
        Component validated
        
        :param context: Bundle context
        """
        self._context = context
        self._qt_loader.run_on_ui(self.__make_ui)

        # Make tabs for already known framework info
        if self._frameworks_info:
            for service in self._frameworks_info:
                self._qt_loader.run_on_ui(self.__add_info_tab, service)

        # Flag to allow un/bind probes to work
        self.__validated = True


    @Invalidate
    def invalidate(self, context):
        """
        Component invalidated
        
        :param context: Bundle context
        """
        # De-activate binding call backs
        self.__validated = False

        # Removes tabs
        if self._frameworks_info:
            for service in self._frameworks_info:
                self._qt_loader.run_on_ui(self.__remove_info_tab, service)

        # Clear the UI
        self._qt_loader.run_on_ui(self.__clear_ui)

        self._context = None
