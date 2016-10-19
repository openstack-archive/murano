.. _cli-ref:

==========================
Murano command-line client
==========================

The ``murano`` client is the command-line
interface (CLI) for the Application catalog API and its extensions.

For help on a specific ``murano`` command, enter:

.. code-block:: console

    murano help COMMAND

    murano usage
    usage: murano \[--version] \[-d] \[-v] \[-k] \[--os-cacert <ca-certificate>]
    \[--cert-file CERT_FILE] \[--key-file KEY_FILE]
    \[--ca-file CA_FILE] \[--api-timeout API_TIMEOUT]
    \[--os-username OS_USERNAME] \[--os-password OS_PASSWORD]
    \[--os-tenant-id OS_TENANT_ID] \[--os-tenant-name OS_TENANT_NAME]
    \[--os-auth-url OS_AUTH_URL] \[--os-region-name OS_REGION_NAME]
    \[--os-auth-token OS_AUTH_TOKEN] \[--os-no-client-auth]
    \[--murano-url MURANO_URL] \[--glance-url GLANCE_URL]
    \[--murano-api-version MURANO_API_VERSION]
    \[--os-service-type OS_SERVICE_TYPE]
    \[--os-endpoint-type OS_ENDPOINT_TYPE] \[--include-password]
    \[--murano-repo-url MURANO_REPO_URL]
    <subcommand> ...

Subcommands
===========

* *bundle-import* Import a bundle.

* *category-create* Create a category.

* *category-delete* Delete a category.

* *category-list* List all available categories.

* *category-show*

* *deployment-list* List deployments for an environment.

* *env-template-add-app* Add application to the environment template.

* *env-template-create* Create an environment template.

* *env-template-del-app* Delete application to the environment template.

* *env-template-delete* Delete an environment template.

* *env-template-list* List the environments templates.

* *env-template-show* Display environment template details.

* *env-template-update* Update an environment template.

* *environment-create* Create an environment.

* *environment-delete* Delete an environment.

* *environment-list* List the environments.

* *environment-rename* Rename an environment.

* *environment-show* Display environment details.

* *package-create* Create an application package.

* *package-delete* Delete a package.

* *package-download* Download a package to a filename or stdout.

* *package-import* Import a package.

* *package-list* List available packages.

* *package-show* Display details for a package.

* *service-show*

* *bash-completion* Prints all of the commands and options to stdout.

* *help* Display help about this program or one of its subcommands.

Murano optional arguments
=========================

**--version**
     show program's version number and exit

**-d, --debug**
     Defaults to env[MURANOCLIENT_DEBUG]

**-v, --verbose**
    Print more verbose output

**-k, --insecure**
    Explicitly allow muranoclient to perform "insecure" SSL (https) requests.
    The server's certificate will not be verified against any certificate
    authorities. This option should be used with caution.

**--os-cacert <ca-certificate>**
    Specify a CA bundle file to use in verifying a TLS (https) server
    certificate. Defaults to env[OS_CACERT]

**--cert-file CERT_FILE**
    Path of certificate file to use in SSL connection. This file can optionally
    be prepended with the private key.

**--key-file KEY_FILE**
    Path of client key to use in SSL connection. This option is not necessary
    if your key is prepended to your cert file.

**--ca-file CA_FILE**
    Path of CA SSL certificate(s) used to verify the remote server certificate.
    Without this option glance looks for the default system CA certificates.

**--api-timeout API_TIMEOUT**
    Number of seconds to wait for an API response, defaults to system socket
    timeout

**--os-username OS_USERNAME**
    Defaults to env[OS_USERNAME]

**--os-password OS_PASSWORD**
    Defaults to env[OS_PASSWORD]

**--os-project-id OS_PROJECT_ID**
    Defaults to env[OS_PROJECT_ID]

**--os-project-name OS_PROJECT_NAME**
    Defaults to env[OS_PROJECT_NAME]

**--os-auth-url OS_AUTH_URL**
    Defaults to env[OS_AUTH_URL]

**--os-region-name OS_REGION_NAME**
    Defaults to env[OS_REGION_NAME]

**--os-auth-token OS_AUTH_TOKEN**
    Defaults to env[OS_AUTH_TOKEN]

