import logging
import shlex
import subprocess
from functools import wraps
from datetime import datetime

from datadog_checks.base import AgentCheck

# content of the special variable __version__ will be shown in the Agent status page
__version__ = "1.0.0"


class GetDeletedStatsException(Exception):
    pass


def get_logger(name=__name__):
    formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')

    logger = logging.getLogger(name)

    fileHandler = logging.FileHandler(
        '/var/log/datadog/dd-check-files-descriptors-{:%Y-%m-%d}.log'.format(datetime.now()))
    fileHandler.setFormatter(formatter)

    logger.setLevel(logging.DEBUG)
    logger.addHandler(fileHandler)

    return logger, fileHandler


def log_wrapper(method):
    @wraps(method)
    def _impl(self, *method_args, **method_kwargs):
        self.log, fileHandler = get_logger()
        method_output = method(self, *method_args, **method_kwargs)
        self.log.removeHandler(fileHandler)
        fileHandler.flush()
        fileHandler.close()
        return method_output

    return _impl


class FilesDescriptorsCheck(AgentCheck):
    metrics_collected = {
        'global': {},
        'local': {}
    }

    @staticmethod
    def _exec_command(command, stdout=subprocess.PIPE, stdin=None, stderr=None):
        return subprocess.Popen(shlex.split(command), stdin=stdin, stdout=stdout, stderr=stderr)

    def _get_init_config(self):
        user_list = self.init_config.get('mon_user_list', [])

        init_config = {
            'mon_user_list': user_list
        }

        return init_config

    @staticmethod
    def _get_size_of_current_open_files(data_stats):
        return int(data_stats[0])

    @staticmethod
    def _get_limit_size(data_stats):
        return int(data_stats[2])

    def _get_global_stats(self):
        with open('/proc/sys/fs/file-nr', 'r') as fh:
            data_stats = fh.readline().split()
        return data_stats


    def _set_metric(self, range, path, value):
        self.metrics_collected[range].setdefault(path, value)
        self.log.debug(f'_set_metric {range}: {path}:{value}')


    def get_size_of_deleted_files(self, user=None):
        cmd_1 = f"sudo lsof -u {user}" if user else "sudo lsof"
        cmd_2 = "grep deleted"
        cmd_3 = "wc -l"
        try:
            pipe_1 = self._exec_command(command=cmd_1)
            pipe_2 = self._exec_command(command=cmd_2, stdin=pipe_1.stdout)
            pipe_3 = self._exec_command(command=cmd_3, stdin=pipe_2.stdout)

            stats_cnt = pipe_3.communicate()[0].decode()
        except Exception as exc:
            self.log.exception(str(exc))
            raise GetDeletedStatsException
        else:
            return int(stats_cnt)


    def collect(self):
        self.init_config = self._get_init_config()
        users = self.init_config.get('mon_user_list')
        fd_data_stats = self._get_global_stats()

        self._set_metric(range='global', path='dd.check_files_descriptors.global.current_size.count',
                         value=self._get_size_of_current_open_files(fd_data_stats))
        self._set_metric(range='global', path='dd.check_files_descriptors.global.limit_size.count',
                         value=self._get_limit_size(fd_data_stats))
        self._set_metric(range='global', path='dd.check_files_descriptors.global.deleted_files.count',
                         value=self.get_size_of_deleted_files())
        [self._set_metric(range='local', path=f'dd.check_files_descriptors.local.{user}.deleted_files.count',
                          value=self.get_size_of_deleted_files(user)) for user in users]

    def report(self):
        [self.log.debug(f'report: {metric_key}{metric_value}') for region in ('global', 'local') for metric_key, metric_value in
         self.metrics_collected[region].items()]
        [self.gauge(metric_key, metric_value) for region in ('global', 'local') for metric_key, metric_value in
         self.metrics_collected[region].items()]

    @log_wrapper
    def check(self, instance):
        self.collect()
        self.report()
