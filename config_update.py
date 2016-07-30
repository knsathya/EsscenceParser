import logging
import sys
import argparse
import textwrap
import os

loglevel = logging.DEBUG
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    config_file_list = []
    config_reg_list = []
    config_file_dict = {}
    update_file_list = []
    update_reg_list = []
    update_file_dict = {}

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', action="store_true", help="update the config file", dest="update", default=False)
    parser.add_argument('--config-file', metavar='config-file', type=argparse.FileType('r+'))
    parser.add_argument('--update-file', metavar='update-file', type=argparse.FileType('rt'))
    results = parser.parse_args()

    print results

    #read current config file
    for line in results.config_file:
        reg_entry = line.strip().split(':')
        config_reg_list.append(reg_entry[0])
        config_file_list.append(line.strip())
        config_file_dict[reg_entry[0]] = line.strip()

    print config_reg_list
    print config_file_dict

    #read update
    if results.update_file is not None:
        for line in results.update_file:
            reg_entry = line.strip().split(':')
            update_reg_list.append(reg_entry[0])
            update_file_list.append(line.strip())
            update_file_dict[reg_entry[0]] = line.strip()

    #update file content
    for reg_entry in update_reg_list:
        config_file_dict[reg_entry] = update_file_dict[reg_entry]

    if results.update is True:
        #clean existing content
        results.config_file.seek(0)
        results.config_file.truncate()

        for reg_entry in sorted(config_reg_list):
            results.config_file.write(config_file_dict[reg_entry] + "\n")
