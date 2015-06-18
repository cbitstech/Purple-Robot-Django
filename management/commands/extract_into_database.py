import copy
import datetime
import json
import os
import pytz

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from purple_robot_app.models import PurpleRobotReading, PurpleRobotPayload

def my_slugify(str_obj):
    return slugify(str_obj.replace('.', ' ')).replace('-', '_')
    
def schema_for_item(name, item, parent=None):
    schema = { 'additional_schema': {} }
    
    if type(item).__name__ == 'int':
        schema[my_slugify(name)] = 'double'
        del schema['additional_schema']
    elif type(item).__name__ == 'long':
        schema[my_slugify(name)] = 'double'
        del schema['additional_schema']
    elif type(item).__name__ == 'float':
        schema[my_slugify(name)] = 'double'
        del schema['additional_schema']
    elif type(item).__name__ == 'str':
        schema[my_slugify(name)] = 'string'
        del schema['additional_schema']
    elif type(item).__name__ == 'unicode':
        schema[my_slugify(name)] = 'string'
        del schema['additional_schema']
    elif type(item).__name__ == 'bool':
        schema[my_slugify(name)] = 'boolean'
        del schema['additional_schema']
    else:
        for field_name, field_value in item.iteritems():
            field_type = None
        
            if field_name == 'PROBE':
                pass
            elif type(field_value).__name__ == 'int':
                field_type = 'double'
            elif type(field_value).__name__ == 'long':
                field_type = 'double'
            elif type(field_value).__name__ == 'float':
                field_type = 'double'
            elif type(field_value).__name__ == 'str':
                field_type = 'string'
            elif type(field_value).__name__ == 'unicode':
                field_type = 'string'
            elif type(field_value).__name__ == 'bool':
                field_type = 'boolean'
            elif type(field_value).__name__ == 'list':
                new_type = 'list'
           
                final_schema = None
           
                for value_item in field_value:
                    item_schema = schema_for_item(field_name, value_item, name)
                
                    if final_schema == None:
                        final_schema = item_schema
                    else:
                        final_schema = merge_schema(final_schema, item_schema)

                if final_schema != None:
                    if 'additional_schema' in final_schema:
                        for add_schema_name, add_schema_value in final_schema['additional_schema'].iteritems():
                            schema['additional_schema'][add_schema_name] = add_schema_value

                        del final_schema['additional_schema']
                    
                    schema['additional_schema'][my_slugify(name) + '_' + my_slugify(field_name)] = final_schema
            elif type(field_value).__name__ == 'dict':
                dict_schema = schema_for_item(field_name, field_value)
                
                for add_schema_name, add_schema_value in dict_schema['additional_schema'].iteritems():
                    schema['additional_schema'][add_schema_name] = add_schema_value
                    
                del dict_schema['additional_schema']
                
                for dict_name, dict_value in dict_schema.iteritems():
                    schema[my_slugify(field_name) + '_' + my_slugify(dict_name)] = dict_value
            
            if field_type != None:
                schema[my_slugify(field_name)] = field_type
            
    if parent != None:
        schema[my_slugify(parent) + '_id'] = 'int'
            
    return schema

def merge_schema(old_schema, new_schema):
    merged_schema = copy.deepcopy(old_schema)
    
    for field_name, field_type in new_schema.iteritems():
        if (field_name in merged_schema) == False:
            merged_schema[field_name] = field_type
        else:
            if field_type == 'string':
                merged_schema[field_name] = field_type
    
    return merged_schema
    

class Command(BaseCommand):
    def handle(self, *args, **options):
#        if os.access('/tmp/extracted_into_database.lock', os.R_OK):
#            return
    
#        open('/tmp/extracted_into_database.lock', 'wa').close() 

        tag = 'extracted_into_database'
        
        payloads = PurpleRobotPayload.objects.exclude(process_tags__contains=tag).order_by('added')[:10]
        
        db_schema = {}
        
        for payload in payloads:
            items = json.loads(payload.payload)

            for item in items:
                probe_name = my_slugify(item['PROBE']).replace('edu_northwestern_cbits_purple_robot_manager_probes_', '')
                
                new_schema = schema_for_item(probe_name, item)
                
                if probe_name in db_schema:
                    new_schema = merge_schema(db_schema[probe_name], new_schema)
                
                for value_name, value_schema in new_schema['additional_schema'].iteritems():
                    if value_name in db_schema:
                        value_schema = merge_schema(db_schema[value_name], value_schema)
                    
                    db_schema[value_name] = value_schema
                    
                del new_schema['additional_schema']
                    
                db_schema[probe_name] = new_schema
                    
        print('SCHEMA: ' + json.dumps(db_schema, indent=2))
                
#            tags = payload.process_tags
#                
#            if tags is None or tags.find(tag) == -1:
#                if tags is None or len(tags) == 0:
#                    tags = tag
#                else:
#                    tags += ' ' + tag
#                        
#                payload.process_tags = tags
#                    
#                payload.save()
#
#        os.remove('/tmp/extracted_into_database.lock')
