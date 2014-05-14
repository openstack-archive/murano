..
      Copyright 2014 Mirantis, Inc.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

========================
Upload Image Into Glance
========================

To deploy applications with Murano, virtual machine images should be uploaded into Glance in a special way - *murano_image_info* property should be set

1. Use the glance image-create command to import your disk image to
   Glance:

   ::

       >$ glance image-create --name <NAME>  --is-public true --disk-format qcow2 --container-format bare --file <IMAGE_FILE> --property <IMAGE_METADATA>

Replace the command line arguments to glance image-create with the
appropriate values for your environment and disk image:

*  Replace **<NAME>** with the name that users will refer to the disk
   image by. E.g. '**ws-2012-std**\ '

*  Replace **<IMAGE\_FILE>** with the local path to the image file to
   upload. E.g. '**ws-2012-std.qcow2**\ '.

*  Replace **<IMAGE\_METADATA>** with the following property string

   ::

       murano_image_info='{"title": "Windows 2012 Standart Edition", "type": "windows.2012"}'

   where

   *  title - user-friendly description of the image
   *  type - is a image type, for example 'windows.2012'

2. To update metadata of the existing image run the command:

    ::

    >$ glance image-update <IMAGE-ID> --property <IMAGE_MATADATA>

*  Replace **<IMAGE-ID>** with image id from the previous command
   output.

*  Replace **<IMAGE\_METADATA>** with murano\_image\_info property, e.g.

   ::

       murano_image_info='{"title": "Windows 2012 Standart Edition", "type": "windows.2012"}'

**Warning**

    The value of the **--property** argument named
    **murano\_image\_info** is a JSON string. Only double quotes are
    valid in JSON, so please type the string exactly as in the example
    above.

**Note**

Already existing image could be marked in a simple way in Horizon UI with Murano dashboard installed. Navigate to *Murano -> Manage -> Images -> Mark Image* and fill up a form:

-  **Image** - ws-2012-std

-  **Title** - My Prepared Image

-  **Type** - Windows Server 2012

After these steps desired image can be chosen in application creation wizard.
