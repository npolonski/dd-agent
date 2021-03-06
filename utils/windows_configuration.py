# (C) Datadog, Inc. 2010-2017
# All rights reserved
# Licensed under Simplified BSD License (see LICENSE)
import logging
import os
import shutil
import tempfile
try:
    import _winreg
except ImportError:
    pass


WINDOWS_REG_PATH = 'SOFTWARE\\Datadog\\Datadog Agent'
SDK_REG_PATH = WINDOWS_REG_PATH + '\\Integrations\\'


log = logging.getLogger(__name__)


def get_registry_conf(agentConfig):
    registry_conf = {}
    try:
        with _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                             WINDOWS_REG_PATH) as reg_key:
            for attribute in ['api_key', 'tags', 'hostname']:
                option = _winreg.QueryValueEx(reg_key, attribute)[0]
                if option != '':
                    registry_conf[attribute] = option
    except (ImportError, WindowsError) as e:
        log.error('Unable to get config keys from Registry: %s', e)

    return registry_conf

def get_windows_sdk_check(name):
    sdk_reg_path = SDK_REG_PATH + name
    try:
        with _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, sdk_reg_path) as reg_key:
            directory = _winreg.QueryValueEx(reg_key, "InstallPath")[0]
            return os.path.join(directory, 'Integrations', name, 'check.py')
    except WindowsError:
        pass
    return None

def update_conf_file(registry_conf, config_path):
    config_dir = os.path.dirname(config_path)
    config_bkp = os.path.join(config_dir, 'datadog.conf.bkp')
    try:
        if os.path.exists(config_bkp):
            os.remove(config_bkp)
        shutil.copy(config_path, config_bkp)
    except OSError as e:
        log.debug('Unable to back up datadog.conf: %s', e)
    temp_config, temp_config_path = tempfile.mkstemp(prefix='config-', text=True)
    temp_config = os.fdopen(temp_config, 'w')
    log.debug('Temporary conf path: %s', temp_config_path)
    with open(config_path, 'r') as f:
        for line in f:
            for k, v in registry_conf.iteritems():
                if k + ":" in line:
                    line = '{}: {}\n'.format(k, v)
            temp_config.write(line)
    temp_config.close()
    try:
        os.remove(config_path)
        os.rename(temp_config_path, config_path)
    except OSError as e:
        log.exception('Unable to save new datadog.conf')
    else:
        log.debug('Successfully saved the new datadog.conf')
