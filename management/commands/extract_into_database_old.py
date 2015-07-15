import copy
import datetime
import json
import os
import psycopg2
import pytz

from datadiff import diff
from django.conf import settings
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

# TODO: BELOW
def inserts_for_item(name, item, parent=None):
	inserts = []
	
	insert_str = 'INSERT INTO ' + name ' ('
	insert_values = []
	
	field_count = 0
	
	for field_name, field_value in item.iteritems():
		field_type = None
		
		if count > 0:
		    insert_str += ', '
	
		if field_name == 'PROBE':
			pass
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
		else:
			insert_str += field_name 
		
		
		if field_type != None:
			schema[my_slugify(field_name)] = field_type
            
    if parent != None:
        schema[my_slugify(parent) + '_id'] = 'int'
            
    return inserts

def merge_schema(old_schema, new_schema):
    merged_schema = copy.deepcopy(old_schema)
    
    for field_name, field_type in new_schema.iteritems():
        if (field_name in merged_schema) == False:
            merged_schema[field_name] = field_type
        else:
            if field_type == 'string':
                merged_schema[field_name] = field_type
    
    return merged_schema
    
def database_schema(connection_str):
    schema = {}
    
    conn = psycopg2.connect(connection_str)
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = \'public\'')

    for table in cursor.fetchall():
        table_def = {}
        
        print(table)
        
        field_cursor = conn.cursor()
        
        field_cursor.execute('select column_name, data_type from information_schema.columns where table_schema = \'public\' and table_name=\'' + table[0] + '\'')
        
        for row in field_cursor:
            type = row[1]
            
            if type == 'text':
                type = 'string'
            elif type == 'double precision':
                type = 'double'
            elif type == 'bigint':
                type = 'int'
            elif type == 'integer':
                type = 'int'
            
            table_def[row[0]] = type
        
        schema[table[0]] = table_def
        
    cursor.close()
    conn.close()
        
    return schema

def create_table(connection_str, table_name, table_def):
    conn = psycopg2.connect(connection_str)
    cursor = conn.cursor()
    
    create_str = 'CREATE TABLE ' + table_name + ' (id SERIAL PRIMARY KEY, payload_id BIGINT'
    
    for field, type in table_def.iteritems():
        if type == 'string':
            type = 'TEXT'
        elif type == 'double':
            type = 'DOUBLE PRECISION'
        elif type == 'int':
            type = 'BIGINT'
            
        create_str += ', ' + field + ' ' + type
    
    create_str += ');'
    
    print('SQL: ' + create_str)
    
    cursor.execute(create_str)
    
    conn.commit()

    cursor.close()
    conn.close()
    
def add_column(connection_str, table_name, name, type):
    conn = psycopg2.connect(connection_str)
    cursor = conn.cursor()

    if type == 'string':
        type = 'TEXT'
    elif type == 'double':
        type = 'DOUBLE PRECISION'
    elif type == 'int':
        type = 'BIGINT'

    alter_str = 'ALTER TABLE ' + table_name + ' ADD COLUMN ' +  name + ' ' + type + ';'
    
    cursor.execute(alter_str)

    conn.commit()

    cursor.close()
    conn.close()
    
def insert_values(table, values):
	pass


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            settings.PURPLE_ROBOT_FLAT_MIRROR
        except AttributeError:
            return
        
#        if os.access('/tmp/extracted_into_database.lock', os.R_OK):
#            return
    
#        open('/tmp/extracted_into_database.lock', 'wa').close() 

        tag = 'extracted_into_database'
        
        payloads = PurpleRobotPayload.objects.exclude(process_tags__contains=tag).order_by('added')[:10]
        
        if payloads.count() > 0:
            
            db_schema = database_schema(settings.PURPLE_ROBOT_FLAT_MIRROR)

            print('DATABASE SCHEMA: ' + json.dumps(db_schema, indent=2))
            
            json_schema = {}
        
            for payload in payloads:
                items = json.loads(payload.payload)

                for item in items:
                    probe_name = my_slugify(item['PROBE']).replace('edu_northwestern_cbits_purple_robot_manager_probes_', '')
                
                    new_schema = schema_for_item(probe_name, item)
                
                    if probe_name in json_schema:
                        new_schema = merge_schema(json_schema[probe_name], new_schema)
                
                    for value_name, value_schema in new_schema['additional_schema'].iteritems():
                        if value_name in json_schema:
                            value_schema = merge_schema(json_schema[value_name], value_schema)
                    
                        json_schema[value_name] = value_schema
                    
                    del new_schema['additional_schema']
                    
                    json_schema[probe_name] = new_schema
                    
            print('PAYLOAD SCHEMA: ' + json.dumps(json_schema, indent=2))

#            print(json.dumps(diff(db_schema, json_schema).diffs, indent=2))
            diffs = diff(db_schema, json_schema).diffs
            
            for d in diffs:
#                print(str(d))
                if d[0] == 'insert':
                    create_table(settings.PURPLE_ROBOT_FLAT_MIRROR, d[1][0][0], d[1][0][1])
                elif d[0] == 'equal':
#                    print('EQUAL: ' + d[1][0][0])
#                    
                    for c in d[1][0][1].diffs:
                        if c[0] == 'insert':
#                            print(json.dumps(c, indent=2))
                            add_column(settings.PURPLE_ROBOT_FLAT_MIRROR, d[1][0][0], c[1][0][0], c[1][0][1])
                        elif c[0] != 'equal' and c[0] != 'context_end_container' and c[0] != 'delete':
                            print(json.dumps(c, indent=2))

            for payload in payloads:
                items = json.loads(payload.payload)

                for item in items:
                    probe_name = my_slugify(item['PROBE']).replace('edu_northwestern_cbits_purple_robot_manager_probes_', '')
                    
                    inserts = inserts_for_item(item)
                    
                    for insert in inserts:
                        insert_values(probe_name, inserts)
                     
        
                
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
