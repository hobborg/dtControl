import multiprocessing
import subprocess

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
    :return: The modified object and True if the call was successful and False otherwise
    """

    # this slight hack is used to properly terminate the OC1Wrapper, which needs to spawn a child process itself
    if hasattr(obj, 'get_{}_command'.format(method)):
        command = getattr(obj, 'get_{}_command'.format(method))(*args)
        with open(obj.output_file, 'w+') as out:
            p = subprocess.Popen(command.split(' '), stdout=out)
            try:
                p.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                p.kill()
                return obj, False
        getattr(obj, '{}_command_called'.format(method))()
        return obj, True
    else:
        with multiprocessing.Manager() as manager:
            return_list = manager.list(range(1))
            p = multiprocessing.Process(target=_call_and_return_in_list, args=(obj, method, return_list, *args))
            p.start()
            p.join(timeout)
            if p.is_alive():
                p.terminate()
                p.join()
                return obj, False
            return return_list[0], True
