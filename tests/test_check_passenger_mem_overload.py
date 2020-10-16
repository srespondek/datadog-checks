from unittest import TestCase
from unittest.mock import patch

from dd_check_passenger_mem_overload import PassengerMemOverloadCheck, GetProcessessOverloadedException, \
    GetInstanceConfigException


class TestPassengerMemOverloadCheck(TestCase):

    def setUp(self):
        super().setUp()
        self.passenger_mem_check = PassengerMemOverloadCheck()
        self.passenger_mem_check.threshold = 900

        self.patch_logging = patch('dd_check_passenger_mem_overload.logging').start()

    def tearDown(self):
        super().tearDown()
        patch.stopall()

    def test_get_processes_overloaded_successfully(self):
        # given
        test_overloaded_pid_list = ['1111111']

        # when
        with patch.object(self.passenger_mem_check, '_exec_command') as mock_exec_cmd:
            mock_exec_cmd().communicate.return_value = (b'1111111\n', None)
            result = self.passenger_mem_check.get_processes_overloaded()

        # then
        self.assertEqual(len(mock_exec_cmd.call_args_list), 4)
        self.assertEqual(test_overloaded_pid_list, result)
        mock_exec_cmd().communicate.assert_called_once()

    def test_get_processess_overloaded_failed_caused_by_exception(self):
        # given
        test_exception_err = 'test exception'

        # when / then
        with self.assertRaises(GetProcessessOverloadedException):
            with patch.object(self.passenger_mem_check, '_exec_command') as mock_exec_cmd:
                mock_exec_cmd().communicate.side_effect = Exception(test_exception_err)
                self.passenger_mem_check.get_processes_overloaded()

        mock_exec_cmd().communicate.assert_called_once()

    def test_detach_process_successfully(self):
        # given
        expected_result = b'Process 20474 detached.\n'

        # when
        with patch.object(self.passenger_mem_check, '_exec_command') as mock_exec_cmd:
            mock_exec_cmd().communicate.return_value = (b'Process 20474 detached.\n', None)
            result = self.passenger_mem_check.detach_process(pid_process='20474', sig_kill=None)

        # then
        self.assertEqual(result, expected_result)
        mock_exec_cmd().communicate.assert_called_once()

    def test_detach_process_successfully_after_retrying(self):
        # given
        expected_result = b'Process 16821 detached.\n'

        # when
        with patch.object(self.passenger_mem_check, '_exec_command') as mock_exec_cmd:
            mock_exec_cmd().communicate.side_effect = [
                (b'', b'Could not detach process 16821.\n'),
                (b'Process 16821 detached.\n', None)
            ]
            result = self.passenger_mem_check.detach_process(pid_process='16821', sig_kill=None)

        # then
        self.assertEqual(result, expected_result)
        self.assertEqual(mock_exec_cmd().communicate.call_count, 2)

    def test_detach_process_successfully_after_signal_kill(self):
        # given
        expected_result = 'Process 16821 killed'
        # when
        with patch.object(self.passenger_mem_check, '_exec_command') as mock_exec_cmd:
            mock_exec_cmd().communicate.side_effect = [
                (b'', b'Could not detach process 16821.\n'),
                (b'', b'Could not detach process 16821.\n'),
                (b'', b'')
            ]
            result = self.passenger_mem_check.detach_process(pid_process='16821', sig_kill=None)

        # then
        self.assertEqual(result, expected_result)
        self.assertEqual(mock_exec_cmd().communicate.call_count, 3)

    def test_collect_successfully(self):
        # given / when
        with patch.object(self.passenger_mem_check, 'get_processes_overloaded',
                          return_value=['11111', '22222']) as mock_get_processess_overloaded:
            with patch.object(self.passenger_mem_check, 'detach_process') as mock_detach_process:
                mock_detach_process.side_effect = ['Process 11111 detached.\n', 'Process 22222 detached.\n']
                self.passenger_mem_check.collect()

        # then
        mock_get_processess_overloaded.assert_called_once()
        self.assertEqual(mock_detach_process.call_count, 2)

    def test_get_instance_config_successfully(self):
        # given
        instance = {
            'threshold': '900'
        }

        # when
        result = self.passenger_mem_check.get_instance_config(instance)

        # then
        self.assertEqual(result, instance)

    def test_get_instance_config_unsuccessfully_caused_exception(self):
        # given
        instance = dict()

        # when
        with self.assertRaises(GetInstanceConfigException) as exc:
            self.passenger_mem_check.get_instance_config(instance)

        # then
        self.assertEqual(exc.exception.message, 'A threshold must be specified in cfg')
