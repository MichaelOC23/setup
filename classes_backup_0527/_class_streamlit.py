
# Standard Python libraries
import streamlit as st
from pathlib import Path
import math
from collections import Counter
from datetime import datetime
import re
import tempfile
import uuid
import os
import nltk
import base64
import asyncio
from datetime import date
from threading import Thread
import requests
import asyncpg
import json
import psycopg2 
from langchain_openai import OpenAIEmbeddings


# Data manipulation libraries
import pandas as pd
from sqlalchemy import create_engine


# To analyze PDF layouts and extract text
# from cv2 import AGAST_FEATURE_DETECTOR_THRESHOLD, log
from pdfminer.high_level import extract_pages, extract_text
from pdfminer.layout import LTTextContainer, LTChar, LTRect, LTFigure
import PyPDF2

# To extract text from tables in PDF
# import pdfplumber
import pdfplumber

# To extract the images from the PDFs
from PIL import Image
from pdf2image import convert_from_path

# To perform OCR to extract text from images 
import pytesseract 

#Office Documents
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain.document_loaders import UnstructuredPowerPointLoader, pdf, text, url
from langchain_community.document_loaders import UnstructuredExcelLoader
import langchain_core as core


BASE_FLASK_URL = base_url="http://127.0.0.1:5005/"

MODEL_DICT = {
            "Finance": "nlpaueb/sec-bert-base", 
            "General": "roberta-base",
            "ChatGPT-3.5": "gpt-3.5-turbo",
            "ChatGPT-4": "gpt-4-turbo",
            
            }
class streamlit_mytech():
    def __init__(self):
        self.model_dict = MODEL_DICT
        self.setup_database = False
        
    def set_up_page(page_title_text="[TITLE NEEDED FOR PAGE]", jbi_or_cfy="jbi", light_or_dark="dark", session_state_variables=[], connect_to_dj=False, hideResultGridButton=False):  
            
        def initialize_session_state_variable(variable_name, variable_value):
            if variable_name not in st.session_state:
                        st.session_state[variable_name] = variable_value
        
        # Page Title and Logo
        if page_title_text != "":
            PAGE_TITLE = page_title_text
            LOGO_URL = ""
            if jbi_or_cfy == "jbi":
                LOGO_URL = "https://devcommunifypublic.blob.core.windows.net/devcommunifynews/jbi-logo-name@3x.png"
            else:
                LOGO_URL = "https://devcommunifypublic.blob.core.windows.net/devcommunifynews/cflogofull.png"
            
        for variable in session_state_variables:
            if isinstance(variable, dict):
                for key in variable.keys():
                    initialize_session_state_variable(key, variable[key])
            
        st.set_page_config(
                page_title=PAGE_TITLE, page_icon=":earth_americas:", layout="wide", initial_sidebar_state="expanded",
                menu_items={'Get Help': 'mailto:michael@justbuildit.com','Report a bug': 'mailto:michael@justbuildit.com',})    

        # if SETUP_DATABASE:
        #     model_list, entity_list, attribute_list = asyncio.run(cs._create_test_data())
        #     cs._setup_parameter_table(cs.parameter_table_name)
            
            # cs.local_postgres_management()
            # asyncio.run(cs.upsert_data(model_list))
            # asyncio.run(cs.upsert_data(entity_list))
            # asyncio.run(cs.upsert_data(attribute_list))
            # asyncio.run(cs.get_data())
            # asyncio.run(cs.delete_data({"partitionkey": "pk"}))
        
            # #! Reset the database
            # delete_all_tables(self.transcription_table)
            # setup_transcription_table(self.transcription_table)
            # asyncio.run(load_test_data())
            # results = asyncio.run(self.get_data())
            # print(f"Results: {results}")   

        if connect_to_dj:
            initialize_session_state_variable("djsession", None)
            initialize_session_state_variable("djtoken", {})
            initialize_session_state_variable("djtoken_status_message", "") 
            initialize_session_state_variable("search_result_cache", "") 
            initialize_session_state_variable("viewed_article_cache", "") 
            initialize_session_state_variable("show_results", False)
            initialize_session_state_variable("show_article", False) 
            initialize_session_state_variable("chat_has_started", False)
            initialize_session_state_variable("show_search_results", False)
            initialize_session_state_variable("current_search_summary", "")
            
            display_dj_connection_status()

        # Standard Session state    
        initialize_session_state_variable("show_session_state", False)
        initialize_session_state_variable("DevModeState", False) 
        initialize_session_state_variable("settings", {"divider-color": "gray",})
        initialize_session_state_variable("model_type_value", MODEL_DICT["Finance"])
        initialize_session_state_variable("temperature", .1)
        
        
        # Page Title Colors
        border_color = "#FFFFFF"
        text_color = "#FFFFFF"
        background_color = "#1D1D1D"
        
        # Display the page title and logo and top buttons
        title_col, button_col1, button_col2 = st.columns([8, 1,1])
        title_col.markdown(f"""
                <div style="display: flex; align-items: start; width: 100%; padding: 10px; border: 1px solid {border_color}; border-radius: 10px; 
                height: 80px; background-color: {background_color}; margin-bottom: 20px;"> 
                <img src="{LOGO_URL}" alt="{PAGE_TITLE}" style="width: 80px; height: auto; margin: 10px 40px 5px 20px;">  
                <span style="flex: 1; font-size: 30px; margin: 2px 0px 10px 10px; font-weight: 400; text-align: top; align: right; white-space: nowrap; 
                overflow: hidden; color: {text_color}; text-overflow: ellipsis;">{PAGE_TITLE}</span>  </div>""", unsafe_allow_html=True)
        
        
        # Datbase tools button
        Tool_Button = button_col1.button("Tools", use_container_width=True, key="MeetingTools", type = "primary")
        if Tool_Button:
            st.toast("Not implemented yet.")
            pass
        
        
        #View Session State Button
        view_ss = button_col2.button(f"Ses. State", use_container_width=True)
        if view_ss:
            if st.session_state.show_session_state:
                st.session_state.show_session_state = False
            else:
                st.session_state.show_session_state = True

        log_exp = st.expander("Extraction Log", expanded=False)
        
        # Display the session state
        if st.session_state.show_session_state:
            ss = st.expander("Session State Value", expanded=False)
            ss.write(st.session_state)
        
        
        # Enable the below to see border around the page and all the columns
        # st.markdown("""<code style="background-color: #FFFFFF; padding: 30px; border-radius: 6px;color: red;">Your HTML content here</code>""", unsafe_allow_html=True)

    def display_data_tools():
        cs = PsqlSimpleStorage()

        st.session_state.models = {}
        st.session_state.entities = {}
        st.session_state.attributes = {}
        
        model_list, entity_list, attribute_list = cs._create_test_data()
        
        bcol, datacol = st.columns(2)
        with bcol:
            
            b_show_stored_data = st.button("Show Stored Data")
            if b_show_stored_data:    
                datacol.subheader("Stored Data", divider=True)
                data = asyncio.run(cs.get_data())
                datacol.write(data)
                    
            b_store_models = st.button("Store Models")
            if b_store_models:
                datacol.subheader("Store Models", divider=True)
                asyncio.run(cs.upsert_data(model_list))
                datacol.write("Stored Models")
            
            b_store_entities = st.button("Store Entities")
            if b_store_entities:
                datacol.subheader("Store Entities", divider=True)
                asyncio.run(  cs.upsert_data(entity_list))
                datacol.write("Stored Entities")
            
            b_store_attributes = st.button("Store Attributes")
            if b_store_attributes:
                datacol.subheader("Store Attributes", divider=True)
                asyncio.run(  cs.upsert_data(attribute_list))
                datacol.write("Stored Attributes")
            
            b_delete_data = st.button("dDlete Data")
            if b_delete_data:
                all_pkeys = asyncio.run(cs.get_unique_pkeys())
                all_rkeys = asyncio.run(cs.get_unique_rkeys())
                Pcol, rcol = datacol.columns(2)
                Pcol.selectbox("Select Partition Key", all_pkeys)
                p = Pcol.button("Delete Data")
                if p:
                    datacol.subheader("Delete Data", divider=True)
                    asyncio.run(cs.delete_data({"partitionkey": p} ))
                    datacol.write("Deleted Data")
                rcol.selectbox("Select Row Key", all_rkeys)

                models = datacol.st.selectbox()
                datacol.subheader("Delete Data", divider=True)
                asyncio.run(cs.delete_data({"partitionkey": "pk"} ))
                datacol.write("Deleted Data")



