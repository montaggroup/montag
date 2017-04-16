# coding=utf-8
import montag_lookup


def build(pydb_, file_server):
    return montag_lookup.MontagLookupByHash(pydb_)
