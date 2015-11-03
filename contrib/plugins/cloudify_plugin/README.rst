This is a Murano Plugin for Cloudify.

You need to install this plugin in your Murano environment using pip (pip install -e .).

You also need to upload the Cloudify Application (cloudify_application folder) to your Murano Packages:

cd cloudify_application
zip -r cloudify_application.zip .

Then you will be able to deploy TOSCA applications using Cloudify.

To test this plugin you will need the cloudify-nodecellar-application.

Read "nodecellar_example_application/README.rst".

Download the Nodecellar Example to the nodecellar_example_application/Resources folder.

You will also need a manager. Follow these instructions to create a manager (http://getcloudify.org/guide/3.2/quickstart.html).

Then take Cloudify Manager IP and update your murano.conf file in ./murano/etc:

[cloudify]
cloudify_manager = 10.10.1.10 # Change this.

Restart the Murano Engine and API.

