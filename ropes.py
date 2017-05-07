__version__ = '0.0.1'

class Rope(object):
    # NOTE: self.left and self.right should either both point to subnodes or
    #       both set to `None`, so checking both should not be necessary.

    def __init__(self, data=''):
        if isinstance(data, list):
            if len(data) == 0:
                self.__init__()
            elif len(data) == 1:
                self.__init__(data[0])
            else:
                # Round-up division (to match rope arithmetic associativity)
                idiv = len(data) // 2 + (len(data) % 2 > 0)

                self.left = Rope(data[:idiv])
                self.right = Rope(data[idiv:])
                self.data = ''
                self.length = self.left.length + self.right.length
        elif isinstance(data, str):
            self.left = None
            self.right = None
            self.data = data
            self.length = len(data)
        else:
            raise TypeError('Only strings are currently supported')

        # Word iteration
        self.current = self

    def __eq__(self, other):
        if (self.left and self.right) and (other.left and other.right):
            return self.left == other.left and self.right == other.right
        elif (self.left and self.right) or (other.left and other.right):
            return False
        else:
            return self.data == other.data

    def __add__(self, other):
        # TODO: Automatically collapse empty ropes
        r = Rope()
        r.left = self
        r.right = other
        r.length = self.length + other.length
        r.current = self
        return r

    def __len__(self):
        if self.left and self.right:
            return len(self.left.data) + len(self.right.data)
        else:
            return(len(self.data))

    def __getitem__(self, index):

        if isinstance(index, int):
            if self.left and self.right:
                if index < -self.right.length:
                    subindex = index + self.right.length
                elif index >= self.left.length:
                    subindex = index - self.left.length
                else:
                    subindex = index

                if index < -self.right.length or 0 <= index < self.left.length:
                    return self.left[subindex]
                else:
                    return self.right[subindex]
            else:
                return Rope(self.data[index])

        elif isinstance(index, slice):
            if self.left and self.right:
                start = index.start
                if index.start is None:
                    if index.step is None or index.step > 0:
                        head = self.left
                    else:
                        head = self.right
                elif (index.start < -self.right.length or
                        0 <= index.start < self.left.length):
                    head = self.left
                    if index.start and index.start < -self.right.length:
                        start += self.right.length
                else:
                    head = self.right
                    if index.start and index.start >= self.left.length:
                        start -= self.left.length

                # TODO: stop = -right.length could be on either subrope.
                # There are two options:
                #   1. tail = left and stop = None (or left.length)
                #   2. tail = right as a '' string, which is removed
                # Currently doing method 2, but I'm on the fence here.
                stop = index.stop
                if index.step is None or index.step > 0:
                    if (index.stop is None or
                            -self.right.length <= index.stop < 0 or
                            index.stop > self.left.length):
                        tail = self.right
                        if index.stop and index.stop > self.left.length:
                            stop -= self.left.length
                    else:
                        if head == self.right:
                            tail = self.right
                            stop = 0
                        else:
                            tail = self.left
                            if index.stop < -self.right.length:
                                stop += self.right.length
                else:
                    if (index.stop is None or
                            index.stop < -self.right.length - 1 or
                            0 <= index.stop < self.left.length - 1):
                        tail = self.left
                        if index.stop and index.stop < -self.right.length:
                            stop += self.right.length
                    else:
                        if head == self.left:
                            tail = self.left
                            stop = -1   # Or self.left.length - 1 ?
                        else:
                            tail = self.right
                            if index.stop > self.left.length:
                                stop -= self.left.length

                # Construct the rope
                if head == tail:
                    return head[start:stop:index.step]
                else:
                    if index.step:
                        if start is None:
                            delta = -head.length
                        elif start >= 0:
                            delta = start - head.length
                        else:
                            delta = max(index.start, -self.length) + tail.length

                        offset = delta % index.step
                        if offset == 0:
                            offset = None
                    else:
                        offset = None

                    if not tail[offset:stop:index.step]:
                        return head[start::index.step]
                    else:
                        return head[start::index.step] + tail[offset:stop:index.step]
            else:
                return Rope(self.data[index])

            #----------------------------------------------------
            # Old explicit implementation

            # Slice logic taken from CPython's sliceobject.c
            # It may be possible to streamline this in Python

            if self.left and self.right:
                # Step initialization
                if index.step is None:
                    step = 1
                else:
                    if index.step == 0:
                        raise ValueError('slice step cannot be zero')
                    else:
                        step = index.step

                # Default start/stop indices
                if step < 0:
                    default_start = self.length - 1
                    default_stop = -1
                else:
                    default_start = 0
                    default_stop = self.length

                # Start index
                if index.start is None:
                    start = default_start
                else:
                    start = index.start
                    if start < 0:
                        start += self.length
                    if start < 0:
                        start = 0 if step > 0 else -1
                    if start >= self.length:
                        start = self.length if step > 0 else (self.length - 1)

                # Stop index
                if index.stop is None:
                    stop = default_stop
                else:
                    stop = index.stop
                    if stop < 0:
                        stop += self.length
                    if stop < 0:
                        stop = 0 if step > 0 else -1
                    if stop >= self.length:
                        stop = self.length if step > 0 else (self.length - 1)

                # Apply slice
                print('index', index.start, index.stop, index.step)
                print('slice', start, stop, step)
                if start < self.left.length:
                    if stop <= self.left.length:
                        print('LEFT')
                        return self.left[start:stop:step]
                    else:
                        print('MIXED')
                        return (self.left[start::step]
                                + self.right[(start + step - self.left.length) % step
                                             :(stop - self.left.length):step])
                else:
                    print('RIGHT')
                    return self.right[(start - self.left.length)
                                      :max(stop - self.left.length, 0)
                                      :step]
            else:
                return Rope(self.data[index])

        else:
            raise TypeError('rope indices must be integers or slices, not {}'
                            ''.format(type(index).__name__))

    def __repr__(self):
        # TODO: Parentheses are too conservative, need to clean this up
        if self.left and self.right:
            return '{}{} + {}{}'.format('(' if self.left else '',
                                        self.left.__repr__(),
                                        self.right.__repr__(),
                                        ')' if self.right else '')
        else:
            return "Rope('{}')".format(self.data)

    def __str__(self):
        if self.left and self.right:
            return self.left.__str__() + self.right.__str__()
        else:
            return self.data

    def __iter__(self):
        return self

    def __next__(self):
        if self.current:
            if self.left and self.right:
                try:
                    return next(self.left)
                except StopIteration:
                    self.current = self.right
                return next(self.right)
            else:
                self.current = None
                return self.data
        else:
            raise StopIteration

    def next(self):
        return self.__next__()

    # API
    def reduce(self):
        """Search the tree and remove any redundant nodes."""
        raise NotImplementedError

    def insert(self, index, s):
        """Insert string s at index i."""
        raise NotImplementedError
