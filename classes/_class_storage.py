from curses.ascii import alt
import os
import json
from datetime import datetime
import asyncio
import re
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
# from azure.core.exceptions import ResourceExistsError, HttpResponseError

bmm_table = "public.bmmdicts"

class PsqlSimpleStorage():
    def __init__(self ):
        
        if 'USE_LOCAL_POSTGRES' in os.environ:
            self.connection_string = os.environ.get('LOCAL_POSTGRES_CONNECTION_STRING', 'No Postgres Key or Connection String found')
        
        else:
            ngrok_url = os.environ.get('NGROK_PUBLIC_URL', False)
            if not ngrok_url:
                raise ValueError("NGROK_PUBLIC_URL not found in environment variables.")
            ngrok_parts = ngrok_url.replace("tcp://", "").split(":")
            remote_postgres_host = ngrok_parts[0]
            remote_postgres_port = ngrok_parts[1]
            remote_postgres_db = os.environ.get('BMM_DB', 'No Postgres DB found')
            username = 'postgres'
            self.connection_string = f'postgresql://{username}:@{remote_postgres_host}:{remote_postgres_port}/{remote_postgres_db}'
        if self.connection_string == 'NONE':
            self.connection_string = self.get_new_connection_string()
        
        self.unique_initialization_id = uuid.uuid4()
        self.bmm_table = bmm_table
        self.parameter_table_name = "devparameters"
        self.parameter_partition_key = "parameter"
        self.access_token_table_name = "accesstoken"
        self.search_results_table_name = "searchresults"
        self.url_results_table_name = "urlcontent"
        
    def get_new_connection_string(self):
        ngrok_tcp_url = self.get_ngrok_public_url()
        
    def get_ngrok_public_url(self, get_new_url=False):
        if 'NGROK_TCP_URL_POSTGRES' in os.environ and not get_new_url:
            return os.environ['NGROK_TCP_URL_POSTGRES']
        elif get_new_url:
            return self.extract_ngrok_public_url(get_new_url=True)
        
        if 'NGROK_API_KEY' not in os.environ:
            print("NGROK_API_KEY not found in environment variables.")
            raise ValueError("NGROK_API_KEY not found in environment variables.")
        
        NGROK_API_KEY = os.getenv("NGROK_API_KEY")
        headers = {
            "Authorization": f"Bearer {NGROK_API_KEY}",
            "Ngrok-Version": "2"
        }
        url = "https://api.ngrok.com/endpoints"

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raises a HTTPError for bad responses
            data = response.json()
            
            if "endpoints" in data and len(data["endpoints"]) > 0:
                public_url = data["endpoints"][0]["public_url"]
                print(f"Extracted Public URL: {public_url}")
                os.environ['NGROK_TCP_URL_POSTGRES'] = public_url
                return public_url
            else:
                print("Failed to extract the public URL.")
                return None
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None
        
    async def get_data(self, partitionkey=None, rowkey=None, table_name=bmm_table, unpack_structdata=True):
        query = f"SELECT id, is_current, archivedon, partitionkey, rowkey, structdata FROM {table_name}"
        conditions = [" is_current = TRUE "]
        params = []

        
        if partitionkey:
            conditions.append("partitionkey = $1")
            params.append(partitionkey)
        if rowkey:
            conditions.append("rowkey = $2" if partitionkey else "rowkey = $1")
            params.append(rowkey)
        
        if conditions:
            query += " WHERE" + " AND ".join(conditions)
            
        try:
            conn = await asyncpg.connect(self.connection_string)
            try:

                async with conn.transaction():
                    records = []
                    all_records = await conn.fetch(query, *params)
                    for record in all_records:
                        # Convert Record to a dict. merge with 'structdata' JSON (if unpack_structdata is True)
                        full_record = dict(record)
                        if unpack_structdata:
                            full_record.update(json.loads(record['structdata']))
                        records.append(full_record)
                return records

            finally:
                await conn.close()
        except Exception as e:
            print(f"Database error during Get Data: {e}")
            return []

    async def upsert_data(self, data_items, table_name=bmm_table):
        if not isinstance(data_items, list):
            data_items = [data_items]

        try:
            conn = await asyncpg.connect(self.connection_string)
            for item in data_items:
                async with conn.transaction():
                    # Fetch the current structdata for merging
                    existing_structdata = await conn.fetchval(f"""
                        SELECT structdata FROM {table_name} 
                        WHERE partitionkey = $1 AND rowkey = $2 AND is_current = TRUE
                    """, item['partitionkey'], item['rowkey'])
                    
                    # If existing data is found, merge it with the new structdata
                    if existing_structdata:
                        existing_data_dict = json.loads(existing_structdata)
                        merged_data = existing_data_dict 
                        merged_data.update(item.get('structdata', {})) 
                        # merged_data = {**existing_data_dict, **item.get('structdata', {})}
                    else:
                        merged_data = item.get('structdata', {})
                    
                    # Update the existing current record if it exists
                    archive_result = await conn.execute(f"""
                        UPDATE {table_name} SET archivedon = NOW() AT TIME ZONE 'UTC', is_current = FALSE
                        WHERE partitionkey = $1 AND rowkey = $2 AND is_current = TRUE
                    """, item['partitionkey'], item['rowkey'])
                    # print(f"Archived data: {item['partitionkey']} - {item['rowkey']} with result: {archive_result}")

                    update_sql = f"""
                    INSERT INTO {table_name} (partitionkey, rowkey, structdata, is_current)
                        VALUES ($1, $2, $3, TRUE)"""
                    # print(f"Upserting data: {item['partitionkey']} - {item['rowkey']} with sql: {update_sql}")
                    updated_result = await conn.execute(update_sql, item['partitionkey'], item['rowkey'], json.dumps(merged_data))
                    # print(f"Upserted data: {item['partitionkey']} - {item['rowkey']} with result: {updated_result}")
            await conn.close()
            return data_items
        except Exception as e:
            print(f"Database error during upsert: {e}")
  
    async def delete_data(self, keys, table_name=bmm_table):
        if not isinstance(keys, list):
            keys = [keys]

        try:
            conn = await asyncpg.connect(self.connection_string)
            for key in keys:
                # Construct the WHERE clause based on input keys
                where_clause = []
                values = []
                if 'partitionkey' in key:
                    where_clause.append("partitionkey = $1")
                    values.append(key['partitionkey'])
                if 'rowkey' in key:
                    where_clause.append(f"rowkey = ${len(values) + 1}")
                    values.append(key['rowkey'])

                # Construct and execute the update query to mark records as archived
                if where_clause:
                    query = f"""
                        UPDATE {table_name}
                        SET is_current = FALSE, archivedon = (NOW() AT TIME ZONE 'UTC')
                        WHERE {" AND ".join(where_clause)}
                    """
                    deleted_result = await conn.execute(query, *values)
                    print(f"Deleted data: {key} and got result: {deleted_result}")

            await conn.close()
        except Exception as e:
            print(f"Database error during delete: {e}")

    def setup_bmm_tables(self, table_name):

        conn = psycopg2.connect(self.connection_string)
        cursor = conn.cursor()
        
        create_table_dict = {

        "create_table": f"""CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            partitionkey VARCHAR(100),
            rowkey VARCHAR(100),
            structdata JSONB,
            binarydoc BYTEA,
            createdon TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            archivedon TIMESTAMP,  
            is_current BOOLEAN DEFAULT TRUE,  
            createdby VARCHAR(50),
            archivedby VARCHAR(50),
            loadsource VARCHAR(10)
        );""",
            
            "index1": f"CREATE UNIQUE INDEX idx_partitionkey_rowkey_current ON {table_name} (partitionkey, rowkey) WHERE is_current = TRUE;"

        
        # 'constraint1': f"CREATE UNIQUE INDEX idx_unique_current ON {table_name} (partitionkey, rowkey) WHERE is_current = TRUE;",
        
        # # # Index for pattern 3
        # # "index3": f"CREATE INDEX IF NOT EXISTS idx_rowkey_archivedon_null ON {table_name} (rowkey) WHERE is_current = TRUE;",

        # # GIN index for structdata searches
        # "index4": f"CREATE INDEX IF NOT EXISTS idx_structdata_gin ON {table_name} USING GIN (structdata);"

        

        }
        
        conn = psycopg2.connect(self.connection_string)
        with conn:
            with conn.cursor() as cursor:
                for key, command in create_table_dict.items():
                    try:
                        cursor.execute(command)
                    except Exception as e:
                        print(f"Database error during table setup: {e} with statement: {command}")
                        break  # Or decide how to handle the error

    def delete_all_tables(self):
        # Safety check or environment check could go here
        # e.g., confirm deletion or check if running in a production environment

        try:
            # Connect to the database
                conn = psycopg2.connect(self.connection_string)
                with conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                        tables = cursor.fetchall()

                        # Build list of table names, excluding system tables
                        table_names = [table[0] for table in tables if not table[0].startswith(('pg_', 'sql_'))]

                        # Generate and execute DROP TABLE statements in a single transaction
                        if table_names:
                            drop_query = "DROP TABLE IF EXISTS " + ", ".join(table_names) + " CASCADE;"
                            print(drop_query)  # Optional: for logging or confirmation
                            cursor.execute(drop_query)
                            
                        # Commit changes
                        conn.commit()
                    
        except psycopg2.Error as e:
            print(f"An error occurred: {e}")
            return False
        
        return True
    

