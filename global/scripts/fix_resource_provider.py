from regex import findall
from sys import argv

tf_files = [
    "appsync_api.tf",
    "appsync_functions.tf",
    "appsync_resolvers.tf",
    "appsync_sources.tf",
    "dynamodb_tables.tf",
    "lambdas.tf"
]

providers = ["aws.infrastructure"]

if "--uncomment" in argv:
    is_comment_fix = False
else:
    is_comment_fix = True

if is_comment_fix:
    for tf_file in tf_files:
        with open(tf_file, "r") as file:
            file_content = file.read()

        regex_matches = findall(
            f"([ ]{{2,}})(provider[ ]+= (?:{'|'.join(providers)}))",
            file_content
        )

        for regex_match in regex_matches:
            file_content = file_content.replace(
                "".join(regex_match), f"{regex_match[0]}# {regex_match[1]}", 1
            )

        with open(f"{tf_file}", "w") as file:
            file.write(file_content)
else:
    for tf_file in tf_files:
        with open(tf_file, "r") as file:
            file_content = file.read()

        regex_matches = findall(
            f"# provider[ ]+= (?:{'|'.join(providers)})",
            file_content
        )

        for regex_match in regex_matches:
            file_content = file_content.replace(
                regex_match, regex_match[2:], 1
            )

        with open(f"{tf_file}", "w") as file:
            file.write(file_content)
