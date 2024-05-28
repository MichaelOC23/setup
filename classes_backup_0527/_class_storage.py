
import os
import json
from datetime import datetime
import asyncio
import asyncpg
import base64
import random
from typing import Any, Dict, List, Mapping, Tuple, Union
import json
import requests
import uuid
from azure.data.tables import UpdateMode, TransactionOperation, TableEntity, TableTransactionError
from azure.data.tables.aio import TableClient, TableServiceClient
from azure.storage.blob.aio import BlobServiceClient, BlobClient, ContainerClient
import psycopg2
from sympy import div
# from azure.core.exceptions import ResourceExistsError, HttpResponseError

bmm_table = "public.bmmdicts"



class az_storage():
    def __init__(self ):
        # self.account_name="productstoragecommunify"
        # self.endpoint_suffix = "core.windows.net"
        self.connection_string = os.environ.get('PERSONAL_STORAGE_CONNECTION_STRING', 'No Key or Connection String found')
        self.jbi_connection_string = os.environ.get('JBI_CONNECTION_STRING', 'No Key or Connection String found')
        self.transaction_pf_con_string = os.environ.get('PERSONAL_STORAGE_CONNECTION_STRING', 'No Key or Connection String found')
        self.unique_id = uuid.uuid4()
        self.log_container_name = "devcommunifylogs"
        self.content_container_name = "content"
        self.test_container_name = "testcontainer"
        self.parameter_table_name = "mytechparameters"
        self.parameter_partition_key = "parameter"
        # self.access_token_table_name_and_keys = "accesstoken"
        self.search_results_table_name = "searchresults"
        self.url_results_table_name = "urlcontent"
        self.table_field_data_extension = "table-field-data-extension"


        # Two different clients are provided to interact with the various 
        # components of the Table Service:

        #? (1) TableServiceClient -
            # Get and set account setting
            # Query, create, and delete tables within the account.
            # Get a TableClient to access a specific table using the get_table_client method.
        
        #? (2) TableClient -
            # Interacts with a specific table (which need not exist yet).
            # Create, delete, query, and upsert entities within the specified table.
            # Create or delete the specified table itself.


#?   ##################################################
#?   ##########       BLOB MANAGEMENT        ##########
#?   ##################################################

    async def recreate_container(self, container_name=None):
        # Instantiate a BlobServiceClient using a connection string
        if container_name is None or container_name == "":
            raise ValueError("Container name cannot be None or empty")
        
        blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        async with blob_service_client:
            # Instantiate a ContainerClient
            container_client = blob_service_client.get_container_client(container_name)
            
            # Delete Container
            try:
                await blob_service_client.delete_container(container_name)
            except Exception as e:
                # Doesn't Exist
                pass
            await asyncio.sleep(30)
            # Create new Container
            try:
                result = await blob_service_client.create_container(container_name)
                return result
            except Exception as e:
                return f"Error: {e}"
            
    def create_unique_blob_name(self):
        return f"{uuid.uuid4()}"
    
    async def upload_blob(self, container_name, blob_name, blob_data, overwrite_if_exists=True, alternate_connection_string=""):       
        
        if alternate_connection_string != "":
            blob_service_client = BlobServiceClient.from_connection_string(alternate_connection_string)
        else:
            blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        
        container_client = blob_service_client.get_container_client(container=container_name)
   
        async with blob_service_client:
            try: 
                blob_client = await container_client.upload_blob(name=blob_name, data=blob_data, overwrite=overwrite_if_exists)
                properties = await blob_client.get_blob_properties()
                return properties

            except Exception as e:
                raise ValueError(f"Error: {e}")
    
    async def get_blob(self, container_name, blob_name):
        
        blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        container_client = blob_service_client.get_container_client(container=container_name)
   
        async with blob_service_client:
            try: 
                blob_client = container_client.get_blob_client(blob_name)
                stream = await blob_client.download_blob()
                data =  await stream.readall()
                return data
            except Exception as e:
                raise ValueError(f"Error: {e}")
     
    async def get_last_n_blobs(self, container_name, n=200):
        blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        container_client = blob_service_client.get_container_client(container=container_name)

        blob_list = []
        async for page in container_client.list_blobs().by_page():
            async for blob in page:
                blob_dict = {
                    "name": blob.name,
                    "size": blob.size,
                    "container": container_name,
                    "creation_time": blob.creation_time,
                    "etag": blob.etag,
                    "tags": blob.tags
                }
                blob_list.append(blob_dict)
                if len(blob_list) >= n:
                    break
            if len(blob_list) >= n:
                break

        # Sort the list of blobs if necessary
        blob_list.sort(key=lambda x: x['creation_time'], reverse=True)
        return blob_list[:n]
      
    async def delete_blob(self, container_name, blob_name, overwrite_if_exists=True):       
        
        blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        container_client = blob_service_client.get_container_client(container=container_name)
        
        async with container_client:
            try: 
                blob_client = container_client.get_blob_client(blob_name)
                response = await blob_client.delete_blob()    
                return True
            except Exception as e:
                raise ValueError(f"Error: {e}")
                
   