**--os-no-client-auth**
    Do not contact keystone for a token. Defaults to env[OS_NO_CLIENT_AUTH].

**--murano-url MURANO_URL**
    Defaults to env[MURANO_URL]**

**--glance-url GLANCE_URL**
    Defaults to env[GLANCE_URL]

**--murano-api-version MURANO_API_VERSION**
    Defaults to env[MURANO_API_VERSION] or 1

**--os-service-type OS_SERVICE_TYPE**
    Defaults to env[OS_SERVICE_TYPE]

**--os-endpoint-type OS_ENDPOINT_TYPE**
    Defaults to env[OS_ENDPOINT_TYPE]

**--include-password**
    Send os-username and os-password to murano.

**--murano-repo-url MURANO_REPO_URL**
    Defaults to env[MURANO_REPO_URL] or
    `http://storage.apps.openstack.org_`

Application catalog API v1 commands
===================================

murano bundle-import
~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano bundle-import \[--is-public] \[--exists-action {a,s,u}]
 <FILE> \[<FILE> ...]

Import a bundle. ``FILE`` can be either a path to a zip file, URL or name from
repo. if ``FILE`` is a local file does not attempt to parse requirements and
treat Names of packages in a bundle as file names, relative to location of
bundle file.

Positional arguments
--------------------

**<FILE>**
    Bundle URL, bundle name, or path to the bundle file

Optional arguments
------------------

**--is-public**
    Make packages available to users from other project

**--exists-action {a,s,u}**
    Default action when a package already exists

murano category-create
~~~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano category-create <CATEGORY_NAME>

Create a category.

Positional arguments
--------------------

**<CATEGORY_NAME>**
    Category name

murano category-delete
~~~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano category-delete <ID> \[<ID> ...]

Delete a category.

Positional arguments
--------------------

**<ID>**
    ID of a category(s) to delete

murano category-list
~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano category-list

List all available categories.

murano category-show
~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano category-show <ID>

Positional arguments
--------------------

**<ID>**
    ID of a category(s) to show

murano deployment-list
~~~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano deployment-list <ID>

List deployments for an environment.

Positional arguments
--------------------

**<ID>**
    Environment ID for which to list deployments

murano env-template-add-app
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano env-template-add-app <ENV_TEMPLATE_NAME> <FILE>

Add application to the environment template.

Positional arguments
--------------------

**<ENV_TEMPLATE_NAME>**
    Environment template name

**<FILE>**
    Path to the template.

murano env-template-create
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano env-template-create <ENV_TEMPLATE_NAME>

Create an environment template.

Positional arguments
--------------------

**<ENV_TEMPLATE_NAME>**
    Environment template name

murano env-template-del-app
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano env-template-del-app <ENV_TEMPLATE_ID> <ENV_TEMPLATE_APP_ID>

Delete application to the environment template.

Positional arguments
--------------------

**<ENV_TEMPLATE_ID>**
    Environment template ID

**<ENV_TEMPLATE_APP_ID>**
    Application ID

murano env-template-delete
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano env-template-delete <ID> \[<ID> ...]

Delete an environment template.

Positional arguments
--------------------

**<ID>**
   ID of environment(s) template to delete

murano env-template-list
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano env-template-list

List the environments templates.

murano env-template-show
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano env-template-show <ID>

Display environment template details.

Positional arguments
--------------------

**<ID>**
    Environment template ID

murano env-template-update
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano env-template-update <ID> <ENV_TEMPLATE_NAME>

Update an environment template.

Positional arguments
--------------------

**<ID>**
    Environment template ID

**<ENV_TEMPLATE_NAME>**
    Environment template name

murano environment-create
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano environment-create <ENVIRONMENT_NAME>

Create an environment.

Positional arguments
--------------------

**<ENVIRONMENT_NAME>**
    Environment name

murano environment-delete
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano environment-delete <NAME or ID> \[<NAME or ID> ...]

Delete an environment.

Positional arguments
--------------------

**<NAME or ID>**
    ID or name of environment(s) to delete

Optional arguments
------------------

**--abandon**
    If set will abandon environment without deleting any of its resources

murano environment-list
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano environment-list

List the environments.

murano environment-rename
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano environment-rename <NAME or ID> <ENVIRONMENT_NAME>