####################################
####      POSTGRESQL CLASS      ####
####################################
class PsqlSimpleStorage():
    def __init__(self ):
        
        self.connection_string = os.environ.get('LOCAL_POSTGRES_CONNECTION_STRING1', 'postgresql://mytech:mytech@localhost:5400/mytech')    
        self.unique_initialization_id = uuid.uuid4()
        self.transcription_table = "transcription"
        self.bmm_table = "bmm_table"
        self.parameter_table_name = "parameter"
        self.access_token_table_name = "accesstoken"
        self.search_results_table_name = "searchresults"
        self.url_results_table_name = "urlcontent"
        self.default = self.transcription_table
        
        
    def get_ngrok_public_url(self, get_new_url=False):
        def get_new_connection_string(self):
            ngrok_tcp_url = self.get_ngrok_public_url()
        
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
    
    def get_database_connection_string(self):
        return self.connection_string
    
    def get_parameter(self, parameter_name, parameter_value=None):
        try:
            conn = psycopg2.connect(self.connection_string)
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM {self.parameter_table_name} WHERE partitionkey = '{self.parameter_partition_key}' AND rowkey = '{parameter_name}'")
                    record = cursor.fetchone()
                    if record:
                        return record[2]
                    else:
                        return parameter_value
        except psycopg2.Error as e:
            print(f"An error occurred: {e}")
            return parameter_value  
        
    async def get_data(self, partitionkey=None, rowkey=None, table_name=None, unpack_structdata=True):
        
        def try_to_dict(record):
            try:
                return json.loads(record)
            except:
                return record
        
        if table_name is None or table_name == "": table_name = self.default
        
        
        
        query = f"SELECT Id, iscurrent, archivedon, partitionkey, rowkey, structdata FROM {table_name}"
        conditions = [" iscurrent = TRUE "]
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
                        full_record['structdata'] = try_to_dict(record['structdata'])
                        if unpack_structdata:
                            full_record.update(json.loads(record['structdata'].lower()))
                        records.append(full_record)
                return records

            finally:
                await conn.close()
        except Exception as e:
            print(f"Database error during Get Data: {e}")
            return []

    async def get_unique_pkeys(self, rowkey = None, table_name=None):
        if table_name is None or table_name == "": table_name = self.default
        if rowkey is None or rowkey == "": rowkey_condition = ""
        else: rowkey_condition = f"AND rowkey = '{rowkey}'"
        
        query = f"SELECT DISTINCT partitionkey FROM {table_name} WHERE iscurrent = TRUE {rowkey_condition}"
        try:
            conn = await asyncpg.connect(self.connection_string)
            try:
                async with conn.transaction():
                    records = await conn.fetch(query)
                return [record['partitionkey'] for record in records]
            finally:
                await conn.close()
        except Exception as e:
            print(f"Database error during Get Unique PKeys: {e}")
            return []
    
    async def get_unique_rkeys(self, partitionkey = None, table_name=None):
        if table_name is None or table_name == "": table_name = self.default
        if partitionkey is None or partitionkey == "": partitionkey_condition = ""
        else: partitionkey_condition = f"AND partitionkey = '{partitionkey}'"
        
        query = f"SELECT DISTINCT rowkey FROM {table_name} WHERE iscurrent = TRUE {partitionkey_condition}"
        try:
            conn = await asyncpg.connect(self.connection_string)
            try:
                async with conn.transaction():
                    records = await conn.fetch(query)
                return [record['rowkey'] for record in records]
            finally:
                await conn.close()
        except Exception as e:
            print(f"Database error during Get Unique rowkeys: {e}")
            return []
            
    async def upsert_data(self, data_items, table_name=None):
        if table_name is None or table_name == "": table_name = self.default
        
        if not isinstance(data_items, list):
            data_items = [data_items]
            conn = await asyncpg.connect(self.connection_string)
        # try:
            for item in data_items:
                async with conn.transaction():
                    # Fetch the current data for merging
                    existing_data = await conn.fetchrow(f"""
                        SELECT title, url, authors, publishdate, contenttype, structdata, bypage, allpages, alltext, summaryparts, 
                        textdump, summary, topics, speakers, loadsource, recordcontext, entities, sentiment FROM {table_name} 
                        WHERE partitionkey = $1 AND rowkey = $2 AND iscurrent = TRUE
                    """, item['partitionkey'], item['rowkey'])
                    
                    # Prepare the merged data
                    merged_data = {}
                    
                    if existing_data:
                        # Merge text fields (replace)
                        merged_data['title'] = item.get('title', existing_data['title'])
                        merged_data['contenttype'] = item.get('contenttype', existing_data['contenttype'])
                        merged_data['textdump'] = item.get('textdump', existing_data['textdump'])
                        merged_data['summary'] = item.get('summary', existing_data['summary'])
                        merged_data['sentiment'] = item.get('sentiment', existing_data['sentiment'])
                        merged_data['url'] = item.get('url', existing_data['url'])
                        merged_data['rowkey'] = item['rowkey']
                        merged_data['partitionkey'] = item['partitionkey']
                        merged_data['loadsource'] = existing_data['loadsource']
                        merged_data['recordcontext'] = existing_data['recordcontext']
                        
                        # Merge JSONB fields
                        jsonb_fields = ['structdata', 'bypage', 'allpages', 'alltext', 'summaryparts']
                        for field in jsonb_fields:
                            existing_json = existing_data[field]
                            new_json = item.get(field, {})
                            # Ensure both are dictionaries
                            if not isinstance(existing_json, dict):
                                existing_json = {}
                            if not isinstance(new_json, dict):
                                new_json = {}
                            merged_json = {**existing_json, **new_json}
                            merged_data[field] = json.dumps(merged_json)  # Convert to JSON string
                        
                        # Merge text[] fields (add unique values)
                        text_array_fields = ['authors', 'topics', 'speakers', 'entities']
                        for field in text_array_fields:
                            existing_array = existing_data[field] or []
                            new_array = item.get(field, [])
                            merged_array = list(set(existing_array) | set(new_array))
                            merged_data[field] = merged_array
                    else:
                        # If no existing data, use incoming data as is
                        for key, value in item.items():
                            if key in ['structdata', 'bypage', 'allpages', 'alltext', 'summaryparts']:
                                merged_data[key] = json.dumps(value)  # Convert to JSON string
                            else:
                                merged_data[key] = value

                    # Archive the existing current record if it exists
                    await conn.execute(f"""
                        UPDATE {table_name} SET archivedon = NOW() AT TIME ZONE 'UTC', iscurrent = FALSE
                        WHERE partitionkey = $1 AND rowkey = $2 AND iscurrent = TRUE
                    """, item['partitionkey'], item['rowkey'])

                    # Insert the new record
                    columns =  list(merged_data.keys()) + ['iscurrent']
                    values_placeholders = ', '.join([f"${i+1}" for i in range(len(columns))])
                    insert_sql = f"""
                        INSERT INTO {table_name} ({', '.join(columns)})
                        VALUES ({values_placeholders})
                    """
                    values = list(merged_data.values()) + [True]
                    await conn.execute(insert_sql, *values)
        # finally:
        #     await conn.close()
  
    async def add_update_or_delete_some_entities(self, table_name=None, entities_list=None, instruction_type="UPSERT_MERGE", alternate_connection_string="", attempt=1):
        def create_unique_blob_name():
            return f"{uuid.uuid4()}"
        
        #Check the validity of the parameters
        if table_name is None or table_name == "":
            table_name = self.default
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
            if entity.get("rowkey", '') == '' or entity.get("rowkey", None) == None:
                raise ValueError("rowkey cannot be None or empty")
            
            #partitionkey is required for each Entity
            if entity.get("partitionkey") == '' or entity['partitionkey'] == None:
                raise ValueError("partitionkey cannot be None or empty")
            
            #If the instruction type is not DELETE, then check for blob fields in the entity
            # Not point in checking for blobs if we are deleting the entity
            if instruction_type not in ["DELETE"]:    
                pass
                # # Iterate through each key in the entity. If the field has _blob in it,
                # # that is the indicator that the size could be too large for the entity.
                # for key in entity.keys():
                #     if "_blob".lower() in key.lower():
                #         # If the value in the field is empty, skip it
                #         blob_value = entity.get(key, None)  
                #         if blob_value is None:
                #             continue
                #         # if not isinstance(blob_value, list) and blob_value == "":
                #         #     continue
                #         # if (isinstance(blob_value, list) and len(blob_value) == 0):
                #         #     continue
                #         # If it's not empty, then create a new unique key for the blob field
                #         blob_field_key = f"{key}|{create_unique_blob_name()}"        
                #         # Put the value of the field in the blob_extension dictionary
                #         blob_extension[blob_field_key] = entity[key]
                #         # Replace the value in the entity with the new blob field key
                #         entity[key] = blob_field_key
                
                # # If there are any blob fields in the entity, then upload the blob to the storage account
                # if blob_extension != {}:
                #     for key in blob_extension.keys():
                #         raise ValueError("Blob extension is created yet")
                #         # resp = await self.upload_blob(self.table_field_data_extension, blob_field_key, blob_extension[blob_field_key], overwrite_if_exists=True, alternate_connection_string=self.transaction_pf_con_string)
                #         # print(f"Uploaded blob: {blob_field_key}")
            
            

            resp_list = []
            #The entity is now ready to be added, updated, or deleted in the tale
            conn = await asyncpg.connect(self.connection_string)
            async with conn.transaction():
                try:
                        
                    if instruction_type == "DELETE":
                        raise ValueError("DELETE Not Implemented Yet")
                    
                    if instruction_type == "UPSERT_MERGE":
                        resp = await self.upsert_data(entity, table_name)
                        
                    if instruction_type == "UPSERT_REPLACE":
                        raise ValueError("UPSERT_REPLACE Not Implemented Yet")
                        # resp = await table_client.upsert_entity(mode=UpdateMode.REPLACE, entity=entity)
                        # print(f"UPSERT_REPLACE entity: {entity['rowkey']}: {resp}")
                    
                    if instruction_type == "INSERT":
                        raise ValueError("INSERT Not Implemented Yet")
                    
                    resp_list.append(resp)
                
                except Exception as e:
                    print(f"Error: {e}")

        return resp_list
    
           #! get_entities_by_partition_key
     
    async def delete_data(self, keys, table_name=None):
        if table_name is None or table_name == "": table_name = self.default
        
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
                        SET iscurrent = FALSE, archivedon = (NOW() AT TIME ZONE 'UTC')
                        WHERE {" AND ".join(where_clause)}
                    """
                    deleted_result = await conn.execute(query, *values)
                    print(f"Deleted data: {key} and got result: {deleted_result}")

            await conn.close()
        except Exception as e:
            print(f"Database error during delete: {e}")

    def _setup_transcription_table(self, table_name):

        conn = psycopg2.connect(self.connection_string)
        cursor = conn.cursor()
        
        create_table_dict = {

        "create_table": f"""CREATE TABLE IF NOT EXISTS {table_name} (

                id serial4 NOT NULL,
                partitionkey varchar(100) NULL,
                rowkey varchar(100) NULL,
                title varchar(500) NULL,
                url text NULL,
                authors text[] NULL,
                publishdate date null,
                contenttype varchar(100) null,
                structdata jsonb NULL,
                bypage jsonb NULL,
                allpages jsonb NULL,
                alltext jsonb NULL,
                summaryparts jsonb NULL,
                textdump text NULL,
                summary text NULL,
                topics text[] NULL,
                speakers text[] NULL,
                entities text[] NULL,
                binarydoc bytea NULL,
                sentiment varchar(100) NULL,
                recordcontext varchar(15) DEFAULT 'PERSONAL'::character varying NULL,
                createdon timestamp DEFAULT CURRENT_TIMESTAMP NULL,
                archivedon timestamp NULL,
                iscurrent bool DEFAULT true NULL,
                createdby varchar(50) NULL,
                archivedby varchar(50) NULL,
                loadsource varchar(10) NULL,
                CONSTRAINT transcription_pkey PRIMARY KEY (id)
            );""",

            "index1": "CREATE UNIQUE INDEX idx_partitionkey_rowkey_current ON {table_name} USING btree (partitionkey, rowkey) WHERE (iscurrent = true);"
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

    def _setup_parameter_table(self, table_name):

        conn = psycopg2.connect(self.connection_string)
        cursor = conn.cursor()
        
        create_table_dict = {

        "create_table": f"""CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            parametername VARCHAR(50),
            parametervalue VARCHAR(50),
            parametervaluelong VARCHAR(200),
            recordcontext VARCHAR(15) DEFAULT 'PARAMETER',
            createdon TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            archivedon TIMESTAMP,  
            iscurrent BOOLEAN DEFAULT TRUE,  
            createdby VARCHAR(50),
            archivedby VARCHAR(50),
            loadsource VARCHAR(10)
        );""",
            
            "index1": f"CREATE UNIQUE INDEX idx_partitionkey_rowkey_current ON {table_name} (parametername) WHERE iscurrent = TRUE;"


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
                        
    async def _create_test_data(self):
                
        model_list = []
        entity_list = []
        attribute_list = []

        test_volume = 5
        

        for _ in range(test_volume):
            # Unique Key
            modelId = f"{uuid.uuid4()}"
            
            for _ in range(test_volume):
                # Unique Key
                entityId = f"{uuid.uuid4()}"
                
                for _ in range(test_volume):
                    # Unique Key
                    attributeId = f"{uuid.uuid4()}"
                    
                    #Nest all the constructed dictionaries
                    attribute_list.append({"partitionkey": entityId, "rowkey": attributeId, "structdata": {'attributename': attributeId, 'attributedescription': f"{uuid.uuid4()}",  'entitiId': entityId, 'id': attributeId}})
                entity_list.append({"partitionkey": modelId, "rowkey": entityId, "structdata": {'entityname': entityId, 'entitydescription': f"{uuid.uuid4()}", 'modelid': modelId, 'id': entityId}})
            model_list.append({"partitionkey": "bmm_model", "rowkey": modelId, "structdata": {'modelname': modelId, 'modeldescription': f"{uuid.uuid4()}", 'id': modelId}})
        
        return model_list, entity_list, attribute_list
    
    def _delete_all_tables(self, limit_to_table=None):
        
        # Safety check or environment check could go here
        # e.g., confirm deletion or check if running in a production environment

        try:
            # Connect to the database
                conn = psycopg2.connect(self.connection_string)
                with conn:
                    with conn.cursor() as cursor:
                        if limit_to_table:
                            cursor.execute(f"DROP TABLE IF EXISTS {limit_to_table} CASCADE;")
                        else:
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
                     
                     
######################################
####    EMBEDDINGS MANAGEMENT    ####
######################################
class embeddings_management():
    def __init__(self ):
        self.azure_storage_connection_string = os.environ.get('PERSONAL_STORAGE_CONNECTION_STRING', 'No Key or Connection String found')
        # self.local_chromadb = None
        self.CACHE_DIR = "cache"
        if not os.path.exists(self.CACHE_DIR):
            os.makedirs(f"{self.CACHE_DIR}/")
        
      
        self.supported_file_types = ["pdf", "txt", "mp3", "mp4", 'mpeg', 'doc', 'docx', "txt"]
        
        self.sec_bert_base_description = """
            ### *Model*: nlpaueb/sec-bert-base 
            #### Focused on financial and technical text data 

            ##### Strengths:
            - *Domain-Specific Pre-Training:* This BERT model was pre-trained specifically on a large corpus of financial documents (260,773 SEC 10-K filings), which should allow it to better capture domain-specific terminology, jargon, and nuances compared to general pre-trained models.
            - *Masked Language Modeling:* The examples show that the model performs well on financial text for masked language modeling tasks, which could be useful for tasks like named entity recognition or text summarization that you mentioned needing.
            - *Flexible Base Model:* Being a variant of BERT-base, this model can potentially be fine-tuned or adapted for various downstream tasks beyond just language modeling.
            - *Open-Source:* Like the previous model, this is also an open-source model available for free use.

            ##### Weaknesses:
            - Limited to Language Modeling: While the model shows strong performance on financial language modeling, it may still need task-specific fine-tuning for your use cases like summarization and named entity recognition.
            - Quantitative Evaluation Missing: The model card doesn't provide quantitative evaluation metrics for summarization or NER tasks specifically, so you may need to evaluate it yourself on your data."""

    # Cache uploaded files
    def cache_files(self, files) -> list[str]:
        filepaths = []
        for file in files:
            # Determine the file extension from the mime type
            ext = file.type.split("/")[-1]
            if ext == "plain":  # Handle text/plain mime type
                ext = "txt"
            elif ext in ["vnd.openxmlformats-officedocument.wordprocessingml.document", "vnd.ms-word"]:
                ext = "docx"  # or "doc" depending on your needs
            if ext not in self.supported_file_types:
                continue
            
            filepath = f"{self.CACHE_DIR}/{file.name}"
            
            with open(filepath, "wb") as f:
                f.write(file.getvalue())
            
            if ext in ["mp3", "mp4"]:
                pass
                # filepath = transcribe_audio_video(filepath)
            filepaths.append(filepath)
        
        # st.sidebar.write("Uploaded files", filepaths)  # Debug statement
        
        with st.sidebar:
            with st.expander("Uploaded Files"):
                filepaths_pretty = "\n".join(f"- {filepath}" for filepath in filepaths)
                st.markdown(f"{filepaths_pretty}")
        return filepaths
     
    def display_file_uploader(self, **kwargs):
        files = st.file_uploader(
            label=f"Upload files", type=self.supported_file_types, **kwargs
        )
        if not files:
            st.info("Please upload documents to get started.")
            return []
        return self.cache_files(files)
    
    def create_embeddings(self, text, title, description, file_type="General", as_of_date=date.today()):
        
        def get_embeddings(file_type="General"):
            """Generates text embeddings using a type-specific Transformer model.

            Args:
                text (str): The text to embed.
                title (str): Title associated with the text.
                description (str): Description associated with the text.
                type (str, optional): Type of embedding ('finance' or 'general'). Defaults to 'finance'.
                as_of_date (date, optional): Effective date of the embedding. Defaults to today's date.

            Returns:
                dict: A dictionary containing the embedding and metadata.
            """

            from transformers import AutoTokenizer, AutoModel
            from transformers import pipeline
            
            
            embeddings = None
            
            model = self.model_dict.get(file_type, self.general_model)
            
            def process_text_in_chunks(text, embedder, max_chunk_size=500):
            
                chunks = split_text_into_chunks(text, max_chunk_size)  # You'll need to implement this splitting function
                embeddings = []
                for chunk in chunks:
                    chunk_embeddings = embedder(chunk)
                    embeddings.append(chunk_embeddings)
                return embeddings 
            
            def split_text_into_chunks(text, max_chunk_size=100):
                """Splits text into chunks aiming for a target size, attempting to preserve sentences.

                Args:
                    text: The input text string.
                    max_chunk_size:  The approximate maximum number of tokens per chunk.

                Returns:
                    A list of text chunks.
                """

                nltk.download('punkt', quiet=True)  # Download sentence tokenizer if not present
                sentences = nltk.sent_tokenize(text)
                chunks = []
                current_chunk = []
                current_chunk_size = 0

                for sentence in sentences:
                    words = nltk.word_tokenize(sentence)  
                    current_chunk_size += len(words)

                    if current_chunk_size <= max_chunk_size:
                        current_chunk.append(sentence)
                    else:
                        # Chunk is getting too big, save it and start a new one
                        chunks.append(' '.join(current_chunk))  
                        current_chunk = [sentence]  
                        current_chunk_size = len(words)  

                # Add the last chunk (if any)
                if current_chunk:
                    chunks.append(' '.join(current_chunk))

                return chunks
            


            
            if file_type == "Finance":
                tokenizer = AutoTokenizer.from_pretrained(model)
                model = AutoModel.from_pretrained(model)
                embedder = pipeline('feature-extraction', model=model, tokenizer=tokenizer)
                embeddings = process_text_in_chunks(text, embedder)
                
            
            
            elif file_type == "General":
                from transformers import RobertaTokenizer, RobertaModel
                import torch
                import math

                # Load the RoBERTa tokenizer and model
                tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
                model = RobertaModel.from_pretrained('roberta-base')

                # Define the input text (a 2000-word article)
                # text = "This is a 2000-word article. It contains a lot of text... [2000 words of text]"

                # Split the text into chunks of maximum length 510 (512 - 2 for special tokens)
                max_len = 510
                chunks = [text[i:i+max_len] for i in range(0, len(text), max_len)]

                # Initialize a tensor to store the embeddings
                sentence_embeddings = torch.tensor([])
                chunks_to_process = len(chunks)
                processed_chunks = 0
                chunking_progress = st.progress(processed_chunks / chunks_to_process, f"Processing chunk {processed_chunks + 1}/{chunks_to_process}")
                # Process each chunk of text
                for chunk in chunks:
                    inputs = tokenizer(chunk, return_tensors="pt", padding=True, truncation=True, max_length=512)
                    chunking_progress.progress((processed_chunks + 1) / chunks_to_process)
                    

                    # Move the input tensors to the GPU (if available)
                    if torch.cuda.is_available():
                        inputs = {k: v.cuda() for k, v in inputs.items()}

                    # Get the embeddings from the RoBERTa model
                    with torch.no_grad():
                        outputs = model(**inputs)
                        last_hidden_state = outputs.last_hidden_state

                    # Get the chunk embeddings by taking the mean of the token embeddings
                    chunk_embeddings = torch.mean(last_hidden_state, dim=1)

                    # Concatenate the chunk embeddings to the sentence embeddings
                    embeddings = torch.cat((sentence_embeddings, chunk_embeddings), dim=0)
                    processed_chunks += 1

                # Print the shape of the sentence embeddings
                print(f"Shape of sentence embeddings: {embeddings.shape}")
            
            elif file_type == "ChatGPT-3.5":
                openai_3_large = OpenAIEmbeddings(model="text-embedding-3-large")
                embeddings = openai_3_large.embed_query(text)


                # openai = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
                # embeddings = openai.embed(text, model=model)
        
            elif file_type == "ChatGPT-4":
                openai = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
                embeddings = openai.embed(text, model=model)
                
            else:
                #Raise an error
                return "Invalid type. Please choose either 'finance' or 'general' as the type."
            

            return embeddings
        
        def sanitize_key(key, strip_before_encoding=True):
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
        
        def format_embeddings(embeddings, text, title, description, file_type="General", as_of_date=date.today()):
            import torch
            import numpy as np
            # Detach from computational graph (optional for memory efficiency)
            # Check if embeddings is a tensor and detach if necessary
            if isinstance(embeddings, torch.Tensor):
                embeddings = embeddings.detach()
            
            # Convert to NumPy array if it's still a tensor
            if isinstance(embeddings, torch.Tensor):
                embeddings = embeddings.cpu().numpy()
            
            elif isinstance(embeddings, list):  # Assuming embeddings from OpenAI are in list format
                embeddings = np.array(embeddings)  # Convert list to NumPy array

            
            #create a unique date-time key with the format: YYYY.MM.DD.HH.MM.SS.MS
            date_time_key = date.today().strftime("%Y.%m.%d.%H.%M.%S.%f")
            date_only_string = date.today().strftime("%Y-%m-%d")


            return_dict = {}
            if isinstance(embeddings, np.ndarray):
                embeddings = embeddings.tobytes()
                
            row_key_value = sanitize_key(f"{title}_{date_time_key}")
            
            return_dict = {  "PartitionKey": date_time_key,
                                            "RowKey": row_key_value,
                                            "Title": title,
                                            "Description": description,
                                            "EmbeddingModel": file_type,
                                            "EffectiveDate": date_only_string,
                                            "TextExtraction_blob": text,
                                            "EmbeddingsBinary_blob": embeddings,
                                            }
            
            return return_dict
        
        embeddings = get_embeddings(file_type)
        formatted_embeddings = format_embeddings(embeddings, text, title, description, file_type, as_of_date)
        
        return formatted_embeddings
    
    def get_embeddings_from_user_files(self):
        
        with st.sidebar:
            with st.expander("Advanced Settings"):
                model_type_value = st.radio("Select Model Type", list(self.model_dict.keys()))
                if model_type_value:
                    st.session_state['model_type_value'] = model_type_value
                st.session_state['temperature'] = st.number_input("Enter Temperature", help="It determines how creative the model should be", min_value=0.0,max_value=1.0, value=0.1)
                

            # Upload PDFs, DOCs, TXTs, MP3s, and MP4s
            documents = []
            new_documents = self.display_file_uploader(accept_multiple_files=True)
            if new_documents and len(new_documents) > 0:
                documents.extend(new_documents) 
            
            embeddings_list = []
            if len(documents) > 0:
                for file_path in documents:
                    with open(file_path, "r") as file:
                        text = file.read()

                    embeddings = self.create_embeddings(text, file.name, f"{text[:100]}...", "ChatGPT-3.5")
                    embeddings_list.append(embeddings)
                return embeddings_list


