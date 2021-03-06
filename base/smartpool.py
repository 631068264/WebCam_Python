#!/usr/bin/env python
# -*- coding:utf-8 -*-

import threading
from functools import wraps

# ###### copy from werkzeug.local #######
# since each thread has its own greenlet we can just use those as identifiers
# for the context.  If greenlets are not available we fall back to the
# current thread ident depending on where it is.
try:
    from greenlet import getcurrent as get_ident
except ImportError:
    try:
        from thread import get_ident
    except ImportError:
        from _thread import get_ident


# ####### global vars ########


lock = threading.Lock()
pools = {}


# ####### setting ########


coroutine_mode = False
pool_logger = None


# ########## utils ############


class EmptyPoolError(Exception):
    pass


def log(ident, msg, logger):
    if logger is None:
        return
    logger("%d - %s" % (ident, msg))


def plog(msg):
    tid = threading.current_thread().ident
    log(tid, msg, pool_logger)


def safe_call(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except:
        pass


def total_seconds(td):
    return td.days * 60 * 60 * 24 + td.seconds


# ########## local storage ############


class Local(object):
    def __init__(self):
        self._storage = {}

    @property
    def ident(self):
        return get_ident()

    @property
    def local_storage(self):
        return self._storage.setdefault(self.ident, {})

    def __getitem__(self, key):
        return self.local_storage[key]

    def __setitem__(self, key, value):
        self.local_storage[key] = value

    def get(self, key, default=None):
        return self.local_storage.get(key, default)

    def pop(self, key):
        return self.local_storage.pop(key)


# ########### pool logic ###########


def getlock(old_handler):
    @wraps(old_handler)
    def new_handler(*args, **kwargs):
        if coroutine_mode:
            return old_handler(*args, **kwargs)
        else:
            lock.acquire(True)
            try:
                return old_handler(*args, **kwargs)
            finally:
                lock.release()

    return new_handler


class Connection(object):
    """the connection class base"""

    def __init__(self, **db_config):
        self._db_config = db_config

    def __del__(self):
        """make sure close connection finally"""
        safe_call(self.close)

    @property
    def reusable(self):
        """identify this connection can be reuse or not.
        for example, if connection is in a started transaction, then it's not reusable.
        if you don't set this sign properly, the pool might be useless.
        """
        return True

    @property
    def idle(self):
        """the idle seconds after last action."""
        return 0

    def ping(self):
        """just as it says"""
        return False

    def connect(self):
        """just as it says"""
        pass

    def close(self):
        """just as it says"""
        pass

    def make_reusable(self):
        """call by pool to make sure this connetion reusable.
        for example, if this kind of connections support transaction,
        call rollback to be sure it's not in a started transaction.
        """
        pass


class ConnectionManager(object):
    def __init__(self, pool, conn):
        self._pool = pool
        self._conn = conn

    def __dead__(self):
        if self._pool is None or self._conn is None:
            return

        try:
            self._pool.setback(self._conn)
        finally:
            self._pool = None
            self._conn = None

    def __del__(self):
        self.__dead__()

    def __getattr__(self, name):
        return getattr(self._conn, name)


class ConnectionPool(object):
    def __init__(self, db_config, conn_cls, minnum, maxnum=None, maxidle=60, clean_interval=100):
        self._db_config = db_config
        self._conn_cls = conn_cls
        self._min = minnum
        self._max = minnum if maxnum is None else maxnum
        self._maxidle = maxidle
        self._clean_interval = clean_interval
        self._pool = []
        self._deflict = 0
        self._clean_count = 0

    def _pop_pool(self):
        return self._pool.pop(0)

    def _enter_pool(self, conn):
        for i in xrange(0, len(self._pool)):
            item = self._pool[i]
            if item.idle > conn.idle:
                self._pool.insert(i, conn)
                return

        self._pool.append(conn)

    @property
    def deep(self):
        return len(self._pool)

    @property
    def big(self):
        return len(self._pool) + self._deflict

    def _clean(self):
        if self.big <= self._min:
            plog("clean: pool not big [%d / %d]" % (self.big, self._min))
            return

        if self.deep < 1:
            plog("clean: no idle conn found [deep: %d, big: %d]" % (self.deep, self.big))
            return

        total, found = (self.big - self._min), []
        for conn in self._pool:
            if conn.idle > self._maxidle:
                found.append(conn)
                if len(found) >= total:
                    break

        if len(found) < 1:
            plog("clean: no idle conn found [deep: %d, big: %d]" % (self.deep, self.big))
            return

        # be sure to remove from pool first
        for conn in found:
            self._pool.remove(conn)

        # do close
        for conn in found:
            safe_call(conn.close)
        plog("clean: %d conns closed [deep: %d, big: %d]" % (len(found), self.deep, self.big))

    @getlock
    def get(self):
        if self.deep > 0:
            self._deflict += 1
            conn = self._pop_pool()

            if not conn.ping():
                conn.connect()

            plog("get: pop conn(%d) [deep: %d, big: %d]" % (id(conn), self.deep, self.big))
            return ConnectionManager(self, conn)

        if self.big < self._max:
            self._deflict += 1

            conn = self._conn_cls(**self._db_config)
            conn.connect()

            plog("get: new conn(%d) [deep: %d, big: %d]" % (id(conn), self.deep, self.big))
            return ConnectionManager(self, conn)

        return None

    @getlock
    def setback(self, conn):
        if conn is None:
            self._deflict -= 1
            plog("setback: conn(%d) drop because it's broken [deep: %d, big: %d]" % (id(conn), self.deep, self.big))
            return

        try:
            conn.make_reusable()
        except:
            self._deflict -= 1
            plog("setback: conn(%d) drop because it can't reuse [deep: %d, big: %d]" % (id(conn), self.deep, self.big))
            return

        self._deflict -= 1
        self._enter_pool(conn)
        plog("setback: conn(%d) return [deep: %d, big: %d]" % (id(conn), self.deep, self.big))

        # clean if need
        self._clean_count += 1
        if self._clean_count >= self._clean_interval:
            self._clean_count = 0
            self._clean()


# ########### lazy proxy  #############


def lazy(db_name, local, name):
    def wrap_func(*args, **kwargs):
        conn = local.get("conn")
        if conn is None:
            conn = getconn(db_name)
            if conn is None:
                raise EmptyPoolError()

        try:
            return getattr(conn, name)(*args, **kwargs)
        finally:
            if conn.reusable:
                safe_call(local.pop, "conn")
                conn.__dead__()
            else:
                local["conn"] = conn

    return wrap_func


class ConnectionProxy(object):
    def __init__(self, db_name):
        self._db_name = db_name
        self._local = Local()

    def __getattr__(self, name):
        return lazy(self._db_name, self._local, name)


# #######################  free to use  ########################


def getconn(db_name):
    return pools[db_name].get()


# init before concurrence
def init_pool(db_name, *args, **kwargs):
    pools[db_name] = ConnectionPool(*args, **kwargs)
