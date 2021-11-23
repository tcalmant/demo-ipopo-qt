iPOPO Qt Demo
#############

A two-parts demonstration of the iPOPO framework, shown during the
`OSGi Users' Group France 2013 <http://france.osgiusers.org/Meeting/201305>`_
in Grenoble.

* PC: a Qt application that summarizes some information about the local and
  remote Pelix frameworks
  A fake compass service is available to show up the compass widget

* Android: a Kivy application embedding iPOPO and jsonrpclib that is visible by
  the PC part (coming soon).
  The framework on the Android device notifies the Qt application of its the
  value of its compass.

More details on
`Mixing Qt and iPOPO <https://ipopo.coderxpress.net/wiki/doku.php?id=ipopo:tutorials:qt>`_.


Requirements
************

This demonstration requires ``iPOPO``, ``jsonrpclib-pelix`` and ``PyQt``
(tested with PyQt5).

On Ubuntu, those are installed using:

.. code-block:: bash

   sudo pip install --upgrade iPOPO
   sudo pip install --upgrade jsonrpclib-pelix
   sudo apt-get install python-qt5
