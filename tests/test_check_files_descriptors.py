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

    def test_collect_successfully_without_users(self):
        # given
        self.file_descriptors_check.init_config = {'mon_user_list': []}

        expected_collected_metrics = {
            'global': {'dd.check_files_descriptors.global.current_size.count': 1000,
                       'dd.check_files_descriptors.global.deleted_files.count': 10,
                       'dd.check_files_descriptors.global.limit_size.count': 66666},
            'local': {}
        }

        # when
        with patch.object(self.file_descriptors_check, '_get_global_stats') as mock_glob_stats:
            with patch.object(self.file_descriptors_check, 'get_size_of_deleted_files') as mock_del_files:
                mock_glob_stats.return_value = ['1000', '0', '66666']
                mock_del_files.side_effect = [10]
                self.file_descriptors_check.collect()

        # then
        self.assertDictEqual(self.file_descriptors_check.metrics_collected, expected_collected_metrics)


    def test_collect_successfully_with_two_users(self):
        # given
        self.file_descriptors_check.init_config = {'mon_user_list': ['test1', 'test2']}

        expected_collected_metrics = {
            'global': {'dd.check_files_descriptors.global.current_size.count': 20000,
                       'dd.check_files_descriptors.global.deleted_files.count': 20,
                       'dd.check_files_descriptors.global.limit_size.count': 333333},
            'local': {'dd.check_files_descriptors.local.test1.deleted_files.count': 25,
                      'dd.check_files_descriptors.local.test2.deleted_files.count': 30}
        }

        # when
        with patch.object(self.file_descriptors_check, '_get_global_stats') as mock_glob_stats:
            with patch.object(self.file_descriptors_check, 'get_size_of_deleted_files') as mock_del_files:
                mock_glob_stats.return_value = ['20000', '0', '333333']
                mock_del_files.side_effect = [20, 25, 30]
                self.file_descriptors_check.collect()

        # then
        self.assertDictEqual(self.file_descriptors_check.metrics_collected, expected_collected_metrics)