.. _yaml:

YAML
~~~~

YAML is an easily readable data serialization format that is a superset
of JSON. Unlike JSON, YAML is designed to be read and written by humans
and relies on visual indentation to denote nesting of data structures.
This is similar to how Python uses indentation for block structures
instead of curly brackets in most C-like languages. Also YAML may
contain more data types as compared to JSON. See http://yaml.org/
for a detailed description of YAML.

MuranoPL is designed to be representable in YAML so that MuranoPL code could
remain readable and structured. Usually MuranoPL files are YAML encoded documents.
But MuranoPL engine itself does not deal directly with YAML documents, and it is up to
the hosting application to locate and deserialize the definitions of particular classes.
This gives the hosting application the ability to control where those definitions can be
found (a file system, a database, a remote repository, etc.) and possibly use some other
serialization formats instead of YAML.

MuranoPL engine relies on a host deserialization code when detecting YAQL
expressions in a source definition. It provides them as instances of the YaqlExpression
class rather than plain strings. Usually, YAQL expressions can be distinguished by the
presence of $ (the dollar sign) and operators, but in YAML, a developer can always
state the type by using YAML tags explicitly. For example:

.. code-block:: yaml
   :linenos:

    Some text - a string
    $.something() - a YAQL expression
    "$.something()" - a string because quotes are used
    !!str $ - a string because a YAML tag is used
    !yaql "text" - a YAQL expression because a YAML tag is used