#####################################
####    TEXT EXTRACTION CLASS    ####
#####################################
class text_extraction():
    def __init__(self):
        
        self.parent_dir = str(Path(__file__).resolve().parent.parent)
        self.entropy_threshold = 4.8 # Entropy is a measure of the randomness in a string of text (used to ignore serial numbers, etc.)
        self.prior_values_set = set() 

        self.office_document_types = ['.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls']
        self.pdf_types = ['.pdf']
        self.gif_types = ['.gif']
        self.image_types = ['.jpg', '.jpeg', '.png', '.bmp', '.eps', '.tiff', 
                            '.webp', '.svg', '.ppm', '.sgi', '.iptc', '.pixar', '.psd', '.wmf']
        
        
        self.all_types = self.office_document_types + self.pdf_types + self.image_types + self.gif_types
        
        #Construction of the dictionary which will drive the structure of the JSON to be output
        self.text_structures = ['bypage', 'allpages', 'useful', 'ignored']
        self.text_styles = ['max_font_size', 'formats_concat']
        self.text_element_types = ['element_type']
        self.new_files_for_append = set()
        self.pytesseract_executable_path = '/opt/homebrew/bin/tesseract'
        self.all_extracts_dict = {}
        self.all_extracts_path = ''
        
    def create_empty_record(self):
        import datetime
        import uuid
        return {
        
                "id": str(uuid.uuid4()),
                "timestamp": datetime.datetime.now().isoformat(),
                "content": "",
                "source": "",
                "filename": "",
                "last_modified": "",
                "page_count": -1,
                "type":"",
                "categories": [],
                "languages": [],
                "filetype": "",
                "collection": "",
                "tags": []
                }
        
    def safe_remove(self, file_path):
        try:
            # Attempt to remove the file
            os.remove(file_path)
        except FileNotFoundError:
            # If the file does not exist, just pass
            pass
        except Exception as e:
            pass
            # Handle other possible exceptions (e.g., permission issues)
            # print(f"Error while deleting file: {e}")

    def log_it(self, message, level='info'):
        if level == 'info':
            print(message)
        elif level != 'info':
            print(f"\033[96m{level.upper()}: {message}\033[00m")

    def calculate_entropy(self, text):
        # Count the frequency of each character in the string
        frequencies = Counter(text)
        total_chars = len(text)

        # Calculate probabilities and entropy
        entropy = 0
        for freq in frequencies.values():
            prob = freq / total_chars
            if prob != 0:  # Handle the case where the probability is zero
                entropy -= prob * math.log2(prob)

        return entropy
    
    def get_file_extension(self, file_path):
            # Split the path and get the extension part
            _, file_extension = os.path.splitext(file_path)
            file_extension = file_extension.lower()
            return file_extension
    
    def create_key_safe_path(self, file_path):
        # Get the home directory for the current user to remove it from the file path
        home_dir = os.path.expanduser('~')
        
        # Remove the user-specific part from the path
        if file_path.startswith(home_dir):
            file_path = file_path[len(home_dir):]  # Remove the home directory part

        # Replace spaces with underscores and remove characters that are not allowed in JSON keys
        file_path = file_path.replace(' ', '_')
        file_path = re.sub(r'[^\w\s_-]', '', file_path)  # Keep alphanumeric, underscores, hyphens

        return file_path
    
    def save_json_to_file(self, doc_dict, output_path, mode='appendasnew', file_path=None):
        try:
            
            if not output_path:
                # get the name of the file and replace the extension with .json and put it in the output folder
                output_path = file_path.replace(self.get_file_extension(file_path), '.json')
                print(f"Output Path: {output_path}")
    
            # Create a safe path for the JSON file
            safe_path = self.create_key_safe_path(file_path)
            
            if mode == "replace":
                self.safe_remove(output_path)
            
            # Only erase the first time the file is appended
            if mode == "appendasnew":
                if os.path.exists(output_path) and output_path not in self.new_files_for_append:
                    self.safe_remove(output_path)
                    self.new_files_for_append.add(output_path)
                mode = "append"
            
            self.all_extracts_dict[safe_path] = doc_dict
            
            if output_path != self.all_extracts_path:
                if os.path.exists(output_path) and mode == "append":
                    with open(output_path, 'r') as f:
                        current_document = f.read()
                        current_doc_dict = json.loads(current_document)
                        current_doc_dict[safe_path] = doc_dict
                        f.close()
                        
                    with open(output_path, 'w') as f:
                        f.write(json.dumps(current_doc_dict, indent=4))
                        self.new_files_for_append.add(output_path)
                        f.close()
                
                else:
                    with open(output_path, 'w') as f:
                        # Create a dictionary with the safe path as the key
                        dict_to_save = {}
                        dict_to_save[safe_path] = doc_dict
                        f.write(json.dumps(dict_to_save, indent=4))
                        self.new_files_for_append.add(output_path)
                        f.close()
            return True, output_path
            
        except Exception as e:
            return False, f"Error: saving file:{output_path}    {e}"

    def extract_json_from_pdf(self, pdf_path, output_path=None, mode="appendasnew", entropy_threshold=4.8 ):
        
        def _create_empty_dict():
            pdf_text = {}

            for structure_item in self.text_structures:
                pdf_text[structure_item] = []
            
            pdf_text['bypage'] = {}

            pdf_text['by_style'] = {}
            for style_item in self.text_styles:
                pdf_text['by_style'][style_item] = {}
                
            pdf_text['by_element_type'] = {}
            for element_type in self.text_element_types:
                pdf_text['by_element_type'][element_type] = []
            
            pdf_text['alltext'] = []
            


            return pdf_text

        def _add_element_dict_to_json(pdf_text, element_dict):
            if element_dict.get('text', '') == '':
                return pdf_text
            
            pdf_text['alltext'].append(element_dict.get('text', ''))
            
            #structure bypage
            page_str = element_dict['page']
            if element_dict['page'] not in pdf_text['bypage']:
                pdf_text['bypage'][page_str] = []
            pdf_text['bypage'][page_str].append(element_dict)
            
            #structure allpages
            pdf_text['allpages'].append(element_dict)
            
            #structure useful/ignored
            pdf_text[element_dict['ignored_or_useful']].append(element_dict)
            
            #style by_style
            for style_item in self.text_styles:
                if element_dict[style_item] not in pdf_text['by_style'][style_item]:
                    pdf_text['by_style'][style_item][element_dict[style_item]] = []
                pdf_text['by_style'][style_item][element_dict[style_item]].append(element_dict)
                
            #element_type by_element_type
            for element_type in self.text_element_types:
                if element_dict[element_type]  not in pdf_text['by_element_type'][element_type]:
                    pdf_text['by_element_type'][element_type]= []
                pdf_text['by_element_type'][element_type].append(element_dict)
            
            print(f"Added element to JSON: {page_str} {element_dict['text']}")
            return pdf_text

        def _text_extraction(element):
            
            try: 
                # Extracting the text from the in-line text element
                extracted_text = element.get_text()
                if extracted_text == None or extracted_text == '':
                    return (None, None, None)
                
                # Find the formats of the text
                # Initialize the list with all the formats that appeared in the line of text
                font_name = []
                font_size = []
                font_name_and_size = []
                
                max_font_size = 0
                
                # Iterating through each character in each line of text
                #capture the font name and size for each character
                for text_line in element:
                    if isinstance(text_line, LTTextContainer):
                        # Iterating through each character in the line of text
                        for character in text_line:
                            if isinstance(character, LTChar):
                                # Append the font name of the character
                                font_name.append(character.fontname)

                                # Append the font size of the character
                                # Rounding because interpreted font sizes can vary slightly (and this is meaningless for this purpose)
                                font_size_rounded = int(round(character.size, 0))
                                font_size.append(font_size_rounded)
                                
                                # Append a string of fontname and size to line_formats
                                font_name_and_size.append(f'{font_size_rounded:04d}_{character.fontname};')
                                
                # Find the unique font sizes and names in the line
                formats_per_line = list(set(font_name_and_size))

                # Find the maximum font size in the line
                
                if len(font_size) > 0:
                    max_font_size = max(font_size)
                
                # Return a tuple with the text in each line along with its format
                return (extracted_text, formats_per_line, max_font_size)    
            except Exception as e:
                print(f"Error: {e}")
                return (None, None, None)

        def _table_converter(table):
            table_string = ''
            # Iterate through each row of the table
            for row_num in range(len(table)):
                row = table[row_num]
                # Remove the line breaker from the wrapped texts
                cleaned_row = [item.replace('\n', ' ') if item is not None and '\n' in item else 'None' if item is None else item for item in row]
                # Convert the table into a string 
                table_string+=('|'+'|'.join(cleaned_row)+'|'+'\n')

                # Adding the clean and dirty row to the list of prior values:
                if isinstance(row, list):
                    self.prior_values_set.add(" ".join([item for item in row if item is not None]).strip())
                    self.prior_values_set.add(" ".join(cleaned_row).strip())
                else:
                    self.prior_values_set.add(row)
                    self.prior_values_set.add(cleaned_row)
            
            # Removing the last line break
            table_string = table_string[:-1]

            

            return table_string

        def _extract_nested_dict_from_pdf(pdf_path):

            # pdf_path = 'example.pdf'

            pages_where_tables_processed = set()

            # Initialize the dictionary that is the final output of this function
            pdf_text = _create_empty_dict()
            
            # PDF Plumber is a specialized librar for extracting tables from PDFs
            # better to open it once here then on every table below
            
            plumbed_pdf = pdfplumber.open(pdf_path) 

            # We extract the pages from the PDF
            #? PDFMiner for loop
            self.log_it(f"Extracting text from PDF: {pdf_path}")
            extracted_pages = list(extract_pages(pdf_path))

            self.log_it(f"PDF Length: {len(extracted_pages)}")
            for pagenum, page in enumerate(extracted_pages):

                # Find all the elements and create a list of tuples with the y coordinate and the element
                # The y coordinate is the top of the element measured from the bottom of the page
                # The greater the y coordinate the higher the element is in the page
                page_elements = [(element.y1, element) for element in page._objs]
                self.log_it(f"Page {pagenum} has {len(page_elements)} elements")
                
                
                # Sort all the elements as they appear in the page 
                # The elements are sorted from the top of the page to the bottom (largest y coordinate to smallest  y coordinate)
                sorted_elements = sorted(page_elements, key=lambda a: a[0], reverse=True)
            

                # Iterate through each element in the page (sorted) to extract the text
                sorted_elements = list(enumerate(sorted_elements))
                for i, sorted_element in sorted_elements:
                    self.log_it(f"Page {pagenum} Element {i} of {len(sorted_elements)} percent complete: {round((i/len(sorted_elements))*100, 2)}%")
                    # Extract the element from the tuple
                    element = sorted_element[1]

                    # Initialize the variable needed for tracking the extracted text from the element
                    element_text = []

                    # Initialize the variables needed for tracking the concatenated formats
                    formats_per_line = []
                    formats_per_line.append("None")
                    max_font_size = 0

                    # initialize a variable to store the page number as a string
                    page_number_str = f'Page_{pagenum:04d}' 
                    
                    # Get the y value for the element in the current iteration
                    y_value= int(round(sorted_element[0],0))
                            
                    # Check the elements for images (if so OCR them)
                    if isinstance(element, LTFigure):

                        # Since there is an image, we will need to crop it out of the PDF,
                        # convert the cropped pdf to an image, and then OCR the image

                        # create a PDF file object
                        pdfFileObj = open(pdf_path, 'rb')
                        
                        # create a PDF reader object (pdfReaded) which is used for cropping images (if there are any)
                        pdfReaded = PyPDF2.PdfReader(pdfFileObj)

                        # This object is used to crop the image from the PDF (if there are any images)
                        pageObj = pdfReaded.pages[pagenum]
                        
                        text_element_type = "image_ocr"

                        # Crop the image from the PDF
                        # Get the coordinates to crop the image from the PDF
                        [image_left, image_top, image_right, image_bottom] = [element.x0,element.y0,element.x1,element.y1] 
            
                        # Crop the page using coordinates (left, bottom, right, top)
                        pageObj.mediabox.lower_left = (image_left, image_bottom)
                        pageObj.mediabox.upper_right = (image_right, image_top)
            
                        # Create a PDF writer object that will be used to save the cropped PDF to a new file
                        cropped_pdf_writer = PyPDF2.PdfWriter()
                        cropped_pdf_writer.add_page(pageObj)
            
                        # Save the cropped PDF to a new file
                        # cropped_file_path = os.path.join(self.temp_folder, f'{spli{page_number_str}_y{y_value}_cropped_pdf_of_image.pdf')
                        
                        with tempfile.TemporaryDirectory() as temp_dir:
                            cropped_pdf_file_path = os.path.join(temp_dir, f'{page_number_str}_y{y_value}_cropped_pdf_of_image.pdf')
                            cropped_pdf_writer.write(cropped_pdf_file_path)
                            
                            # with open(cropped_file_path, 'wb') as cropped_pdf_file:
                            #      cropped_pdf_writer
                            #      cropped_pdf_writer.write(cropped_pdf_file)
                            # use PdftoImage to convert the cropped pdf to an image
                            images = convert_from_path(cropped_pdf_file_path)
                            image = images[0]
                            image_file_path = os.path.join(temp_dir, f'{page_number_str}_y{y_value}_image_of_cropped_pdf.png')  
                            image.save(image_file_path, "PNG")
                            
                            # Extract the text from the image
                            # Read the image
                            img = Image.open(image_file_path)
                            # Extract the text from the image
                            extracted_text = pytesseract.image_to_string(img)

                        # Add the extracted text to the list of text elements
                        if extracted_text != None and extracted_text != '':
                            element_text.append(extracted_text)
                        
                        # Closing the pdf file object
                        pdfFileObj.close()

                    # Check the elements for tables
                    if isinstance(element, LTRect):
                        text_element_type = "rich_text" 
                        
                        if page_number_str not in pages_where_tables_processed:
                            #! .pages is a list containing one pdfplumber.Page instance per page loaded.
                            pdf_plumber_page = plumbed_pdf.pages[pagenum]
                            
                            # Find the number of tables on the page
                            tables_list = pdf_plumber_page.find_tables()

                            # Check if there are tables on the page
                            if len(tables_list) > 0:

                                # if there are tables on the page, extract the table
                                i = 0
                                for table in tables_list:
                                    table_raw_data = pdf_plumber_page.extract_tables()[i]
                                    formatted_table = _table_converter(table_raw_data)
                                    if formatted_table != None and formatted_table != '':
                                        element_text.append(formatted_table)
                                    i+=1
                                    text_element_type = "table_grid"
                            
                            pages_where_tables_processed.add(page_number_str)
                            

                    
                    # Check if the element is a text element (rich text)
                    if isinstance(element, LTTextContainer):
                        
                        text_element_type = "rich_text" 

                        # Use the function to extract the text and format for each text element
                        (extracted_text, formats_concatenated, font_size) = _text_extraction(element)

                        if extracted_text != None and extracted_text != '':
                            element_text.append(extracted_text)
                            formats_per_line = formats_concatenated
                            max_font_size = font_size

                            self.prior_values_set.add(extracted_text)
                    
                    #combine the list of formats into a single string if there is more than one.
                    if isinstance(formats_per_line, list):
                        all_line_formats = '_'.join(formats_per_line)
                    else:
                        all_line_formats = formats_per_line


                    #detailed json for 2nd pass (wich needs to break out the document into nested sections)
                    line_text = {}
                    line_text['text'] = " ".join(element_text) #the text in element
                    line_text['text_as_list'] = []
                    line_text['text_as_list'].append(element_text) #the text in element
                    line_text['formats_concat'] = all_line_formats #the font size appended to font name
                    line_text['max_font_size'] = max_font_size #the max font size across all chars in the element
                    line_text['element_type'] = text_element_type
                    line_text['page'] = page_number_str # either text_from_body (has a format/font/size) or text_from_image / text from table (which don't have formats/fonts/sizes)
                    line_text['y_value'] = y_value # the y value of the element
                    
                    #The entropy calculation is the likelihood, based on the commonness of proximity of letters of the 
                    #text being a real sentence (or nonsense, likes a serial number)
                    line_text_entropy = self.calculate_entropy(line_text['text'])
                    line_text['entropy'] = round(line_text_entropy, 1)
                    line_text['self.entropy_threshold'] = self.entropy_threshold
                
                
                    structure = 'useful'
                    ignore_reason = ''
                    #determine if the text is useful or ignored based on the entropy threshold
                    
                    if line_text['text'] == None or line_text['text'] == '':
                        structure = 'ignored'
                        ignore_reason = 'Empty or None'
                        
                        if line_text_entropy < self.entropy_threshold:
                            structure = 'ignored'
                            ignore_reason = f'Exceed Entropy Threshold of {self.entropy_threshold}'
                    
                            if line_text['text'] in self.prior_values_set:
                                structure = 'ignored'
                                ignore_reason = 'Duplicate'
                    
                    line_text['ignored_or_useful'] = structure
                    line_text['ignore_reason'] = ignore_reason
                    
                    self.prior_values_set.add(line_text['text'])
                    
                    #add the element to the json
                    pdf_text = _add_element_dict_to_json(pdf_text, line_text)
            
            return pdf_text
            
        def main_extract_text_from_pdf(pdf_path, output_path=None, mode="appendasnew", entropy_threshold=4.8, ):

            # Note/Reminder: Tested entropy_thresholds: 2.1-5.5. 4.8 seems to be the best for this purpose. 
            # It captures the most useful text and ignores the most noise.
            
            self.entropy_threshold = entropy_threshold
            supported_doc_types = ['.pdf']
            
            # Get the file extension
            file_extension = self.get_file_extension(pdf_path)
            
            # Check if the file extension is supported
            if file_extension not in supported_doc_types:
                msg = f"File type {file_extension} not supported for file {pdf_path}"
                self.log_it(msg, level='error')
                return pdf_path, False, msg
            
            # try:
            pdf_text = _extract_nested_dict_from_pdf(pdf_path=pdf_path)
            save_result, output_path = self.save_json_to_file(pdf_text, output_path=output_path, mode=mode, file_path=pdf_path)

            return output_path, save_result, pdf_text
        
            # except Exception as e:
            #     msg = f"Error: {e}"
            #     self.log_it(msg, "ERROR")
            #     return pdf_path, False, msg
        
        # Call the main function to extract text from the PDF
        main_extract_text_from_pdf(pdf_path, output_path, mode, entropy_threshold)

    def extract_json_from_office_doc(self, file_path, output_path=None, mode="appendasnew", entropy_threshold=4.8 ):
        """
        Extracts JSON data from an office document (docx, doc, pptx, ppt, xlsx, xls).

        Args:
            file_path (str): The path to the office document file.
            output_path (str, optional): The path to save the extracted JSON file. If not provided, the JSON file will be saved in the same directory as the input file. Defaults to None.
            mode (str, optional): The mode for extracting elements from the document. Defaults to "replace". Can also be "append" to append to an existing JSON file or appendasnew to create a new JSON file with a new name and append to it.
            entropy_threshold (float, optional): The entropy threshold for filtering elements. Defaults to 4.8.

        Returns:
            tuple: A tuple containing the path to the extracted JSON file, a boolean indicating if the extraction was successful, and the extracted JSON data.

        Raises:
            None

        """
        
        def create_dictionary_from_ppt(ppt_documents):
            # Dictionary to store the converted documents
            ppt_dict = {}

            for doc in ppt_documents:
                # Generate a key-safe filename from the original filename in the metadata
                filename = doc.metadata['filename']
                safe_key = re.sub(r'[^\w]', '_', filename)  # Replace non-word characters with underscore

                # Create a list under this filename if it does not already exist
                if safe_key not in ppt_dict:
                    ppt_dict[safe_key] = []

                # Each document's content and metadata can be stored in a dictionary
                doc_info = {
                    'content': doc.page_content,
                    'metadata': doc.metadata
                }

                # Append this document's information to the list associated with the filename
                ppt_dict[safe_key].append(doc_info)

            return ppt_dict

        supported_doc_types = ['.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls']
        
        # Get the file extension
        file_extension = self.get_file_extension(file_path)
        
        # Check if the file extension is supported
        if file_extension not in supported_doc_types:
            msg = f"File type {file_extension} not supported for file {file_path}"
            self.log_it(msg, level='error')
            return file_path, False, msg
        
        # Get the approaciate document loader based on the file extension
        if file_extension in ['.docx', '.doc']:
            doc_loader = self.UnstructuredWordDocumentLoader(file_path=file_path, mode="elements")
        if file_extension in ['.pptx', '.ppt']:
            doc_loader = self.UnstructuredPowerPointLoader(file_path=file_path, mode="elements")
        if file_extension in ['.xlsx', '.xls']:
            doc_loader = self.UnstructuredExcelLoader(file_path=file_path, mode="elements")
        
        try:
            
            # Open the document and extract the JSON data from the document elements
            doc_doc_objs = doc_loader.load()
            
            if file_extension in ['.pptx', '.ppt']:
                doc_dict = create_dictionary_from_ppt(doc_doc_objs)

            else:    
                # turn the document objects into a dictionary
                doc_dict = self.core.load.dump.dumpd(doc_doc_objs)
                
            save_result, output_path = self.save_json_to_file(doc_dict, output_path=output_path, mode=mode, file_path=file_path)

            return output_path, save_result, doc_dict
        
        except Exception as e:
            msg = f"Error: {e}"
            self.log_it(msg, "ERROR")
            return output_path, False, msg
        
    def extract_json_from_image(self, file_path, output_path=None, mode="appendasnew", entropy_threshold=4.8 ):
        
        # Get the file extension
        file_extension = self.get_file_extension(file_path)
        
        # Check if the file extension is supported
        if file_extension not in self.image_types:
            msg = f"File type {file_extension} not supported for file {file_path}"
            self.log_it(msg, level='error')
            return file_path, False, msg
        
        # Configure the path to the tesseract executable
        self.pytesseract.pytesseract.tesseract_cmd = self.pytesseract_executable_path

        try:
            # Load the image
            image = self.Image.open(file_path)
            
            # Use Tesseract to do OCR on the image
            text = self.pytesseract.image_to_string(image)
            
            # Extract detailed information
            # image_cv = cv2.imread(file_path)
            # data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Create a structured dictionary to store text and its box coordinates
            text_dict = {}
            
            text_dict['text'] = text
        
            save_result, output_path = self.save_json_to_file(text_dict, output_path=output_path, mode=mode, file_path=file_path)

            return output_path, save_result, text_dict
        
        except Exception as e:
            msg = f"Error: {e}"
            self.log_it(msg, "ERROR")
            return output_path, False, msg
        
    def extract_json_from_files(self, file_path_list, output_path=None, mode="appendasnew", entropy_threshold=4.8 ):
        
        # Check if the file path is a list
        if not isinstance(file_path_list, list):
            file_path_list = [file_path_list]
        
        if output_path is not None:
            self.all_extracts_path = output_path
        
        for file_path in file_path_list:
            # Get the file extension
            file_extension = self.get_file_extension(file_path)
            
            if file_extension in self.office_document_types:
                self.extract_json_from_office_doc(file_path, output_path, mode, entropy_threshold)
            elif file_extension in self.pdf_types:
                self.extract_json_from_pdf(file_path, output_path, mode, entropy_threshold)
            elif file_extension in self.image_types:
                self.extract_json_from_image(file_path, output_path, mode, entropy_threshold)
            else:
                msg = f"File type {file_extension} not supported for file {file_path}"
                self.log_it(msg, level='error')
                continue
        
        # Create a unique string based on the current time
        unique_string = datetime.now().strftime("%YY.%m.%dd.%H.%M.%S")
        
        for key in self.all_extracts_dict.keys():
                file_dict = self.all_extracts_dict[key]
                if isinstance(file_dict, dict):
                    alltext = file_dict.get('alltext', [])
                    alltext = "\n".join(alltext)
                    with open (f"{self.all_extracts_path}/{key}.txt", 'w') as f:
                        f.write(alltext)
                        f.close()
                        self.all_extracts_dict[key]["textdump"] = alltext
                            
        return_dict = {} 
        return_dict['rowkey'] = unique_string
        return_dict['partitionkey'] = "Multi-Document-Text-Extraction"
        return_dict['structdata'] = self.all_extracts_dict
        
        return_dict['contenttype'] = "Document"
        # return_dict['title'] = ""
        # return_dict['url'] = ""
        return_dict['textdump'] = file_dict.get('textdump', "")
        return_dict['alltext'] = json.dumps(file_dict.get('alltext', {}))
        return_dict['bypage'] = json.dumps(file_dict.get('bypage', {}))
        return_dict['allpages'] = json.dumps(file_dict.get('allpages', {}))
        
        
            
        if self.all_extracts_path != '' and self.all_extracts_dict != {}:    
            with open(f"{self.all_extracts_path}/{unique_string}.json", 'w') as f:
                f.write(json.dumps(return_dict, indent=4))
                f.close()
        
        return return_dict
            
      

