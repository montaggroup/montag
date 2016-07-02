import re

# coding=utf-8
def coalesce_title(title, subtitle):
    if not subtitle:
        return title
    return title+": "+subtitle


def title_split(title):
    subtitle = None
    edition = None

    title = title.strip()

    m = re.match('(.*), ([^,]+) edition$', title, re.IGNORECASE)
    if m:
        title = m.group(1)
        edition = m.group(2)+" Edition"

    if ":" in title:
        title, subtitle = title.split(':', 1)
        title = title.strip()
        subtitle = subtitle.strip()
    return title, subtitle, edition
