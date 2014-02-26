#!/usr/bin/python
# -- Content-Encoding: UTF-8 --
"""
UI Application core modules

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

SVC_PROBE = "pelix.probe"
""" Probe service """

PROP_PROBE_UID = "core.probe.uid"
""" UID of the dispatcher that exports the probe """

# ------------------------------------------------------------------------------

SVC_QT_LOADER = "core.qt.loader"
""" Specification of the Qt loader service """

QT_MAIN_FRAME = "core.qt.frame.main"
""" Specification of the main frame """

SVC_FRAMEWORK_INSTANCE_INFO_FACTORY = "core.framework.instance.info.factory"
""" Factory for the framework instance information components """

SVC_FRAMEWORK_INSTANCE_INFO = "core.framework.instance.info"
""" Framework instance information service """

SVC_DETAILS_CREATOR_FACTORY = "core.framework.details.factory"
""" Framework details component creator """

SVC_DETAILS = "core.framework.details"
""" Framework details component """

PROP_DISPATCHER_UID = "pelix.remote.dispatcher.uid"
""" The remote dispatcher UID property """

# ------------------------------------------------------------------------------