####################################
####      DEEPGRAM CLASS       ####
####################################

class deepgram_audio_transcription():
    def __init__(self):
        #Audio Transcription
        
        from io import BytesIO
        from deepgram import (
            DeepgramClient,
            DeepgramClientOptions,
            FileSource,
            LiveOptions,
            LiveTranscriptionEvents,
            PrerecordedOptions,
            Microphone)
        
        
        self.deepgram_api_key = os.getenv('DEEPGRAM_API_KEY')
        self.base_flask_url = BASE_FLASK_URL
        self.models = {
            "Nova-2": "nova-2-ea",
            "Nova": "nova",
            "Whisper Cloud": "whisper-medium",
            "Enhanced": "enhanced",
            "Base": "base",}
        self.languages = {
            "Automatic Language Detection": None,
            "English": "en",
            "French": "fr",
            "Hindi": "hi",}
        
    # Function to make an asynchronous request to the specified URL
    def fire_and_forget(self, flask_path, params=None, ):
            """Make an asynchronous GET request to the specified URL."""
            url = self.base_flask_url + flask_path
            def request_thread(url, params):
                """The thread function that performs the request."""
                try:
                    requests.get(url, params=params)
                    print("Request sent successfully to Flask Background")
                except Exception as e:
                    print(f"Failed to send request: {e}")

            # Create and start a thread to make the request
            thread = Thread(target=request_thread, args=(url, params))
            thread.start()

    def transcribe_youtube(self, yt_url):
        import requests
        from io import BytesIO
        from pytube import YouTube
        
        # Function to get the audio from a YouTube video
        def get_youtube_audio(yt_url):
            yt = YouTube(yt_url)
            
            # extract only the audio
            video = yt.streams.filter(only_audio=True).first()

            # download the video’s audio to a buffer
            audio = BytesIO()
            video.stream_to_buffer(buffer=audio)

            return audio
        
        # Initialize the file dictionary to be returned
        file_dict = {}
        file_dict.update({"structdata": {}})
        
        
        #Obtain the audio from the YouTube video
        audio = get_youtube_audio(yt_url)
        
        
        headers = {
            'Authorization': f'Token {self.deepgram_api_key}',
            'content-type': 'audio/mp3'
        }
        
        url = 'https://api.deepgram.com/v1/listen?punctuate=true&summarize=true&topics=true&diarize=true'
        
        # Send the audio to Deepgram for transcription
        response = requests.post(url, headers=headers, data=audio.getvalue())
        
        topics = []
        
        ## If the response is successful, extract the summary, transcript, and topics
        if response.ok:
            response = response.json()
        
        else:
            # Transcription failed
            print(f"ERROR: {response.status_code} {response.text}")
            return None
            
        # AI Summmarization of the Audio
        summary = response['results']['channels'][0]['alternatives'][0]['summaries'][0]['summary']
        
        #Full Transcript of the Audio
        transcript = response['results']['channels'][0]['alternatives'][0]['transcript']
        
        #List of Topics in the Audio
        for topic_segment in response['results']['topics']['segments'][0]['topics']:    
            new_topic = topic_segment.get('topic', False)
            if not new_topic:
                continue
            topics.append(new_topic)
        
        file_dict['contenttype'] = "Youtube"
        file_dict['title'] = yt_url
        file_dict['url'] = yt_url
        file_dict['structdata'] = response
        file_dict["rowkey"] = yt_url
        file_dict["partitionkey"] = "Youtube-Text-Extraction"
        file_dict['textdump'] = json.dumps(transcript)
        file_dict['summary'] = json.dumps(summary)
        file_dict['topics'] = topics
        
        return file_dict

    def transcribe_url(self, source) -> None:
        options = self.PrerecordedOptions
        
        response = (
            self.deepgram.listen.prerecorded.v("1")
            .transcribe_url(
                source,
                options,
            )
            .to_dict()
        )
        return response

    def start_live_transcription(self):
        try:
            self.fire_and_forget("startaudiorec")
            st.info("Starting ...")
            st.session_state.btn_transcription_start_stop = "Starting ..."

        except Exception as e:
            err_message = f"Could not connect to Flask Background "
            st.session_state.btn_transcription_start_stop = "Unable to start"
            print(err_message)
            st.error(err_message)
            return

    async def transcribe_audio_files_async(self, audio_file_path_list):
        # Initializes the Deepgram SDK
        # # API key for Deepgram
        # from deepgram import (DeepgramClient)
        # deepgram: DeepgramClient = DeepgramClient()
        
        # Open the audio file
        if not isinstance(audio_file_path_list, list):
            audio_file_path_list = [audio_file_path_list]
        
        paths_are_valid = True
        for audio_file_path in audio_file_path_list:
            if not os.path.exists(audio_file_path):
                paths_are_valid = False
        
        if not paths_are_valid:
            st.info(f"One or more of the file paths received are not valid: {audio_file_path_list}")
            return
        
        transcription_tasks = []
        for audio_file_path in audio_file_path_list:
            with open(audio_file_path, 'rb') as audio:
                # ...or replace mimetype as appropriate
                source = {'buffer': audio, 'mimetype': 'audio/wav'}
                transcription_tasks.append(await self.DeepgramClient.transcription.prerecorded(source, {'punctuate': True}))
        responses = asyncio.gather(*transcription_tasks)

        for response in responses:    
            json_obj = json.dumps(response, indent=4)
            print(json_obj)
            with open("transcribed.txt", "w") as f:
                f.write(json_obj)

    def get_audio_device_list(self):
        import pyaudio

        # Create an instance of PyAudio
        p = pyaudio.PyAudio()

        # Get the number of audio devices
        num_devices = p.get_device_count()

        # Get the info for each audio device
        device_list = []
        for i in range(0, num_devices):
            info = p.get_device_info_by_index(i)
            device_list.append(f"-  Device {i}: {info['name']} - Max Input Channels: {info['maxInputChannels']}  \n")
        return device_list


