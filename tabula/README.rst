====================================
Horizon Customization Demo Dashboard
====================================

This Django project demonstrates how the `Horizon`_ app can be used to
construct customized dashboards (for OpenStack or anything else).

The ``horizon`` module is pulled down from GitHub during setup
(see setup instructions below) and added to the virtual environment.

.. _Horizon: http://github.com/openstack/horizon

Setup Instructions
==================

The following should get you started::

    $ git clone https://github.com/gabrielhurley/horizon_demo.git
    $ cd horizon_demo
    $ python tools/install_venv.py
    $ cp demo_dashboard/local/local_settings.py.example demo_dashboard/local/local_settings.py

Edit the ``local_settings.py`` file as needed.

When you're ready to run the development server::

    $ ./run_tests.sh --runserver

Using Fake Test Data
====================

If you want a more interesting visualization demo, you can uncomment line
24 of ``dashboards/visualizations/flocking/views.py`` to load fake instance
data instead of using data from a real Nova endpoint.