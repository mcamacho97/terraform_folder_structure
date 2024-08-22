from file_helper import (
    read_json_file, write_to_output_file, write_to_variables_file
)
from os import listdir, path
from script_helper import get_config_parameters, get_replace_length
from sys import argv

# Config section
relative_resources_path = './src/lambda'
# End of config section

# Default script behaviour
debug = True
split_files = True

replace_path_length = get_replace_length(argv.pop(0))

if argv and "--no-debug" in argv:
    debug = False

if argv and "--single-file" in argv:
    split_files = False

config_parameters = get_config_parameters(argv)

variables_filename = 'terraform'
if 'variables_filename' in config_parameters:
    variables_filename = config_parameters['variables_filename']

# * Getting script path
initial_path = path.dirname(__file__)
# * Replacing reversed slash for slash char
initial_path = initial_path.replace('\\', '/')
# * Removing subdirectories from project root folder path
initial_path = initial_path[:-replace_path_length]

full_resource_path = f"{initial_path}{relative_resources_path.strip('.')}"

resources = {}

# Add the resource names you will extract
resources['lambdas'] = {}
lambdas = resources['lambdas']


# Create the resource extract logic here
lambda_function_list = [
    folder for folder in listdir(full_resource_path) if '.' not in folder
]

for lambda_name in lambda_function_list:
    overwrite_file_path = f"{full_resource_path}/{lambda_name}/settings_overwrite.json"
    overwrite_file_content = None
    if path.exists(overwrite_file_path):
        overwrite_file_content = read_json_file(overwrite_file_path)
    if overwrite_file_content:
        lambdas[lambda_name] = overwrite_file_content
    else:
        lambdas[lambda_name] = {}
# End of custom logic

if debug:
    write_to_output_file(resources, initial_path, split_files)
else:
    write_to_variables_file(
        resources, initial_path, split_files, variables_filename
    )
