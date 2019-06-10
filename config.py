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


class DefinitionMappingConfig(Configuration):
    def __init__(self, *cfg_search_path, definition_key):
        super().__init__(*cfg_search_path)
        self.def_key = definition_key

        self.element_definitions = self.content.pop(self.def_key)
        for key in self.content:
            # self.content[key] needs to be a list of strings or dicts
            for i in range(len(self.content[key])):
                if isinstance(self.content[key][i], str):
                    definition_name = self.content[key][i]
                    if self.content[key][i] in self.element_definitions:
                        self.content[key][i] = self.element_definitions[self.content[key][i]]
                    else:
                        raise ConfigError('No column definition for %s' % self.content[key][i])
                elif isinstance(self.content[key][i], dict):
                    definition_name = self.content[key][i][self.def_key]
                    if self.content[key][i][self.def_key] in self.element_definitions:
                        # take a copy of the column def and update it with the specific info
                        tmp = copy.copy(self.element_definitions[self.content[key][i][self.def_key]])
                        tmp.update(self.content[key][i])
                        self.content[key][i] = tmp
                    else:
                        # leave the definition as it is
                        pass
                else:
                    raise ConfigError('Invalid column definition %s' % self.content[key][i])

                self.content[key][i]['name'] = definition_name


class ProjectStatusConfig(Configuration):
    def __init__(self, *cfg_search_path):
        super().__init__(*cfg_search_path)

        self.started_steps = self.content.get('started_steps')
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
col_mappings = DefinitionMappingConfig(_cfg_file('column_mappings.yaml'), definition_key='column_def')
chart_metrics_mappings = DefinitionMappingConfig(_cfg_file('charts_metrics_mappings.yaml'), definition_key='metrics_def')
project_status = ProjectStatusConfig(_cfg_file('project_status_definitions.yaml'))
