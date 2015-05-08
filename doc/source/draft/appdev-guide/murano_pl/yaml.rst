.. _yaml:

YAML
~~~~

YAML is a human-readable data serialization format that is a superset of JSON. Unlike JSON YAML was designed to be read and written by humans and relies on visual indentation to denote nesting of data structures. This is similar to how Python uses indentation for block structures instead of curly brackets in most C-like languages. Also YAML may contain more data types comparing to JSON. See http://yaml.org/ for a detailed description of YAML.

MuranoPL was designed to be representable in YAML so that MuranoPL code could remain readable and structured. Thus usually MuranoPL files are YAML encoded documents. But MuranoPL engine itself doesn't  deal directly with YAML documents and it is up to hosting application to locate and deserialize definitions of particular classes. This gives hosting application ability to control where those definitions can be found (a file system, a database, a remote repository, etc.) and possibly use some other serialization formats instead of YAML.

MuranoPL engine relies on a host deserialization code to automatically detect YAQL expressions in a source definition and to provide them as instances of YaqlExpression class rather than plain strings. Usually YAQL expressions can be distinguished by presence of $ (dollar sign) and operators, but in YAML, a developer can always explicitly state the type by using YAML tags. For example:

.. code-block:: yaml
   :linenos:

     Some text - a string
     $.something() - YAQL expression
     "$.something()" - a string because of quotes are used
     !!str $ - a string due to YAML tag is used
     !yaql "text" - YAQL due to YAML tag is used
