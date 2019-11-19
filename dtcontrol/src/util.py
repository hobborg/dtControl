from os.path import basename, splitext
import numpy as np


def format_seconds(sec):
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    pattern = '%%02d:%%02d:%%0%d.%df' % (6, 3)
    if d == 0:
        return pattern % (h, m, s)
    return ('%d days, ' + pattern) % (d, h, m, s)


def get_filename_and_ext(filename):
    path, ext = splitext(filename)
    return basename(path), ext


def make_set(v):
    if isinstance(v, tuple):
        return {v}
    try:
        return set(v)
    except TypeError:
        return {v}


def objround(obj, precision):
    if isinstance(obj, list) or isinstance(obj, np.ndarray):
        return [objround(o, precision) for o in obj]
    if isinstance(obj, tuple):
        return tuple(round(o, precision) for o in obj)
    # if just a float
    return round(obj, precision)


def split_into_lines(l):
    if not isinstance(l, list) or len(l) < 5:
        return str(l)
    i = 0
    l2 = []
    while i < len(l):
        l2.append(','.join([str(j) for j in l[i:min(i+5, len(l))]]))
        i += 5
    return '[' + '\n'.join(l2) + ']'

def peek_line(file):
    pos = file.tell()
    line = file.readline()
    file.seek(pos)
    return line
