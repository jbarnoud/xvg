#!/usr/bin/env python

import operator
import re
import numpy

# A regular expression to split a string around spaces, while keeping quoted
# strings together. The regexp is modified from
# <http://stackoverflow.com/questions/2785755/how-to-split-but-ignore-separators-in-quoted-strings-in-python>
RE_SPLIT = re.compile(r'''((?:[^\s"']|"[^"]*"|'[^']*')+)''')


class XvgSingle(object):
    """
    A dataset with metadata from a XVG file

    A XVG file contains one or multiple dataset along with metadata and plot
    instructions. This class gives access to one dataset and its metadata.

    The accessible metadata are the dataset title, the label of the X axis, the
    label of the Y, and the name of the columns. They are accessible *via* the
    `title`, `xlabel`, `ylabel`, and `columns attributes, respectively.

    The data can be accessed and manipulated like a numpy array. In addition,
    columns can be acessed by their name.
    """
    _translate_commands = {
        'title': 'title',
        'xaxis': 'xlabel',
        'yaxis': 'ylabel'
    }

    def __init__(self):
        self._columns = {}
        self._array = numpy.empty((0,))
        self.xlabel = ''
        self.ylabel = ''
        self.title = ''

    def parse(self, content):
        """
        Read an input to fill the current instance

        Only the first dataset is read from the input. The reading stops at
        the first occurence of '//' in the file or at the end of the file if
        there is only one dataset.

        Parameters
        ----------
        content: iterator
            Iterator over the lines of a XVG file.
        """
        values = []
        for line in content:
            if line.startswith('//'):
                break  # For now we read only one dataset
            elif line.startswith('@'):
                self._parse_header_line(line)
            elif line.startswith('#'):
                continue
            else:
                values.append(line.split())
        self._array = numpy.array(values, dtype='float')

    @property
    def columns(self):
        items = list(sorted(self._columns.items(), key=operator.itemgetter(1)))
        columns = []
        i = 0
        while items:
            if items[0][1] == i:
                columns.append(items.pop(0)[0])
            else:
                columns.append('')
            i += 1
        return columns

    @classmethod
    def from_iter(cls, content):
        """
        Create an instance from an iterator over XVG lines
        """
        xvg = cls()
        xvg.parse(content)
        return xvg

    @classmethod
    def from_fname(cls, fname):
        """
        Create an instance from the path to a XVG file
        """
        xvg = cls()
        with open(fname, 'rt') as infile:
            xvg.parse(infile)
        return xvg

    def _parse_header_line(self, line):
        tokens = RE_SPLIT.findall(line[1:].strip())
        # the quotation symbols are kept, but we want them removed
        tokens = [
            token[1:-1]
            if token[0] == token[-1] and token[0] in '"\'' else token
            for token in tokens
        ]
        command = tokens.pop(0)
        if command == 'title':
            self.title = tokens.pop(0)
        elif command in self._translate_commands:
            setattr(self, self._translate_commands[command], tokens.pop(0))
        elif command.startswith('s') and tokens[0] == 'legend':
            tokens.pop(0)
            self._columns[tokens.pop()] = int(command[1:]) + 1

    def __getitem__(self, key):
        try:
            hash(key)
        except TypeError:
            key_is_mutable = False
        else:
            key_is_mutable = True
        if key_is_mutable and key in self._columns:
            return self._array[:, self._columns[key]]
        return self._array[key]

    def __getattr__(self, attr):
        return getattr(self._array, attr)


# Keep the XVG name for retro-compatibility
XVG = XvgSingle
