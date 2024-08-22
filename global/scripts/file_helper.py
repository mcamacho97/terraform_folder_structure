from json import dumps, loads
from os import path


def read_json_file(file_path: str) -> dict:
    with open(file_path, 'r') as file:
        file_content = file.read()
        return loads(file_content)


def write_json_file(file_path: str, file_content: any):
    with open(file_path, 'w') as file:
        file_content = file.write(dumps(file_content, indent=2))


def write_to_variables_file(resources: dict, output_path: str = '.', split_files: bool = True, variables_filename: str = 'terraform'):
    print(output_path)
    if split_files:
        for key, value in resources.items():
            output_file_path = f'{output_path}/{key}.auto.tfvars.json'

            write_json_file(output_file_path, {key: value})
    else:
        if variables_filename != 'terraform':
            variables_filename += '.auto'
        variables_file_path = f'{output_path}/{variables_filename}.tfvars.json'

        tfvars_content = (
            read_json_file(variables_file_path)
            if path.exists(variables_file_path)
            else {}
        )

        tfvars_content = {**tfvars_content, **resources}

        write_json_file(variables_file_path, tfvars_content)


def write_to_output_file(resources: dict, output_path: str = '.', split_file: bool = True):
    if split_file:
        for key, value in resources.items():
            output_file_path = f'{output_path}/output.{key}.json'

            write_json_file(output_file_path, {key: value})
    else:
        output_file_path = f'{output_path}/output.resources.json'

        write_json_file(output_file_path, resources)
