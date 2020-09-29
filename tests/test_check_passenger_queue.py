from unittest import TestCase
from unittest.mock import patch

from dd_check_passenger_queue import PassengerQueueCheck, GetQueueSizeException, GetRequestsException

class TestPassengerQueueCheck(TestCase):

    def setUp(self):
        super().setUp()

        self.passenger_queue_check = PassengerQueueCheck()

    def tearDown(self):
        super().tearDown()
        patch.stopall()

    def test_get_queue_size_successfully(self):
        # given
        expected_result = 25

        # when
        with patch.object(self.passenger_queue_check, '_exec_command') as mock_exec_cmd:
            mock_exec_cmd().communicate.return_value = (b'25\n', None)
            result = self.passenger_queue_check.get_queue_size()

        # then
        self.assertEqual(result, expected_result)

    def test_get_queue_size_unsuccessfully_caused_exception(self):
        # given
        test_exception_err = 'test exception'

        # when
        with self.assertRaises(GetQueueSizeException):
            with patch.object(self.passenger_queue_check, '_exec_command') as mock_exec_cmd:
                mock_exec_cmd().communicate.side_effect = Exception(test_exception_err)
                self.passenger_queue_check.get_queue_size()

        # then
        mock_exec_cmd().communicate.assert_called_once()
        mock_exec_cmd().stdout.close.not_called()