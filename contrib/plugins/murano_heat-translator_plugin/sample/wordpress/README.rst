===============================================================
Build Murano Application Definition Archive from wordpress CSAR
===============================================================
In order to build a Murano application definition archive from the wordpress
CSAR and the corresponding logo and manifest files, from inside the wordpress
folder run this command:

1. Download archive from https://github.com/openstack/heat-translator/raw/0.4.0/translator/tests/data/csar_single_instance_wordpress.zip
2. Rename it to 'csar.zip'
3. *zip csar_wordpress_murano_package.zip csar.zip logo.png manifest.yaml*

The resulting file *csar_wordpress_murano_package.zip* is the application
definition archive that can be imported into the Murano application catalog.
