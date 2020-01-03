import multiprocessing
import os
import signal
import time

import psutil

import dtcontrol.globals

def is_windows():
    return os.name == 'nt'

def use_multiprocessing_for_timeout():
    return is_windows()

def _call_and_return_in_list(obj, method, return_list, *args):
    getattr(obj, method)(*args)
    return_list[0] = obj

def call_with_timeout(obj, method, *args, timeout=60):
    """
    Calls a method on an object and stops the execution once the time limit is reached.
    :param obj: the object on which the method is to be called
    :param method: the method to be called on the object
    :param timeout: the time limit
    :param args: the arguments to be passed to the method
    :return: the modified object, True if the call was successful and False otherwise, and the actual time needed
    """

    if use_multiprocessing_for_timeout():
        with multiprocessing.Manager() as manager:
            return_list = manager.list(range(1))
            p = multiprocessing.Process(target=_call_and_return_in_list, args=(obj, method, return_list, *args))
            start = time.time()
            p.start()
            p.join(timeout)
            if p.is_alive():
                p.terminate()
                p.join()
                kill_oc1()
                return obj, False, time.time() - start
            return return_list[0], True, time.time() - start
    else:
        def raise_timeout(signum, frame):
            raise TimeoutError

        signal.signal(signal.SIGALRM, raise_timeout)
        signal.alarm(timeout)
        start = time.time()
        try:
            getattr(obj, method)(*args)
            return obj, True, time.time() - start
        except TimeoutError:
            kill_oc1()
            return obj, False, time.time() - start
        finally:
            signal.signal(signal.SIGALRM, signal.SIG_IGN)

def kill_oc1():
    if dtcontrol.globals.oc1_pid is not None:
        psutil.Process(dtcontrol.globals.oc1_pid).terminate()
        dtcontrol.globals.oc1_pid = None
