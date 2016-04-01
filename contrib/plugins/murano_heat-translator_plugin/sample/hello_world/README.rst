=================================================================
Build Murano Application Definition Archive from hello_world CSAR
=================================================================
In order to build a Murano application definition archive from the hello_world
CSAR and the corresponding logo and manifest files, from inside the hello_world
folder run following commands:

1. Download archive from https://github.com/openstack/heat-translator/raw/0.4.0/translator/tests/data/csar_hello_world.zip
2. Rename it to 'csar.zip'
3. *zip csar_helloworld_murano_package.zip csar.zip logo.png manifest.yaml*

The resulting file *csar_helloworld_murano_package.zip* is the application
definition archive that can be imported into the Murano application catalog.
