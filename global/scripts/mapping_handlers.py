GET_ATT = 'Fn::GetAtt'
JOIN = 'Fn::Join'
REF = 'Ref'

key_schema = {}


def extract_functions_names(value: list, appsync_resources: dict) -> list:
    for index, item in enumerate(value):
        if GET_ATT in item:
            function_name_doubled = item[GET_ATT][0].split('AppSyncFunction')[
                0]
            function_name_length = int(len(function_name_doubled)/2)
            value[index] = function_name_doubled[:function_name_length]
        elif REF in item and 'Outputstransformerrootstack' in item[REF]:
            for function_name in appsync_resources['appsync_functions'].keys():
                if function_name in item[REF]:
                    value[index] = function_name
    return value


def get_table_name_from_ref(value: str) -> str:
    return value.replace('referencetotransformerrootstack', '').split('NestedStack')[0]


def set_char_case(target: str, case_map: dict = {"0": "l"}):
    char_cases = {
        "u": lambda x: x.upper(),
        "l": lambda x: x.lower()
    }
    chars = list(target)
    for index, char_case in case_map.items():
        if index.removeprefix("-").isdecimal() and char_case in char_cases:
            index = int(index)
            chars[index] = char_cases[char_case](chars[index])
    return "".join(chars)


def get_data_source(value: dict) -> str:
    if REF in value and 'NONEDS' in value[REF]:
        return 'NONE_DS'
    elif REF in value and 'NestedStack' in value[REF]:
        return get_table_name_from_ref(value[REF])
    else:
        data_source = value[GET_ATT][0]
        return data_source[:-10] if 'Lambda' not in data_source else set_char_case(data_source[:-16])


def get_attribute_name(new_key: str, key_schema: dict, attribute_name: str, key_value, attribute_number: int) -> tuple[str, int]:
    if new_key == 'name':
        for schema_key, schema_value in key_schema.items():
            if schema_value == key_value:
                attribute_name = schema_key
        if not attribute_name:
            attribute_name = f'attribute_{attribute_number}'
            attribute_number += 1
    return attribute_name, attribute_number


def get_dynamodb_attributes(value: list, key_schema: dict) -> dict:
    key_map = {
        'AttributeName': 'name',
        'AttributeType': 'type',
    }
    new_value = {}
    attribute_number = 1

    for item in value:
        attribute_name = ''
        new_item = {}
        for old_key, key_value in item.items():
            new_key = key_map.get(old_key, old_key)
            attribute_name, attribute_number = get_attribute_name(
                new_key, key_schema, attribute_name, key_value, attribute_number
            )
            new_item[new_key] = key_value
        new_value[attribute_name] = new_item
    return new_value


def get_dynamodb_keys(value: list):
    key_map = {
        'HASH': 'hash_key',
        'RANGE': 'range_key',
    }
    new_value = {}
    for item in value:
        key = key_map.get(item['KeyType'], item['KeyType'])
        new_value[key] = item['AttributeName']
    return new_value


def get_global_secondary_indexes(value: list[dict]) -> list:
    key_maps = {
        "IndexName": {
            'target_key': 'name',
            'handler': just_pass
        },
        "KeySchema": {
            'target_key': None,
            'handler': get_dynamodb_keys
        },
        "Projection|ProjectionType": {
            'target_key': 'projection_type',
            'handler': just_pass
        }
    }
    new_value = [get_mappings(item, key_maps, key_schema) for item in value]
    return new_value


def get_template_location(value: dict, prefix: str) -> str:
    return prefix + value[JOIN][1][-1]


def just_pass(value: any) -> any: return value


def get_single_item_list(
    value: any
) -> list[bool]: return [True] if value != None else []


def replace_template_refs(value: str | dict) -> str:
    if isinstance(value, str):
        return value

    template_mapping = value[JOIN][1]

    selector = {
        'Table': 'replace:Table',
        'ApiId': '%s',
        'NestedStack': 'rootStack:'
    }
    changer = {
        'replace': lambda x, y: f"%{x.replace(y, '')}%",
        'rootStack': lambda x, y: f"%{get_table_name_from_ref(x)}%"
    }

    for index, template_line in enumerate(template_mapping):
        for selector_key, selector_value in selector.items():
            if isinstance(template_line, dict) and selector_key in template_line[REF]:
                if ':' in selector_value:
                    key_split = selector_value.split(':')
                    template_mapping[index] = changer.get(key_split[0])(
                        template_line[REF], key_split[1])
                else:
                    template_mapping[index] = selector_value
    return ''.join(template_mapping)


def set_mapping_value(target_dict: dict, old_key: str) -> any:
    if '|' in old_key:
        old_key_split = old_key.split('|')
        value = target_dict
        for key_split in old_key_split:
            value = value.get(key_split, {})
    else:
        value = target_dict.get(old_key)
    return value


def set_value_to_nested(nested_dict: dict, new_key: str) -> tuple[dict, str]:
    if isinstance(new_key, str) and '|' in new_key:
        new_key_split = new_key.split('|')

        for index, key_split in enumerate(new_key_split):
            new_key = key_split
            nested_dict[key_split] = {}
            if index < len(new_key_split) - 1:
                nested_dict = nested_dict[key_split]

    return nested_dict, new_key


def combine_dict_mutating(main_dict: dict, secondary_dict: dict) -> dict:
    for key_name, key_value in secondary_dict.items():
        main_dict[key_name] = key_value


def clean_dict_mutating(target_dict: dict) -> dict:
    keys = list(target_dict.keys())
    for key in keys:
        target_dict.pop(key)
    return target_dict


def get_mappings(target_dict: dict, resource_mappings: dict, key_schema: dict) -> dict:
    new_dict = {}
    for old_key, key_maps in resource_mappings.items():
        new_key = key_maps['target_key']
        handler = key_maps['handler']
        value = set_mapping_value(target_dict, old_key)

        if not value:
            continue

        nested_dict = new_dict

        nested_dict, new_key = set_value_to_nested(nested_dict, new_key)

        result_value = handler(value)

        if old_key == 'KeySchema':
            key_schema = clean_dict_mutating(key_schema)
            key_schema = combine_dict_mutating(key_schema, result_value)

        if new_key:
            nested_dict[new_key] = result_value
        else:
            nested_dict = combine_dict_mutating(nested_dict, result_value)
    return new_dict