####################################
####    Dow Jones Functions     ####
####################################
def display_dj_connection_status():
        
    def get_new_token():    
        import classes._class_dow_jones as dj
        if st.session_state.djsession is not None:
            DJ_Session = st.session_state.djsession
        else:
            DJ_Session = dj.DJSearch()
            DJ_Session.connect()
            
        with st.spinner(':orange[Connecting to Dow Jones...]'):
            if st.session_state.djtoken is None or st.session_state.djtoken == {}:
                access_token = DJ_Session.get_nearest_valid_authz_token()
            else:
                st.session_state.djtoken = access_token
        
        #If connection failed
        if access_token is None:
            message=f":red[✘ Disconnected: Dow Jones API Authorization Failed]"
            st.session_state._message = message
        
        else:
            #Successful
            message = (f"**Dow Jones Connection :green[Successful**]")
            st.session_state.djtoken_status_message = message
            st.session_state.djtoken = access_token
            
    if st.session_state.djtoken == {}:
        get_new_token()
    
    st.markdown(st.session_state.djtoken_status_message, unsafe_allow_html=True)
    if st.button('DJ ♾️', use_container_width=True):
        get_new_token()
         
def display_dj_search_results2(simple_search_string = "", search_date_range="Last6Months", page_offset=0, search_results=None, show_chatbot=False):
    st.subheader('Search Results', divider='gray')
    list_result_col, viewer_col = st.columns([1, 2])
    st.session_state.show_results = False
    st.session_state.show_article = False
    
    #Logic to display previous search results or article details
    for key in st.session_state.keys():
        if key.startswith("drn:"):
            if st.session_state[key] == True:
                st.session_state.viewed_article_id = key
                for result in st.session_state.search_result_cache:
                    for article in result:
                        if isinstance(article, dict):
                            if article.get('id', '') == key:
                                st.session_state.viewed_article_cache = article
                                st.session_state.show_article = True
                                st.session_state.show_results = True
                                break  
    
    def execute_search():
        import classes._class_dow_jones as dj
        import asyncio
        DJ_Session = dj.DJSearch()
        search_results = asyncio.run(DJ_Session.search_async(
            search_string=simple_search_string, search_date_range=search_date_range, 
            page_offset=page_offset, number_of_pages_to_request=5))
        if DJ_Session.search_has_results:
            st.session_state.search_result_cache = search_results
            st.session_state.current_search_summary = DJ_Session.current_search_summary
            st.session_state.show_results = True
            st.session_state.show_article = False
    
    if simple_search_string != "" and search_results is None:
        execute_search()
        st.session_state.show_results = True
    else:
        st.session_state.show_results = False
    
    # Means this is a re-run with results get the prior results
    if st.session_state.search_result_cache is not None and st.session_state.search_result_cache != "" and search_results is None:
        st.session_state.show_results = True
    
    # Means this is a new search
    if search_results is not None:
        st.session_state.show_results = True
        st.session_state.search_result_cache = search_results
    
    if st.session_state.show_results:
        
        with list_result_col:
            summary = st.expander("Search Summary", expanded=False)
            summary.write(st.session_state.current_search_summary)
            result_id_set = set()
            for result_run in st.session_state.search_result_cache:
                for result in result_run:
                    if isinstance(result, dict):
                        if result.get('id', '') != '' and result.get('id', '') not in result_id_set:
                            result_id_set.add(result.get('id', ''))
                            img_col, text_col, full_article_btn = st.columns([.5, 3, .3])
                            with img_col:
                                st.image(result.get('image_dict', {}).get('url', ""), use_column_width="always")
                            with text_col:
                                list_html_dict = result.get('html', {}).get('html_list', [])
                                for item in list_html_dict:
                                    st.markdown(item, unsafe_allow_html=True)
                            st.markdown("---", unsafe_allow_html=True)
                            with full_article_btn:
                                st.button("►", key=result.get('id', uuid.uuid4()),  use_container_width=True, type="secondary")
            
        # If this is a re-run with article details get the prior article details
        if st.session_state.show_article:
            # viewer_col.write(st.session_state.viewed_article_cache)     
            lspace, article_space, rspace = viewer_col.columns([2, 7, 2])     
            html_dict = st.session_state.viewed_article_cache.get('html', []) #dict is sequeced for article display
            for key in html_dict.keys():
                html_list = html_dict.get(key)
                for html in html_list:          #value of each node is a list of html strings
                    if 'html_list' in key:
                        continue
                    if 'image' in key:
                        html_out = html.get('html', '')    
                        article_space.markdown(html_out, unsafe_allow_html=True)
                    else:
                        if html is not None and html != "":
                            article_space.markdown(html, unsafe_allow_html=True)     

