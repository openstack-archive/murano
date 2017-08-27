.. _install-client:

Install and use the murano client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Application Catalog project provides a command-line client,
python-muranoclient, which enables you to access the project API.
For prerequisites, see `Install the prerequisite software <http://docs.openstack.org/cli-reference/common/cli_install_openstack_command_line_clients.html#install-the-prerequisite-software>`_.

To install the latest murano CLI client, run the following command in your
terminal:

.. code-block:: console

   $ pip install python-muranoclient

Discover the client version number
----------------------------------

To discover the version number for the python-muranoclient, run the following
command:

.. code-block:: console

   $ murano --version

To check the latest version, see `Client library for Murano API <https://git.openstack.org/cgit/openstack/python-muranoclient>`_.


Upgrade or remove the client
----------------------------

To upgrade or remove the python-muranoclient, use the corresponding commands.

**To upgrade the client:**

.. code-block:: console

   $ pip install --upgrade python-muranoclient

**To remove the client:**

.. code-block:: console

   $ pip uninstall python-muranoclient

Set environment variables
-------------------------

To use the murano client, you must set the environment variables. To do this,
download and source the OpenStack RC file. For more information, see
`Download and source the OpenStack RC file <http://docs.openstack.org/user-guide/common/cli_set_environment_variables_using_openstack_rc.html#download-and-source-the-openstack-rc-file>`_.

Alternatively, create the ``PROJECT-openrc.sh`` file from scratch. For this,
perform the following steps:

#. In a text editor, create a file named ``PROJECT-openrc.sh`` containing the
   following authentication information:

   .. code-block:: console

      export OS_USERNAME=user
      export OS_PASSWORD=password
      export OS_TENANT_NAME=tenant
      export OS_AUTH_URL=http://auth.example.com:5000
      export MURANO_URL=http://murano.example.com:8082/

#. In the terminal, source the ``PROJECT-openrc.sh`` file. For example:

   .. code-block:: console

      $ . admin-openrc.sh

Once you have configured your authentication parameters, run
:command:`murano help` to see a complete list of available commands and
arguments. Use :command:`murano help <sub_command>` to get help on a specific
subcommand.

.. seealso::

   `Set environment variables using the OpenStack RC file <http://docs.openstack.org/user-guide/common/cli_set_environment_variables_using_openstack_rc.html>`_.

Bash completion
---------------

To get the latest bash completion script, download
`murano.bash_completion <https://git.openstack.org/cgit/openstack/python-muranoclient/plain/tools/murano.bash_completion>`_
from the source repository and add it to your completion scripts.

If you are not aware of the completion scripts location, perform the following
steps:

#. Create a new directory:

   .. code-block:: console

      $ mkdir -p ~/.bash_completion/

#. Create a file containing the bash completion script:

   .. code-block:: console

      $ curl https://git.openstack.org/cgit/openstack/python-muranoclient/plain/tools/murano.bash_completion > ~/.bash_completion/murano.sh

#. Add the following code to the ``~/.profile`` file:

   .. code-block:: bash

      for file in $HOME/.bash_completion/*.sh; do
          if [ -f "$file" ]; then
              . "$file"
          fi
      done

#. In the current terminal, run:

   .. code-block:: console

      $ . ~/.bash_completion/murano.sh
