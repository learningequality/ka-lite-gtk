===============================
KA Lite Control Panel (GTK3)
===============================

.. image:: https://api.travis-ci.org/benjaoming/ka-lite-gtk.svg
        :target: https://travis-ci.org/learningequality/ka-lite-gtk

.. image:: https://badge.fury.io/py/ka-lite-gtk.svg
        :target: https://pypi.python.org/pypi/ka-lite-gtk

.. image:: https://readthedocs.org/projects/ka-lite-gtk/badge/?version=latest
        :target: https://readthedocs.org/projects/ka-lite-gtk/?badge=latest
        :alt: Documentation Status


User interface for KA Lite server control (GTK3)

* Free software: MIT license
* Documentation: https://ka-lite-gtk.readthedocs.org.


Features
--------

* Control the KA Lite server from a simple Control Panel
* Supports a multi-user environment, i.e. User A controls User Bs server, provided User A has local sudo access.
* Add and remove system services for automatically starting up KA Lite.
* Notification area icon (TODO)


Development
-----------

Run directly from source::

    python kalite_gtk --debug

Installing in editable mode and running directly::

    pip install -e .
    ka-lite-gtk --debug