def display_dj_search_results(streamlit_column):
    # Dow Jones Search Results

    with streamlit_column:
        view_res = st.button(f"Result Grid", use_container_width=True)
        if view_res:
            if st.session_state.show_search_results:
                st.session_state.show_search_results = False
            else:
                st.session_state.show_search_results = True
    if st.session_state.show_search_results:
        rg = st.expander("Result Grid", expanded=False)
    
        if st.session_state.search_result_cache is not None and st.session_state.search_result_cache != "":
            if isinstance(st.session_state.search_result_cache, list) and len(st.session_state.search_result_cache) >0:  
                ss_data = st.session_state.search_result_cache
                formatted_result_list = []
                for search_group in ss_data:
                    for result in search_group:
                        if isinstance(result, dict):
                            next_result = {
                            'search_string': result.get('PartitionKey', ""),
                            'id': result.get('id', ""),
                            'Rich': result.get('is_rich', ""),
                            'headline': result.get('headline', ""),
                            'date-time': result.get('user_customized_date_time', ""),
                            'link': result.get('link', ""),
                            }
                            formatted_result_list.append(next_result)
                rg.dataframe(formatted_result_list)
        else: 
            rg.write("No search results to display")


####################################
##    CRUD FOR TRANSCRIPTION    ####
####################################         
class transcription_library_crud():
    def __init__(self):
        pass
    # Database connection
    def get_db_connection(self):
        db_url = os.environ.get('LOCAL_POSTGRES_CONNECTION_STRING1', 'postgresql://mytech:mytech@localhost:5400/mytech')
        engine = create_engine(db_url)
        return engine.connect()

    # Load data from the database
    def load_data(self, conn):
        query = "SELECT * FROM mytech.transcription where iscurrent = true"
        return pd.read_sql(query, conn)

    # Insert a new record into the database
    def insert_data(self, conn, data):
        data.to_sql('transcription', conn, schema='mytech', if_exists='append', index=False)

    # Update an existing record in the database
    def update_data(self, conn, data):
        data.to_sql('transcription', conn, schema='mytech', if_exists='replace', index=False)

    # Delete a record from the database
    def delete_data(self,  conn, data):
        query = f"DELETE FROM mytech.transcription WHERE id = {data['id'].iloc[0]}"
        conn.execute(query)


