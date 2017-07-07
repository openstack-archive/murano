.. _login-murano-instance:

=================================
Log in to murano-spawned instance
=================================

After the application is successfully deployed, you may need to log in to the
virtual machine with the installed application.

All cloud images, including images imported from the
`OpenStack Application Catalog <http://apps.openstack.org/>`_,
have password authentication turned off. Therefore, it is not possible
to log in from the dashboard console. SSH is used to reach an instance spawned
by murano.

Possible default image users are:


* *ec2-user*
* *ubuntu* or *debian* (depending on the operating system)

To log in to murano-spawned instance, perform the following steps:

#. Prepare a key pair.

   To log in through SSH, provide a key pair during the application creation.
   If you do not have a key pair, click the plus sign to create one directly
   from the :guilabel:`Configure Application` dialog.

   .. image:: ../figures/add_key_pair.png
      :alt: Application creation: key pair
      :width: 630 px

#. After the deployment is completed, find out the instance IP address. For
   this, see:

   * Deployment logs

   .. image:: ../figures/app_logs.png
    :alt: Application logs: IP is provided
    :width: 630 px

   * Detailed instance parameters

     See the :guilabel:`Instance name` link on the
     :guilabel:`Component Details` page.

   .. image:: ../figures/app_details.png
    :alt: Application details: instance details link
    :width: 630 px

#. To connect to the instance through SSH with the key pair, run:

   .. code-block:: console

      $ ssh <username>@<IP> -i <key.location>
