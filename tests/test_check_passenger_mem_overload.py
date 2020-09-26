from unittest import TestCase
from unittest.mock import patch

from dd_check_passenger_mem_overload import PassengerMemOverloadCheck, GetProcessessOverloadedException


class TestPassengerMemOverloadCheck(TestCase):

    def setUp(self):
        super().setUp()
        self.passenger_mem_check = PassengerMemOverloadCheck()
        self.passenger_mem_check.threshold = 900

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
        mock_exec_cmd().stdout.close.assert_called()

    def test_get_processess_overloaded_failed_caused_by_exception(self):
        # given
        test_exception_err = 'test exception'

        # when / then
        with self.assertRaises(GetProcessessOverloadedException):
            with patch.object(self.passenger_mem_check, '_exec_command') as mock_exec_cmd:
                mock_exec_cmd().communicate.side_effect = Exception(test_exception_err)
                self.passenger_mem_check.get_processes_overloaded()

        mock_exec_cmd().communicate.assert_called_once()
        mock_exec_cmd().stdout.close.not_called()