####################################
##    PROSPECT LIST CLASS    ####
####################################         
class prospect_list():
    def __init__(self):
        self.connection_string = os.getenv('LOCAL_POSTGRES_CONNECTION_STRING1', 'postgresql://mytech:mytech@localhost:5400/mytech')
        
    async def create_prospect(self, table_name):
        create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS prospect (
                id serial4 NOT NULL,
                Organization_CRD varchar(100) NULL,
                SEC varchar(100) NULL,
                Primary_Business_Name varchar(100) NULL,
                Legal_Name varchar(100) NULL,
                Main_Office_Street_Address_1 varchar(100) NULL,
                Main_Office_Street_Address_2 varchar(100) NULL,
                Main_Office_City varchar(100) NULL,
                Main_Office_State varchar(100) NULL,
                Main_Office_Country varchar(100) NULL,
                Main_Office_Postal_Code varchar(100) NULL,
                Main_Office_Telephone_Number varchar(100) NULL,
                Chief_Compliance_Officer_Name varchar(100) NULL,
                Chief_Compliance_Officer_Other_Titles varchar(100) NULL,
                Chief_Compliance_Officer_Telephone varchar(100) NULL,
                Chief_Compliance_Officer_Email varchar(100) NULL,
                SEC_Status_Effective_Date varchar(100) NULL,
                Website_Address varchar(200) NULL,
                Entity_Type varchar(100) NULL,
                Governing_Country varchar(100) NULL,
                Total_Gross_Assets_of_Private_Funds DECIMAL
            );
        """
        
        
        
        conn = await asyncpg.connect(self.connection_string)
        try:
            await conn.execute(create_table_sql)
            print(f"Table prospect created successfully.")
        finally:
            await conn.close()
            
    async def load_json_to_table(connection_string, table_name, json_file_path):
        conn = await asyncpg.connect(connection_string)
        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)

            insert_sql = f"""
            INSERT INTO {table_name} (
                Organization_CRD,
                SEC,
                Primary_Business_Name,
                Legal_Name,
                Main_Office_Street_Address_1,
                Main_Office_Street_Address_2,
                Main_Office_City,
                Main_Office_State,
                Main_Office_Country,
                Main_Office_Postal_Code,
                Main_Office_Telephone_Number,
                Chief_Compliance_Officer_Name,
                Chief_Compliance_Officer_Other_Titles,
                Chief_Compliance_Officer_Telephone,
                Chief_Compliance_Officer_Email,
                SEC_Status_Effective_Date,
                Website_Address,
                Entity_Type,
                Governing_Country,
                Total_Gross_Assets_of_Private_Funds
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20
            );
            """

            for record in data:
                values = (
                    record.get("Organization_CRD"),
                    record.get("SEC"),
                    record.get("Primary_Business_Name"),
                    record.get("Legal_Name"),
                    record.get("Main_Office_Street_Address_1"),
                    record.get("Main_Office_Street_Address_2"),
                    record.get("Main_Office_City"),
                    record.get("Main_Office_State"),
                    record.get("Main_Office_Country"),
                    record.get("Main_Office_Postal_Code"),
                    record.get("Main_Office_Telephone_Number"),
                    record.get("Chief_Compliance_Officer_Name"),
                    record.get("Chief_Compliance_Officer_Other_Titles"),
                    record.get("Chief_Compliance_Officer_Telephone"),
                    record.get("Chief_Compliance_Officer_Email"),
                    record.get("SEC_Status_Effective_Date"),
                    record.get("Website_Address"),
                    record.get("Entity_Type"),
                    record.get("Governing_Country"),
                    record.get("Total_Gross_Assets_of_Private_Funds")
                )
                await conn.execute(insert_sql, *values)

            print(f"Data from {json_file_path} loaded into {table_name} successfully.")
        finally:
            await conn.close()


#!#######    SCRIPT BODY     ########    
            
SETUP_DATABASE = False
# cs = PsqlSimpleStorage

prospect_list = prospect_list()
asyncio.run(prospect_list.create_prospect("prospect"))