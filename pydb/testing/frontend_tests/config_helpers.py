# coding=utf-8
import os


def get_config_file_path(testcase_folder):
    config_file_path = os.path.join(testcase_folder, 'pydb.conf')
    return config_file_path


def clear_settings(testcase_folder):
    config_file_path = get_config_file_path(testcase_folder)
    os.unlink(config_file_path)


def add_setting(testcase_folder, section_name, name, value):
    config_file_path = get_config_file_path(testcase_folder)
    with open(config_file_path, "a") as cfg_file:
        cfg_file.write("[{}]\n".format(section_name))
        cfg_file.write("{} = {}\n".format(name, value))

