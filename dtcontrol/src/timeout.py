import multiprocessing
import os
import signal
import subprocess
import time


def is_windows():
    return os.name == 'nt'


def use_multiprocessing():
    return is_windows()


def _call_and_return_in_list(obj, method, return_list, *args):
    getattr(obj, method)(*args)
    return_list[0] = obj


def call_with_timeout(obj, method, *args, timeout=60):
    """
    Calls a method on an object and stops the execution once the time limit is reached.
    :param obj: The object on which the method is to be called
    :param method: The method to be called on the object
    :param timeout: The time limit
    :param args: The arguments to be passed to the method
    :return: The modified object, True if the call was successful and False otherwise, and the actual time needed
    """

    # this slight hack is used to properly terminate the OC1Wrapper, which needs to spawn a child process itself
    if hasattr(obj, 'get_{}_command'.format(method)):
        command = getattr(obj, 'get_{}_command'.format(method))(*args)
        with open(obj.output_file, 'w+') as out:
            start = time.time()
            p = subprocess.Popen(command.split(' '), stdout=out, stderr=out)
            try:
                p.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                p.kill()
                return obj, False, time.time() - start
        getattr(obj, '{}_command_called'.format(method))()
        return obj, True, time.time() - start
    else:
        if use_multiprocessing():
            with multiprocessing.Manager() as manager:
                return_list = manager.list(range(1))
                p = multiprocessing.Process(target=_call_and_return_in_list, args=(obj, method, return_list, *args))
                start = time.time()
                p.start()
                p.join(timeout)
                if p.is_alive():
                    p.terminate()
                    p.join()
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
                return obj, False, time.time() - start
            finally:
                signal.signal(signal.SIGALRM, signal.SIG_IGN)
