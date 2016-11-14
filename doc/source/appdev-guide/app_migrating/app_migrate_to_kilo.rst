.. _app_migrate_to_kilo:

Migrate applications to Stable/Kilo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In Kilo, there are no breaking changes that affect backward compatibility.
But there are two new features which you can use since Kilo.

1. Pluggable Pythonic classes for murano
----------------------------------------

Now you can create plug-ins for MuranoPL. A plug-in (extension) is an
independent Python package implementing functionality which you want
to add to the workflow of your application.

For a demo application demonstrating the usage of plug-ins, see the
``murano/contrib/plugins/murano_exampleplugin`` folder.

The application consist of the following components:

  * An `ImageValidatorMixin` class that inherits the generic instance class
    (``io.murano.resources.Instance``) and adds a method capable of validating
    the instance image for having an appropriate murano metadata type. This
    class may be used as a mixin when added to inheritance hierarchy of
    concrete instance classes.

  * A concrete class called `DemoInstance` that inherits from
    `io.murano.resources.LinuxMuranoInstance` and `ImageValidatorMixin`
    to add the image validation logic to a standard, murano-enabled and
    Linux-based instance.

  * An application that deploys a single VM using the `DemoInstance`
    class if the tag on the user-supplied image matches the user-supplied
    constant.

The **ImageValidatorMixin** demonstrates the instantiation of plug-in provided
class and its usage, as well as handling of exception which may be thrown if
the plug-in is not installed in the environment.

2. Murano mistral integration
-----------------------------

The core library has a new system class for mistral client that allows to call
Mistral APIs from the murano application model.

The system class allows you to:

  * Upload a mistral workflow to mistral.

  * Trigger the mistral workflow that is already deployed, wait for completion
    and return the execution output.

To use this feature, add some mistral workflow to ``Resources`` folder
of your package. For example, create file `TestEcho_MistralWorkflow.yaml`:

  .. code-block:: yaml

    version: '2.0'

    test_echo:
      type: direct
      input:
        - input_1
      output:
        out_1: <% $.task1_output_1 %>
        out_2: <% $.task2_output_2 %>
        out_3: <% $.input_1 %>
     tasks:
       my_echo_test:
         action: std.echo output='just a string'
         publish:
           task1_output_1: 'task1_output_1_value'
           task1_output_2: 'task1_output_2_value'
         on-success:
           - my_echo_test_2

       my_echo_test_2:
         action: std.echo output='just a string'
         publish:
           task2_output_1: 'task2_output_1_value'
           task2_output_2: 'task2_output_2_value'
  ..

And provide workflow to use the mistral client:

  .. code-block:: yaml

   Namespaces:
   =: io.murano.apps.test
   std: io.murano
   sys: io.murano.system


   Name: MistralShowcaseApp

   Extends: std:Application

   Properties:
     name:
       Contract: $.string().notNull()

     mistralClient:
       Contract: $.class(sys:MistralClient)
       Usage: Runtime


   Methods:
     initialize:
       Body:
         - $this.mistralClient: new(sys:MistralClient)

     deploy:
       Body:
         - $resources: new('io.murano.system.Resources')
         - $workflow: $resources.string('TestEcho_MistralWorkflow.yaml')
         - $.mistralClient.upload(definition => $workflow)
         - $output: $.mistralClient.run(name => 'test_echo', inputs => dict(input_1 => input_1_value))
         - $this.find(std:Environment).reporter.report($this, $output.get('out_3'))
