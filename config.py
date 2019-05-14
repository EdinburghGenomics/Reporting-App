import os
import copy
from egcg_core.config import Configuration
from egcg_core.exceptions import ConfigError


class SplitConfiguration(Configuration):
    def __init__(self, app_type, *cfg_search_path):
        self.app_type = app_type
        super().__init__(*cfg_search_path)

    def load_config_file(self, *search_path, env_var=None):
        super().load_config_file(*search_path, env_var=env_var)
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
                    column_name = self.content[key][i]
                    if self.content[key][i] in self.column_def:
                        self.content[key][i] = self.column_def[self.content[key][i]]
                    else:
                        raise ConfigError('No column definition for %s' % self.content[key][i])
                elif isinstance(self.content[key][i], dict):
                    column_name = self.content[key][i]['column_def']
                    if self.content[key][i]['column_def'] in self.column_def:
                        # take a copy of the column def and update it with the specific info
                        tmp = copy.copy(self.column_def[self.content[key][i]['column_def']])
                        tmp.update(self.content[key][i])
                        self.content[key][i] = tmp
                    else:
                        # leave the definition as it is
                        pass
                else:
                    raise ConfigError('Invalid column definition %s' % self.content[key][i])

                self.content[key][i]['name'] = column_name


class ProjectStatusConfig(Configuration):
    def __init__(self, *cfg_search_path):
        super().__init__(*cfg_search_path)

        self.started_steps = self.content.get('started_steps')
        self.qc_finished_steps = self.content.get('qc_steps')
        self.status_names = self.content.get('status_names')
        # Replace variable names in a list
        self.status_order = [self.status_names.get(x) for x in self.content['status_order']]
        # Replace variable names in a dict
        for section in [
            'step_completed_to_status',
            'step_queued_to_status',
            'additional_step_completed',
            'library_type_step_completed',
            'library_planned_alias',
            'protocol_names'
        ]:
            transformed_section = dict(
                [(k, self.status_names.get(v)) for k, v in self.content[section].items()]
            )
            setattr(self, section, transformed_section)
        # finished steps contains the name of all steps that provided status finished
        self.finished_steps = [k for k, v in self.step_completed_to_status.items() if v == 'finished']
        # reverse from step_completed_to_status
        self.status_to_step_completed = dict((name, []) for name in self.status_names)
        for k, v in self.content['step_completed_to_status'].items():
            self.status_to_step_completed[v].append(k)

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
