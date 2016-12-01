import os
import copy
from egcg_core.config import Configuration
from egcg_core.exceptions import ConfigError


class SplitConfiguration(Configuration):
    def __init__(self, app_type, *cfg_search_path):
        self.app_type = app_type
        super().__init__(*cfg_search_path)

    def load_config_file(self, cfg_file):
        super().load_config_file(cfg_file)
        if self.content:
            self.content = self.content[self.app_type]


class ColumnMappingConfig(Configuration):
    def __init__(self, *cfg_search_path):
        super().__init__(*cfg_search_path)

        self.column_def = self.content.pop('column_def')
        for key in self.content:
            # self.content[key] needs to be a list of strings or dicts
            for i in range(len(self.content[key])):
                if isinstance(self.content[key][i], str):
                    if self.content[key][i] in self.column_def:
                        self.content[key][i] = self.column_def[self.content[key][i]]
                    else:
                        raise ConfigError('No column definition for %s' % self.content[key][i])
                elif isinstance(self.content[key][i], dict):
                    if self.content[key][i]['column_def'] in self.column_def:
                        # take a copy of the column def and update it with the specific info
                        tmp = copy.copy(self.column_def[self.content[key][i]['column_def']])
                        tmp.update(self.content[key][i])
                        self.content[key][i] = tmp
                    else:
                        # leave the definition as it is
                        pass

class ProjectStatusConfig(Configuration):
    def __init__(self, *cfg_search_path):
        super().__init__(*cfg_search_path)

        self.status_names = self.content.get('status_names')
        self.status_order = [self.status_names.get(x) for x in self.content['status_order']]
        self.step_completed_to_status = dict(
            [(k, self.status_names.get(v)) for k, v  in self.content['step_completed_to_status'].items()]
        )
        self.step_queued_to_status = dict(
            [(k, self.status_names.get(v)) for k, v in self.content['step_queued_to_status'].items()]
        )



def _cfg_file(cfg_path):
    if cfg_path == cfg_path.upper():
        return os.getenv(cfg_path)
    elif cfg_path.startswith('~'):
        return os.path.expanduser(cfg_path)
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'etc', cfg_path)


reporting_app_config = SplitConfiguration(
    'reporting_app',
    _cfg_file('REPORTINGCONFIG'),
    _cfg_file('~/.reporting.yaml'),
    _cfg_file('example_reporting.yaml')
)
rest_config = SplitConfiguration(
    'rest_app',
    _cfg_file('REPORTINGCONFIG'),
    _cfg_file('~/.reporting.yaml'),
    _cfg_file('example_reporting.yaml')
)
schema = Configuration(_cfg_file('schema.yaml'))
col_mappings = ColumnMappingConfig(_cfg_file('column_mappings.yaml'))
project_status = ProjectStatusConfig(_cfg_file('project_status_definitions.yaml'))
