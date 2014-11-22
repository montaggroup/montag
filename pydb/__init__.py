import re


class FileType(object):
    """ Enum class for the tome file types """
    Content = 1
    Cover = 2


class TomeType(object):
    """ Enum class for the tome types """
    Fiction = 1
    NonFiction = 2
    Unknown = None


def tome_type_text(tome_type):
    if tome_type == TomeType.Fiction:
        return 'Fiction'
    if tome_type == TomeType.NonFiction:
        return 'Non-Fiction'
    if tome_type == TomeType.Unknown:
        return 'Unknown'


def suggested_winning_local_fidelity(local_fidelity, max_foreign_fidelity):
    """ return the minimum required local fidelity to make a change visible at all friends
    without reducing our local fidelity"""

    return max(max_foreign_fidelity + 5 + 5 + 0.1, local_fidelity)


def assert_hash(file_hash):
    if not re.match("[0-9a-f]{64}", file_hash):
        raise ValueError("Invalid hash specified: {}".format(file_hash))


def assert_guid(guid):
    if not re.match("[0-9a-f-]{32,63}", guid):
        raise ValueError("Invalid guid specified: {}".format(guid))


def assert_id(id_string):
    if not re.match("[0-9]+}", id_string):
        raise ValueError("Invalid id specified: {}".format(id_string))
