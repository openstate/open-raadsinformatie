import os
import json
from time import sleep
from unittest import TestCase
import redis
from click.testing import CliRunner
from unittest.mock import MagicMock, patch

import ocd_backend.utils.misc
from ocd_backend.settings import SOURCES_CONFIG_FILE

class ManageTests(TestCase):
    def setUp(self):
        self.PWD = os.path.dirname(__file__)

    @patch.object(ocd_backend.utils.misc, 'load_sources_config')
    @patch.object(redis, 'StrictRedis')
    def test_process(self, redis_mock, load_sources_config_mock):
        site_name = "ori.ibabs.nameofacity"

        def redis_keys(key):
            if key == site_name:
                return [site_name]
            elif key == "_all.*":
                return ["_all.start_date", "_all.end_date"]
            else:
                raise Exception()
            
        def redis_get(key):
            if key == site_name:
                return 'all daily monthly'
            elif key == "_all.start_date":
                return "2024-10-01"
            elif key == "_all.end_date":
                return "2024-10-31"
            else:
                raise Exception()
            
            
        redis_mock.return_value.keys.side_effect = redis_keys
        redis_mock.return_value.get.side_effect = redis_get
        with open(os.path.join(self.PWD, './test_dumps/available_sources_nameofacity.json'), 'r') as f:
            available_sources = json.loads(f.read())
        load_sources_config_mock.return_value = available_sources

        from manage import extract_process

        runner = CliRunner()
        result = runner.invoke(extract_process, ["all", "--source_path", site_name, "--sources_config", SOURCES_CONFIG_FILE])
        print(f"result: {result.exit_code}, {result.output}")
        load_sources_config_mock.assert_called()

        # TODO: mock API calls, assert DB save calls and ES save calls

