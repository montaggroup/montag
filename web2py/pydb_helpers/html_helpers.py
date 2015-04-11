# coding: utf8
import time
from gluon import *


def concat_link_list(link_list):
    if not link_list:
        return ""
    result = link_list[0]
    for link in link_list[1:]:
        result = CAT(result, ", ", link)
    return result


def string_or_empty(text):
    return unicode(text) if text is not None else ""


def short_hash(full_hash):
    return full_hash[:4]


def generate_download_filename(tome, tome_file):
    return u"{} ({}).{}".format(tome['title'], short_hash(tome_file['hash']), tome_file['file_extension'])


def human_readable_time(unixtime):
    # <!--2014-01-18T12:34Z-->
    if not unixtime:
        return "Never"
    return time.strftime('%Y-%m-%dT%H:%MZ', time.gmtime(unixtime))


def human_readable_time_elapsed_since(unixtime):
    if not unixtime:
        return "Never"

    dt = time.time()-unixtime
    if dt < 2:
        return "Just now"
    if dt < 55:
        return "{} seconds ago".format(int((dt+5)/10)*10)

    dt /= 60
    if dt < 1.5:
        return "One minute ago"
    if dt < 59.5:
        return "{} minutes ago".format(int(dt+0.5))

    dt /= 60
    if dt < 1.5:
        return "One hour ago"
    if dt < 59.5:
        return "{} hours ago".format(int(dt+0.5))

    dt /= 24
    if dt < 1.5:
        return "One day ago"

    return "{} days ago".format(int(dt+0.5))


def nice_name(name):
    tn = name.replace("_", " ")
    tn = tn[0].upper() + tn[1:]
    return tn


def nice_name_lcfirst(name):
    tn = name.replace("_", " ")
    return tn


def nice_table_name(table_name):
    tn = table_name.replace("_", " ")
    # remove trailing s
    tn = tn[:-1]
    tn = tn[0].upper() + tn[1:]
    return tn

def wrap_lines(text, min_line_length, max_line_length):
    lines = []
    for line in text.split("\n"):
        while len(line) > max_line_length:
            pos = max_line_length-1
            while line[pos] != " " and pos > min_line_length:
                pos -= 1
            if line[pos] != " ":
                pos = max_line_length-1
            shortened_line = line[0:pos+1]
            line = line[pos+1:]
            lines.append(shortened_line)
        lines.append(line)
    return '\n'.join(lines)