EntityType = Union[TableEntity, Mapping[str, Any]]
OperationType = Union[TransactionOperation, str]
TransactionOperationType = Union[Tuple[OperationType, EntityType], Tuple[OperationType, EntityType, Mapping[str, Any]]]

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
        
        entity["Orig_RowKey"] = entity.get("RowKey")
        entity["Orig_PartitionKey"] = entity.get("PartitionKey")
        if entity.get("RowKey") is not None:
            entity["RowKey"] = await self.sanitize_key(entity["RowKey"])
            
        if entity.get("PartitionKey") is not None:
            entity["PartitionKey"] = await self.sanitize_key(entity["PartitionKey"])    
        
        return entity

    async def create_test_entities(self):
                       
        entity1 = {"PartitionKey": "pk002", "RowKey": "rk002", "Value": 1, "day": "Monday", "float": 1.003}
        entity2 = {"PartitionKey": "pk002", "RowKey": "rk002", "Value": 2, "day": "Tuesday", "float": 2.003}
        entity3 = {"PartitionKey": "pk002", "RowKey": "rk003", "Value": 3, "day": "Wednesday", "float": 3.003}
        entity4 = {"PartitionKey": "pk002", "RowKey": "rk004", "Value": 4, "day": "Thursday", "float": 4.003}

        list_of_entities = [entity1, entity2, entity3, entity4]
        
        return list_of_entities
    
    async def load_test_entity_update_batch(self, table_name, list_of_entities):
        
        operations: List[TransactionOperationType] = [
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

            #RowKey is required for each Entity
            if entity.get("RowKey") == '' or entity['RowKey'] == None:
                raise ValueError("RowKey cannot be None or empty")
            
            #PartitionKey is required for each Entity
            if entity.get("PartitionKey") == '' or entity['PartitionKey'] == None:
                raise ValueError("PartitionKey cannot be None or empty")
            
            #If the entity does not have an "Orig_PartitionKey" and "Orig_RowKey" key, then sanitize the 
            #entity by encoding the RowKey and PartitionKey and storing the original values in the entity. 
            if "Orig_PartitionKey" not in entity.keys() and"Orig_RowKey" not in entity.keys():
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
                        resp = await table_client.delete_entity(row_key=entity["RowKey"], partition_key=entity["PartitionKey"])
                    
                    if instruction_type == "UPSERT_MERGE":
                        resp = await table_client.upsert_entity(mode=UpdateMode.MERGE, entity=entity)
                        # print(f"UPSERT_MERGE table: {table_name}  entity: {entity['RowKey']}: {resp}")
                    
                    if instruction_type == "UPSERT_REPLACE":
                        resp = await table_client.upsert_entity(mode=UpdateMode.REPLACE, entity=entity)
                        # print(f"UPSERT_REPLACE entity: {entity['RowKey']}: {resp}")
                    
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
    
    async def get_some_entities(self, table_name=None, PartitionKey=None, RowKey=None, re_sanitize_keys = False, get_blob_extensions=False):
        if table_name is None or table_name == "":
            raise ValueError("Table name cannot be None or empty")
        
        pk_filter = ""
        rk_filter = ""
        
        # The below contemplates that you might be searching for a the  original value (which would be displated to the user)
        # or by the sanitized value (which is the value stored in the table)
        
        if re_sanitize_keys:
            PartitionKey = await self.sanitize_key(PartitionKey)
            RowKey = await self.sanitize_key(RowKey)
        
        async with TableClient.from_connection_string(self.connection_string, table_name) as table_client:
            
            parameters = {}
            
            if PartitionKey is not None and PartitionKey != "" and isinstance(PartitionKey, str):
                parameters["pk"] = PartitionKey
                pk_filter = "PartitionKey eq @pk"
                
            if RowKey is not None and RowKey != "" and isinstance(RowKey, str) :
                parameters["rk"] = RowKey
                rk_filter = "RowKey eq @rk"
            
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
                        
    async def get_all_prospects(self, table_name="prospects", PartitionKey=None, RowKey=None, re_sanitize_keys = False, get_blob_extensions=False):
        if table_name is None or table_name == "":
            raise ValueError("Table name cannot be None or empty")
        
        pk_filter = ""
        rk_filter = ""
        
        # The below contemplates that you might be searching for a the  original value (which would be displated to the user)
        # or by the sanitized value (which is the value stored in the table)
        
        if re_sanitize_keys:
            PartitionKey = await self.sanitize_key(PartitionKey)
            RowKey = await self.sanitize_key(RowKey)
        
        async with TableClient.from_connection_string(self.jbi_connection_string, table_name) as table_client:
            
            parameters = {}
            
            if PartitionKey is not None and PartitionKey != "" and isinstance(PartitionKey, str):
                parameters["pk"] = PartitionKey
                pk_filter = "PartitionKey eq @pk"
                
            if RowKey is not None and RowKey != "" and isinstance(RowKey, str) :
                parameters["rk"] = RowKey
                rk_filter = "RowKey eq @rk"
            
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
                "PartitionKey": self.parameter_partition_key,
                "RowKey": parameter_code,   # Article ID (unique)
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
            return_param = await self.get_some_entities(table_name=self.parameter_table_name, PartitionKey=self.parameter_partition_key, RowKey=parameter_code, re_sanitize_keys=True)
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
            await self.add_update_or_delete_some_entities(table_name=self.parameter_table_name, PartitionKey=self.parameter_partition_key, RowKey=parameter_code)
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
            await self.add_update_or_delete_some_entities(table_name=self.access_token_table_name_and_keys, entities_list= {"PartitionKey": self.access_token_table_name_and_keys, "RowKey": self.access_token_table_name_and_keys}, instruction_type="DELETE")
        except Exception as e:
            raise ValueError(f"Error: {e}")
                        
    async def save_token(self, access_token):
        if access_token is None or access_token == "":
            raise ValueError("Access token cannot be None or empty")

        try:
            new_parameter = {
                "PartitionKey": self.access_token_table_name_and_keys,
                "RowKey": self.access_token_table_name_and_keys,   # Article ID (unique)
                "parameter_value": access_token      # Image URL
                }
            
            resp = await self.add_update_or_delete_some_entities(table_name=self.access_token_table_name_and_keys, entities_list=new_parameter, instruction_type="UPSERT_MERGE")
            return resp
            
        except Exception as e:
            raise ValueError(f"Error: {e}")
    
    async def get_token(self):
        try:
            access_token_table_entry = await self.get_some_entities(table_name=self.access_token_table_name_and_keys, PartitionKey=self.access_token_table_name_and_keys, RowKey=self.access_token_table_name_and_keys)
            
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
                "PartitionKey": search_query,
                "RowKey": url,   
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
                "PartitionKey": txtCategory,
                "RowKey": txtUniqueBusinessKey,   
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
    
    storage = az_storage()
    prospect_entity_list = asyncio.run(storage.get_all_prospects())
    pass
    # table = "public.bmmdicts"
    # storage = PsqlSimpleStorage()
    # # storage.delete_all_tables()
    # storage.setup_bmm_tables(table)
    
    # async def test():
    #     model_list = []
    #     entity_list = []
    #     attribute_list = []

    #     test_volume = 5
        
    #     model = f"{uuid.uuid4()}"
    #     for i in range(test_volume):
    #         modelId = f"{uuid.uuid4()}"
    #         for j in range(test_volume):
    #             entityId = f"{uuid.uuid4()}"
    #             for k in range(test_volume):
    #                 attributeId = f"{uuid.uuid4()}"
    #                 attribute_list.append({"partitionkey": entityId, "rowkey": attributeId, "structdata": {'attributeName': attributeId, 'attributeDescription': f"{uuid.uuid4()}",  'entityId': entityId, 'id': attributeId}})
    #             entity_list.append({"partitionkey": modelId, "rowkey": entityId, "structdata": {'entityName': entityId, 'entityDescription': f"{uuid.uuid4()}", 'modelId': modelId, 'id': entityId}})
    #         model_list.append({"partitionkey": "bmm_model", "rowkey": modelId, "structdata": {'modelName': modelId, 'modelDescription': f"{uuid.uuid4()}", 'id': modelId}})
        
    #     await storage.upsert_data(model_list)
    #     await storage.upsert_data(entity_list)
    #     await storage.upsert_data(attribute_list)
    #     # await storage.get_data()
    #     # await storage.delete_data({"partitionkey": "pk"})

    # asyncio.run(test())
    
    
