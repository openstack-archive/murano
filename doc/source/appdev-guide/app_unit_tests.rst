.. _app-unit-tests:

======================
Application unit tests
======================

Murano applications are written in :ref:`MuranoPL <murano-pl>`.
To make the development of applications easier and enable application
testing, a special framework was created. So it is possible to add
unit tests to an application package and check if the application is in
actual state. Also, application deployment can be simulated with unit tests,
so you do not need to run the murano engine.

A separate service that is called *murano-test-runner* is used to run
MuranoPL unit tests.

All application test cases should be:

* Specified in the MuranoPL class, inherited from
  `io.murano.test.testFixture <https://git.openstack.org/cgit/openstack/murano/tree/murano/engine/system/test_fixture.py>`_

  This class supports loading object model with the corresponding `load(json)`
  function. Also it contains a minimal set of assertions such as
  ``assertEqual`` and etc.

  Note, that test class has the following reserved methods are:

    * *initialize* is executed once, like in any other murano application
    * *setUp* is executed before each test case
    * *tearDown* is executed after each test case

* Named with *test* prefix

.. code-block:: console

    usage: murano-test-runner [-h] [--config-file CONFIG_FILE]
                              [--os-auth-url OS_AUTH_URL]
                              [--os-username OS_USERNAME]
                              [--os-password OS_PASSWORD]
                              [--os-project-name OS_PROJECT_NAME]
                              [-l [</path1, /path2> [</path1, /path2> ...]]] [-v]
                              [--version]
                              <PACKAGE_FQN>
                              [<testMethod1, className.testMethod2> [<testMethod1, className.testMethod2> ...]]

    positional arguments:
      <PACKAGE_FQN>
                            Full name of application package that is going to be
                            tested
      <testMethod1, className.testMethod2>
                            List of method names to be tested

    optional arguments:
      -h, --help            show this help message and exit
      --config-file CONFIG_FILE
                            Path to the murano config
      --os-auth-url OS_AUTH_URL
                            Defaults to env[OS_AUTH_URL]
      --os-username OS_USERNAME
                            Defaults to env[OS_USERNAME]
      --os-password OS_PASSWORD
                            Defaults to env[OS_PASSWORD]
      --os-project-name OS_PROJECT_NAME
                            Defaults to env[OS_PROJECT_NAME]
      -l [</path1 /path2> [</path1 /path2> ...]], --load_packages_from [</path1 /path2> [</path1 /path2> ...]]
                            Directory to search packages from. Will be used instead of
                            directories, provided in the same option in murano configuration file.
      -v, --verbose         increase output verbosity
      --version             show program's version number and exit


The fully qualified name of a package is required to specify the test location.
It can be an application package that contains one or several classes with all
the test cases, or a separate package. You can specify a class name to
execute all the tests located in it, or specify a particular test case name.

Authorization parameters can be provided in the murano configuration file, or
with higher priority ``-os-`` parameters.

Consider the following example of test execution for the Tomcat application.
Tests are located in the same package with application, but in a separate class
called ``io.murano.test.TomcatTest``. It contains ``testDeploy1`` and
``testDeploy2`` test cases.
The application package is located in the */package/location/directory*
(murano-apps repository e.g). As the result of the following command, both
test cases from the specified package and class will be executed.

.. code-block:: console

   murano-test-runner io.murano.apps.apache.Tomcat io.murano.test.TomcatTest -l /package/location/directory /io.murano/location -v

The following command runs a single *testDeploy1* test case from the
application package.

.. code-block:: console

   murano-test-runner io.murano.apps.apache.Tomcat io.murano.test.TomcatTest.testDeploy1

The main purpose of MuranoPL unit test framework is to enable mocking.
Special :ref:`yaql` functions are registered for that:

`def inject(target, target_method, mock_object, mock_name)`
  ``inject`` to set up mock for *class* or *object*, where mock definition is a *name of the test class method*

`def inject(target, target_method, yaql_expr)`
  ``inject`` to set up mock for *a class* or *object*, where mock definition is a *YAQL expression*

Parameters description:

**target**
 MuranoPL class name (namespaces can be used or full class name
 in quotes) or MuranoPL object

**target_method**
 Method name to mock in target

**mock_object**
 Object, where mock definition is contained

**mock_name**
 Name of method, where mock definition is contained

**yaql_expr**
 YAQL expression, parameters are allowed

So the user is allowed to specify mock functions in the following ways:

* Specify a particular method name
* Provide a YAQL expression

Consider how the following functions may be used in the MuranoPL class with
unit tests:

.. code-block:: yaml

    Namespaces:
      =: io.murano.test
      sys: io.murano.system

    Extends: TestFixture

    Name: TomcatTest

    Methods:
      initialize:
            Body:
                # Object model can be loaded from JSON file, or provided
                # directly in MuranoPL code as a YAML insertion.
                - $.appJson: new(sys:Resources).json('tomcat-for-mock.json')
                - $.heatOutput: new(sys:Resources).json('output.json')
                - $.log: logger('test')
                - $.agentCallCount: 0

        # Mock method to replace the original one
        agentMock:
          Arguments:
            - template:
                Contract: $
            - resources:
                Contract: $
            - timeout:
                Contract: $
                Default: null
          Body:
            - $.log.info('Mocking murano agent')
            - $.assertEqual('Deploy Tomcat', $template.Name)
            - $.agentCallCount: $.agentCallCount + 1

        # Mock method, that returns predefined heat stack output
        getStackOut:
          Body:
            - $.log.info('Mocking heat stack')
            - Return: $.heatOutput

        testDeploy1:
          Body:
            # Loading object model
            - $.env: $this.load($.appJson)

            # Set up mock for the push method of *io.murano.system.HeatStack* class
            - inject(sys:HeatStack, push, $.heatOutput)

            # Set up mock with YAQL function
            - inject($.env.stack, output, $.heatOutput)

            # Set up mock for the concrete object with mock method name
            - inject('io.murano.system.Agent', call, $this, agentMock)

            # Mocks will be called instead of original function during the deployment
            - $.env.deploy()

            # Check, that mock worked correctly
            - $.assertEqual(1, $.agentCallCount)


        testDeploy2:
          Body:
            - inject(sys:HeatStack, push,  $this, getStackOut)
            - inject(sys:HeatStack, output, $this, getStackOut)

            # Mock is defined with YAQL function and it will print the original variable (agent template)
            - inject(sys:Agent, call, withOriginal(t => $template) -> $.log.info('{0}', $t))

            - $.env: $this.load($.appJson)
            - $.env.deploy()

            - $isDeployed: $.env.applications[0].getAttr(deployed, false, 'com.example.apache.Tomcat')
            - $.assertEqual(true, $isDeployed)

Provided methods are test cases for the Tomcat application. Object model and
heat stack output are predefined and located in the package ``Resources``
directory. By changing some object model or heat stack parameters, different
cases may be tested without a real deployment. Note, that some asserts are used
in those example. The first one is checked, that agent call function was called
only once as needed. And assert from the second test case checks for a variable
value at the end of the application deployment.

Test cases examples can be found in :file:`TomcatTest.yaml` class of the
Apache Tomcat application located at `murano-apps repository <https://git.openstack.org/cgit/openstack/murano-apps/tree/Tomcat/package/Classes/TomcatTest.yaml>`_.
You can run test cases with the commands provided above.
