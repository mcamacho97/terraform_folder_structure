def get_replace_length(script_relative_path: str) -> int:
    script_relative_path = script_relative_path.replace('\\', '/')

    splited_script_relative_path = script_relative_path.split('/')[:-1]

    replace_path = '/' + '/'.join([
        folder_name
        for folder_name in splited_script_relative_path
        if folder_name != '.' and folder_name != '..'
    ])

    return len(replace_path)


def get_config_parameters(arguments: str) -> dict:
    raw_config_parameters = [
        argument for argument in arguments if '=' in argument
    ]
    config_parameters = {}

    for parameter in raw_config_parameters:
        key, value = parameter.split('=')
        key = key[2:].replace('-', '_')
        config_parameters[key] = value
    return config_parameters
