import sys
import time
import codecs
import contextlib
import numpy
from collections import deque


class PicklableObject(object):

    _saveable_fields = None

    def __getstate__(self):
        if getattr(self, '__slots__', None):
            return {key: getattr(self, key) for key in self.__slots__}
        if self._saveable_fields:
            return {key: value for key, value in self.__dict__.items()
                    if key in self._saveable_fields}
        return self.__dict__

    def __setstate__(self, data):
        if getattr(self, '__slots__', None):
            [setattr(self, key, value) for key, value in data.items()]
        else:
            if self._saveable_fields:
                data = {key: value for key, value in data.items()
                        if key in self._saveable_fields}
            self.__dict__.update(data)


class Logger(object):
    """ Convenient double logger that redirects `stdout` and save the output also to the file """
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = codecs.open(filename, "w", encoding="utf8")

    def write(self, message, terminal=True, log=True):
        if terminal:
            self.terminal.write(message)
        if log:
            self.log.write(message.decode('utf8'))

    def __del__(self):
        if sys:
            sys.stdout = self.terminal

    def __getattr__(self, attr):
        return getattr(self.terminal, attr)


class ring_deque(deque):
    """ Circular deque implementation """

    max = 0
    min = 0

    def __init__(self, data, length):
        self.length = length
        super(ring_deque, self).__init__(data)

    def append_more(self, data):

        if len(self) > self.length:
            self.popleft()

        self.max = max(data, self.max)
        self.min = min(data, self.min)
        super(ring_deque, self).append(data)

    def append(self, data):
        self.max = data
        self.min = data

        self.append = self.append_more

        super(ring_deque, self).append(data)


class benchmark(object):
    """ Simple benchmarking context manager """
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, ty, val, tb):
        end = time.time()
        print("{:s} : {:0.3f} seconds"
              .format(self.name if not callable(self.name) else self.name(), end-self.start))
        return False


@contextlib.contextmanager
def printoptions(*args, **kwargs):
    original = numpy.get_printoptions()
    numpy.set_printoptions(*args, **kwargs)
    yield
    numpy.set_printoptions(**original)
