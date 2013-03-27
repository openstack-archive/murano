class Context(object):
    def __init__(self, parent=None):
        self._parent = parent
        self._data = None

    def _get_data(self):
        if self._data is None:
            self._data = {} if self._parent is None \
                else self._parent._get_data().copy()
        return self._data

    def __getitem__(self, item):
        context, path = self._parseContext(item)
        return context._get_data().get(path)

    def __setitem__(self, key, value):
        context, path = self._parseContext(key)
        context._get_data()[path] = value

    def _parseContext(self, path):
        context = self
        index = 0
        for c in path:
            if c == ':' and context._parent is not None:
                context = context._parent
            elif c == '/':
                while context._parent is not None:
                    context = context._parent
            else:
                break

            index += 1

        return context, path[index:]

    def assign_from(self, context, copy=False):
        self._parent = context._parent
        self._data = context._data
        if copy and self._data is not None:
            self._data = self._data.copy()

    @property
    def parent(self):
        return self._parent

    def __str__(self):
        if self._data is not None:
            return str(self._data)
        if self._parent:
            return str(self._parent)
        return str({})