#!   ##################################################
#!   ##########       TABLE MANAGEMENT       ##########
#!   ##################################################
    async def validate_connection_string(self, connection_string=None):
        if connection_string is None or connection_string == "":
            connection_string = self.transaction_pf_con_string
        async with TableServiceClient.from_connection_string(connection_string) as table_service_client:
            try:
                table_list = await self.get_list_of_tables()
                if isinstance(table_list, list):
                    return True
                else:
                    return False
            except: 
                return False
    
    async def get_tables_names_as_markdown(self, connection_string=None):
        if connection_string is None or connection_string == "":
            connection_string = self.transaction_pf_con_string
        async with TableServiceClient.from_connection_string(connection_string) as table_service_client:
            try:
                table_list = await self.get_list_of_tables()
                if isinstance(table_list, list):
                    table_names = "\n- ".join(table_list)
                    return f"###### List of Tables:  \n- {table_names}"                    
                else:   
                    return "No tables found"
            except Exception as e: 
                return f":red[ERROR: {e}]"
    
    async def get_list_of_tables(self, connection_string=None):
        if connection_string is None or connection_string == "":
            connection_string = self.transaction_pf_con_string
        # This method uses a connection string to create the TableServiceClient
        async with TableServiceClient.from_connection_string(connection_string,) as table_service:
            table_list = []
            async for table in table_service.list_tables():
                table_list.append(table.name)
            return table_list    
    
    async def create_table_safely(self, table_name=None):
        if table_name is None or table_name == "":
            raise ValueError("Table name cannot be None or empty")
        
        async with TableServiceClient.from_connection_string(self.connection_string) as table_service_client:
            response = await table_service_client.create_table_if_not_exists(table_name=table_name)
            # print(f"Created new table: {table_name} ")
            return response
    
    async def table_exists(self, table_name=None):
        if table_name is None or table_name == "":
            raise ValueError("Table name cannot be None or empty")
        
        table_list = await self.get_list_of_tables()
        
        if table_name in table_list:    return True
        else:                           return False
    
    async def delete_table(self, table_name=None):
        if table_name is None or table_name == "":
            raise ValueError("Table name cannot be None or empty")
        try: 
            async with TableServiceClient.from_connection_string(self.connection_string) as table_service_client:
                response = await table_service_client.delete_table(table_name=table_name)
            return True
        except:
            False
            
