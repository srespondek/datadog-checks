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


class GetProcessessOverloadedException(Exception):
    pass


def get_logger(name=__name__):
    formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')

    logger = logging.getLogger(name)

    fileHandler = logging.FileHandler(
        '/var/log/passenger/passenger-mem-overloaded-{:%Y-%m-%d}.log'.format(datetime.now()))
    fileHandler.setFormatter(formatter)

    logger.setLevel(logging.DEBUG)
    logger.addHandler(fileHandler)

    return logger, fileHandler


class PassengerMemOverloadCheck(AgentCheck):

    def _exec_command(self, command, stdout=subprocess.PIPE, stdin=None, stderr=subprocess.DEVNULL):
        return subprocess.Popen(shlex.split(command), stdin=stdin, stdout=stdout, stderr=stderr)

    def get_processes_overloaded(self):
        try:
            cmd_pipe_1 = "sudo passenger-memory-stats"
            cmd_pipe_2 = "grep AppPreloader"
            cmd_pipe_3 = 'awk \'{{if ($4 > {0}) print $1}}\''.format(self.threshold)

            pipe_1 = self._exec_command(cmd_pipe_1)
            pipe_2 = self._exec_command(cmd_pipe_2, stdin=pipe_1.stdout)
            pipe_3 = self._exec_command(cmd_pipe_3, stdin=pipe_2.stdout)

            pids_list = pipe_3.communicate()[0].decode().split()

            if pids_list: self.log.info('List processess to detach: {}'.format(pids_list))
        except Exception as exc:
            self.log.exception(exc)
            raise GetProcessessOverloadedException
        else:
            pipe_1.stdout.close()
            pipe_2.stdout.close()
            pipe_3.stdout.close()

            return pids_list

    def _kill_process(self, pid_process):
        kill_cmd = "sudo kill -9 {}".format(pid_process)
        pipe = self._exec_command(kill_cmd, stderr=subprocess.PIPE)
        pid_status, pid_err = pipe.communicate()
        self.log.info('stdout: {}, stderr: {}'.format(pid_status, pid_err))

        if pid_err: self.log.error(pid_err)

        return pid_status

    def detach_process(self, pid_process, sig_kill=None):
        detach_cmd = "sudo passenger-config detach-process {}".format(pid_process)

        pipe = self._exec_command(detach_cmd, stderr=subprocess.PIPE)
        pid_status, pid_err = pipe.communicate()
        self.log.debug('stdout: {}, stderr: {}'.format(pid_status, pid_err))

        if pid_err and sig_kill is None:
            pid_status = self.detach_process(pid_process, sig_kill=True)

        elif pid_err and sig_kill:
            self.log.debug("SIGKILL to PID: {}".format(pid_process))
            pid_status = self._kill_process(pid_process)

        return pid_status

    def collect(self):
        self.log, fileHandler = get_logger()

        pid_processes_overloaded_list = self.get_processes_overloaded()
        detached_processes_list = [self.detach_process(pid_process) for pid_process in pid_processes_overloaded_list]

        self.log.removeHandler(fileHandler)
        fileHandler.flush()
        fileHandler.close()

        self.gauge('dd.check_passenger_mem_overload.detached_processess.count', len(detached_processes_list))

    def get_instance_config(self, instance):
        threshold = instance.get('threshold', None)

        if threshold is None:
            raise Exception('A threshold must be specified in instance cfg')

        config = {
            'threshold': threshold
        }

        return config

    def check(self, instance):
        config = self.get_instance_config(instance)
        self.threshold = config.get('threshold')

        self.collect()
