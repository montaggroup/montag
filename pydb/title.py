
def coalesce_title(title, subtitle):
    if not subtitle:
        return title
    return title+": "+subtitle