#?   ##################################################
#?   ##########      ENTITY MANAGEMENT       ##########
#?   ##################################################

    async def collect_entities_async(self, table_client, query_filter, parameters):
        if query_filter == "":
            async_pageable =  table_client.list_entities()
        else:
            async_pageable = table_client.query_entities(query_filter=query_filter, parameters=parameters)
        return [entity async for entity in async_pageable]
    
    async def sanitize_key(self, key, strip_before_encoding=True):
        """
        Encodes the key into a base64 string to avoid disallowed characters.
        The base64 string is safe for Azure Table Storage keys.
        """
        if key is None:
            return None
        if strip_before_encoding:
            key = key.strip()
        # Ensure the key is in bytes, then encode
        key_bytes = key.encode('utf-8')
        encoded_key = base64.b64encode(key_bytes).decode('utf-8')
        # Replace base64 characters that are not allowed in Azure Table keys
        safe_encoded_key = encoded_key.replace('+', '-').replace('/', '_')
        return safe_encoded_key
    
    async def restore_sanitized_key(self, encoded_key):
        """
        Decodes a base64 encoded key back to its original form.
        """
        try:
            # Reverse the replacements for base64 encoding
            base64_key = encoded_key.replace('-', '+').replace('_', '/')
            # Decode from base64 back to bytes, then decode bytes to string
            key_bytes = base64.b64decode(base64_key)
            original_key = key_bytes.decode('utf-8')
            return original_key
        except Exception as e:
            raise ValueError(f"Error: {e}")
    
    async def sanitize_entity(self, entity):
        if not isinstance(entity, dict):
            raise ValueError("Entity must be a dictionary")
        
        entity["Orig_rowkey"] = entity.get("rowkey")
        entity["Orig_partitionkey"] = entity.get("partitionkey")
        if entity.get("rowkey") is not None:
            entity["rowkey"] = await self.sanitize_key(entity["rowkey"])
            
        if entity.get("partitionkey") is not None:
            entity["partitionkey"] = await self.sanitize_key(entity["partitionkey"])    
        
        return entity

    async def create_test_entities(self):
                       
        entity1 = {"partitionkey": "pk002", "rowkey": "rk002", "Value": 1, "day": "Monday", "float": 1.003}
        entity2 = {"partitionkey": "pk002", "rowkey": "rk002", "Value": 2, "day": "Tuesday", "float": 2.003}
        entity3 = {"partitionkey": "pk002", "rowkey": "rk003", "Value": 3, "day": "Wednesday", "float": 3.003}
        entity4 = {"partitionkey": "pk002", "rowkey": "rk004", "Value": 4, "day": "Thursday", "float": 4.003}

        list_of_entities = [entity1, entity2, entity3, entity4]
        
        return list_of_entities
    
    async def load_test_entity_update_batch(self, table_name, list_of_entities):
        EntityType = Union[TableEntity, Mapping[str, Any]]
        OperationType = Union[TransactionOperation, str]
        
        TransactionOperationType = Union[Tuple[OperationType, EntityType], Tuple[OperationType, EntityType, Mapping[str, Any]]]
        
        operations: List[TransactionOperationType] = [ # type: ignore
            ("delete", list_of_entities[0]),
            ("delete", list_of_entities[1]),
            ("upsert", list_of_entities[2]),
            ("update", list_of_entities[3], {"mode": "replace"}),
        ]
        async with TableClient.from_connection_string(conn_str=self.connection_string, table_name=table_name) as table_client:
        
            await table_client.submit_transaction(operations)
    
           #! add_update_or_delete_some_entities 
   
    async def add_update_or_delete_some_entities(self, table_name=None, entities_list=None, instruction_type="UPSERT_MERGE", alternate_connection_string="", attempt=1):
        #Check the validity of the parameters
        if table_name is None or table_name == "":
            raise ValueError("Table name cannot be None or empty")
        if entities_list is None or entities_list == [] or entities_list == {}:
            return ""
        if instruction_type not in ["DELETE", "UPSERT_MERGE", "UPSERT_REPLACE", "INSERT"]:
            raise ValueError("Instruction type must be either 'DELETE' 'UPSERT_REPLACE', 'INSERT', 'UPSERT_MERGE' ")
        
        #entities_list should ideally be a list of dicts
        if not isinstance(entities_list, list):
            # If it isn't and it's one dict, just turn that into a one-tem list
            if isinstance(entities_list, dict):
                entities_list = [entities_list]
            #Not sure what to do with the input value
            else:
                raise ValueError("Entities must be a list or dictionary")
        
        # Initialize the blob extension dictionary.
        # We will put large dictionary values into blobs and store the blob name in the entity.
        blob_extension = {}
        
        entity_count = len(entities_list)
        prior_percent_complete = 0
        percent_complete = 0
        on_entity = 0
        #Iterate through each entity in the list
        for entity in entities_list:
            on_entity += 1
            
            prior_percent_complete = percent_complete
            percent_complete = (on_entity / entity_count)
            
            # if round(percent_complete, 1) > round(prior_percent_complete, 1):
            #     print(f"Percent Complete: {round(percent_complete * 100, 2)}%")

            #rowkey is required for each Entity
            if entity.get("rowkey") == '' or entity['rowkey'] == None:
                raise ValueError("rowkey cannot be None or empty")
            
            #partitionkey is required for each Entity
            if entity.get("partitionkey") == '' or entity['partitionkey'] == None:
                raise ValueError("partitionkey cannot be None or empty")
            
            #If the entity does not have an "Orig_partitionkey" and "Orig_rowkey" key, then sanitize the 
            #entity by encoding the rowkey and partitionkey and storing the original values in the entity. 
            if "Orig_partitionkey" not in entity.keys() and"Orig_rowkey" not in entity.keys():
                entity = await self.sanitize_entity(entity)
            
            #If the instruction type is not DELETE, then check for blob fields in the entity
            # Not point in checking for blobs if we are deleting the entity
            if instruction_type not in ["DELETE"]:    
                
                # Iterate through each key in the entity. If the field has _blob in it,
                # that is the indicator that the size could be too large for the entity.
                for key in entity.keys():
                    if "_blob".lower() in key.lower():
                        # If the value in the field is empty, skip it
                        blob_value = entity.get(key, None)  
                        if blob_value is None:
                            continue
                        # if not isinstance(blob_value, list) and blob_value == "":
                        #     continue
                        # if (isinstance(blob_value, list) and len(blob_value) == 0):
                        #     continue
                        # If it's not empty, then create a new unique key for the blob field
                        blob_field_key = f"{key}|{self.create_unique_blob_name()}"        
                        # Put the value of the field in the blob_extension dictionary
                        blob_extension[blob_field_key] = entity[key]
                        # Replace the value in the entity with the new blob field key
                        entity[key] = blob_field_key
                
                # If there are any blob fields in the entity, then upload the blob to the storage account
                if blob_extension != {}:
                    for key in blob_extension.keys():
                        resp = await self.upload_blob(self.table_field_data_extension, blob_field_key, blob_extension[blob_field_key], overwrite_if_exists=True, alternate_connection_string=self.transaction_pf_con_string)
                        # print(f"Uploaded blob: {blob_field_key}")
            
            
            conn_str = self.connection_string if alternate_connection_string == "" else alternate_connection_string
            resp_list = []
            #The entity is now ready to be added, updated, or deleted in the tale
            async with TableClient.from_connection_string(conn_str=conn_str, table_name=table_name) as table_client:
                try:
                        
                    if instruction_type == "DELETE":
                        resp = await table_client.delete_entity(row_key=entity["rowkey"], partition_key=entity["partitionkey"])
                    
                    if instruction_type == "UPSERT_MERGE":
                        resp = await table_client.upsert_entity(mode=UpdateMode.MERGE, entity=entity)
                        # print(f"UPSERT_MERGE table: {table_name}  entity: {entity['rowkey']}: {resp}")
                    
                    if instruction_type == "UPSERT_REPLACE":
                        resp = await table_client.upsert_entity(mode=UpdateMode.REPLACE, entity=entity)
                        # print(f"UPSERT_REPLACE entity: {entity['rowkey']}: {resp}")
                    
                    if instruction_type == "INSERT":
                        resp = await table_client.create_entity(entity)    
                    
                    resp_list.append(resp)
                
                except Exception as e:
                    if attempt > 5:
                        raise ValueError(f"Error: {e} ... after 3 attempts")
                    seed = 5
                    wait_time = random.uniform((seed * .1 * 1000), (seed * 2 * 1000))/1000
                    print(f"Error: {e} ... waiting {wait_time} seconds before retrying")
                    await asyncio.sleep(wait_time)
                    return await self.add_update_or_delete_some_entities(table_name=table_name, entities_list=entity, instruction_type=instruction_type, attempt=attempt+1)
            
        return resp_list
    
           #! get_entities_by_partition_key
    
    async def get_some_entities(self, table_name=None, partitionkey=None, rowkey=None, re_sanitize_keys = False, get_blob_extensions=False):
        if table_name is None or table_name == "":
            raise ValueError("Table name cannot be None or empty")
        
        pk_filter = ""
        rk_filter = ""
        
        # The below contemplates that you might be searching for a the  original value (which would be displated to the user)
        # or by the sanitized value (which is the value stored in the table)
        
        if re_sanitize_keys:
            partitionkey = await self.sanitize_key(partitionkey)
            rowkey = await self.sanitize_key(rowkey)
        
        async with TableClient.from_connection_string(self.connection_string, table_name) as table_client:
            
            parameters = {}
            
            if partitionkey is not None and partitionkey != "" and isinstance(partitionkey, str):
                parameters["pk"] = partitionkey
                pk_filter = "partitionkey eq @pk"
                
            if rowkey is not None and rowkey != "" and isinstance(rowkey, str) :
                parameters["rk"] = rowkey
                rk_filter = "rowkey eq @rk"
            
            if pk_filter != "" and rk_filter != "":
                query_filter = f"{pk_filter} and {rk_filter}"
            else:
                query_filter = f"{pk_filter}{rk_filter}"

            some_entities =  await self.collect_entities_async(table_client, query_filter=query_filter , parameters=parameters)
            
            if get_blob_extensions:
                async for entity in some_entities:
                    for key in entity.keys():
                        if "_blob" in key and entity[key] != "":
                            try:
                                blob_data = await self.get_blob(self.table_field_data_extension, entity[key])
                            except:
                                print(f"Error getting blob data for {entity[key]} ... no data returned")
                                blob_data = ""
        
                            entity[key.replace("_blob", "")] = blob_data
        
            return some_entities
    
           #! add_update_or_delete_some_entities
    
