Known Issues
============

1. After benchmarking has finished and dtControl prints the message "All benchmarks completed. Shutting down dtControl.", a RuntimeError might occur.

```
Traceback (most recent call last):
  File "/home/pranav/anaconda3/envs/ali/lib/python3.6/site-packages/tqdm/_tqdm.py", line 931, in __del__
    self.close()
  File "/home/pranav/anaconda3/envs/ali/lib/python3.6/site-packages/tqdm/_tqdm.py", line 1133, in close
    self._decr_instances(self)
  File "/home/pranav/anaconda3/envs/ali/lib/python3.6/site-packages/tqdm/_tqdm.py", line 496, in _decr_instances
    cls.monitor.exit()
  File "/home/pranav/anaconda3/envs/ali/lib/python3.6/site-packages/tqdm/_monitor.py", line 52, in exit
    self.join()
  File "/home/pranav/anaconda3/envs/ali/lib/python3.6/threading.py", line 1053, in join
    raise RuntimeError("cannot join current thread")
RuntimeError: cannot join current thread
```

This is a known bug in tqdm (see https://github.com/tqdm/tqdm/issues/613).
