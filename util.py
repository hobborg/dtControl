from os.path import basename, splitext, isdir
from os import makedirs
from time import strftime

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