#?   ##################################################
#?   ##########       CUSTOM STORAGE         ##########
#?   ##################################################           
                        
    async def get_all_prospects(self, table_name="prospects", partitionkey=None, rowkey=None, re_sanitize_keys = False, get_blob_extensions=False):
        if table_name is None or table_name == "":
            raise ValueError("Table name cannot be None or empty")
        
        pk_filter = ""
        rk_filter = ""
        
        # The below contemplates that you might be searching for a the  original value (which would be displated to the user)
        # or by the sanitized value (which is the value stored in the table)
        
        if re_sanitize_keys:
            partitionkey = await self.sanitize_key(partitionkey)
            rowkey = await self.sanitize_key(rowkey)
        
        async with TableClient.from_connection_string(self.jbi_connection_string, table_name) as table_client:
            
            parameters = {}
            
            if partitionkey is not None and partitionkey != "" and isinstance(partitionkey, str):
                parameters["pk"] = partitionkey
                pk_filter = "partitionkey eq @pk"
                
            if rowkey is not None and rowkey != "" and isinstance(rowkey, str) :
                parameters["rk"] = rowkey
                rk_filter = "rowkey eq @rk"
            
            if pk_filter != "" and rk_filter != "":
                query_filter = f"{pk_filter} and {rk_filter}"
            else:
                query_filter = f"{pk_filter}{rk_filter}"
                
            #!REMOVE ME
            query_filter = "Version eq '0'"

            some_entities =  await self.collect_entities_async(table_client, query_filter=query_filter , parameters=parameters)
            
            if get_blob_extensions:
                async for entity in some_entities:
                    for key in entity.keys():
                        if "_blob" in key and entity[key] != "":
                            try:
                                blob_data = await self.get_blob(self.table_field_data_extension, entity[key])
                            except:
                                print(f"Error getting blob data for {entity[key]} ... no data returned")
                                blob_data = ""
        
                            entity[key.replace("_blob", "")] = blob_data
        
            return some_entities
        
        
        
    async def create_parameter(self, parameter_code, parameter_value):
        if parameter_code is None or parameter_code == "":
            raise ValueError("Parameter code cannot be None or empty")
        if parameter_value is None or parameter_value == "":
            raise ValueError("Parameter value cannot be None or empty")
        try:
            new_parameter = {
                "partitionkey": self.parameter_partition_key,
                "rowkey": parameter_code,   # Article ID (unique)
                "parameter_value": parameter_value      # Image URL
                }
            
            resp = await self.add_update_or_delete_some_entities(table_name=self.parameter_table_name, entities_list=new_parameter, instruction_type="UPSERT_MERGE")
            return resp
            
        except Exception as e:
            raise ValueError(f"Error: {e}")
    
    async def store_article(self, blob_article, entity_article, wait_increment=1):
        start_time = datetime.now()
        id = entity_article.get('id', "BAD_ID")
        wait_duration = wait_increment * .75
        print(f"Storing article: {id} ... waiting {wait_duration} seconds")
        await asyncio.sleep(wait_duration)
        resp = await self.upload_blob(self.content_container_name, blob_article.get('id', "BAD_ID"), json.dumps(blob_article, indent=4 ) , overwrite_if_exists=True)
        resp = await self.add_update_or_delete_some_entities(table_name=self.search_results_table_name, entities_list=entity_article, instruction_type="UPSERT_MERGE")
        run_time = datetime.now() - start_time  
        print (f"Article stored: {id} in {run_time} seconds.")
    
    async def get_all_parameters(self):
        try:
            resp = await self.get_some_entities(self.parameter_table_name)
            return resp
              
        except Exception as e:
                raise ValueError(f"Error: {e}")
    
    async def get_one_parameter(self, parameter_code):
        try:
            # unsanitized_pkey = await(self.restore_sanitized_key(self.parameter_table_name))
            # unsanitized_rkey = await(self.restore_sanitized_key(parameter_code))
            return_param = await self.get_some_entities(table_name=self.parameter_table_name, partitionkey=self.parameter_partition_key, rowkey=parameter_code, re_sanitize_keys=True)
            if not return_param:
                return "No Param Found"
            elif isinstance(return_param, list) and len(return_param) > 0:
                return return_param[0].get('parameter_value', "No Value Found")
            else: 
                return "Error"
              
        except Exception as e:
            raise ValueError(f"Error: {e}")
            return None
                      
    async def delete_parameter(self, parameter_code=None):
        if parameter_code is None or parameter_code == "":
            raise ValueError("Parameter code cannot be None or empty")
        try:
            await self.add_update_or_delete_some_entities(table_name=self.parameter_table_name, partitionkey=self.parameter_partition_key, rowkey=parameter_code)
        except Exception as e:
            raise ValueError(f"Error: {e}")

    async def upload_log(self, log_unique_name, log_data):
        asyncio.create_task(self.upload_blob(self.log_container_name, log_unique_name, log_data)) 

    async def get_recent_logs(self):
        return await self.get_blob_list(self.log_container_name)  
    
    async def _upload_required_assets(self):
            files= ['wsj.png', 'dj_FIXED_taxonomy.json', 'cflogo.png', 'dj_COMPLETE_taxonomy.json']
            for file in files:
                await self.upload_blob_file(file, open(file=os.path.join('assets', file), mode="rb"))
       
    async def delete_token(self):
    
        try:
            await self.add_update_or_delete_some_entities(table_name=self.access_token_table_name_and_keys, entities_list= {"partitionkey": self.access_token_table_name_and_keys, "rowkey": self.access_token_table_name_and_keys}, instruction_type="DELETE")
        except Exception as e:
            raise ValueError(f"Error: {e}")
                        
    async def save_token(self, access_token):
        if access_token is None or access_token == "":
            raise ValueError("Access token cannot be None or empty")

        try:
            new_parameter = {
                "partitionkey": self.access_token_table_name_and_keys,
                "rowkey": self.access_token_table_name_and_keys,   # Article ID (unique)
                "parameter_value": access_token      # Image URL
                }
            
            resp = await self.add_update_or_delete_some_entities(table_name=self.access_token_table_name_and_keys, entities_list=new_parameter, instruction_type="UPSERT_MERGE")
            return resp
            
        except Exception as e:
            raise ValueError(f"Error: {e}")
    
    async def get_token(self):
        try:
            access_token_table_entry = await self.get_some_entities(table_name=self.access_token_table_name_and_keys, partitionkey=self.access_token_table_name_and_keys, rowkey=self.access_token_table_name_and_keys)
            
            access_token_string = access_token_table_entry.get("parameter_value")
            try:
                access_token_dict = json.loads(access_token_string)
            except:
                access_token_dict = None
            
            return access_token_dict
        
        
        except Exception as e:
                return None
 
    async def update_one_url(self, result):
        if result is None or result == "":
            raise ValueError("search_querycannot be None or empty")
        try:
            resp = await self.add_update_or_delete_some_entities(table_name=self.parameter_table_name, entities_list=result, instruction_type="UPSERT_MERGE")
            return resp
            
        except Exception as e:
            raise ValueError(f"Error: {e}")
    
    async def save_url(self, search_type="web", 
                       search_query ="None", 
                       result_name = "",
                       site="",
                       page_snippet="", 
                       url = "", 
                       primary_result_image="", 
                       primary_site_image=""):
        if search_query is None or search_query == "":
            raise ValueError("search_query cannot be None or empty")
        if url is None or url == "":
            raise ValueError("url cannot be None or empty")

        try:
            new_url = {
                "partitionkey": search_query,
                "rowkey": url,   
                "search_type": search_type,
                "result_name": result_name,
                "page_snippet": page_snippet,
                "result_url": url,
                "result_site_url": site,
                "primary_result_image": primary_result_image,
                "primary_site_image": primary_site_image,
                "full_html_blob": "",
                "full_text_blob": "",
                "full_text_summary_blob": "",
                "extracted_data_blob": "",
                "extracted_images": "",
                "date_added": datetime.now().isoformat(),
                "status": "NEW",   #NEW, PROCESSING, COMPLETE, ERROR
                "status_message": ""
                }
            
            resp = await self.add_update_or_delete_some_entities(table_name=self.url_results_table_name, entities_list=new_url, instruction_type="UPSERT_MERGE")
            return resp

        except Exception as e:
            raise ValueError(f"Error: {e}")