Rename an environment.

Positional arguments
--------------------

**<NAME or ID>**
    Environment ID or name

**<ENVIRONMENT_NAME>**
    A name to which the environment will be renamed

murano environment-show
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano environment-show <NAME or ID>

Display environment details.

Positional arguments
--------------------

**<NAME or ID>**
    Environment ID or name

murano package-create
~~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano package-create \[-t <HEAT_TEMPLATE>] \[-c <CLASSES_DIRECTORY>]
 \[-r <RESOURCES_DIRECTORY>] \[-n <DISPLAY_NAME>]
 \[-f <full-name>] \[-a <AUTHOR>]
 \[--tags \[<TAG1 TAG2> \[<TAG1 TAG2> ...]]]
 \[-d <DESCRIPTION>] \[-o <PACKAGE_NAME>]
 \[-u <UI_DEFINITION>] \[--type TYPE] \[-l <LOGO>]

Create an application package.

Optional arguments
------------------

**-t <HEAT_TEMPLATE>, --template <HEAT_TEMPLATE>**
    Path to the Heat template to import as an Application Definition

**-c <CLASSES_DIRECTORY>, --classes-dir <CLASSES_DIRECTORY>**
    Path to the directory containing application classes

**-r <RESOURCES_DIRECTORY>, --resources-dir <RESOURCES_DIRECTORY>**
    Path to the directory containing application resources

**-n <DISPLAY_NAME>, --name <DISPLAY_NAME>**
    Display name of the Application in Catalog

**-f <full-name>, --full-name <full-name>**
    Fully-qualified name of the Application in Catalog

**-a <AUTHOR>, --author <AUTHOR>**
    Name of the publisher

**--tags \[<TAG1 TAG2> \[<TAG1 TAG2> ...]]**
    A list of keywords connected to the application

**-d <DESCRIPTION>, --description <DESCRIPTION>**
    Detailed description for the Application in Catalog

**-o <PACKAGE_NAME>, --output <PACKAGE_NAME>**
    The name of the output file archive to save locally

**-u <UI_DEFINITION>, --ui <UI_DEFINITION>**
    Dynamic UI form definition

**--type TYPE**
    Package type. Possible values: Application or Library

**-l <LOGO>, --logo <LOGO>**
    Path to the package logo

murano package-delete
~~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano package-delete <ID> \[<ID> ...]

Delete a package.

Positional arguments
--------------------

**<ID>**
    Package ID to delete

murano package-download
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano package-download <ID> \[file]

Download a package to a filename or stdout.

Positional arguments
--------------------

**<ID>**
    Package ID to download

**file**
    Filename for download (defaults to stdout)

murano package-import
~~~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano package-import \[-c \[<CAT1 CAT2 CAT3> \[<CAT1 CAT2 CAT3> ...]]]
 \[--is-public] \[--package-version VERSION]
 \[--exists-action {a,s,u}]
 <FILE> \[<FILE> ...]

Import a package. ``FILE`` can be either a path to a zip file, URL or a FQPN.
``categories`` can be separated by a comma.

Positional arguments
--------------------

**<FILE>**
    URL of the murano zip package, FQPN, or path to zip package

Optional arguments
------------------

**-c \[<CAT1 CAT2 CAT3> \[<CAT1 CAT2 CAT3> ...]], --categories \[<CAT1 CAT2 CAT3> \[<CAT1 CAT2 CAT3> ...]]**
    Category list to attach

**--is-public**
    Make the package available for user from other project

**--package-version VERSION**
    Version of the package to use from repository (ignored when importing with
    multiple packages)

**--exists-action {a,s,u}**
    Default action when package already exists

murano package-list
~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano package-list \[--include-disabled]

List available packages.

Optional arguments
------------------

**--include-disabled**

murano package-show
~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano package-show <ID>

Display details for a package.

Positional arguments
--------------------

**<ID>**
    Package ID to show

murano service-show
~~~~~~~~~~~~~~~~~~~

.. code-block::console

 usage: murano service-show \[-p <PATH>] <ID>

Positional arguments
--------------------

**<ID>**
    Environment ID to show applications from

Optional arguments
------------------

**-p <PATH>, --path <PATH>**

Level of detalization to show. Leave empty to browse
all services in the environment
