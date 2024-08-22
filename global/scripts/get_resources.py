from file_helper import (
    read_json_file, write_to_output_file, write_to_variables_file
)
from os import listdir, path
from script_helper import get_config_parameters, get_replace_length
from sys import argv

from mapping_handlers import (
    extract_functions_names, get_data_source, get_dynamodb_attributes, get_dynamodb_keys,
    get_global_secondary_indexes, get_mappings, get_single_item_list, get_template_location,
    just_pass, replace_template_refs, set_char_case
)

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

appsync_resources = {}

# Add the resource names you will extract
appsync_resources['appsync_sources'] = {}
appsync_resources['appsync_functions'] = {}
appsync_resources['appsync_resolvers'] = {}
appsync_resources['dynamodb_tables'] = {}

# Create the resource extract logic here
api_folder_path = f'{initial_path}/amplify/backend/api'
api_name = listdir(api_folder_path)[0]

schema_path = f'{api_folder_path}/{api_name}/schema.graphql'

stacks_folder_path = f'{api_folder_path}/{api_name}/build/stacks'

folder_stack_names = listdir(stacks_folder_path)

schema_lines = None

with open(schema_path, 'r') as file_content:
    schema_lines = file_content.readlines()

if not schema_lines:
    print('The are no lines in schema')
    exit()

stack_names = [
    f"{line[5:].split(' ')[0]}.json" for line in schema_lines if '@model' in line
]

for name in folder_stack_names:
    if name not in stack_names:
        stack_names.append(name)

function_path_prefix = f'./amplify/backend/api/{api_name}/build'

key_schema = {}

RESOURCE_TYPES = {
    'Source': 'AWS::AppSync::DataSource',
    'Function': 'AWS::AppSync::FunctionConfiguration',
    'Resolver': 'AWS::AppSync::Resolver',
    'Table': 'AWS::DynamoDB::Table'
}

resource_categories = {
    RESOURCE_TYPES['Source']: 'appsync_sources',
    RESOURCE_TYPES['Function']: 'appsync_functions',
    RESOURCE_TYPES['Resolver']: 'appsync_resolvers',
    RESOURCE_TYPES['Table']: 'dynamodb_tables'
}

GET_ATT = 'Fn::GetAtt'
JOIN = 'Fn::Join'
REF = 'Ref'

MAPPINGS = {
    RESOURCE_TYPES['Source']: {
        'Type': {
            'target_key': 'type',
            'handler': just_pass
        },
        'DynamoDBConfig|TableName': {
            'target_key': 'table_name',
            'handler': get_single_item_list
        },
        'LambdaConfig|LambdaFunctionArn': {
            'target_key': 'function_arn',
            'handler': get_single_item_list
        }
    },
    RESOURCE_TYPES['Function']: {
        'DataSourceName': {
            'target_key': 'data_source',
            'handler': get_data_source
        },
        'RequestMappingTemplate': {
            'target_key': 'request_mapping_template',
            'handler': just_pass
        },
        'RequestMappingTemplateS3Location': {
            'target_key': 'request_mapping_template_path',
            'handler': lambda x: get_template_location(x, function_path_prefix)
        },
        'ResponseMappingTemplate': {
            'target_key': 'response_mapping_template',
            'handler': just_pass
        },
        'ResponseMappingTemplateS3Location': {
            'target_key': 'response_mapping_template_path',
            'handler': lambda x: get_template_location(x, function_path_prefix)
        }
    },
    RESOURCE_TYPES['Resolver']: {
        'FieldName': {
            'target_key': 'field',
            'handler': just_pass
        },
        'PipelineConfig|Functions': {
            'target_key': 'functions',
            'handler': lambda x: extract_functions_names(x, appsync_resources)
        },
        'Kind': {
            'target_key': 'kind',
            'handler': just_pass
        },
        'RequestMappingTemplate': {
            'target_key': 'request_template',
            'handler': replace_template_refs
        },
        'ResponseMappingTemplate': {
            'target_key': 'response_template',
            'handler': just_pass
        },
        'ResponseMappingTemplateS3Location': {
            'target_key': 'response_template_path',
            'handler': lambda x: get_template_location(x, function_path_prefix)
        },
        'TypeName': {
            'target_key': 'type',
            'handler': just_pass
        }
    },
    RESOURCE_TYPES['Table']: {
        'KeySchema': {
            'target_key': None,
            'handler': get_dynamodb_keys
        },
        'AttributeDefinitions': {
            'target_key': 'attributes',
            'handler': lambda x: get_dynamodb_attributes(x, key_schema)
        },
        "GlobalSecondaryIndexes": {
            'target_key': 'global_secondary_indexes',
            'handler': get_global_secondary_indexes
        }
    }
}


def is_dynamo_stack(resources: dict, table_name: str) -> bool:
    table_resource = resources.get(f'{table_name}Table', {})
    return table_resource.get('Type') == RESOURCE_TYPES['Table']


def get_resource_name(resource_key: str, resource_type: str, properties: dict) -> str:
    if resource_type == RESOURCE_TYPES['Table']:
        resource_key = resource_key[:-5]

    elif resource_type == RESOURCE_TYPES['Source']:
        source_type = properties.get('Type')
        is_dynamo = source_type == 'AMAZON_DYNAMODB'
        resource_key = resource_key[
            :-10] if is_dynamo else set_char_case(resource_key[:-16])

    return properties['Name'] if resource_type == RESOURCE_TYPES['Function'] and 'Name' in properties else resource_key


for name in stack_names:
    table_name = name.split('.')[0]
    stack = read_json_file(f'{stacks_folder_path}/{name}')
    stack_resources = stack.get('Resources', {})

    for resource_name, resource in stack.get('Resources', {}).items():
        resource_type = resource.get('Type')
        properties = resource.get('Properties')
        if resource_type not in resource_categories:
            continue
        resource_category = resource_categories.get(resource_type)
        resource_key = get_resource_name(
            resource_name, resource_type, properties)
        appsync_resources[resource_category][resource_key] = get_mappings(
            properties, MAPPINGS[resource_type], key_schema)
# End of custom logic

if debug:
    write_to_output_file(appsync_resources, initial_path, split_files)
else:
    write_to_variables_file(
        appsync_resources, initial_path, split_files, variables_filename
    )
