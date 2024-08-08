import json
import os
import sys


class ConfigManager:
    def __init__(self, config_file=None):
        if config_file is None:
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_file = os.path.join(base_dir, '..', '..', '.config', 'config.json')
        else:
            self.config_file = config_file
        self.config_data = {}

    def load_config(self, file_path=None):
        if file_path is None:
            file_path = self.config_file

        try:
            with open(file_path, 'r') as file:
                content = file.read()
                if content.strip():
                    self.config_data = json.loads(content)
                else:
                    raise ValueError("Empty configuration file")
        except (json.JSONDecodeError, ValueError, FileNotFoundError) as e:
            self.config_data = self.default_config()
            self.save_config()
        return self.config_data

    def save_config(self):
        """Write the configuration data to disk."""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as file:
            json.dump(self.config_data, file, indent=4)

    def default_config(self):
        return {
            'audience_src': '',
            'audience_dest': '',
            'cost_src': '',
            # OTHERS HERE
        }

    def update_config(self, key, value):
        if isinstance(value, str) and '\\' in value:
            value = value.replace('\\', '\\\\')
        self.config_data[key] = value
        self.save_config()

    def get_config(self):
        return self.config_data
