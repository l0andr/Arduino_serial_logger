def constant(f):
    def fset(self, value):
        raise TypeError

    def fget(self):
        return f()

    return property(fget, fset)


class _Const(object):
    @constant
    def serial_speeds():
        return [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]


CONST = _Const()
