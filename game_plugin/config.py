import os
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

DEFAULT_IP = "127.0.0.1"
DEFAULT_PORT = 20777
DEFAULT_UPDATE_RATE = 30

def load_config(ini_path):
    config = configparser.ConfigParser()

    defaults = {
        'ip': DEFAULT_IP,
        'port': str(DEFAULT_PORT),
        'update_rate_hz': str(DEFAULT_UPDATE_RATE)
    }

    if os.path.exists(ini_path):
        try:
            config.read(ini_path)
        except:
            pass

    result = {}

    try:
        result['ip'] = config.get('UDP', 'ip')
    except:
        result['ip'] = DEFAULT_IP

    try:
        result['port'] = int(config.get('UDP', 'port'))
    except:
        result['port'] = DEFAULT_PORT

    try:
        result['update_rate_hz'] = int(config.get('GENERAL', 'update_rate_hz'))
    except:
        result['update_rate_hz'] = DEFAULT_UPDATE_RATE

    return result
