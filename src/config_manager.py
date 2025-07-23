import os
import configparser
from colorama import Fore, init
init(autoreset=True)


class ConfigManager:
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.default_config = {
            'Settings': {
                'show_keepalive_activity_control': 'False',
                'show_sequence_number_control': 'True',
                'show_receive_control': 'False',
                'show_crc_check_control': 'False',
                'LOCAL_IP': '0.0.0.0',
                'REMOTE_IP': '10.10.38.231',
                'OUT_PORT': '55001',
                'IN_PORT': '55002',
                'FRAGMENT_SIZE': '1370',
                'error_rate': '0.25',
                'STORAGE_PATH': 'files/',
                'keepalive_interval': '5',
                'keepalive_probes': '3',
                'window_size': '10',
                'check_ack_interval': '0.01',
                'auto_bind': 'False'
            }
        }
        self._load_or_create_config()

    def _load_or_create_config(self):
        if not os.path.exists(self.config_file):
            self.config.read_dict(self.default_config)
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
            print(Fore.LIGHTYELLOW_EX + 'Default configuration was created\n')
        else:
            print(Fore.LIGHTYELLOW_EX + 'Configuration configured from config file\n')
            self.config.read(self.config_file)

    def save_config(self):
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
        print(Fore.LIGHTYELLOW_EX + "Configuration saved.")

    def load_default_config(self):
        self.config.read_dict(self.default_config)
        self.save_config()
        print(Fore.LIGHTYELLOW_EX + "Default configuration loaded.")

    # Properties for config values
    @property
    def show_keepalive_activity_control(self):
        return self.config.getboolean('Settings', 'show_keepalive_activity_control')

    @show_keepalive_activity_control.setter
    def show_keepalive_activity_control(self, value):
        self.config.set('Settings', 'show_keepalive_activity_control', str(value))

    @property
    def show_sequence_number_control(self):
        return self.config.getboolean('Settings', 'show_sequence_number_control')

    @show_sequence_number_control.setter
    def show_sequence_number_control(self, value):
        self.config.set('Settings', 'show_sequence_number_control', str(value))

    @property
    def show_receive_control(self):
        return self.config.getboolean('Settings', 'show_receive_control')

    @show_receive_control.setter
    def show_receive_control(self, value):
        self.config.set('Settings', 'show_receive_control', str(value))

    @property
    def show_crc_check_control(self):
        return self.config.getboolean('Settings', 'show_crc_check_control')

    @show_crc_check_control.setter
    def show_crc_check_control(self, value):
        self.config.set('Settings', 'show_crc_check_control', str(value))

    @property
    def LOCAL_IP(self):
        return self.config.get('Settings', 'LOCAL_IP')

    @LOCAL_IP.setter
    def LOCAL_IP(self, value):
        self.config.set('Settings', 'LOCAL_IP', value)

    @property
    def REMOTE_IP(self):
        return self.config.get('Settings', 'REMOTE_IP')

    @REMOTE_IP.setter
    def REMOTE_IP(self, value):
        self.config.set('Settings', 'REMOTE_IP', value)

    @property
    def OUT_PORT(self):
        return self.config.getint('Settings', 'OUT_PORT')

    @OUT_PORT.setter
    def OUT_PORT(self, value):
        self.config.set('Settings', 'OUT_PORT', str(value))

    @property
    def IN_PORT(self):
        return self.config.getint('Settings', 'IN_PORT')

    @IN_PORT.setter
    def IN_PORT(self, value):
        self.config.set('Settings', 'IN_PORT', str(value))

    @property
    def FRAGMENT_SIZE(self):
        return self.config.getint('Settings', 'FRAGMENT_SIZE')

    @FRAGMENT_SIZE.setter
    def FRAGMENT_SIZE(self, value):
        self.config.set('Settings', 'FRAGMENT_SIZE', str(value))

    @property
    def error_rate(self):
        return self.config.getfloat('Settings', 'error_rate')

    @error_rate.setter
    def error_rate(self, value):
        self.config.set('Settings', 'error_rate', str(value))

    @property
    def STORAGE_PATH(self):
        return self.config.get('Settings', 'STORAGE_PATH')

    @STORAGE_PATH.setter
    def STORAGE_PATH(self, value):
        self.config.set('Settings', 'STORAGE_PATH', value)

    @property
    def keepalive_interval(self):
        return self.config.getint('Settings', 'keepalive_interval')

    @keepalive_interval.setter
    def keepalive_interval(self, value):
        self.config.set('Settings', 'keepalive_interval', str(value))

    @property
    def keepalive_probes(self):
        return self.config.getint('Settings', 'keepalive_probes')

    @keepalive_probes.setter
    def keepalive_probes(self, value):
        self.config.set('Settings', 'keepalive_probes', str(value))

    @property
    def window_size(self):
        return self.config.getint('Settings', 'window_size')

    @window_size.setter
    def window_size(self, value):
        self.config.set('Settings', 'window_size', str(value))

    @property
    def check_ack_interval(self):
        return self.config.getfloat('Settings', 'check_ack_interval')

    @check_ack_interval.setter
    def check_ack_interval(self, value):
        self.config.set('Settings', 'check_ack_interval', str(value))

    @property
    def auto_bind(self):
        return self.config.getboolean('Settings', 'auto_bind')

    @auto_bind.setter
    def auto_bind(self, value):
        self.config.set('Settings', 'auto_bind', str(value))


