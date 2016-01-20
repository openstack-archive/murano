.. _yaql:

YAQL
~~~~

YAQL (Yet Another Query Language) is a query language that was also
designed as a part of the murano project. MuranoPL makes an extensive
use of YAQL. A description of YAQL can be found `here <https://yaql.readthedocs.org>`_.

Simply speaking, YAQL is the language for expression evaluation.
The following examples are all valid YAQL expressions:
``2 + 2, foo() > bar(), true != false``.

The interesting thing in YAQL is that it has no built in list of
functions. Everything YAQL can access is customizable. YAQL cannot call
any function that was not explicitly registered to be accessible by YAQL.
The same is true for operators. So the result of the expression 2 *
foo(3, 4) completely depends on explicitly provided implementations
of "foo" and "operator_*".

YAQL uses a dollar sign ($) to access external variables, which are also
explicitly provided by the host application, and function arguments.
``$variable`` is a syntax to get a value of the variable "$variable",
$1, $2, etc. are the names for function arguments. "$" is a name for current object:
data on which an expression is evaluated, or a name of a single argument. Thus,
"$" in the beginning of an expression and "$" in the middle of it can refer
to different things.

By default, YAQL has a lot of functions that can be registered in a YAQL
context. This is very similar to how SQL works but uses more Python-like
syntax. For example: :code:`$.where($.myObj.myScalar > 5`,
:code:`$.myObj.myArray.len() > 0`, and :code:`$.myObj.myArray.any($ = 4)).select($.myObj.myArray[0])` can be executed on :code:`$ = array` of objects,
and result in another array that is a filtration and projection of a source data.

.. note::
   There is no assignment operator in YAQL, and ``=`` means
   comparison, the same what ``==`` means in Python.

As YAQL has no access to underlying operating system resources and
is fully controllable by the host, it is secure to execute YAQL expressions
without establishing a trust to the executed code. Also, because functions
are not predefined, different methods can be accessible in different
context. So, YAQL expressions that are used to specify property
contracts are not necessarily valid in workflow definitions.


