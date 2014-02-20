The contrib/devstack/ directory contains the files necessary to integrate Murano with Devstack.

To install:

    $ DEVSTACK_DIR=.../path/to/devstack
    $ cp lib/murano ${DEVSTACK_DIR}/lib
    $ cp extras.d/70-murano.sh ${DEVSTACK_DIR}/extras.d

To configure Devstack to run Murano:

    $ cd ${DEVSTACK_DIR}
    $ echo "enable_service murano" >> localrc
    $ echo "enable_service murano-api" >> localrc

Run devstack as normal:

    $ ./stack.sh
