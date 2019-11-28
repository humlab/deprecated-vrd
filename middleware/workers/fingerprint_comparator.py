from rq import Connection, Queue, Worker

from . import redis_connection


listen = ['compare']
COMPARE_QUEUE_NAME = listen[0]


def start():
    with Connection(redis_connection):
        worker = Worker(list(map(Queue, listen)))
        worker.work()
