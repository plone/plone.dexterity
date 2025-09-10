def synchronized(lock):
    """Decorate a method with this and pass in a threading.Lock object to
    ensure that a method is synchronised over the given lock.
    """

    def wrap(f):
        def synchronized_function(*args, **kw):
            lock.acquire()
            try:
                return f(*args, **kw)
            finally:
                lock.release()

        return synchronized_function

    return wrap
