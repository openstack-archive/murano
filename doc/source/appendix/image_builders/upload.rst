.. _upload_images:

========================
Upload image into glance
========================

To deploy applications with murano, virtual machine images should be uploaded into glance in a special way - *murano_image_info* property should be set.

1. Use the OpenStack client image create command to import your disk image to glance:

.. code-block:: console

  openstack image create --public \
  > --disk-format qcow2 --container-format bare \
  > --file <IMAGE_FILE> --property <IMAGE_METADATA> <NAME>
..

Replace the command line arguments to openstack image create with the appropriate values for your environment and disk image:

*  Replace **<IMAGE_FILE>** with the local path to the image file to upload. E.g. **ws-2012-std.qcow2**.

*  Replace **<IMAGE_METADATA>** with the following property string

*  Replace **<NAME>** with the name that users will refer to the disk image by. E.g. **ws-2012-std**

.. code-block:: text

  murano_image_info='{"title": "Windows 2012 Standard Edition", "type": "windows.2012"}'
..

where:

* **title** - user-friendly description of the image
* **type** - murano image type, see :ref:`murano_image_types`

2. To update metadata of the existing image run the command:

.. code-block:: console

  openstack image set --property <IMAGE_MATADATA> <IMAGE_ID> 
..

*  Replace **<IMAGE_METADATA>** with murano_image_info property, e.g.

*  Replace **<IMAGE_ID>** with image id from the previous command output.

.. code-block:: text

  murano_image_info='{"title": "Windows 2012 Standard Edition", "type": "windows.2012"}'
..

.. warning::

  The value of the **--property** argument (named **murano_image_info**) is a JSON string.
  Only double quotes are valid in JSON, so please type the string exactly as in the example above.
..

.. note::

  Existing images could be marked in a simple way in the horizon UI with the murano dashboard installed.
  Navigate to *Applications -> Manage -> Images -> Mark Image* and fill up a form:

  *  **Image** - ws-2012-std
  *  **Title** - My Prepared Image
  *  **Type** - Windows Server 2012
..

After these steps desired image can be chosen in application creation wizard.


.. _murano_image_types:

Murano image types
------------------

.. list-table::
  :header-rows: 1

  * - Type Name
    - Description

  * - windows.2012
    - Windows Server 2012

  * - linux
    - Generic Linux images, Ubuntu / Debian, RedHat / Centos, etc

  * - cirros.demo
    - Murano demo image, based on CirrOS
..
