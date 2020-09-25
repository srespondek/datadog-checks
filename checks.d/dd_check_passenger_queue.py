import json
import logging
import shlex
import subprocess
from datetime import datetime

try:
    from datadog_checks.base import AgentCheck
except ImportError:
    from checks import AgentCheck

# content of the special variable __version__ will be shown in the Agent status page
__version__ = "1.0.0"


class GetRequestsException(Exception):
    pass


class GetQueueSizeException(Exception):
    pass


def get_logger(name=__name__):
    formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')

    logger = logging.getLogger(name)

    fileHandler = logging.FileHandler(
        '/var/log/passenger/passenger-status-requests-{:%Y-%m-%d}.log'.format(datetime.now()))
    fileHandler.setFormatter(formatter)

    logger.setLevel(logging.DEBUG)
    logger.addHandler(fileHandler)

    return logger, fileHandler


class PassengerQueueCheck(AgentCheck):
    CRIT_REQ_CNT = 800
    CMD_1 = "sudo passenger-status"
    CMD_2 = """awk /"Requests in queue"/'{print $4 }'"""
    CMD_3 = "sudo passenger-status --show=requests --no-header"

    def _exec_command(self, command, stdin=None, stderr=None):
        return subprocess.Popen(shlex.split(command), stdin=stdin, stdout=subprocess.PIPE, stderr=stderr)

    def _convert_to_json(self, pipe):
        return json.loads(pipe)

    def _get_queue_size(self):
        try:
            pipe_1 = self._exec_command(self.CMD_1)
            pipe_2 = self._exec_command(self.CMD_2, stdin=pipe_1.stdout)
            data = pipe_2.communicate()[0].decode().split()[0]
        except Exception as exc:
            self.log.exception(exc)
            raise GetQueueSizeException
        else:
            pipe_1.stdout.close()
            pipe_2.stdout.close()

            return int(data)

    def _get_requests_from_queue(self):
        try:
            pipe_3 = self._exec_command(self.CMD_3)
            data = pipe_3.communicate()[0]
            data_in_json = self._convert_to_json(data)
        except Exception as exc:
            self.log.exception(exc)
            raise GetRequestsException
        else:
            pipe_3.stdout.close()

            return data_in_json

    def log_if_urgent(self, queue_size, requests_details):
        if queue_size > self.CRIT_REQ_CNT:
            self.log.debug("Queue_size: {}".format(queue_size))
            self.log.debug("Requests details : {}".format(requests_details))

    def collect(self):
        self.log, fileHandler = get_logger()

        queue_size = self._get_queue_size()
        requests_details_in_json = self._get_requests_from_queue()
        self.log_if_urgent(queue_size, requests_details_in_json)

        self.log.removeHandler(fileHandler)
        fileHandler.flush()
        fileHandler.close()

        self.gauge('dd.check_passenger_queue.requests.count', queue_size)

    def check(self, instance):
        self.collect()
