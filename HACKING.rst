Style Commandments
==================

Read the OpenStack Style Commandments https://docs.openstack.org/hacking/latest/

Murano Specific Commandments
----------------------------

- [M318] Change assertEqual(A, None) or assertEqual(None, A) by optimal assert
  like assertIsNone(A)
- [M322] Method's default argument shouldn't be mutable.
- [M323] Python 3: do not use dict.iteritems.
- [M324] Python 3: do not use dict.iterkeys.
- [M325] Python 3: do not use dict.itervalues.
- [M326] Python 3: do not use basestring.
