
from autoinstall_generator.convert import convert, Directive, ConversionType
import copy
import json
import jsonschema
import yaml


def do_merge(a, b):
    '''Take a pair of dictionaries, and provide the merged result.
       Assumes that any key conflicts have values that are themselves
       dictionaries and raises TypeError if found otherwise.'''
    result = copy.deepcopy(a)

    for key in b:
        if key in result:
            left = result[key]
            right = b[key]
            if type(left) is not dict or type(right) is not dict:
                result[key] = right
            else:
                result[key] = do_merge(left, right)
        else:
            result[key] = b[key]

    return result


def merge(directives):
    '''Take a list of directives, and do_merge() their trees.'''

    result = {}
    for d in directives:
        result = do_merge(result, d.tree)

    return result


def mirror_http(parent_directive):
    hostname = parent_directive.fragments['mirror/http']['hostname']
    directory = parent_directive.fragments['mirror/http']['directory']
    parent_directive.tree = {
        'apt': {
            'primary': [
                {
                    'arches': ['default'],
                    'uri': f'http://{hostname}{directory}'
                }
            ]
        }
    }


def netcfg(parent_directive):
    netmask_bits = parent_directive.fragments['netcfg']['netmask_bits']
    ipaddress = parent_directive.fragments['netcfg']['ipaddress']
    parent_directive.tree = {
        'network': {
            'version': 2,
            'ethernets': {'any': {
                'match': {'name': 'en*'},
                'addresses': [f'{ipaddress}/{netmask_bits}'],
            }}
        }
    }


coalesce_map = {
    'mirror/http': mirror_http,
    'netcfg': netcfg,
}


def coalesce(directives):
    '''Take a list of co-dependent directives, and output a coalesced
       Directive that represents resolution of all the dependent values.'''
    result = Directive({}, '', ConversionType.Coalesced)
    result.children = directives

    result.fragments = {}
    for d in directives:
        result.fragments = do_merge(result.fragments, d.fragments)

    key = list(result.fragments)[0]
    coalesce_map[key](result)

    return result


class Bucket:
    def __init__(self):
        self.independent = []
        self.dependent = {}

    def coalesce(self):
        result = copy.copy(self.independent)
        for key in self.dependent:
            cur = self.dependent[key]
            result.append(coalesce(cur))
        return result


def bucketize(directives):
    '''Categorize Directives into independent and dependent.  Dependent
       type directives are grouped into a list in the dependent dict and
       grouped on their fragment toplevel key.  Non-Dependent type
       directives are placed into the independent list.'''

    bucket = Bucket()

    for cur in directives:
        if cur.convert_type != ConversionType.Dependent:
            bucket.independent.append(cur)
            continue

        key = list(cur.fragments)[0]
        if key not in bucket.dependent:
            bucket.dependent[key] = [cur]
        else:
            bucket.dependent[key].append(cur)

    return bucket


def validate_yaml(tree):
    with open('autoinstall-schema.json', 'r') as fp:
        schema_data = fp.read()
        schema = json.loads(schema_data)

    jsonschema.validate(tree, schema)


def implied_directives():
    return [Directive({'version': 1}, None, ConversionType.Implied)]


def debug_output(directives):
    trailer = []
    for cur in directives:
        out = cur.debug()
        if out:
            trailer.append(out)
    return ''.join(trailer)


def convert_file(preseed_file, debug=False):
    directives = implied_directives()

    for idx, line in enumerate(preseed_file.readlines()):
        directives.append(convert(line.strip('\n'), idx + 1))

    buckets = bucketize(directives)
    coalesced = buckets.coalesce()
    result_dict = merge(coalesced)

    validate_yaml(result_dict)

    result = yaml.dump(result_dict, default_flow_style=False)

    if debug:
        result += debug_output(coalesced)

    return result
