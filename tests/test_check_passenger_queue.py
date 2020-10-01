import json
from unittest import TestCase
from unittest.mock import patch

from dd_check_passenger_queue import PassengerQueueCheck, GetQueueSizeException, GetRequestsException
from tests.test_samples.queue_requests_samples import TEST_REQUESTS


class TestPassengerQueueCheck(TestCase):

    def setUp(self):
        super().setUp()

        self.patch_logging = patch('dd_check_passenger_queue.logging').start()
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
        mock_exec_cmd().communicate.assert_called_once()

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

    def test_get_requests_details_successfully(self):
        # given
        queue_req_sample = TEST_REQUESTS
        expected_result = json.loads(TEST_REQUESTS[0])

        # when
        with patch.object(self.passenger_queue_check, '_exec_command') as mock_exec_cmd:
            mock_exec_cmd().communicate.return_value = queue_req_sample
            result = self.passenger_queue_check.get_requests_details()

        # then
        self.assertEqual(expected_result, result)
        mock_exec_cmd().communicate.assert_called_once()

    def test_get_requests_details_unsuccessfully_caused_exception(self):
        # given
        test_exception_err = 'test exception'

        # when
        with self.assertRaises(GetRequestsException):
            with patch.object(self.passenger_queue_check, '_exec_command') as mock_exec_cmd:
                mock_exec_cmd().communicate.side_effect = Exception(test_exception_err)
                self.passenger_queue_check.get_requests_details()

        # then
        mock_exec_cmd().communicate.assert_called_once()
        mock_exec_cmd().stdout.close.not_called()

    def test_collect_data_successfully_with_queue_above_crit_threshold(self):
        # given / when
        with patch.object(self.passenger_queue_check, 'get_queue_size', return_value=900) as mock_queue_size:
            with patch.object(self.passenger_queue_check, 'get_requests_details') as mock_requests_details:
                self.passenger_queue_check.collect()

        # then
        self.assertEqual(self.passenger_queue_check.log.debug.call_count, 2)
        mock_queue_size.assert_called_once()
        mock_requests_details.assert_called_once()

    def test_collect_data_successfully_without_log_caused_normal_queue_size(self):
        # given / when
        with patch.object(self.passenger_queue_check, 'get_queue_size', return_value=100) as mock_queue_size:
            with patch.object(self.passenger_queue_check, 'get_requests_details') as mock_requests_details:
                self.passenger_queue_check.collect()

        # then
        self.assertEqual(self.passenger_queue_check.log.debug.call_count, 0)
        mock_queue_size.assert_called_once()
        mock_requests_details.assert_called_once()
