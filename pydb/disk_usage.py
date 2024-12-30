#!/usr/bin/env python3

"""
Return disk usage statistics about the given path as a (total, used, free)
namedtuple.  Values are expressed in bytes.
"""
# Author: Giampaolo Rodola' <g.rodola [AT] gmail [DOT] com>
# License: MIT

import os
import collections

DiskUsage = collections.namedtuple('DiskUsage', 'total used free')

if hasattr(os, 'statvfs'):  # POSIX
    def disk_usage(path):
        st = os.statvfs(path)
        free = st.f_bavail * st.f_frsize
        total = st.f_blocks * st.f_frsize
        used = (st.f_blocks - st.f_bfree) * st.f_frsize
        return DiskUsage(total, used, free)

elif os.name == 'nt':  # Windows
    import ctypes

    def disk_usage(path):
        _, total, free = ctypes.c_ulonglong(), ctypes.c_ulonglong(), \
                         ctypes.c_ulonglong()
        fun = ctypes.windll.kernel32.GetDiskFreeSpaceExW
        ret = fun(path, ctypes.byref(_), ctypes.byref(total), ctypes.byref(free))
        if ret == 0:
            raise ctypes.WinError()
        used = total.value - free.value
        return DiskUsage(total.value, used, free.value)
else:
    raise NotImplementedError("platform not supported")

disk_usage.__doc__ = __doc__

if __name__ == '__main__':
    print(disk_usage(os.getcwd()))
