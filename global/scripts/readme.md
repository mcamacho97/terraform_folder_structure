## Table of content

- [Main readme](../readme.md)

## How to use

### Simply execute the script

An easy way to do this is to rigth click the script file and left click the "Copy Relative Path" option  
then write in your terminal python + "(relative_path)"

### Script behaviour

By default diferent resources will be create in separated **output files**  
if the file exist and already has other keys only specifics keys will be overwriten  
to dump all stracted data to a single file add the parameter `--single-file`

To overwrite real terraform variables use `--no-debug`

- In this case if `--single-file` is also used, by default `"terraform.tfvars.json"` will be used
- To change the output file name to `"<selected_name>.auto.tfvars.json"` use the parameter `--variables-filename` like `--variables-filename=variables`
- The `--variables-filename` parameter only works with `--no-debug` for normal output `"output.resources.json"` will always be used as filename

### Scripts detailed explanation

`TODO`
