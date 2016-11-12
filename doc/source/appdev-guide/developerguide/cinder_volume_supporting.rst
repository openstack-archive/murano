.. _cinder_volume_supporting:

Cinder volume support
~~~~~~~~~~~~~~~~~~~~~

Cinder volume is a block storage service for OpenStack, which represents a
detachable device, similar to a USB hard drive. You can attach a volume to
only one instance. In murano, it is possible to work with Cinder volumes
in several ways:

* Attaching Cinder volumes to murano instance
* Booting from Cinder volume

Below both ways are considered with ApacheHttpServer application as an
example.

For more information about Cinder volumes, see
`Manage Cinder volumes
<http://docs.openstack.org/user-guide/common/cli_manage_volumes.html>`_.

Attaching Cinder volumes
------------------------

Several volumes can be attached to the murano instance. Consider an example
that shows how to attach a created volume to the instance (next, in the
*Booting from Cinder volume* section, we are going to boot from a volume
created by us).

**Example**

#. In the OpenStack dashboard, go to :guilabel:`Volumes` to create a volume.

#. Modify the ``ui.yaml`` file:

.. code-block:: yaml

    ....

    Application:
      ....
      instance:
        ....
        volumes:
          $.volumeConfiguration.volumePath:
            ?:
              type: io.murano.resources.ExistingCinderVolume
            openstackId: $.volumeConfiguration.volumeID

     ....

An existing Cinder volume can be initialized with its ``openstackId`` and can
be attached with its ``volumePath``. These parameters come here from
modified ``Forms`` section of the ``ui.yaml`` file:

.. code-block:: yaml

    ....

    Forms:
      - appConfiguration:
          ....
      - instanceConfiguration:
          ....
      - volumeConfiguration:
          fields:
            - name: volumeID
              type: string
              label: Existing volume ID
              description: Put in existing volume openstackID
              required: true
            - name: volumePath
              type: string
              label: Path
              description: Put in volume path to be mounted
              required: true

Therefore, create a ZIP archive of the built package and upload it to murano.
Attach created application to the environment. Enter its openstackId (which
can be found in OpenStack dashboard) and path for mounting. For example, you
can fill the latter with ``/dev/vdb`` value.

After the application is deployed, verify that the volume is attached to the
instance in the OpenStack dashboard :guilabel:`Volumes` tab. Alternatively,
see the topology of the ``Heat Stack``.


Booting from Cinder volume
--------------------------

You can create a volume from an existing image. The example below shows how to
create a volume from an image and use the volume to boot an instance.

**Example**

It is possible to create a volume through the Heat template, instead of
the OpenStack dashboard. For this, modify the ``ui.yaml`` file:

.. code-block:: yaml

    ....

    Templates:
      customJoinNet:
        ....
      bootVolumes:
        - volume:
            ?:
              type: io.murano.resources.CinderVolume
            size: $.instanceConfiguration.volSize
            sourceImage: $.instanceConfiguration.osImage
          bootIndex: 0
          deviceName: vda
          deviceType: disk
    ....

    Application:
      ....
      instance:
        ....
        blockDevices: $bootVolumes

    ....

The example above shows that the ``Templates`` section now has a
``bootVolumes`` field, which is stored in the changed ``Application``
section.
Pay attention that ``image`` property should be deleted from
``Application`` to avoid defining both image and volume to boot.
The ``size`` and ``sourceImage`` properties come in ``Templates`` from the
changed ``Forms`` section of the ``ui.yaml`` file:

.. code-block:: yaml

    ....

    Forms:
      - appConfiguration:
          ....

      - instanceConfiguration:
          fields:
            ....
            - name: volSize
              type: integer
              label: Size of volume
              required: true
              description: >-
                Specify volume size which is going to be created from image
            ....

After sending this package to murano you can boot your instance from the
volume by chosen image.
