.. _muranopl_extensions:

.. toctree::
   :maxdepth: 2


MuranoPL extension plug-ins
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Murano plug-ins allow extending MuranoPL with new classes. Therefore, using
such plug-ins applications with MuranoPL format, you access some additional
functionality defined in a plug-in. For example, the Magnum plug-in, which
allows murano to deploy applications such as Kubernetes using the capabilities
of the Magnum client.

MuranoPL extension plug-ins can be used for the following purposes:

* Providing interaction with external services.

  For example, you want to interact with the OpenStack Image service to get
  information about images suitable for deployment. A plug-in may request image
  data from glance during deployment, performing any necessary checks.

* Enabling connections between murano applications and external hardware

  For example, you have an external load balancer located on a powerful
  hardware and you want your applications launched in OpenStack to use that
  load balancer. You can write a plug-in that interacts with the load balancer
  API. Once done, add new apps to the pool of your load balancer or make any
  other configurations from within your application definition.

* Extending Core Library class functionality, which is responsible for creating
  networks, interaction with murano-agent, and others

  For example, you want to create networks with special parameters for all of
  your applications. You can just copy the class that is responsible for
  network management from the Murano Core library, make the desired
  modification, and load the new class as a plug-in. Both classes will be
  available, and it is up to you to decide which way to create your networks.

* Optimization of frequently used operations. Plug-in classes are written in
  Python, therefore, the opportunity for improvement is significant.

  Murano provides a number of optimization opportunities depending on the
  improvement needs. For example, classes in the Murano Core Library can be
  rewritten in C and used from Python code to improve their performance in
  particular use cases.
