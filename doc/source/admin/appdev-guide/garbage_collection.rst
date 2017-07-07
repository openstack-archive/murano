.. _garbage_collection:

=====================================
Garbage collection system in MuranoPL
=====================================

A garbage collection system (GC) manages the deallocation of resources in
murano. The garbage collection system implementation is based on the execution
of special ``.destroy()`` methods that you may define in MuranoPL classes.
These methods contain logic to deallocate any resources that were allocated
by MuranoPL objects. During deployment all objects that are not referenced by
any other object and that are not present in the object model anymore is deleted
by GC.

* The ``.destroy()`` methods are executed for each class in the class hierarchy of
  the object that has this method. Child classes cannot prevent parent classes
  ``.destroy`` from being called and cannot call base classes
  implementation manually

* ``.destroy()`` methods for class hierarchy are called in reversed order from that
  of ``.init()`` - starting from the actual object type and up to the
  `io.murano.Object` class

* If object `Bar` is owned (directly or indirectly) by object `Foo` then `Bar`
  is going to be destroyed before `Foo`. There is a way for `Foo` to get
  notified on `Bar`'s destruction so that it can prepare for it. See below for
  details.

* For objects that are not related to each other the destruction
  order is undefined. However objects may establish destruction dependency between
  them to establish the order.

* Unrelated objects might be destroyed in different green threads.

* Any exceptions thrown in the ``.destroy()`` methods are muted (but still logged).

Destruction dependencies may be used to notify `Foo` of `Bar`'s destruction even if
`Bar` is not owned by `Foo`. If you subscribe `Foo` to `Bar`'s destruction,
the following will happen:

* `Foo` will be notified when `Bar` is about to be destroyed.

* If both `Foo` and `Bar` are going to be destroyed in the same garbage
  collection execution, `Bar` will be destroyed before `Foo`.

Garbage collector methods
~~~~~~~~~~~~~~~~~~~~~~~~~

Murano garbage collector class (``io.murano.system.GC``) has
the following methods:

``collect()``
 Initiates garbage collection of unreferenced objects of current deployment.
 Usually, it is called by murano ``ObjectStore`` object during deployment.
 However, it can be called from MuranoPL code like
 ``io.murano.system.GC.collect()``.

``isDestroyed(object)``
 Checks if the ``object`` was already destroyed during a GC session and thus
 its methods cannot be called.

``isDoomed(object)``
 Can be used within the ``.destroy()`` method to check if another object is
 also going to be destroyed.

``subscribeDestruction(publisher, subscriber, handler=null)``
 Establishes a destruction dependency from the ``subscriber`` to the object
 passed as ``publisher``. This method may be called several times with the same
 arguments. In this case, only a single destruction dependency will be established.
 However, the same amount of calls of ``unsubscribeDestruction`` will be required to
 remove it.

 The ``handler`` argument is optional. If passed, it should be the name of an
 instance method defined by the caller class to handle the notification of
 ``publisher`` destruction. The following argument will be passed to the
 ``handler`` method:

  ``object``
   A target object that is going to be destroyed. It is not recommended
   persisting the reference to this object anywhere. This will not prevent the
   object from being garbage collected but the object will be moved to the
   "destroyed" state. This is an advanced feature that should
   not be used unless it is absolutely necessary.

``unsubscribeDestruction(publisher, subscriber, handler=null)``
 Removes the destruction dependency from the ``subscriber`` to the object
 passed as ``publisher``. The method may be called several times with the same
 arguments without any side effects. If ``subscribeDestruction`` was called more
 than once, the same (or more) amount of calls to ``unsubscribeDestruction`` is
 needed to remove the dependency.

 The ``handler`` argument is optional and must correspond to the handler
 passed during subscription if it was provided.

Using destruction dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To use direct destruction dependencies in your murano applications, use the
methods from MuranoPL ``io.murano.system.GC``. To establish a
destruction dependency, call the
``io.murano.system.GC.subscribeDestruction`` method in you
application code:

.. code-block:: console

   .init:
      Body:
        - If: $.publisher
          Then:
            - sys:GC.subscribeDestruction($.publisher, $this, onPublisherDestruction)


In the example above, ``onPublisherDestruction`` is a `Foo` object method that
will be called when `Bar` is destroyed. If you do not want to do something
specific with the destroyed object omit the third parameter.
The destruction dependencies will be persisted between deployments and
deserialized from the objects model to murano object.
