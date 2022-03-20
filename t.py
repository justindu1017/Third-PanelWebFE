from ast import arg
import multiprocessing
from operator import eq
import threading
import queue
from multiprocessing import Process, Value
import time
import random

# q = queue.Queue()

# q = []


# Turn-on the worker thread.
def deq(a):
    # print("dealing with: ", a)
    while a:
        item = a.pop()
        # print(f'Working on {item}')
        # print(f'Finished {item}')
    return


def enq():
    print("start enq")
    tmp = []
    i = 11
    q = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    # t1 = multiprocessing.Process(target=deq, args=(tmp,))
    t1 = threading.Thread(target=deq, args=(tmp,))

    while True:
        if random.random() > 0.9:
            q.append(i)
            i += 1
        if not t1.is_alive() and len(q):
            tmp += q
            q = []
            t1.start()
            print("passing", tmp)
            # t1 = multiprocessing.Process(target=deq, args=(tmp,))
            t1 = threading.Thread(target=deq, args=(tmp,))

            tmp = []
        # print(tmp)

# def pp():
#     t1 = threading.Thread(target=deq).start()
    # t2 = threading.Thread(target=enq).start()


# Send thirty task requests to the worker.
# def foo():
#     for item in range(30):
#         q.append(item)


if __name__ == '__main__':
    # p = Process(target=checkHealth, args=(5, 2,))
    # foo()
    p = Process(target=enq)
    p.start()
