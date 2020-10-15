from unittest import TestCase
from unittest.mock import patch

from dd_check_files_descriptors import FilesDescriptorsCheck, GetDeletedStatsException


class TestFileDescMonCheck(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()

        self.file_descriptors_check = FilesDescriptorsCheck()
        self.collected_metrics = {}

    def tearDown(self):
        super().tearDown()
        patch.stopall()

    def test_get_size_of_deleted_files_successfully(self):
        # given
        expected_result = 3213

        # when
        with patch.object(self.file_descriptors_check, '_exec_command') as mock_exec_cmd:
            mock_exec_cmd().communicate.return_value = (b'3213\n', None)
            result = self.file_descriptors_check.get_size_of_deleted_files()

        # then
        self.assertEqual(expected_result, result)

    def test_get_size_of_deleted_files_unsuccessfully_caused_exception(self):
        # given
        test_exception_err = 'test exception'

        # when
        with self.assertRaises(GetDeletedStatsException):
            with patch.object(self.file_descriptors_check, '_exec_command') as mock_exec_cmd:
                mock_exec_cmd().communicate.side_effect = Exception(test_exception_err)
                self.file_descriptors_check.get_size_of_deleted_files()

        mock_exec_cmd().communicate.assert_called_once()
        mock_exec_cmd().stdout.close.not_called()

    def test_collect_successfully_1(self):
        # given
        self.file_descriptors_check.init_config = {'mon_user_list': ['testing-user-1','testing-user-2']}
        self.file_descriptors_check.metrics_collected = {
            'global': {},
            'local': {}
        }
        expected_result = {
            'global': {'dd.check_files_descriptors.global.current_size.count': 1000,
                       'dd.check_files_descriptors.global.deleted_files.count': 2345,
                       'dd.check_files_descriptors.global.limit_size.count': 999999},
            'local': {'dd.check_files_descriptors.local.testing-user-1.deleted_files.count': 555,
                      'dd.check_files_descriptors.local.testing-user-2.deleted_files.count': 235}
        }

        # when
        with patch.object(self.file_descriptors_check, '_get_global_stats') as mock_glob_stats:
            with patch.object(self.file_descriptors_check, 'get_size_of_deleted_files') as mock_del_files:
                mock_glob_stats.return_value = ['1000', '0', '999999']
                mock_del_files.side_effect = [2345, 555, 235]
                self.file_descriptors_check.collect()

        self.assertEqual(self.file_descriptors_check.metrics_collected, expected_result)

    def test_collect_successfully_2(self):
        # given
        self.file_descriptors_check.init_config = {'mon_user_list': []}
        self.file_descriptors_check.metrics_collected = {
            'global': {},
            'local': {}
        }

        expected_result = {
            'global': {'dd.check_files_descriptors.global.current_size.count': 5020,
                       'dd.check_files_descriptors.global.deleted_files.count': 10,
                       'dd.check_files_descriptors.global.limit_size.count': 88888},
            'local': {}}

        # when
        with patch.object(self.file_descriptors_check, '_get_global_stats') as mock_glob_stats:
            with patch.object(self.file_descriptors_check, 'get_size_of_deleted_files') as mock_del_files:
                mock_glob_stats.return_value = ['5020', '0', '88888']
                mock_del_files.return_value = 10
                self.file_descriptors_check.collect()

        # then
        self.assertEqual(self.file_descriptors_check.metrics_collected, expected_result)
