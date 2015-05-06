
class FileDownloadMonitor(object):
    def __init__(self):
        self.locked_items = set()
        self.completed_items = set()

    def try_lock(self, file_hash):
        # returns true if a lock could be acquired, false if the lock is currently held and None if the lock
        # could not be acquired as the file is already completed

        file_hash = file_hash.lower()
        if file_hash in self.completed_items:
            return None

        if file_hash in self.locked_items:
            return False

        self.locked_items.add(file_hash)
        return True

    def unlock(self, file_hash):
        # unlocks an item
        self.locked_items.remove(file_hash)

    def set_completed_and_unlock(self, file_hash):
        # sets a file as completed
        # can only be called if the file is currently locked
        # an unlock call is required afterwards
        self.completed_items.add(file_hash)

        if file_hash not in self.locked_items:
            raise KeyError("Hash {} not locked in set_completed".format(file_hash))

        self.locked_items.remove(file_hash)

