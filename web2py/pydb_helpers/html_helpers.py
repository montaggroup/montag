# coding: utf8
if False:
    from web2py.applications.montag.models.ide_fake import *


def concat_link_list(link_list):
    if not link_list:
        return ""
    result = link_list[0]
    for link in link_list[1:]:
        result = CAT(result, ", ", link)
    return result


def generate_download_filename(tome, file):
    return u"{} ({}).{}".format(tome['title'], short_hash(file['hash']), file['file_extension'])


def human_readable_time(unixtime):
    # <!--2014-01-18T12:34Z-->
    if not unixtime:
        return "Never"
    return time.strftime('%Y-%m-%dT%H:%MZ', time.gmtime(unixtime))


def human_readable_time_elapsed_since(unixtime):
    if not unixtime:
        return "Never"

    dt = time.time()-unixtime
    if dt <2:
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