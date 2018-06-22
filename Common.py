import numpy as np
# import mutex


class IDManager:
    """
    help keeping track of ID numbers
    """
    def __init__(self, start_value=0, max_value=np.iinfo(np.int64).max):
        self._start_value = start_value
        self._max_value = max_value
        self._current_id = start_value
        self._ids = []
        # self._mutex = mutex.mutex()

    def __iter__(self):
        return self

    def next(self):
        if len(self.ids) == 0:
            self._ids = [self._current_id]
            return self._current_id

        if self._current_id == self._max_value:
            raise StopIteration

        self._current_id = self._ids[-1] + 1
        self._ids += [self._current_id]
        return self._ids[-1]

    @property
    def ids(self):
        return self._ids

    def exists(self, idd):
        try:
            self._ids.index(idd)
            return True
        except ValueError:
            return False

    def remove(self, idd):
        if self.exists(idd):
            idx = self._ids.index(idd)
            self._ids = self._ids[:idx] + self._ids[idx+1:]
#
# import thread
# import time
#
# idm = IDManager(0, 100)
#
#
# def call_idm_next(_idm):
#     print('this is working' + str(_idm.ids))
#     _idm.next()
#
# c = 1
#
# while c < 10:
#     thread.start_new_thread(call_idm_next, (idm, ))
#     # time.sleep(1)
#     c += 1
#
# idm.remove(5)
# print idm.ids