#?   ##################################################
#!   ######       CUSTOM PERSONAL STORAGE       #######
#?   ################################################## 


    async def save_transaction(self, 
        txtFileSource,
        txtUniqueBusinessKey,
        datTransactionDate,
        txtInstitutionName,
        txtAccountType="",
        txtAccountName="",
        txtAccountNumber="",
        txtMerchant="",
        txtTranDesc1="",
        txtTranDesc2="",
        txtTranNameOrig="",
        fltAmount="",
        txtIncomeExpense="",
        txtCategory="",
        txtSubCategory="",
        txtSubSubCategory="",
        txtNote="",
        txtIgnore="",
        txtTaxFlag="",
        txtMedicalFlag="",
        txtReimbursableFlag=""
    ):

        try:
            new_transaction = {
                "partitionkey": txtCategory,
                "rowkey": txtUniqueBusinessKey,   
                "txtFileSource": txtFileSource,
                "txtUniqueBusinessKey": txtUniqueBusinessKey,
                "datTransactionDate": datTransactionDate,
                "txtInstitutionName": txtInstitutionName,
                "txtAccountType": txtAccountType,
                "txtAccountName": txtAccountName,
                "txtAccountNumber": txtAccountNumber,
                "txtMerchant": txtMerchant,
                "txtTranDesc1": txtTranDesc1,
                "txtTranDesc2": txtTranDesc2,
                "txtTranNameOrig": txtTranNameOrig,
                "fltAmount": fltAmount,
                "txtIncomeExpense": txtIncomeExpense,
                "txtCategory": txtCategory,
                "txtSubCategory": txtSubCategory,
                "txtSubSubCategory": txtSubSubCategory,
                "txtNote": txtNote,
                "txtIgnore": txtIgnore,
                "txtTaxFlag": txtTaxFlag,
                "txtMedicalFlag": txtMedicalFlag,
                "txtReimbursableFlag": txtReimbursableFlag
                }
            
            
            resp = await self.add_update_or_delete_some_entities(table_name='TransactionPF', entities_list=new_transaction, instruction_type="UPSERT_MERGE", alternate_connection_string=self.transaction_pf_con_string)
            return resp

        except Exception as e:
            raise ValueError(f"Error: {e}")


if __name__ == "__main__":
    pass
    # storage = az_storage()
    # # prospect_entity_list = asyncio.run(storage.get_all_prospects())
    # # pass
    # table = "public.bmmdicts"
    # storage = PsqlSimpleStorage()
    # # storage.delete_all_tables()
    # storage.setup_bmm_tables(table)
    
    
