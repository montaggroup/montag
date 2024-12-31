from . import *

import logging

logger = logging.getLogger('only_provider')


class OnlyProvider(Strategy):
    def __init__(self, provider, main_db):
        super(OnlyProvider, self).__init__()
        self._provider = provider
        self._main_db = main_db
        self._friend_id = None
        self._session = None
        self._completion_callback = None

    # noinspection PyUnusedLocal
    def associated(self, session, friend_id, completion_callback, bulk_inserter):
        self._session = session
        self._friend_id = friend_id
        self._completion_callback = completion_callback
        self._provider.activate(self._session, self.provider_completed, self.any_requester_failed)

    def provider_completed(self):
        self._completion_callback()

    def any_requester_failed(self):
        logger.warning("A requester or provider failed to complete.")
        self._completion_callback()
