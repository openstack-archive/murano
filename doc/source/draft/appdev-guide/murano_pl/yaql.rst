.. _yaql:

YAQL
~~~~

YAQL (Yet Another Query Language) is a query language that was also designed as a part of the Murano project. MuranoPL makes an extensive use of YAQL. YAQL description can be found here: https://github.com/ativelkov/yaql

In simple words YAQL is a language for expression evaluation. ``2 + 2, foo() > bar(), true != false`` are all valid YAQL expressions. The interesting thing in YAQL is that it has no built in list of functions. Everything YAQL can access is customizable. YAQL cannot call any function that was not explicitly registered to be accessible by YAQL. The same is true for operators. So the result of the expression 2 * foo(3, 4) completely depends on explicitly provided implementations of "foo" and "operator_*".
YAQL uses a dollar sign ($) to access external variables (that are also explicitly provided by host application) and function arguments. ``$variable`` is a syntax to get a value of the variable "$variable",
$1, $2, etc. are the names for function arguments. "$" is a name for current object: data on which an expression is evaluated, or a name of a single argument. Thus, "$" in the beginning of an expression and "$" in the middle of it can refer to different things.

YAQL has a lot of functions out of the box that can be registered in YAQL context. For example:

``$.where($.myObj.myScalar > 5 and $.myObj.myArray.len() > 0 and $.myObj.myArray.any($ = 4)).select($.myObj.myArray[0])`` can be executed on ``$ = array`` of objects and has a result of another array that is a filtration and a projection of a source data. This is very similar to how SQL works but uses more Python-like syntax.

.. note::
   Note, that there is no assignment operator in YAQL and '=' means comparision operator that is what '==' means in Python.

Because YAQL has no access to underlying operating system resources and fully controllable by the host it is secure to execute YAQL expressions without establishing a trust to executed code. Also because of functions are not predefined, different functions can be accessible in different contexts. So, the YAQL expressions that are used to specify property contracts are not necessarily valid in workflow definitions.
