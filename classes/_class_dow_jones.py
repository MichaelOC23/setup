

#!##########   SETUP ENVIRONMENT   ###############
#! Run the file: __py_env_setup_dj.sh
#! This will create the virtual environment and install the required libraries

#!#######    OPEN ITEMS DISCUSSEED    ############
#! 1) As of now, I have turned off the creation of the Complete Taxonomy.
#!    This can be changed when the table is ready to pull it from

#!#######    Use the RunExamples Function    ############
#! 1) At the top there is an example of how to use this this class

from datetime import datetime, timedelta
import time
from numpy import isin
import requests
import pytz
import re
import os
import json
import logging
import inspect
import random
import asyncio
import concurrent.futures
from typing import Any, Dict, LiteralString


from azure.data.tables.aio import TableClient
from azure.storage.blob.aio import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import ResourceExistsError, HttpResponseError
from azure.data.tables import UpdateMode
from _class_storage import _storage as storage
from _class_storage import PsqlSimpleStorage as bmm

from dotenv import load_dotenv
import os

ALLOW_TOKEN_PERSISTENCE=True

# Load the .env file
load_dotenv()


# 
            
# Input seed that drives the wait time between API requests to Dow Joins
DEFAULT_SLEEP_TIME = .3  # Default sleep time in seconds

# get_search_results   
class DJSearch:

    def __init__(self):
        self.last_log_entry = ""       
        
        
        # This Unique Run ID is used to create unique file names where needed    
        self.UNIQUE_RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.time_remaining = ""
        
        self.add_to_dj_log(f'Unique run id: {self.UNIQUE_RUN_ID}')
        logging.basicConfig(level=logging.DEBUG)  
        
        # Configure basic logging
        self.add_to_dj_log('Initializing DJSearch __init__')
        
        # Time Stamps
        self.created_at = datetime.now()
        self.last_token_attempt_time = None
        
        #Dow Jones
        self.CLIENT_ID = os.environ.get('DOW_JONES_CLIENT_ID') #Secrets management
        self.USER_NAME = os.environ.get('DOW_JONES_USER_NAME') #Secrets management
        self.PASSWORD = os.environ.get('DOW_JONES_PASSWORD') #Secrets management

        self.DJ_SEARCH_URL = "https://api.dowjones.com/content/realtime/search" #endpoint
        self.DJ_CONTENT_URL = "https://api.dowjones.com/content" #endpoint
        self.URL = "https://accounts.dowjones.com/oauth2/v1/token"
        

        if not self.CLIENT_ID or not self.USER_NAME or not self.PASSWORD:
            self.add_to_dj_log('Dow Jones credentials not available in environment variables. Required variables: DOW_JONES_CLIENT_ID, DOW_JONES_USER_NAME, DOW_JONES_PASSWORD', 'ERROR')
            raise ValueError(self.last_log_entry)
        
        self.storage = storage()
        self.access_key = os.environ["AZURE_STORAGE_KEY"]
        self.endpoint_suffix = os.environ["TABLES_STORAGE_ENDPOINT_SUFFIX"]
        self.account_name = os.environ["TABLES_STORAGE_ACCOUNT_NAME"]
        self.table_name = "devparameters"
        self.endpoint = f"{self.account_name}.table.{self.endpoint_suffix}"
        self.connection_string = f"DefaultEndpointsProtocol=https;AccountName={self.account_name};AccountKey={self.access_key};EndpointSuffix={self.endpoint_suffix}"
        
        if os.environ.get('DJ_ACCESS_TOKEN', '') !='':  
            self.djtoken = json.loads(os.environ['DJ_ACCESS_TOKEN'])
        else:
            self.djtoken = {}
        
        # Assembled Search Parameters
        self.search_string = ''

        # Loaded/Current Taxonomies
        self.fixed_taxonomy_dict = get_dj_fixed_taxonomy() # This the fixed taxonomy from the Dow Jones API that is in _fixed_taxonomy_dj.py
        self.complete_taxonomy_dict = None
        self.full_taxonomy_by_code_dict = {}
        self.bmm = bmm()
        
        self.current_search_summary = {
                "unique_article_ids":            None,
                "number_of_search_threads":     0,
                "number_of_articles":           0,
                "unique_articles_returned":     0, 
                "rich_articles_returned":       0,
                
            }
        
        self.search_list = []

        
        # Loaded/Current Sub-Category Taxonomies (used for UI)
        self.industries = None
        self.regions = None
        self.subjects = None
        self.languages = None
                
        # Most recent search results
        self.search_payload = None

        self.search_results = None
        self.search_has_results = False
        self.search_has_error = False
        self.search_error_message = None

        
        # If a connectivity, API or JSON error occurs this is the time to wait before trying again
        self.sleep_on_connection_error = 60
        
        #Dictionary of retrieved articles
        self.articles = {}
        
        self.show_meta = False  
        self.content_resources_list = [""]



#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#   
#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
#!#######             AUTHENTICATION             ##########
#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
    def print_search_results(self):
        summary = json.dumps(self.current_search_summary, indent=4)
        self.add_to_dj_log(f"Search Summary: {summary}", 'PINK')
    
    def display_token(self):
        
        token_dict = asyncio.run(self.storage.get_token())
        token = token_dict.get('parameter_value', 'No Token Found')
        # print(token)
        
    def connect(self) -> LiteralString | str | None | Any:            
        
        # Authenticate and get a valid access token
        token = self.get_nearest_valid_authz_token()
        
        #The complete taxonomy is all the fixed available data for searching and filtering. 
        # It's a static file that we update regular
        # If it is not there, it will be created
        # self.set_complete_taxonomy()
        
        #Connection Success!
        self.add_to_dj_log(f'Connected successfully and acquired needed taxonomies')   
        
        return token         

    def get_nearest_valid_authz_token(self):
        
        def try_to_get_env_variable_token():
            
            try:
                if 'DJ_ACCESS_TOKEN' in os.environ:
                    token_dict = json.loads(os.environ['DJ_ACCESS_TOKEN'])
                    access_token = token_dict.get('access_token', '')
                    if access_token != '':
                        now = datetime.now()
                        expiration_time_str = token_dict.get('EXPIRES_AT', '')
                        if expiration_time_str != '':
                            expiration_time = datetime.strptime(expiration_time_str, '%Y-%m-%d %H:%M:%S')
                            if expiration_time > now:
                                self.add_to_dj_log(f"Token Found in Environment Variables", 'GREEN')
                                return token_dict, token_dict.get('access_token', ''), True
                            else: 
                                self.add_to_dj_log(f"Token from Env Variable is Expired", 'YELLOW')
                                os.environ['DJ_ACCESS_TOKEN'] = {}
                                return None, None, False
                        else:
                            return None, None, False
                    else:
                        return None, None, False    
                else:
                    os.environ['DJ_ACCESS_TOKEN'] = {}
                    return None, None, False
            except:
                self.add_to_dj_log(f"Error getting token from environment variables", 'RED_U')
                return None, None, False
        
        def try_to_get_self_token():
            if self.djtoken == {} or not isinstance(self.djtoken, dict):
                return None, None, False
            else:
                if self.djtoken.get('access_token', '') != '':
                    now = datetime.now()
                    expiration_time_str = self.djtoken.get('EXPIRES_AT', '')
                    if expiration_time_str != '':
                        expiration_time = datetime.strptime(expiration_time_str, '%Y-%m-%d %H:%M:%S')
                        if expiration_time > now:
                            return self.djtoken, self.djtoken.get('access_token', 'No Token in Token Dict'), True
            #All other cases
            return None, None, False
             
        def try_to_get_token_from_storage():
            
            # Check if the token file exists, if it does, read it and return the token
            token_dict_entity = asyncio.run(self.storage.get_token())
            
            if token_dict_entity is not None and isinstance(token_dict_entity, dict) and token_dict_entity != {}:
                if token_dict_entity.get('access_token', '') != '':
                    now = datetime.now()
                    expiration_time_str = token_dict_entity.get('EXPIRES_AT', '')
                    if expiration_time_str != '':
                        expiration_time = datetime.strptime(expiration_time_str, '%Y-%m-%d %H:%M:%S')
                        if expiration_time > now:
                            return token_dict_entity, token_dict_entity.get('access_token', 'No Token in Token Dict'), True
            
            #all other cases
            return None, None, False
                           
        def destroy_stored_token():
            # try:
                self.djtoken = {}
                response = asyncio.run (self.storage.delete_token())
                self.add_to_dj_log(f"Token Deleted", 'GREEN')
                os.environ['DJ_ACCESS_TOKEN'] = ""
                return True
            # except:
                # self.add_to_dj_log(f"Error deleting token", 'RED_U')
                # return None

        def get_new_token_from_dj():
            # This function orchestrates tryingt to use the stored token, but, if it's not there, get a new one.
            # Ideally we could validate it in this fucntion, but I'm not clear that's possible without adding overhead and slowing the calls.
            # Usage example (replace with actual credentials):
            
            self.time_remaining = ''
            
            self.add_to_dj_log(f"There are 2 Steps to obtaining a new token) \n Step 1 of 2: Requesting Authentication Token", "YELLOW_BOLD")
            
            # Step 1 of 3: Requesting Authentication Token
            response_text = get_new_authentication_token(self.CLIENT_ID, self.PASSWORD, self.USER_NAME)
            
            response_dict, authn_id_token, success = self.get_dict_and_value_from_text_safely(response_text, "id_token", "Get New Authentication Token")
            
            if success:
                self.add_to_dj_log(f"Step 1 Successful: obtained authn_id_token", "YELLOW_BOLD")
            else:
                return None

            # Get the JWT Authorization Token
            self.add_to_dj_log('Step 2 of 2: Requesting the JWT Authorization Token', "LIGHTBLUE_BOLD")
            jwt_response = get_new_jwt_authorization_token(authn_id_token, self.CLIENT_ID)
            authz_access_token, access_token, success = self.get_dict_and_value_from_text_safely(jwt_response, "access_token", "Get New Authorization Token")
            
            if success:
                self.add_to_dj_log(f"Step 2 Successful: Obtained jwt_response and the authorization token", "LIGHTBLUE_BOLD")
                self.time_remaining = f"Token is valid. {round(3600/60,0)} minutes until expiration."
                self.djtoken = authz_access_token
                os.environ['DJ_ACCESS_TOKEN'] = json.dumps(authz_access_token)
                return access_token
            else:
                return None
        
        def get_new_authentication_token(client_id, password, username):
            url = self.URL

            payload = {
                "client_id": client_id,
                "connection": "service-account",
                "device": "orion-tablet",
                "grant_type": "password",
                "password": password,
                "scope": "openid service_account_id offline_access",
                "username": username
            }

            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }

            request_start = datetime.now()
            response = requests.post(url, data=payload, headers=headers)
            total_request_time = (datetime.now() - request_start).total_seconds()
            
            # self.add_to_dj_log(f"Response from new_ {response.text}")

            if response.ok:
                if total_request_time > 1:
                    self.add_to_dj_log(f"OK: Received authn_id_token in {total_request_time} seconds", "RED")
                else:
                    self.add_to_dj_log(f"OK: Received authn_id_token in {total_request_time} seconds", "GREEN")
                    
                # with open(f'{self.IO_FOLDER_PATH}/djlog_authn_id_token_{self.UNIQUE_RUN_ID}.json', 'w') as f:
                #     f.write(json.dumps(response.json(), indent=4))
                return response.text
            else:
                return f"Error: {response.status_code} - {response.text}"

        def get_new_jwt_authorization_token(authn_id_token, client_id):
            url = "https://accounts.dowjones.com/oauth2/v1/token"

            payload = {
                "assertion": authn_id_token,
                "client_id": client_id,
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "scope": "openid pib"
            }

            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            self.add_to_dj_log(f"Requesting JWT Authorization Token with Payload: {payload} | Headers: {headers} | URL: {url}")
            
            JWT_AuthZ_Request_Start = datetime.now()
            response = requests.post(url, data=payload, headers=headers)
            JWT_AuthZ_Request_Call_time = datetime.now() - JWT_AuthZ_Request_Start
            
            #Create a custom log file for response times only so I can see if there are any patterns
            # with open(f'{self.IO_FOLDER_PATH}/djlog_jwt_authz_request_times.json', 'a') as f:
            #     f.write(f"\n{JWT_AuthZ_Request_Call_time.total_seconds()}")
            
            # Log our additional data points
            response_json = response.json()
            
            # Add the request call time to the response in seconds
            response_json['RESPONSE_TIME'] = f"{JWT_AuthZ_Request_Call_time.total_seconds()}"
            
            # Add 3600 seconds to the current time to get the expiration time (since time is relative to the current time, time zones don't matter)
            response_json['EXPIRES_AT'] = (JWT_AuthZ_Request_Start + timedelta(seconds=3600)).strftime("%Y-%m-%d %H:%M:%S")
            #print(JWT_AuthZ_Request_Start, JWT_AuthZ_Request_Call_time, response_json['EXPIRES_AT'])
            
            destroy_stored_token()
            extract_and_store_new_token_from_dict(response_json)
            
            if response.ok:
                self.add_to_dj_log(f"OK: Received jwt_token")
                return json.dumps(response_json, indent=4)
            else:
                self.add_to_dj_log(f"Error: {response.status_code} - {response.text}", 'ERROR')
                return f"Error: {response.status_code} - {response.text}"
       
        def extract_and_store_new_token_from_dict(token_dict):
            try:    
                token = token_dict.get('access_token', "")
                if token != "":
                    self.djtoken = token_dict
                    asyncio.run(self.storage.save_token(json.dumps(token_dict)))
                    
                    self.add_to_dj_log(f"Token Created, stored and set to self", 'GREEN')

                else:
                    self.add_to_dj_log(f"Token is empty", 'RED_U')


            except:
                self.add_to_dj_log(f"Error creating token", 'RED_U')


        #! BEGINNING OF GET NEAREST VALID AUTHZ TOKEN
         
        now = datetime.now()
        
        # Check if the token exists on the self object of the class    
        token_dict, access_token, success = try_to_get_self_token()
        if success:
            return access_token
        
        token_dict, access_token, success = try_to_get_env_variable_token()
        if success:
            return access_token
        
        
        
        if not success:
            # Check if the token exists in storage
            token_dict, access_token, success = try_to_get_token_from_storage()
            
        if success:
            return access_token
        
        else: # If the token doesn't exist, create a new one
            destroy_stored_token()
            
            #If the last token attempt was less than 10 minutes ago, sleep for 1 minute
            if self.last_token_attempt_time is not None and (datetime.now() - self.last_token_attempt_time).total_seconds() < 600:
                self.add_to_dj_log(f"Last token attempt was less than 10 minutes ago. Sleeping for 1 minute", 'ORANGE')
                time.sleep(60)
            
            new_valid_token = get_new_token_from_dj()
            self.last_token_attempt_time = datetime.now()
            return new_valid_token

    def time_until_expiration(self):
        self.get_nearest_valid_authz_token()
        return self.time_remaining     



#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#   
#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
#!#######          REUSABLE FUNCTIONS            ##########
#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
    def sanitize_filename(self, filename):
            # Characters to remove
            invalid_chars = ':/\\?*|"<>'
            
            # Replace each invalid character with an empty string
            for char in invalid_chars:
                filename = filename.replace(char, '')
            
            # Additionally, remove leading periods to avoid hidden files
            filename = filename.lstrip('.')
            
            return filename
    
    def got_dict_from_text_safely(text_value):
        if text_value is not None and text_value != "":
            try:
                return json.loads(text_value)
            except:
                return 
            
    def get_dict_and_value_from_text_safely(self, text_to_convert, should_be_there_key, purpose_text):
            
        def construct_error_message(point_of_error, text_to_convert, should_be_there_key, purpose_text, e, caller_frame):
            try: 
                c = {"RED": '\033[0;31m', "RED_U": '\033[4;31m', "RED_BLINK": '\033[5;31m', "GREEN": '\033[2;32m', 
                        "GREEN_BLINK": '\033[5;32m',"YELLOW_BOLD": '\033[1;33m', "PURPLE": '\033[1;34m', "PINK": '\033[0;35m', 
                        "LIGHTBLUE_BOLD": '\033[1;36m', "ORANGE": '\033[1;91m', "BLUE": '\033[1;94m', "CYAN": '\033[1;96m', "MAGENTA": '\033[1;95m'}
                
                caller_function_name = caller_frame.f_code.co_name
                err = f""" \n{c["MAGENTA"]}|-----------  JSON Parsing Error  -----------|
                \n{c["RED_U"]}Error occured while parsing JSON from text for the purpose of: {c["PINK"]}{purpose_text}
                \n{c["LIGHTBLUE_BOLD"]}---> Point of error was: {c["RED"]}{point_of_error}
                \n{c["LIGHTBLUE_BOLD"]}---> 'Should-Be-There-Key' was: {c["BLUE"]}{should_be_there_key}
                \n{c["LIGHTBLUE_BOLD"]}---> Calling Function: {c["YELLOW_BOLD"]}{caller_function_name}
                \n{c["LIGHTBLUE_BOLD"]}---> Error: {c["RED"]}{e}
                \n{c["LIGHTBLUE_BOLD"]}---> Text: {c["CYAN"]}{text_to_convert:[:100]}
                \n{c["MAGENTA"]}|------------------------------------------|{c["NONE"]}"""
                return err
            except:
                return f"Error constructing error message: {e}"
        
        """Handles potential errors during an operation, providing context and retries.

        Args:
            text_to_convert (str): The text to convert to a dictionary.
            should_be_there_key (str): The key that should be in the dictionary.
            purpose_text (str): A description of the purpose of the operation.

        Returns:
            tuple: A tuple containing 3 values: 
            1) The dictionary parsed from the text, 
            2) The value of the key that should be there (or the error message if failed)
            and 3) A boolean indicating success or failure.
                
        """
        
        #Robust error handling for parsing JSON from text (this is a common and critical operation)       
        #DICT conversion
        if text_to_convert is not None and text_to_convert != "":
            try:
                dict_value = json.loads(text_to_convert)
            except json.JSONDecodeError as e:
                error_message = construct_error_message("Conversion of Text to Dictionary Failed", text_to_convert, should_be_there_key, purpose_text, e, inspect.currentframe().f_back)
                self.add_to_dj_log(f"Error parsing JSON from text (THIS IS A BIG DEAL. SOMETHING IS DOWN): {error_message}", 'CRITICAL')
                time.sleep(self.sleep_on_connection_error)
                return None, error_message, False
        else:
            error_message = construct_error_message("Text to convert was None or empty", text_to_convert, should_be_there_key, purpose_text, "No Err Message", inspect.currentframe().f_back)
            self.add_to_dj_log(f"Error parsing JSON from text (THIS IS A BIG DEAL. SOMETHING IS DOWN): {error_message}", 'CRITICAL')
            time.sleep(self.sleep_on_connection_error)
            return None, error_message, False
        
        #VALUE retrieval
        if should_be_there_key is not None and should_be_there_key != "":
            if should_be_there_key in dict_value.keys():
                value = dict_value.get(should_be_there_key)
            else:
                error_message = construct_error_message("Key not found in dictionary", text_to_convert, should_be_there_key, purpose_text, "No Err Message", inspect.currentframe().f_back)
                self.add_to_dj_log(f"Dictionary Conversion Successful, (THIS IS A BIG DEAL) Key was not found: {error_message}", 'CRITICAL')
                time.sleep(self.sleep_on_connection_error)
                return dict_value, error_message, False
        else:
            return dict_value, None, True
        return dict_value, value, True
        
    def remove_non_printable(self, text):
        """Removes non-printable characters, except for ':', '[', ']', and '{}'.

        Args:
            text: The string to remove non-printable characters from.

        Returns:
            The string with all non-printable characters removed, except for ':', '[', ']', and '{}'.
        """
        # Define the regular expression pattern.
        # Explanation:
        #   [^...]  - Matches any character NOT inside the brackets
        #   \x20-\x7E - Printable characters (space to '~')
        #   :[]{}    - The literal characters ':', '[', ']', '{}' to preserve
        pattern = r"[^\x20-\x7E:[]{}]"  

        # Substitute non-printable characters with an empty string.
        return re.sub(pattern, "", text)

    def fully_display_date(self, date_str):
        try:
            # Parse the original date string into a datetime object
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")

            # Format the date to "DayOfWeek, Month DD, YYYY"
            # The %-d directive for day is platform specific and may not work on all systems.
            # It's used here to remove the leading zero from the day.
            formatted_date = date_obj.strftime("%A, %B %-d, %Y")
            return formatted_date
        except Exception as e:
            return date_str

    def hours_ago_utc(self, date_str_iso):
        try:
            """
            Calculate how many hours ago a date was from the current time, using an ISO 8601 date string.

            Parameters:
            date_str_iso (str): An ISO 8601 date string.

            Returns:
            int: The number of hours ago.
            """
            # Parse the ISO 8601 date string into a datetime object
            date_obj = datetime.strptime(date_str_iso, "%Y-%m-%dT%H:%M:%S.%fZ")
            
            # Get the current datetime in UTC
            now_utc = datetime.now(datetime.UTC)
            
            # Calculate the difference between now and the date
            time_diff = now_utc - date_obj
            
            # Convert the time difference to hours
            hours_diff = time_diff.total_seconds() / 3600
            
            return round(hours_diff,2)
        except Exception as e:
            return 100

    def convert_iso_to_formatted_date(self, iso_date_str, timezone_str):
        """
        Convert an ISO 8601 date string to a formatted date string with timezone abbreviation.
        
        Parameters:
        iso_date_str (str): An ISO 8601 date string.
        timezone_str (str): A timezone string, e.g., "America/Los_Angeles".
        
        Returns:
        str: The formatted date string.
        """
        try:
            if iso_date_str is None or iso_date_str == "":
                return "Date Not Found"
            
            # Define format specifiers for both cases
            format_specifiers = ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"]
            
            # Try parsing with each format specifier
            for fmt in format_specifiers:
                try:
                    iso_date_obj = datetime.strptime(iso_date_str, fmt)
                    break
                except ValueError:
                    continue
            
            # Set the timezone for the date object to UTC since the 'Z' denotes UTC time
            iso_date_obj = pytz.utc.localize(iso_date_obj)

            # Convert the UTC datetime to the given timezone
            target_timezone = pytz.timezone(timezone_str)
            localized_date = iso_date_obj.astimezone(target_timezone)

            # Format the date to the given pattern with timezone abbreviation (PT for Pacific Time)
            formatted_date = localized_date.strftime("%A, %B %-d, %Y %I:%M %p") + " PT"
            return formatted_date
        except Exception as e:
            print(f"Error converting Date String:[{iso_date_str}] [{timezone_str}] formatted date: {e}")
            return ""
  
  
  
#?##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#   
#?##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
#?#######             SEARCH ASYNC               ##########
#?##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
#?##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#

    def search_quick(self, include_list=['p/pmdm'], exclude_list=[], search_date_range="Last6Months"):
        
        search_config = self.create_user_search_config()
        
        search_config['config']['includeCodes'] = include_list
        search_config['config']['excludeCodes'] = exclude_list
        search_config['config']['dateRange']['dateRangeType'] = search_date_range
        
        search_results = self.search_by_config(search_config)
        
        
        
        return search_results
        
    def create_user_search_config(self):
        user_search_config = {
            "config":{
                "title":        "My news",
                "timeWindow":   {"dayType":"Everyday",
                                 "timeOfDayType": "Anytime"},
                "includeCodes": [],
                "excludeCodes": [],
                "dateRange":    {"dateRangeType": "Last6Months"}
            },
            "possibleValues": {
                "timeWindow": {"dayType": ["Weekdays", "Weekends", "Everyday"],
                               "timeOfDayType": ["Anytime", "Mornings", "Afternoons", "Evenings", "Overnight"]
                },
                # "AllByValue": [self.get_tax_cat('AllByValue')],
                "dateRange": get_valid_dj_date_ranges()
            }   
        }
        return user_search_config
    
    def search_by_config(self, search_config_dict):
        
        #Make sure there is a valid search config request
        if search_config_dict == None or search_config_dict == "":
            return None, "No search request received." , False
        
        #Make sure there are at least include codes. If not, return an error
        include_codes = search_config_dict.get("config", {}).get('includeCodes', [])
        if include_codes == []:
            return None, "Unable to search. No topics were received." , False
        
        #Exclude codes need to be handled but are not required
        
        exclude_codes = search_config_dict.get("config", {}).get('excludeCodes', [])
        
        #Set reasonable defaults for other parameters that may be missing.
        date_range_type = search_config_dict.get('dateRange', {}).get('dateRangeType', "Last6Months").replace(" ", "")
        day_type = search_config_dict.get('dateRange', {}).get('dateRangeType', "Everyday")
        time_of_day_type = search_config_dict.get('dateRange', {}).get('dateRangeType', "Anytime")
        
        #Note: the below should construct a search query like this:
        # djn=((include_code1)or(include_code2))and((not(exclude_cod1))and(not(exclde_code2)))
        inc_list=[]
        exc_list=[]
        
        
        #Assume we have at least one include code..... process from there
        if len(include_codes)>1:
            # match = re.search(r"\((.*?)\)", topic)
            include_string = f"({")or(".join(include_codes)})" 
            include_string = include_string.lower()
        else:
            include_string = f"({include_codes[0].strip().lower()})" 
            
        if len(exclude_codes)>1:
                # match = re.search(r"\((.*?)\)", topic)
                # if match: exc_list.append(match.group(1))
                exclude_string = f"not({")and(not("and(exc_list)}))" 
                include_string = include_string.lower()
        elif len(exclude_codes) == 1:
            exclude_string = f"(not({exclude_codes[0].strip().lower()}))" 
            
        else:
            exclude_string = False
        
        if not exclude_string:
            search_string = f"djn=({include_string})"
        else:
            search_string = f"djn={include_string}and{exclude_string}"
            
        search_results = asyncio.run(self.search_async(search_string=search_string, 
                    search_date_range=date_range_type,
                    page_limit=5, #Hard coding this to 10 given many configs will run at the same time 
                    only_rich_articles=False, #We need pictures, so hard coding this to True
                    number_of_pages_to_request=1)) # we can keep this at 3 for now as it will be many configs
        
        return search_results
    
    async def search_async(self, search_string='p/pmdm', search_date_range="Last6Months", from_date=None, to_date=None, page_offset=0, is_return_headline_coding=True, is_return_djn_headline_coding=True, number_of_pages_to_request=1):

        Search_Tasks = []
 
        
        log_str = f"""Search: search_string {search_string} | search_date_range {search_date_range} | 
                                        | is_return_headline_coding {is_return_headline_coding} | is_return_djn_headline_coding {is_return_djn_headline_coding} 
                                        | number_of_pages_to_request {number_of_pages_to_request} | page_offset {page_offset}"""
        

        self.add_to_dj_log(log_str, "BLUE")
        
        #! FIX ME: TURN OFF THE COMPLETE TAXONOMY DICT
        # if self.complete_taxonomy_dict is None:
        #     with open(COMPLETE_TAXONOMY_FILE_PATH, 'r') as f:
        #         self.complete_taxonomy_dict = json.loads(f.read())
        
        for i in range(number_of_pages_to_request):
            task = asyncio.create_task(self._search_async(search_string, search_date_range, from_date, to_date, page_offset=page_offset+i, is_return_headline_coding=is_return_headline_coding, is_return_djn_headline_coding=is_return_djn_headline_coding))
            Search_Tasks.append(task)

        all_results = await asyncio.gather(*Search_Tasks)
            
            
            # all_results.extend(result_set)
        if len(all_results) > 0:
            self.search_results = all_results
            self.search_has_results = True
        else: 
            self.search_has_results = False
            self.search_results = None
        return all_results

    async def _search_async(self, search_string='p/pmdm', search_date_range="Last6Months", from_date=None, to_date=None, page_offset=0, is_return_headline_coding=True, is_return_djn_headline_coding=True):
        loop = asyncio.get_running_loop()

        with concurrent.futures.ThreadPoolExecutor() as pool:
            search_results = await loop.run_in_executor(pool, self._search, search_string, search_date_range, from_date, to_date, page_offset, is_return_headline_coding, is_return_djn_headline_coding)
            if not search_results:
                return {}
            search_result_task_list = []
            
            for result in search_results:
                
                
                task = asyncio.ensure_future(self.get_article_json_async(result.get('id', ""), search_string))
                search_result_task_list.append(task)
                
                # #! *********  LOGIC TO INCREASE RICH ARTICLES RETURNED **************** 
                # #Articles that have an alt-doc id are usually rich (if you use the alt-doc id)
                alt_id = result.get('meta', {}).get('alternate_document_id', '')
                if alt_id != '':
                    # print(f"Alt ID: {alt_id}")
                    task = asyncio.ensure_future(self.get_article_json_async(alt_id, search_string))
                    search_result_task_list.append(task)
                # #! ******************************************************************************          
            
                
            
            articles_json = await asyncio.gather(*search_result_task_list)
            # print(f"Articles JSON: {articles_json}")
            
            #! ##### Logic to include/exclude articles based on richness
            articles_to_return = []
            wait_increment = 0
            for article in articles_json:
                wait_increment += 1
                if article is None or article == '':
                    # Empty Article
                    continue
                if isinstance(article, dict):
                    if len(article.keys()) == 0:
                        # Empty Article
                        continue
                        
                articles_to_return.append(article)
                
            
        return articles_to_return   

    def _search(self, search_string='p/pmdm', search_date_range="Last6Months", from_date=None, to_date=None, page_offset=0, is_return_headline_coding=True, is_return_djn_headline_coding=True):
        url = self.DJ_SEARCH_URL
        token = self.get_nearest_valid_authz_token()

        headers = {
            "accept": "application/vnd.dowjones.dna.content.v_1.0+json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        if search_date_range is not None and search_date_range == "SpecificDateRange":
            from_date = from_date.strftime("%Y-%m-%d")
            to_date = to_date.strftime("%Y-%m-%d")
            date_key_value = [{"custom": {"from": from_date, "to": to_date}}]
        else:
            date_key_value = {"days_range": search_date_range}
        
        payload = {
            "data": {
                "id": "Search",
                "type": "content",
                "attributes": {
                "query": {
                    "search_string": [
                    {
                        "mode": "Unified",
                        "value": f"{search_string.lower()}"
                    }
                    ],
                    "date": date_key_value
                },
                "formatting": {
                    "is_return_rich_article_id": True
                },
                "navigation": {
                    "is_return_headline_coding": True,
                    "is_return_djn_headline_coding": True
                },
                "page_offset": page_offset,
                "page_limit": 50
                }
            }
            }
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))


        if response.ok:
            total_response = response.json()
            
            try:
                response_Data = total_response.get('data', {})
                
            except:
                return {}
            
            try:
                response_meta = total_response.get('meta', {})
            except:
                pass
            
        
            #Response metadata
            self.current_search_summary['number_of_search_threads'] += 1
            self.current_search_summary['total_in_all_pages'] = total_response.get('meta', {}).get('total_count', 0)
            self.current_search_summary['number_of_articles'] += total_response.get('meta', {}).get('count', 0)
            self.current_search_summary['request_payload'] = payload
            self.current_search_summary['response_meta'] = response_meta
            
            #Search parameters
            self.current_search_summary['search_string']= search_string.lower()
            self.current_search_summary['search_date_range'] = search_date_range
            
            
            return response_Data
            
        elif response.status_code == 401:
            self.add_to_dj_log(f"TOKEN EXPIRED: {response.status_code} - {response.text} ... Getting new token","WARNING")
            self.get_nearest_valid_authz_token()
            return self._search(search_string, search_date_range, from_date, to_date, page_offset, is_return_headline_coding, is_return_djn_headline_coding)
            
        else:
            self.search_has_error = True
            self.search_error_message = f"Error: {response.status_code} - {response.text}"
            self.add_to_dj_log(f"Error: Search Error - code{response.status_code} - {response.text}", 'ERROR')
            self.search_results = response.json
            print(self.last_log_entry)    




#?##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#   
#?##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
#?#######             FORMAT ARTICLES            ##########
#?##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
#?##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
    def get_test_rich_articles(self):
        folder_or_file_path='richarticles'
        self.show_meta = False
        file_path_list = []
        
        #Get the list of files to process
        if os.path.isdir(folder_or_file_path):
            file_list = os.listdir(folder_or_file_path)
            for file in file_list:
                file_path = os.path.join(folder_or_file_path, file)
                file_path_list.append(file_path)
        elif os.path.isfile(folder_or_file_path):
            file_list = [folder_or_file_path]
        else:
            raise ValueError
        completed = 0
        formatted_articles = []
        for file in file_path_list:
            #skip non-json files
            if not ".json" in file:
                continue
            
            
            data_dict = {}
            #load the files as a dictionary
            with open (file, 'r') as  f:
                file_text = f.read()
                article_dict = json.loads(file_text)
                self.add_to_dj_log(article_dict.get('headline', ""), "LIGHTBLUE_BOLD")
                data_dict['data']=article_dict.get('orig_data', {})
                flat_article = self.flatten_article(data_dict, "TEST")

                flat_article['html'] = self.format_article_as_html(flat_article)
                formatted_articles.append(flat_article)
        
        return formatted_articles
        
    def get_formatted_test_articles_from_test_folder(self, folder_or_file_path='articles'):  
        self.show_meta = True
        file_path_list = []
        
        #Get the list of files to process
        if os.path.isdir(folder_or_file_path):
            file_list = os.listdir(folder_or_file_path)
            for file in file_list:
                file_path = os.path.join(folder_or_file_path, file)
                file_path_list.append(file_path)
        elif os.path.isfile(folder_or_file_path):
            file_list = [folder_or_file_path]
        else:
            raise ValueError
        completed = 0
        
        all_body_items = []
        all_content_items = []
        all_content_resources = []
        cnt = 0  
        
            
        for file in file_path_list:
            #skip non-json files
            if cnt > 20:
                continue
            
            if not ".json" in file:
                continue
            
            #load the files as a dictionary
            # formatted_article = self.get_formatted_article(file)

                     
            with open (file, 'r') as  f:
                

                
                
                file_text = f.read()
                article__dict = json.loads(file_text)
                
                content_resources_list = article__dict.get('orig_data', {}).get('attributes', {}).get('content_resources', [])
                if content_resources_list == []:
                    continue
                
                cnt+=1
                
                self.add_to_dj_log(article__dict.get('headline', ""), "LIGHTBLUE_BOLD")
                
                body_item_list = article__dict.get('orig_data', {}).get('attributes', {}).get('body', [])
                
                all_content_resources.extend(content_resources_list)
                all_body_items.extend(body_item_list)
                
                # for b in body_item_list:
                #     if b.get('content', []) != []:
                #         all_content_items.extend(b.get('content', []))

                        
    
            with open('interrogation/all_bodies.json', 'w') as f:
                f.write(json.dumps(all_body_items, indent=4))
            
            with open('interrogation/all_content_resources.json', 'w') as f:
                f.write(json.dumps(all_content_resources, indent=4))
            
            for body_item in all_body_items:
                if body_item.get('content', []) != []:
                    all_content_items.extend(body_item.get('content', []))
            
            with open('interrogation/all_content_items.json', 'w') as f:
                f.write(json.dumps(all_content_items, indent=4))
    
    def format_article(self, article_dict, format='html', show_meta=False):
        
        data_dict = {}
        data_dict['data'] = article_dict
        flat_article = self.flatten_article(data_dict)

        if format.lower() in ['html', 'all']:
            flat_article['html'] = self.format_article_as_html(flat_article)
        
        return flat_article
                     
    
        
        #gff means Get Formatted Field
    
    def gff(self, style, field_dict):
        
        
        
        style = style.lower()
        
        if not isinstance(field_dict, dict):
            field_dict = {
                'text': field_dict
                          }
        
        if field_dict.get("text", "Other") == "":
            return ""
        
        
        font_family = "font-family: 'SF Pro Display', 'SF Pro Icons', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;"
        no_wrap = "white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px;"
        text_color =        "color: #FFFFFF;"
        accent_color1 =     "color: #D15432;"
        accent_color2 =     "color: #D15432;"
        highlight_color =   "color: #D15432;"
        date_color =        "color: #BBBBBB;"
        
        style_dict = {
            
            # Article List Styles                                                                                                                                         top/bottom   rt/lt              
            "title-list":       f"<div  style='font-size: 19px; {text_color}    line-height: 1.2; font-weight: 750;    letter-spacing: 0em; display: flex; align-items: center;   padding:  0px  0px  0px  0px;   margin-left:  0; margin-right:  0; margin-bottom:  0px; margin-top:  0; {font_family} {no_wrap} '>{field_dict.get('text', '')}</div>",
            "author":           f"<div  style='font-size: 14px; {text_color}    line-height: 1.5; font-weight: normal; letter-spacing: 0em; display: flex; align-items: center;   padding:  0px  0px  0px  0px;   margin-left:  0; margin-right:  0; margin-bottom: 20px; margin-top:  0; {font_family} {no_wrap} '>{field_dict.get('text', '')}</div>",
            "article-desig":    f"<div  style='font-size: 13px; {accent_color1} line-height: 1.2; font-weight: 900;    letter-spacing: 0em; display: flex; align-items: center;   padding:  0px  0px 10px  0px;   margin-left:  0; margin-right:  0; margin-bottom:  0px; margin-top:  0; {font_family} {no_wrap} '>{field_dict.get('text', '')}</div>",
            "date-list":        f"<div  style='font-size: 14px; {date_color}    line-height: 1.1; font-weight: 300;    letter-spacing: 0em; display: flex; align-items: center;   padding:  0px  0px  0px  0px;   margin-left:  0; margin-right:  0; margin-bottom:  8px; margin-top:  0; {font_family} {no_wrap} '>{field_dict.get('text', '')}</div>",

            
            # Full Article Styles
            "title":            f"<div style='font-size: 48px; line-height: 1.0; font-weight: 700;    letter-spacing: 0em; padding:  0px  0px  0px  0px; margin:  0px{font_family}'>{field_dict.get('text', '')}</div>",
            "header":           f'<div style="font-size: 22px; line-height: 1.2; font-weight: bold;   letter-spacing: 0em; padding:  0px  0px  0px  0px; margin: 24px 0 16px;{font_family} ">{field_dict.get("text", "")}</div>',
            "subheader":        f'<div style="font-size: 22px; line-height: 1.2; font-weight: bold;   letter-spacing: 0em; padding:  0px  0px  0px  0px; margin: 24px 0 16px;{font_family} ">{field_dict.get("text", "")}</div>',
            "copyright": f'<div style="font-size: 9px; {font_family} color: #333; line-height: 1.0; margin: 20px;">{field_dict.get("text", "")}</div',
            "section-header": f'<div style="border-top: 1px solid rgb(218, 218, 218);{font_family} border-bottom: 1px solid rgb(218, 218, 218); color: #333; font-size: 14px; line-height: 1.23; margin: 0px 0px 10px; padding: 10px 0px; text-transform: uppercase; letter-spacing: 0.8px;">{field_dict.get("text", "")}</div>', 
            "paragraph": f'<p style="font-size: 16px;{font_family} margin-bottom: 20px;">{field_dict.get("text", "")}</p>',
            "list": f'<ul style="list-style-type: disc;{font_family} padding-left: 20px; margin-bottom: 20px;">{field_dict.get("text", "")}</ul>',
            "list-item": f'<li style="margin-bottom: 10px;{font_family}">{field_dict.get("text", "")}</li>',
            "figure": f'<div style="text-align: center;{font_family} margin: 20px 0;">{field_dict.get("text", "")}</div>',
            "figure-img": f'<img style="max-width: 100%;{font_family} height: auto;" src="placeholder_image.jpg">',
            "figcaption": f'<div style="font-size: 14px;{font_family} color: #666; margin-top: 8px;">{field_dict.get("text", "")}</div>',
            
            "link": f'<a style="color: #007bff;{font_family} text-decoration: underline;">{field_dict.get("text", "")}</a>',
            "company-entity": f'<span style="display: inline-block; color: #36454f; font-weight: 300; font-size: 16px;{font_family} border-bottom: 1px solid #ff0000;">{field_dict.get("text", "")}</span>',
            "page-break": f'<hr style="margin-left: 160px; margin-right: 160px; background-color: #c0c0c0; border: 0; clear: both; height: 1px; margin: 32px 0;">' ,
            "body":             f"<body style='font-size: 14px; line-height: 1.5; font-weight: normal; letter-spacing: 0em; padding:  0px  0px  0px  0px; color:  #333;  margin: 20px;{font_family}'>{field_dict.get('text', '')}</body>",
            "wordcount":             f"<body style='font-size: 14px; line-height: 1.5; font-weight: normal; letter-spacing: 0em; padding:  0px  0px  0px  0px; color:  #333;  margin: 20px;{font_family}'>{field_dict.get('text', '')}{' min read'}</body>",

           
            # "article-search-result-title-html": f"<div style='font-size: 19px; line-height: 1.21053; font-weight: 100; letter-spacing: .012em; font-family: 'SF Pro Display', 'SF Pro Icons', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;'>{field_dict.get('text', '')}</div>",
            "article-type-html": f"<div style='margin-bottom: 8px; font-size: 14px; line-height: 1.33337; font-weight: 700; f{font_family}'>{field_dict.get('text', '')}</div>",
            # "search-result-title-html": f"<div style='font-size: 19px; line-height: 1.21053; font-weight: 700; letter-spacing: .012em; font-family: 'SF Pro Display', 'SF Pro Icons', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif; overflow: hidden;'>{field_dict.get('text', '')}</div>",
            "article-date-html": f"<div style='margin-bottom: 8px; font-size: 14px; line-height: 1.1; color: #BBBBBB; font-weight: 300; letter-spacing: -.016em; {font_family} display: flex; justify-content: flex-start; align-items: center;'>{field_dict.get('text', '')}</div>",
            # "subheader-html": f"<div style='font-size: 19px; line-height: 1.21053; font-weight: 700; letter-spacing: .012em; font-family: 'SF Pro Display', 'SF Pro Icons', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;'>{field_dict.get('text', '')}</div>",
            # "snippet-text-html": f"<div style='font-size: 16px; line-height: 1.4211; font-weight: 400; letter-spacing: .012em; font-family: 'SF Pro Display', 'SF Pro Icons', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;'>{field_dict.get('text', '')}</div>",
            # "body-text-html": f"<div style='font-size: 19px; line-height: 1.4211; font-weight: 400; letter-spacing: .012em; font-family: 'SF Pro Display', 'SF Pro Icons', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;'>{field_dict.get('text', '')}</div>",
            # "image-caption-html": f"<div style='position: relative; display: flex; align-items: flex-start; justify-content: space-between; margin: 16px 16px 0; font-size: 12px; line-height: 1.33337; font-weight: 600; letter-spacing: -.01em; font-family: 'SF Pro Text', 'SF Pro Icons', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;'>{field_dict.get('text', '')}</div>",
            # # "caption-header-html": f"<div style='font-size: 14px; line-height: 1.42859; font-weight: 400; letter-spacing: -.016em; font-family: 'SF Pro Text', 'SF Pro Icons', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;'>{field_dict.get('text', '')}</div>",
            # "link_html": f"<a href='{field_dict.get('url', '')}' style='text-decoration: none; color: #06c; letter-spacing: inherit;'>{field_dict.get('text', '')}</a>",
            "chip_html": f"<span style='display: inline-block; margin: -4px; height: auto;'><div style='background-color: #7D55C7; color: #fff; width: auto; margin: -4px; font-size: 12px; line-height: 1.33337; font-weight: 700; letter-spacing: -.01em; {font_family} padding: 5px 10px; border-radius: 15px; display: inline-block;'>{field_dict.get('text', '')}</div></span>",

            "bold":   f"<strong>{field_dict.get('text', '')}</strong>",
            "italic":   f"<em>{field_dict.get('text', '')}</em>",
            "underline":   f"<u>{field_dict.get('text', '')}</u>",
            "strikethrough":   f"<s>{field_dict.get('text', '')}</s>",
            "superscript":   f"<sup>{field_dict.get('text', '')}</sup>",
            "subscript":   f'<span style="font-weight: bold; font-style: italic;">{field_dict.get('text', '')}</span>',
            "highlight":   f"<mark style='background-color: #555; color: #DDD;'>{field_dict.get('text', '')}</mark>",

            "small-header":   f"<h6>{field_dict.get('text', '')}</h6>",
            "medium-header":   f"<h5>{field_dict.get('text', '')}</h5>",
            "sub-header":   f"<h4>{field_dict.get('text', '')}</h4>",
            "large-header":   f"<h3>{field_dict.get('text', '')}</h3>"        
        
        }
                
        formatted_item = style_dict.get(style, '')
        
            
        return formatted_item
        
    def format_article_as_html(self, fa):
        
        #gff is Get Formatted Field
        
            
        
        #Assemble the HTML        
        
        article_desig_list = []
        
        def add_desg(key, desg_list):
            if fa.get(key, '').strip() != '':
                if fa.get(key, '').strip() not in desg_list:
                    desg_list.append(fa.get(key, '').strip())
            return desg_list
        
        article_desig_list = add_desg('publisher_name', article_desig_list)
        article_desig_list = add_desg('source_name', article_desig_list)
        article_desig_list = add_desg('product_section', article_desig_list)
        article_desig_list = add_desg('product', article_desig_list)
        article_desig_list = add_desg('section_name', article_desig_list)
        article_desig_list = add_desg('page', article_desig_list)
        # article_desig_list = add_desg('copyright', article_desig_list)
        
        article_desig = " | ".join(article_desig_list).upper()
        
        
        

        
        content_resources_list = fa.get('content_resources')
        body_list = fa.get('body_list', [])
        formatted_body = self.get_formatted_body(body_list, content_resources_list)
        
        date_value = f"{fa.get('date_tag','')}{fa.get('user_customized_date_time','')}"
        
        
        list_html_dict = {
        'headline':      [self.gff('title-list',            {'text': fa.get('headline','')})],                                  
        'article_desig': [self.gff('article-desig',         {'text': article_desig})],    
        'author':        [self.gff('author',                  {'text': fa.get('byline', fa.get('author',''))})],
        'date':          [self.gff('date-list',     {'text': date_value})],
        # 'copyright':[self.gff('copyright',              {'text': fa.get('copyright','')})],
        # 'html3': [self.gff('subheader',         {'text': fa.get('headline_deck','HEADLNINE DECK')})],                        
        # 'byline': [self.gff('subheader',         {'text': fa.get('byline','BYLINE')})],                              
        }
        
        list_result_html = []
        def get_all_html_parts(key, list_result_html):
            value = list_html_dict.get(key, 'Bad Key')
            if isinstance(value, list):
                return_value = "".join(value)
            else:
                return_value = value                                
            if return_value is not None and return_value != "":
                list_result_html.append(return_value)
            return list_result_html
                            
        
        list_result_html = get_all_html_parts('article_desig', list_result_html)
        list_result_html = get_all_html_parts('headline', list_result_html)
        list_result_html = get_all_html_parts('author', list_result_html)
        list_result_html = get_all_html_parts('date', list_result_html)
        
        
        
        html_dict = {
        'html_list': list_result_html,
        'html1': [self.gff('article-desig', article_desig)],                        
        'html2': [self.gff('title',  {'text': fa.get('headline','')})],                        # Headline     
        'html3': [self.gff('subheader', {'text': fa.get('headline_deck','HEADLNINE DECK')})],                        # Headline Deck      
        'html4': [self.gff('subheader', {'text': fa.get('byline','BYLINE')})],                              # Byline      
    #    'image5': [fa.get('image_dict','')],                                                      # Primary Image/Caption
        'html6': [self.gff('body', {'text': fa.get('author', '')})],
        'html6a':[self.gff('body', {'text': fa.get('copyright','')})],
        'html7': [self.gff('date-list',     {'text': date_value})],
       'html7b': [self.gff('wordcount', {'text': int(round(int(fa.get('word_count','673'))/250,0))})],
        'html8': [self.gff('body', {'text': fa.get('region_later','')})],                        # Region Tags
        'html9': [self.gff('body', {'text': fa.get('subject_later','')})],                        # Subject Tags
        'html10': [self.gff('body', {'text': fa.get('people_later','')})],                        # People Tags
        'html11': [self.gff('body', {'text': fa.get('industry_later','')})],                        # Industry Tags
        'html12': [self.gff('body', {'text': fa.get('source_later','')})],                        # Source Tags ????
        'html13': [self.gff('body', {'text': fa.get('company_later','')})],                        # Company Tags
        'html14': [self.gff('body', {'text': fa.get('org_later','')})],                        # Organization Tags
        'html15': [self.gff('body', {'text': fa.get('ref_media_later','')})],                        # Referenced Media
        # 'html16': [self.gff('body', {'text': fa.get('keywords','')})],                        # Key Words
        # 'html17': [self.gff('body', {'text': fa.get('hosted_url','')})],                        # Hosted URL
        'html18': formatted_body,                        # Article Body
        'html19': [self.gff('body', {'text': fa.get('art_closing','')})],                        # Article Closing/Contributions
        'html20': [self.gff('body', {'text': fa.get('rel_articles','')})],                        # Related Articles
        'html21': [self.gff('body', {'text': fa.get('read_next','')})],                        # What to read next
        }
        
        if 'Takeaway' in fa.get('headline', ''):
            print(f"Effortless: {fa.get('headline', '')}")
            
        with open('article_html.txt', 'w') as f:
            f.write(json.dumps(html_dict, indent=4))

        return html_dict
        
        
        
        # rich_chip = ""
        # if is_rich:
        #     rich_chip = apply_html_style(" Rich Content ", 'chip_html')

     
        
    
        
        

        content_keys = ["alternate_text", "background_info", "caption", "code", "code_scheme", "content", "credit", "display", "emphasis_type", "entity_type", "external", "fragment_id", "height", "icon", "inset_type", "link_type", "media_type", "name", "paragraph_type", "properties", "ref", "rel", "significance", "slug", "sub_type", "text", "ticker", "type", "uri", "width"]
        
    def get_formatted_body(self, body_items, content_resources_list):
        formatted_body_items = []
        for b_item in body_items:
            
            
            valid_body_types = ["Paragraph", "Table", "Heading", "Image", "Dateline", "Tagline", "Video", "Inset", "List", "Media", "Blockquote", "Binary"]
            
            valid_body_props = ["alternate_text", "caption", "content", "content_encoding", "credit", "display", "format", "fragment_id", 
                                "height", "inset_type", "media_type", "name", "ordered", "paragraph_type", "properties", "ref", "slug", "sub_type", "text", "type", "uri", "value", "width"]
            
            
            if "type" not in b_item.keys() or b_item.get('type', 'BADTYPE') not in valid_body_types:
                #! Unhappy Path
                print(f"UNEXPECTED BODY TYPE ... NO TYPE or invalid type")
            
            has_content = False
            has_type = False
            
            b_item_dict = {}
            for prop in valid_body_props:
                if prop in b_item.keys():
                    if prop=='content': has_content=True
                    if prop=='type': has_type=True
                    got_it = b_item.get(prop, False)
                    if got_it:
                        b_item_dict[prop]=got_it

            formatted_body_item = []

            
            if has_type:
                if b_item.get('type', '') in valid_body_types:
                    body_type = b_item.get('type', '')
                    
                    # Happy Path: Valid Body Type
                    if body_type == "Paragraph":
                        if b_item.get('display', '') != "Plain":
                            print("UNEXPECTED PARAGRAPH DISPLAY TYPE")
                        par_text = ""
                        par_list = []
                        if has_content:
                            if b_item.get('text', '') != "":   #Has text AND content
                                print("Has Text AND Content  UNEXPECTED !!!!")
                            par_list = self.gather_all_nested_content(content_resources_list, b_item.get('content', []))
                            if isinstance(par_list, list):       
                                par_text = ''.join(par_list)    
                                if par_text == "":
                                    print("NO TEXT IN NESTED CONTENT --- UNEXPECTED")
                        else:
                            par_text = b_item.get('text', '')
                        if self.show_meta:
                            par_text = f"[{b_item.get('paragraph_type', '')}|{b_item.get('display', '')}]{par_text}"
                        if par_text == "":
                            print("NO TEXT IN PARAGRAPH --- UNEXPECTED")
                        formatted_body_item.extend([par_text])            
                    
                    #Media
                    if body_type ==  "Media":
                        media_id = b_item.get('ref', '')
                        formatted_media = self.get_formatted_content_resources(content_resources_list, media_id)
                        if formatted_media is not None:
                            formatted_body_item.extend([formatted_media])
                        
                
                    #!Table
                    if body_type ==  "Table":
                        self.add_to_dj_log(f"NEW BODY TYPE: {body_type}", "CRITICAL")
                    
                    #Heading
                    if body_type ==  "Heading":
                        header_text = ''
                        if has_content:
                            header_list = self.gather_all_nested_content(content_resources_list, b_item.get('content', []))
                            header_text = ''.join(header_list)
                        else:
                            header_text = b_item.get('text', '')
                        if header_text == "":
                            print("NO TEXT IN HEADING --- UNEXPECTED but did see this occasionally in the test data and it seemed to be a mistake in the data")
                        header_style = f"{b_item.get('sub_type', 'medium').lower()}-header"
                        html = self.gff(header_style, header_text) 
                        formatted_body_item.extend([html])
                    
                    #Image    
                    if body_type ==  "Image":
                        if has_content:
                            print("UNEXPECTED CONTENT IN IMAGE")
                        if 'ref' in b_item.keys() and 'type' in b_item.keys():
                            formatted_image = self.get_formatted_content_resources(content_resources_list, b_item.get('ref', ''))
                            if formatted_image is not None:
                                formatted_body_item.extend([formatted_image])
                            else:
                                print("FORMATTING THE IMAGE FAILED")

                    #Video    
                    if body_type ==  "Video":
                        if has_content:
                            print("UNEXPECTED CONTENT IN VIDEO")
                        formatted_video = self.get_formatted_content_resources(content_resources_list, b_item.get('ref', ''))
                        formatted_body_item.extend([formatted_video])
                    
                    if body_type ==  "Dateline":
                        self.add_to_dj_log(f"NEW BODY TYPE: {body_type}", "CRITICAL")
                    
                    
                    if body_type ==  "Tagline":
                        tagline = ''
                        if has_content:
                            tagline_list = self.gather_all_nested_content(content_resources_list, b_item.get('content', []))
                            tagline = ''.join(tagline_list)
                        else:
                            tagline = b_item.get('text', '')
                        if tagline == "":
                            print("NO TEXT IN TAGLINE --- UNEXPECTED")
                        formatted_body_item.extend([tagline])
                    
                    
                    if body_type ==  "Inset":
                        formatted_inset = self.get_formatted_inset(content_resources_list, b_item.get('ref', ''))
                        formatted_body_item.extend([formatted_inset])
                    
                    
                    if body_type ==  "List":
                        if not has_content:
                            print("NO CONTENT IN LIST --- UNEXPECTED")
                        if b_item.get('text', '') != "":
                            print("UNEXPECTED TEXT IN LIST")
                        if b_item.get('ordered', '') == False:
                            list_tag = "ul"
                        else:
                            list_tag = "ol"
                        formatted_list_items = self.gather_all_nested_content(content_resources_list, b_item.get('content', []))
                        formatted_list = f"<{list_tag}>{''.join(formatted_list_items)}</{list_tag}>"
                        
                        formatted_body_item.extend([formatted_list])
                            
                    if body_type ==  "Blockquote":
                        self.add_to_dj_log(f"NEW BODY TYPE: {body_type}", "CRITICAL")
                    
                    if body_type ==  "Binary":
                        self.add_to_dj_log(f"NEW BODY TYPE: {body_type}", "CRITICAL")
            
            if formatted_body_item is not None and formatted_body_item != [] and isinstance(formatted_body_item, list):
                formatted_body_items.extend(formatted_body_item)
            else:
                self.add_to_dj_log(f"NO FORMATTED BODY ITEM", "CRITICAL")
        return formatted_body_items

    def gather_all_nested_content(self, content_resources_list, content_list):
        format_next_as_link = False
        gathered_content = []
        
        # valid_content_props = ["alternate_text", "background_info", "caption", "code", "code_scheme", "content", "credit", 
        #                        "display", "emphasis_type", "entity_type", "external", "fragment_id", "height", "icon", 
        #                        "inset_type", "link_type", "media_type", "name", "paragraph_type", "properties", "ref", 
        #                        "rel", "significance", "slug", "sub_type", "text", "ticker", "type", "uri", "width"]

      
        for c in content_list:
            if c is None:
                continue
            if c.get('content', '') == '' and c.get('text', '') == "":
                continue
            #Content has text and no type
            if c.get('text', '') != "" and c.get('type', '') == "":
                if format_next_as_link:
                    format_next_as_link = False
                    return  gathered_content.append(self.get_formatted_content_resources(content_resources_list, link_id, c.get('text', '')))
                else:
                    gathered_content.append(c.get('text', ''))

            
            #Content has more nested content
            elif c.get('content') is not None and c.get('conten', []) != []:
                print (type(c.get('content')))
                gathered_content.extend(self.gather_all_nested_content(content_resources_list, c.get('content', [])))
                return gathered_content
            elif c.get('type', '') == "Link":
                if c.get('text', '') == "":
                    format_next_as_link = True
                    link_id = c.get('ref', '')
                    continue
                else:
                    gathered_content.append(self.get_formatted_content_resources(content_resources_list, c.get('ref', ''), c.get('text', '')))

            
            elif c.get('type', '') == "Entity":
                if c.get('text', '') != "":
                    if c.get('entity_type', '') != 'author':
                        gathered_content.append(self.gff('highlight', c.get('text', '')))
                    else: 
                        gathered_content.append(c.get('text', ''))

                else:
                    print("UNEXPECTED ENTITY TYPE")
            
            elif c.get('type', '') == "Emphasis":
                gathered_content.append(self.gff(c.get('emphasis_type', ''), c.get('text', '')))

            
            elif c.get('type', '') == "listitem":
                if c.get('content', []) != []:
                    list_item = f"<li>{''.join(self.gather_all_nested_content(content_resources_list, c.get('content', [])))}</li>"
                else:
                    list_item = f"<li>{c.get('text', '')}</li>"
                gathered_content.append(list_item)

                    
        if gathered_content == []:
            print("NO CONTENT GATHERED")
        
        return gathered_content
                         
    def get_formatted_content_resources(self, content_resources_list, id, text_to_format=''):
        formatted_content_resources = []
        for resource in content_resources_list:
            if resource.get('id', '') == id:
                #!IMAGE
                if resource.get('type', '') == 'image':
                    if resource.get('properties', {}).get('location', '') != "":
                        url = resource.get('properties', {}).get('location', False)
                        alt_text = resource.get('alternate_text', '')
                        credit = resource.get('credit', '') 
                        caption = resource.get('caption', '')
                        if credit != "":
                            credit = f"Credit: {credit}"
                        if caption != "":
                            caption = f'<figcaption style="text-align: center;">{caption} {credit}</figcaption>'
                        
                        str = f'''<img src="{url}" alt="{alt_text}" style="float: left; max-width: 450px; height: auto; margin: 0 20px 20px 0;">'''


                        
                        # str = f'''<figure style="display: inline-block; max-width: 500px; margin: 0;">
                        #             <img src="{url}" alt="{alt_text}" title="{alt_text}" style="max-width: 100%; height: auto;">
                        #                                     {caption}
                        #             </figure>'''
                        return str
                    else:
                        return formatted_content_resources
                elif resource.get('type', '') == 'link':
                    if resource.get('uri', '') != "":
                        if text_to_format == "":
                            text_to_format = resource.get('uri', '')
                        str = f'<a href="{resource.get('uri', '')}">{text_to_format}</a>'
                        return str
                
                elif resource.get('type', '') == 'video':
                    video_data = resource.get('alt_video_data', {})
                    if video_data == {}:
                        return '' #Corrupt video data
                    description = video_data.get('description', '')
                    duration = video_data.get('duration', '')
                    name = video_data.get('name', '')
                    author = video_data.get('author', '')
                    thumbnail_url = video_data.get('video_still_url', '')
                    video_mp4_list = video_data.get('video_mp4_list', [])
                    if len(video_mp4_list) == 0:
                        return ''
                    video_url = video_mp4_list[0]
                    html = f'''<a href="{video_url}" style="text-decoration: none; color: inherit;"><img src="{thumbnail_url}" 
                        alt="Video Thumbnail" style="width: 100%; height: auto; border-bottom: 1px solid #ccc;"><div style="padding: 5px;">
                        <h2 style="font-size: 18px; margin: 5px 0;">{name}</h2>"
                        <p style="margin: 5px 0; font-size: 14px;">Duraiton: {round((duration/60),0)}m</p>"
                        <p style="margin: 5px 0; font-size: 14px;">Author: {author}</p>"
                        <p style="margin: 5px 0; font-size: 14px;">Description: {description}</p>"
                        </div>
                    </a>'''
                    return html
                    
                elif resource.get('type', '') == 'media':
                    if resource.get('media_type', '').lower() == 'audio':
                        #Note this is intentioanlly not implemented
                        #No working example could be found
                        return formatted_content_resources
                
                elif resource.get('type', '') == 'company':
                    print("NEW RESOURCE TYPE")
                    return formatted_content_resources
                    
                else:
                    print("NEW RESOURCE TYPE")
                    return formatted_content_resources
        return formatted_content_resources
      
    def get_formatted_inset(self, content_resources_list, id):
        formatted_str = None
        for resource in content_resources_list:
            if resource.get('id', '') == id:
                if resource.get('type', '') == 'inset':    
        
                    if resource.get('inset_type', '') == 'normal':
                        self.add_to_dj_log(f"NEW INSET_TYPE {resource.get('inset_type', '')}", "CRITICAL")
                    if resource.get('inset_type', '') == 'dynamic':
                        return ""#implement this later (it is related content)
                    
                    if resource.get('inset_type', '') == 'richtext':
                       continue
                    
                    
                    if resource.get('inset_type', '') == 'bigtophero':
                        url = resource.get('properties', {}).get('urllarge', False)
                        credit = resource.get('properties', {}).get('imagecredit', False)
                        caption = resource.get('properties', {}).get('imagecaption', False)
                        if credit != "":
                            credit = f"Credit: {credit}"
                        if caption != "":
                            caption = f'<figcaption style="text-align: center;">{caption} {credit}</figcaption>'
                        
                        str = f'''<img src="{url}" alt="{caption}" style="float: left; max-width: 450px; height: auto; margin: 0 20px 20px 0;">'''


                    
                    if resource.get('inset_type', '') == 'newsletterinset':
                        newslettername = resource.get('properties', {}).get('newslettername', '')
                        if newslettername != '':
                            formatted_str = f'''<blockquote class="inset"><p>"{newslettername}"</p></blockquote>'''
                    
                    if resource.get('inset_type', '') == 'pagebreak':
                        continue
                    if resource.get('inset_type', '') == 'tweet':
                        self.add_to_dj_log(f"NEW INSET_TYPE {resource.get('inset_type', '')}", "CRITICAL")
                    if resource.get('inset_type', '') == 'youtube':
                        self.add_to_dj_log(f"NEW INSET_TYPE {resource.get('inset_type', '')}", "CRITICAL")
                    if resource.get('inset_type', '') == 'tiktok':
                        self.add_to_dj_log(f"NEW INSET_TYPE {resource.get('inset_type', '')}", "CRITICAL")
                    if resource.get('inset_type', '') == 'advisortake':
                        self.add_to_dj_log(f"NEW INSET_TYPE {resource.get('inset_type', '')}", "CRITICAL")
                    if resource.get('inset_type', '') == 'pullquote':
                        self.add_to_dj_log(f"NEW INSET_TYPE {resource.get('inset_type', '')}", "CRITICAL")
                    if resource.get('inset_type', '') == 'bankruptcydocket':
                        self.add_to_dj_log(f"NEW INSET_TYPE {resource.get('inset_type', '')}", "CRITICAL")
                    if resource.get('inset_type', '') == 'instagramphoto        ':
                        self.add_to_dj_log(f"NEW INSET_TYPE {resource.get('inset_type', '')}", "CRITICAL")
        
        
        return formatted_str

    def try_and_get_any_image(self, content_resources_list):
        url = ''
        for resource in content_resources_list:
            if url != "":
                continue
            if resource.get('type', '') == 'image':
                url = resource.get('properties', {}).get('location', '')
                good_resource = resource
                if url == '':
                    url = resource.get('name', {})
                    good_resource = resource
                
        for resource in content_resources_list:
            if url != "":
                continue
            if resource.get('type', '') == 'video':
                video_data = resource.get('alt_video_data', {})
                url = video_data.get('video_still_url', '')
                good_resource = resource
        
        if url != "":
            url_dict = {'url': url, 
                        'slug': good_resource.get('slug', ''),
                        'alt_text': good_resource.get('alternate_text', ''),
                        'width': good_resource.get('width', 0),
                        'height': good_resource.get('height', 0),
                        'credit': good_resource.get('credit', ''),
                        'html': f'<img src="{url}" alt="{good_resource.get('alternate_text', '')}" style="float: left; max-width: 250px; height: auto; margin: 0 20px 20px 0;">'
                        }
            return url_dict
        
        
        return ""
    
    
    
    
    
    
#?##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#   
#?##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
#?#######             GET ARTICLES            ##########
#?##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
#?##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#

    async def get_article_json_async(self, article_id, search_string):
        loop = asyncio.get_running_loop()
        # Use a ThreadPoolExecutor to run the synchronous function in a separate thread
        with concurrent.futures.ThreadPoolExecutor() as pool:
            wait_time = random.uniform(DEFAULT_SLEEP_TIME * .5 * 1000, DEFAULT_SLEEP_TIME * 1.25 * 1000) / 1000
            await asyncio.sleep(wait_time)
            article_json = await loop.run_in_executor(pool, self.get_article_json_sync, article_id, search_string)
            try:
                article_cache = {
                'partitionkey': "djcontent",
                'rowkey': article_json.get('id', 'NOID'),
                'structdata' : article_json
                }
                #!FIXME FIX ME! await self.bmm.upsert_data(data_items=article_cache)
            except:
                pass
            
        return article_json
    
    def get_article_json_sync(self, article_id, search_string):
        # This function remains synchronous and will be called by an executor in an async manner
        
        content_item  = self.get_content_item(article_id, search_string)
        
        return content_item

    def get_content_item(self, content_id, search_string):

                
        if not content_id:
            self.add_to_dj_log(f"Error: No content_id provided", 'ERROR')
            return f"Error: No content_id provided | {self.last_log_entry}"
        
        url = f"{self.DJ_CONTENT_URL}/{content_id}"

        token = self.get_nearest_valid_authz_token()

        headers = {
            "accept": "application/vnd.dowjones.dna+json",
            "Authorization": f"Bearer {token}"
        }

        response = requests.get(url, headers=headers)
        
        # time.sleep(DEFAULT_SLEEP_TIME)

        if response.ok:
            flat_article = self.flatten_article(response.json(), search_string)
            flat_article['html'] = self.format_article_as_html(flat_article)

            return flat_article
            
        
        elif response.status_code == 401:
            # Token Expired
            self.add_to_dj_log(f"TOKEN EXPIRED: {response.status_code} - {response.text} ... Getting new token","WARNING")
            self.get_nearest_valid_authz_token()
            return self.get_content_item(content_id)
        
        else:
            # Error of some kind other than 401 (expired token)
            if len(content_id) != 47:
                with open('bad_content_id.txt', 'a') as f:
                    f.write(f"{content_id}\n")
                self.add_to_dj_log(f"Error: Bad content_id: {content_id}", 'ERROR')
                return f"Error: Bad content_id | {self.last_log_entry}"
            else: 
                self.add_to_dj_log(f"Error with content id:{content_id} \n {response.status_code} - {response.text}", 'ERROR')
                return self.last_log_entry

    def flatten_article(self, article_dict: dict, search_string: str = ""):

        
        data_dict = {}
        # get the main article data_node as a dictionary
        # the incoming article_dict can be a list or a dictionary
        # (no idea why, but this needs to be handled)
        if isinstance(article_dict.get('data', {}), dict):
            data_dict = article_dict.get('data', {})
        if isinstance(article_dict.get('data', []), list):
            data_dict = article_dict.get('data', [])[0]
        
        # This is a sub dictionary with all of the rich data for the article (if it is rich)
        content_resources_list = data_dict.get('attributes', {}).get('content_resources', [])


        # This function gets any image that can be used in place of the  source icon for the article.
        def get_rich_indicator_image (content_resources_list = []):
            try:
                
                if content_resources_list == []:
                    return "", False
                url_dict = self.try_and_get_any_image(content_resources_list)
                if url_dict != "":
                    return url_dict, True
                else:
                    return "", False
            except:
                return "", False
        
        #We need a date/time to show on the UI ... there is not always one avaialble.  Show with this priority:
        def get_best_ui_time(a_dict = {}):
            
            if a_dict.get('publish_time', False):
                return a_dict.get('publish_time', ""), "Published: "
            elif a_dict.get('modification_time', False):
                return a_dict.get('modification_time', ""), "Last Updated: "
            elif a_dict.get('live_time', False):
                return a_dict.get('live_time', ""), "Live as of: "
            elif a_dict.get('load_time', False):
                return a_dict.get('load_time', ""), "Available as of: "
            elif a_dict.get('dist_publish_time', False):
                return a_dict.get('dist_publish_time', ""), "Published: "
            else:
                return "", ""
        
        best_ui_time, date_tag = get_best_ui_time(data_dict.get('attributes', {}))
        
        # byline ... this uses 'content items' like the body and must
        # be recursively parsed to get the text and any other attributes
        byline_concat = ""
        if 'byline' in data_dict.get('attributes', {}):
            by_line_content = data_dict.get('attributes', {}).get('byline', {}).get('content',[])
            if by_line_content != []:
                byline_list = self.gather_all_nested_content(content_resources_list, by_line_content)
                byline_concat = ''.join(byline_list)
                if byline_concat == "":
                    byline_concat = data_dict.get('attributes', {}).get('byline', {}).get('text', '')
                    

                      
                
        
        
        #Code Sets
        region_code_list = []
        subject_code_list = []
        people_code_list = []
        industry_code_list = []
        language_code_list = []
        source_code_list = []
        company_code_list = []
        author_code_list = []
        organization_code_list = []
        
        #Get the code sets
        code_set_list= data_dict.get('meta', {}).get('code_sets', [])
        
        for code_set in code_set_list:
            if code_set['type'] == 'Region':
                region_code_list.extend(code_set['codes'])
            elif code_set['type'] == 'NewsSubject':
                subject_code_list.extend(code_set['codes'])
            elif code_set['type'] == 'People':
                people_code_list.extend(code_set['codes'])
            elif code_set['type'] == 'Industry':
                industry_code_list.extend(code_set['codes'])
            elif code_set['type'] == 'Language':
                language_code_list.extend(code_set['codes'])
            elif code_set['type'] == 'Source':
                source_code_list.extend(code_set['codes'])
            elif code_set['type'] == 'Company':
                company_code_list.extend(code_set['codes'])
            elif code_set['type'] == 'Organization':
                organization_code_list.extend(code_set['codes'])
            elif code_set['type'] == 'Author':
                author_code_list.extend(code_set['codes'])
                
        #Headline Special Handling
        headline_text = data_dict.get('attributes', {}).get('headline', {}).get('main', {}).get('text', "")
        headline_deck_content = data_dict.get('attributes', {}).get('headline', {}).get('deck', {}).get('content', [])
        headline_deck_text = self.gather_all_nested_content(content_resources_list, headline_deck_content)
        if isinstance(headline_deck_text, list):
            headline_deck_text = ''.join(headline_deck_text)
            
        
        user_profile = {"user_name": "michasmi", "user_email": "michael@justbuildit.com","time_zone": "America/Los_Angeles"}
        
        time_zone = user_profile.get('time_zone', "America/New_York")   
        iso_pub_date = data_dict.get('attributes', {}).get('dist_publish_time', "")
        user_customized_date = self.convert_iso_to_formatted_date(best_ui_time, time_zone)
        hours_ago = self.hours_ago_utc(best_ui_time)
        if hours_ago <= 24:
            if hours_ago < 1:
                user_customized_date = f"{int(hours_ago*60)} minutes ago"
            else:
                user_customized_date = f"{int(hours_ago)} hours ago"    
            
        image_dict = ""
        is_rich = False
        image_dict, is_rich = get_rich_indicator_image(content_resources_list)
        
        if image_dict == "":
            image_dict = {"url": "https://devcommunifypublic.blob.core.windows.net/devcommunifynews/wsj-dark.png"}
            
        flat_article = {
                
                #Storage Keys
                "PartitionKey": search_string,
                "RowKey": data_dict.get('id', ""),
                
                # "id_from_retrieval":        data_dict.get('id', ""),
                "id":                       data_dict.get('id', ""),
                "alternate_document_id":    data_dict.get('meta', {}).get('alternate_document_id', ""),
                "alternate_document_ref":   data_dict.get('meta', {}).get('alternate_document_ref', ""),
                "original_doc_id":          data_dict.get('meta', {}).get('original_doc_id', ""),   
                "link":  data_dict.get('links', {}).get('self', ""),
                
                # Article Details
                "type":  data_dict.get('type', ""),
                "content_type":  data_dict.get('attributes', {}).get('content_type', ""),
                "is_rich": is_rich,
                "image_dict": image_dict,
                "copyright":  " ".join(data_dict.get('attributes', {}).get('copyright', {}).values()),
                "word_count":  data_dict.get('meta', {}).get('metrics', {}).get('word_count', "0"),  
                "source_name": data_dict.get('meta', {}).get('source', {}).get('name', ""),
                "publisher_name": data_dict.get('attributes', {}).get('publisher', {}).get('name', ''),
                "publisher_code": data_dict.get('attributes', {}).get('publisher', {}).get('code', ''),
                "column_name":  data_dict.get('attributes', {}).get('column_name', ""),
                "hosted_url":  data_dict.get('attributes', {}).get('hosted_url', ""),
                "page":  data_dict.get('attributes', {}).get('page', ""),
                "product":  data_dict.get('attributes', {}).get('product', ""),
                "section_type":  data_dict.get('attributes', {}).get('section_type', ""),
                "section_name":  data_dict.get('attributes', {}).get('section_name', {}).get('text', ""),
                "keywords":  data_dict.get('meta', {}).get('keywords', []),
                "is_translation_allowed":  data_dict.get('meta', {}).get('is_translation_allowed', ""),
                
                #Short Text (frequently not on the article)
                "headline": headline_text,
                "headline_deck": headline_deck_text,
                "byline":  byline_concat,
                
                #Body
                "body_list": data_dict.get('attributes', {}).get('body', []),
                # "html_article": self.get_html_article(attributes_dict = data_dict.get('attributes', {})),
                
                #Meta Strings
                "language_code":  data_dict.get('meta', {}).get('language', {}).get('code', ""),
                
                #Dates
                "publication_date":  data_dict.get('attributes', {}).get('publication_date', ""),
                "publication_time": data_dict.get('attributes', {}).get('publication_time', ""),
                "modification_date":  data_dict.get('attributes', {}).get('modification_date', ""),
                "modification_time": data_dict.get('attributes', {}).get('modification_time', ""),
                "dist_publish_date": data_dict.get('attributes', {}).get('dist_publish_date', ""),
                "dist_publish_time": data_dict.get('attributes', {}).get('dist_publish_time', ""),
                "load_date": data_dict.get('attributes', {}).get('load_date', ""),
                "load_time": data_dict.get('attributes', {}).get('load_time', ""),
                "live_date": data_dict.get('attributes', {}).get('live_date', ""),
                "live_time": data_dict.get('attributes', {}).get('live_time', ""),
                "best_ui_time": best_ui_time,
                "date_tag": date_tag,
                
                #Date Time
                "user_customized_date_time": user_customized_date,
                "hours_ago": data_dict.get('attributes', {}).get('dist_publish_date', ""),
                
                #Code Sets
                "region_codes": region_code_list ,
                "subject_codes": subject_code_list,
                "people_codes": people_code_list ,
                "industry_codes": industry_code_list ,
                "language_codes": language_code_list ,
                "source_codes": source_code_list ,
                "company_codes": company_code_list ,
                "author_codes": author_code_list ,
                "organization_codes": organization_code_list ,
                "content_resources": content_resources_list,
            
        }
        

        
        
        
        return flat_article



#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#   
#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
#!#######               TAXONOMY                 ##########
#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#

            
    def set_complete_taxonomy(self):
        
        def create_new_complete_taxonomy():
            
            def get_fixed_taxonomy():
            
                # Get the fixed "Category" taxonomy. 
                # This is the top level categories published by Dow Jones structured from the top down.
                # Note: I (Michael S.) made this document from the fixed taxonomy list published by Dow Jones
                # and gave it a sensible structure for our purposes.  It is high level is this structure 
                # is extremely unlikely to change; (it's a JSON file that I created from the fixed taxonomy list) that is stored
                # in the same folder as this script.  It is in a py file named _dj_fixed_taxonomy.py and is imported at the top.
                
                fixed_tax = asyncio.run(self.bmm.get_data(partitionkey="communify_data", rowkey="fixed_taxonomy"))
                if isinstance(fixed_tax, dict):
                    self.fixed_taxonomy_dict = fixed_tax
                else:
                    self.fixed_taxonomy_dict = json.loads(fixed_tax)
                return self.fixed_taxonomy_dict
                    
            def make_api_request_for_taxonomy(category=None, endpoint=None, child_endpoint_suffix="", language="en", request_attempt=1):
                # API endpoint

                url = f"https://api.dowjones.com{endpoint}{child_endpoint_suffix}?language={language}"
                #print(url)

                token = self.get_nearest_valid_authz_token()

                # Headers
                headers = {
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {token}'
                }
                # Making the GET request
                wait_time = random.uniform((DEFAULT_SLEEP_TIME*.5*1000), (DEFAULT_SLEEP_TIME*1.5*1000))
                wait_time = wait_time/1000
                time.sleep(wait_time)
                response = requests.get(url, headers=headers)

                if response.ok:
                    # Token is valid, response is good.
                    self.add_to_dj_log(f"OK: Received category taxonomy for {category}")
                    return response.json()
                elif response.status_code == 400:
                    self.add_to_dj_log(f"URL: {url} Error: {response.status_code} - {response.text}", 'ERROR')
                    return self.last_log_entry  
                # Token Expired
                elif response.status_code == 401:
                    # Token Expired
                    self.add_to_dj_log(f"TOKEN EXPIRED: {response.status_code} - {response.text} ... Getting new token","WARNING")
                    self.get_nearest_valid_authz_token()
                    return self.get_category_taxonomy(category=category, endpoint=endpoint, child_endpoint_suffix=child_endpoint_suffix, language=language)
                
                # Rate Limit or no children (DJ logging is not clear on this so have to assume it's a rate limit and try again)
                elif response.status_code == 500:
                    break_time = 0
                    
                    # This error is not clear, so we'll try again
                    if request_attempt == 1 and "does not have any children" not in response.text:
                        break_time = 10
                        self.add_to_dj_log(f"Taking a {break_time} second break from API Calls as code 500 was returned with error description of {response.text}.  Attempt {request_attempt} of 2 for category {category}", 'WARNING')
                        
                        # Take a break from API Calls (may have exceeded rate limit)
                        time.sleep(break_time)
                        request_attempt += 1
                        return self.make_api_request_for_taxonomy(category=category, endpoint=endpoint, child_endpoint_suffix=child_endpoint_suffix, language=language, request_attempt=request_attempt)
                    
                    # We already retried, so we'll log the error and return and give up
                    else:
                        self.add_to_dj_log(f"Error: {response.status_code} - {response.text}", 'ERROR')
                        return self.last_log_entry
                        
                else:
                    # Error of some kind other than 401 (expired token) or 500 (rate limit)
                    self.add_to_dj_log(f"Error: {response.status_code} - {response.text}", 'ERROR')
                    return self.last_log_entry
            
            def get_category_list_taxonomy(category="", endpoint=None, language="en", list_key_name=''):
                
                def strip_problem_characters(text):
                    text = text.replace('[', '')
                    text = text.replace(']', '')
                    # text = text.replace('(', '')
                    # text = text.replace(')', '')
                    text = text.replace('{', '')
                    text = text.replace('}', '')
                    text = text.replace(':', '-')
                    text = text.replace('\\', '-')
                    text = text.replace('/', '-')
                    return text
                    
                    
                #getting the endpoint for the list for the passed in category
                if not endpoint:
                    endpoint = self.fixed_taxonomy_dict[category].get("list", {}).get('endpoint', "")
                
                #Something is wrong if we don't have a list endpoint would likely be a corrupt or missing file.
                if not endpoint or endpoint == "":
                    self.add_to_dj_log(f"Error: {category} list endpoint not found in fixed taxonomy", 'ERROR')
                    ValueError(self.last_log_entry)

                else:
                    #We have a list endpoint, so we'll use it to get the list
                    list_dict = make_api_request_for_taxonomy(category=category, endpoint=endpoint, child_endpoint_suffix="", language=language)
                    
                    with open(f"{self.COMPLETE_TAXONOMY_FILE_PATH.replace('COMPLETE_dj_fixed_taxonomy', list_key_name)}", 'w') as f:
                        f.write(json.dumps(list_dict, indent=4))
                    
                    
                    #The complete_taxonomy_dict has the fixed as its base. We will add these values to it.
                    self.complete_taxonomy_dict[category]['data'] = list_dict['data']['attributes'][list_key_name]
                    
                    #Flatten the list of dictionaries to a list of strings. Use this for list of things to search for.
                    list_of_dicts_to_flatten = list_dict['data']['attributes'][list_key_name]
                    flattened_dictby_description = {}
                    flattened_dictby_code = {}
                    
                    for dict_item in list_of_dicts_to_flatten:
                        if dict_item is not None and dict_item != {}:
                            desc = dict_item.get('descriptor', '')
                            desc = strip_problem_characters(self.remove_non_printable(desc))
                            flat_value = self.remove_non_printable(dict_item.get('code', ''))
                            flat_key = strip_problem_characters(f"{desc} ({flat_value})").replace(' ', '_')  
                            flattened_dictby_description[flat_key]=flat_value
                            flattened_dictby_code[flat_value]=flat_key
                    
                    self.full_taxonomy_by_code_dict.update(flattened_dictby_code)   
                    self.complete_taxonomy_dict[category]['simple_dict'] = flattened_dictby_description
                    
                    self.add_to_dj_log(f"Retrieved {category} list and appended to complete taxonomy and saved to file")
                
                return flattened_dictby_code
        
            
            
            ##### Start of the create_new_complete_taxonomy function
            fixed_taxonomy = get_fixed_taxonomy()
            
                
            #Step #1: Reset the fixed and complete taxonomy to be the fixed taxonomy (the fixed is the base for the complete)
            self.fixed_taxonomy_dict = fixed_taxonomy
            self.complete_taxonomy_dict = self.fixed_taxonomy_dict
            
            #Step #2: get the list results for each category that has a list endpoint
            #The list endpoint is a simplified version of the regular taxonomy (simpler because there is no nesting)
        
            #GET /taxonomy/factiva-industries/list - Retrieves the plain list of industries.
            all_taxonomies = {
                "industry_dict": get_category_list_taxonomy(category='Industry', list_key_name='industries', language="en"),
                
                #GET /taxonomy/factiva-languages - Retrieves the full taxonomy of languages.,
                "region_dict": get_category_list_taxonomy(category='Region', list_key_name='regions', language="en"),
                
                #GET /taxonomy/factiva-news-subjects/list - Retrieves the plain list of news subjects.,
                "subject_dict": get_category_list_taxonomy(category='Subject', list_key_name='news_subjects', language="en"),
                
                #GET /taxonomy/factiva-regions/list - Retrieves the plain list of regions.,
                "language_dict": get_category_list_taxonomy(category='Language', endpoint='/taxonomy/factiva-languages', list_key_name='languages', language="en"),
                
                "all_codes_dict": self.full_taxonomy_by_code_dict,
            }
                
            # Add the full taxonomy by code to the complete taxonomy
            self.complete_taxonomy_dict['full_taxonomy_by_code'] = self.full_taxonomy_by_code_dict
            
            #Save the complete taxonomy to the the defined location
            complete_taxonomy_dict = {
            'partitionkey': "communify_files",
            'rowkey': "complete_taxonomy",
            'structdata' : self.full_taxonomy_by_code_dict
            }
            
            asyncio.run(self.bmm.upsert_data(data_items=complete_taxonomy_dict))
                
            self.add_to_dj_log(f"Completed the recreation of the complete taxonomy")

        
        
        # Get the complete "Category" taxonomy. This should exist (at least a prior version) unless there a file
        # access issue or the first time this code is run. A schduled job should keep this file up to date. It 
        # should be a complete list of all categories and sub-categories.  It is important to update it regularly
        # but it doesn't materially change hour-to-hour. 
                    
        if self.complete_taxonomy_dict is not None:
            # If it's already loaded, return it
            return self.complete_taxonomy_dict
        
        else:
            # Try to load it; if it can't be loaded, recreate it
            #Is the file there?
            # First try to get it locally
            got_taxonomy = False
            
            
            if not got_taxonomy:
                #Try to get it from azure
            
                #It's not loaded and there's no existing file, so we must create it
                create_new_complete_taxonomy()
            
            complete_taxonomy_dict, value, success = self.get_dict_and_value_from_text_safely(file_contents, "Language", "Getting Taxonomy Dictionary and Value from the stored text files")
            
            #Now we have a file, so try to load it
            if not os.path.exists(f'{self.COMPLETE_TAXONOMY_FILE_PATH}'):
                # Have to give up if we can't find the file or create it .... something big is wrong.
                raise ValueError(f'Cannot find or create the complete taxonomy file at {self.COMPLETE_TAXONOMY_FILE_PATH}. Cannot continue without it.')
                exit()
            
            # The file either now exists or we exited so we can assume it is there
            with open(f'{self.COMPLETE_TAXONOMY_FILE_PATH}', 'r') as f:
                #get the file contents
                file_contents = f.read()
            
            
            
            if success:
                self.complete_taxonomy_dict = complete_taxonomy_dict
                self.full_taxonomy_by_code_dict = complete_taxonomy_dict.get('full_taxonomy_by_code', {})
                self.add_to_dj_log(f'Loaded complete taxonomy and AllByCode at path {self.COMPLETE_TAXONOMY_FILE_PATH}')
                return self.complete_taxonomy_dict
            else:
                self.add_to_dj_log(f'Error loading complete taxonomy at path {self.COMPLETE_TAXONOMY_FILE_PATH}: {value}', 'CRITICAL')
                exit()    

    def get_tax_cat(self, category_code):
        """
        Retrieves the data for a particular taxonomy category based ona  given code

        Parameters:
        - category_code (str): The code of the category. Valid values are:
        Industry, Region, Subject, Language, AllByCode

        Returns:
        - tax_category (diyctionary): ALLBYCODE returns all categories with the code as the key.
        The others return a single category with the description as the key. 
        Make sure to replace spaces with underscores as appropriate for visualization or key lookup.
        """
        valid_category_codes = ['Industry', 'Region', 'Subject', 'Language', 'AllByCode', 'AllByValue']
        
        if category_code not in valid_category_codes:
            return None

        # Get the stored complete Taxonomy
        complete_taxonomy_list = asyncio.run(self.bmm.get_data(partitionkey="communify_files", rowkey="complete_taxonomy"))
        
        if complete_taxonomy_list is None or not isinstance(complete_taxonomy_list, list):
            self.add_to_dj_log(f"Error: No complete taxonomy found of type LIST", 'ERROR')
            return None
        
        complete_taxonomy = complete_taxonomy_list[0]
        
        list_of_strings = []
        if category_code == 'AllByCode':
            list_of_strings = complete_taxonomy.keys()
        
        if category_code == 'AllByValue':
            list_of_strings = complete_taxonomy.values()

        else:
            list_of_strings = complete_taxonomy.get(category_code, {}).get('simple_dict', {}).keys()
            
        str_list = [str(s) for s in list_of_strings]

        #Remove the underscores from the strings
        new_list = [s.replace("_", " ") for s in str_list]    
        
        return new_list



#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#   
#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
#!###########          LOGGING            #################
#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
    
    def add_to_dj_log(self, message, status=logging.INFO, status_str = ""):
        def get_level_num(self, status):
            try: 
                return  logging.get_logging_level(status.upper())
            except: 
                pass
                return logging.ERROR
            
        #Dictionary of Terminal Colors
        c = {"BLACK": '\033[0;30m', "RED": '\033[0;31m', "RED_U": '\033[4;31m', "RED_BLINK": '\033[5;31m', "GREEN": '\033[2;32m', "GREEN_BLINK": '\033[5;32m', "YELLOW": '\033[0;33m', "YELLOW_BOLD": '\033[1;33m', "PURPLE": '\033[1;34m', "PURPLE_U": '\033[4;34m', "PURPLE_BLINK": '\033[5;34m', "PINK": '\033[0;35m', "PINK_U": '\033[4;35m', "PINK_BLINK": '\033[5;35m', "LIGHTBLUE": '\033[0;36m', "LIGHTBLUE_BOLD": '\033[1;36m', "GRAY": '\033[0;37m', "ORANGE": '\033[1;91m', "BLUE": '\033[1;94m', "CYAN": '\033[1;96m', "WHITE": '\033[1;97m', "MAGENTA": '\033[1;95m', "BOLD": '\033[1m', "UNDERLINE": '\033[4m', "BLINK": '\033[5m', "NONE": '\033[0m'}

        has_already_been_printed = False
        def print_log_entry(log_entry, has_already_been_printed):
            if not has_already_been_printed:
                print(log_entry)
                has_already_been_printed = True
            return has_already_been_printed

        
        try:
            if isinstance(status, str) and status.upper() in c.keys():
                log_entry = [f"""{status} ({datetime.now().strftime('%y.%m.%d %H:%M:%S')}) {message}"""]
                # log_entry_terminal  = f"{c[status]}{log_entry}{c['NONE']}"
                log_entry_terminal  = f"{log_entry}{c['NONE']}"
                status_num = logging.INFO
            else:
                if isinstance(status, str): 
                    try:
                        status_num = self.get_level_num(status)
                    except: 
                        status_num = logging.ERROR
                else: 
                    status_num = status
            
                status_str = logging.getLevelName(status_num)
                
                log_entry = [f"""{status_str} ({datetime.now().strftime('%y.%m.%d %H:%M:%S')}) {message}"""]

                
                if status_num <= 20 : 
                    log_entry_terminal  = f"{c['NONE']}{log_entry}{c['NONE']}"
                elif status_num <= 30 : 
                    log_entry_terminal  = f"{c['ORANGE']}{log_entry}{c['NONE']}"
                    has_already_been_printed=print_log_entry(log_entry_terminal, has_already_been_printed)    
                elif status_num <= 40 : 
                    log_entry_terminal  = f"{c['RED']}{log_entry}{c['NONE']}"
                    has_already_been_printed=print_log_entry(log_entry_terminal, has_already_been_printed)    
                elif status_num <= 50 :
                    log_entry_terminal  = f"{c['RED_U']}{log_entry}{c['NONE']}"
                    has_already_been_printed=print_log_entry(log_entry_terminal, has_already_been_printed)    
            
            if status in c.keys():
                log_entry_terminal  = f"{c[status]}{log_entry}{c['NONE']}"
                has_already_been_printed=print_log_entry(log_entry_terminal, has_already_been_printed)    

            logging.log(status_num, log_entry_terminal) # Log message
            
        except Exception as e:
            print(f"""{c['RED_U']}
                    Error adding log entry: {e}
                    Message: {message} Status: {status}
                    Last Log Entry: {self.last_log_entry}
                    Session Log File Path: {self.session_log_file_path}
                    {c['NONE']}""")
    
    async def upload_required_assets(self):
        files= ['wsj.png', 'dj_FIXED_taxonomy.json', 'cflogo.png', 'dj_COMPLETE_taxonomy.json']
        for file in files:
            await self.upload_blob_file(file, open(file=os.path.join('assets', file), mode="rb"))

    async def upsert_parameter(self, parameter_code, parameter_value):
        
        new_parameter = {
            "PartitionKey": "parameter_code",
            "RowKey": parameter_code,   # Article ID (unique)
            "parameter_value": parameter_value      # Image URL
            }
    
        table_client = TableClient.from_connection_string(self.connection_string, self.table_name)
        
        async with table_client:
            try:
                resp = await table_client.upsert_entity(mode=UpdateMode.MERGE, entity=new_parameter)
                return resp
            except ResourceExistsError:
                resp = await table_client.update_entity(mode=UpdateMode.REPLACE, entity=new_parameter)
                print(resp)

    async def get_parameters(self, parameter_code=None):

            # [START query_entities]
            async with TableClient.from_connection_string(self.connection_string, self.table_name) as table_client:
                try:
                    parameters: Dict[str, Any] = {"RowKey": "None"}
                    article_id_filter = "RowKey ne @RowKey"
                    
                    queried_entities = table_client.query_entities(
                        query_filter=article_id_filter, select=["RowKey", "parameter_value"], parameters=parameters
                    )
                    async for entity_chosen in queried_entities:
                        if entity_chosen and entity_chosen != {}:
                            parameter_dict = {}
                            for key, value in entity_chosen.items():
                                parameter_dict[key] = value
                                # print(parameter_dict)
                            return parameter_dict
                except HttpResponseError as e:
                    raise
                return {}     
            # ND query_entities]
            
    async def delete_parameter(self, parameter_code=None):

            # [START query_entities]
            async with TableClient.from_connection_string(self.connection_string, self.table_name) as table_client:
                try:
                    resp = await table_client.delete_entity(partition_key=parameter_code)
                    return resp
                except HttpResponseError as e:
                    raise
 
    def __str__(self):
        # Return a string representation of the object
        self_description = f'''
        ## DJSearch
        ___
        ###### Created at: {self.created_at}   
        ###### Executed at: {self.executed_at}   
        ###### Returned at: {self.returned_at}   
        ###### Session Log: {self.session_log_file_path}   
        ###### Env. Var: DJ_AUTHZ_ACCESS_TOKEN: {os.environ.get('DJ_AUTHZ_ACCESS_TOKEN')}  
        
        ___
        
        ##### Search String: {self.search_string}
        ___
        
        ### Search Results: 
        {self.search_results}
        ___
        
        ### Articles
        {self.articles} 
        
        ___
                    
                    '''
        return self_description




#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#   
#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
#!###########        STATIC DICTS         #################
#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#
#!##*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*##*#*#*#*#*#*#*#*#

def get_valid_dj_date_ranges():
    return {
        "None": "None",
        "LastDay": "Last 24hrs",
        "LastWeek": "Last Week",
        "LastMonth": "Last Month",
        "Last3Months": "Last 3 Months",
        "Last6Months": "Last 6 Months",
        "LastYear": "Last Year",
        "Last2Years": "Last 2 Years",
        "Last5Years": "Last 5 Years",
        "AllDates": "All available dates",
        "<Custom>": "<Custom>"
    }

def get_test_categories():
    
    #Add 100 names of people
    test_search_categories = ['Elon Musk', 'Jeff Bezos', 'Bill Gates', 'Warren Buffet', 'Larry Page', 'Sergey Brin', 'Mark Zuckerberg', 'Jack Ma', 'Tim Cook', 'Satya Nadella', 'Larry Ellison', 'Steve Ballmer', 'Steve Jobs', 'Michael Dell', 'Reed Hastings', 'Marc Benioff', 'Brian Chesky', 'Travis Kalanick', 'Dara Khosrowshahi', 'Daniel Ek', 'Evan Spiegel', 'Bobby Murphy']
    #Add 100 random search terms
    test_search_categories.extend(['Electric Cars', 'SpaceX', 'Artificial Intelligence', 'Machine Learning', 'Quantum Computing', '5G', 'Cloud Computing', 'Cybersecurity', 'Blockchain', 'Cryptocurrency', 'Virtual Reality', 'Augmented Reality', 'Internet of Things', 'Smart Cities', 'Renewable Energy', 'Sustainable Agriculture', 'Biotechnology', 'Genomics', 'CRISPR', 'Nanotechnology', '3D Printing', 'Robotics', 'Drones', 'Autonomous Vehicles', 'Smart Homes', 'Wearable Technology', 'Health Tech', 'EdTech', 'FinTech', 'InsurTech', 'RegTech', 'Legal Tech', 'GovTech', 'AgTech', 'Food Tech', 'Retail Tech', 'Travel Tech', 'Hospitality Tech', 'Real Estate Tech', 'Construction Tech', 'Manufacturing Tech', 'Supply Chain Tech', 'Logistics Tech', 'Transportation Tech', 'Energy Tech', 'Utilities Tech', 'Telecom Tech', 'Media Tech', 'Entertainment Tech', 'Sports Tech', 'Gaming Tech', 'Music Tech', 'Film Tech', 'TV Tech', 'Advertising Tech', 'Marketing Tech', 'Sales Tech', 'Customer Service Tech', 'HR Tech', 'Recruiting Tech', 'Training Tech', 'Learning Tech', 'Development Tech', 'Engineering Tech', 'Design Tech', 'Product Tech', 'Project Tech', 'Management Tech', 'Leadership Tech', 'Strategy Tech', 'Consulting Tech', 'Finance Tech', 'Accounting Tech', 'Legal Tech', 'Compliance Tech', 'Risk Tech', 'Security Tech', 'Privacy Tech', 'Ethics Tech', 'Sustainability Tech', 'CSR Tech', 'ESG Tech', 'Diversity Tech', 'Inclusion Tech', 'Equity Tech', 'Justice Tech', 'Human Rights Tech', 'Civil Rights Tech', 'Social Justice Tech', 'Environmental Justice Tech', 'Economic Justice Tech', 'Political Justice Tech', 'Legal Justice Tech', 'Health Justice Tech', 'Educational Justice Tech', 'Criminal Justice Tech', 'Restorative Justice Tech', 'Reparative Justice Tech', 'Transitional Justice Tech', 'Peace Tech', 'Conflict Resolution Tech', 'Diplomacy Tech', 'Negotiation Tech', 'Mediation Tech', 'Arbitration Tech', 'Litigation Tech', 'Adjudication Tech', 'Judicial Tech'])
    # Add 100 cities
    test_search_categories.extend(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose', 'Austin', 'Jacksonville', 'Fort Worth', 'Columbus', 'Charlotte', 'San Francisco', 'Indianapolis', 'Seattle', 'Denver', 'Washington', 'Boston', 'El Paso', 'Nashville', 'Detroit', 'Oklahoma City', 'Portland', 'Las Vegas', 'Memphis', 'Louisville', 'Baltimore', 'Milwaukee', 'Albuquerque', 'Tucson', 'Fresno', 'Mesa', 'Sacramento', 'Atlanta', 'Kansas City', 'Colorado Springs', 'Omaha', 'Raleigh', 'Miami', 'Long Beach', 'Virginia Beach', 'Oakland', 'Minneapolis', 'Tulsa', 'Arlington', 'Tampa', 'New Orleans', 'Wichita', 'Cleveland', 'Bakersfield', 'Aurora', 'Anaheim', 'Honolulu', 'Santa Ana', 'Riverside', 'Corpus Christi', 'Lexington', 'Stockton', 'St. Paul', 'Anchorage', 'Newark', 'Plano', 'Fort Wayne', 'St. Petersburg', 'Glendale', 'Lincoln', 'Norfolk', 'Jersey City', 'Greensboro', 'Chandler', 'Birmingham', 'Henderson', 'Scottsdale', 'North Las Vegas', 'Laredo', 'Madison', 'Lubbock', 'Reno', 'Buffalo', 'Gilbert', 'Winston-Salem', 'Glendale', 'Hialeah', 'Garland', 'Chesapeake', 'Irving', 'North Las Vegas', 'Fremont', 'Baton Rouge', 'Richmond', 'Boise', 'San Bernardino', 'Spokane', 'Des Moines', 'Modesto', 'Birmingham', 'Tacoma', 'Fontana', 'Rochester', 'Oxnard', 'Moreno Valley', 'Fayetteville', 'Aurora', 'Glendale', 'Yonkers', 'Huntington Beach', 'Montgomery', 'Amarillo', 'Akron', 'Little Rock', 'Augusta', 'Grand Rapids', 'Mobile', 'Salt Lake City', 'Huntsville', 'Tallahas'])
    # Add 100 countries
    test_search_categories.extend(['United States', 'China', 'Japan', 'Germany', 'India', 'United Kingdom', 'France', 'Brazil', 'Italy', 'Canada', 'South Korea', 'Russia', 'Australia', 'Spain', 'Mexico', 'Indonesia', 'Netherlands', 'Saudi Arabia', 'Turkey', 'Switzerland', 'Sweden', 'Poland', 'Belgium', 'Norway', 'Austria'])
    #List 200 Companies
    test_search_categories.extend(['Apple', 'Microsoft', 'Amazon', 'Alphabet', 'Facebook', 'Alibaba', 'Tencent', 'Tesla', 'Samsung', 'Walmart', 'Berkshire Hathaway', 'Johnson & Johnson', 'Visa', 'Procter & Gamble', 'Mastercard', 'JPMorgan Chase', 'UnitedHealth Group', 'Nestle', 'Taiwan Semiconductor', 'Roche', 'Walt Disney', 'Home Depot', 'Novartis', 'Verizon', 'Intel', 'Coca-Cola', 'Adobe', 'Netflix', 'Pfizer', 'Comcast', 'Toyota', 'Merck', 'Cisco', 'Abbott Laboratories', 'Accenture', 'PepsiCo', 'Broadcom', 'Novo Nordisk', 'LVMH', 'Salesforce', 'ASML', 'BHP', 'T-Mobile', 'Qualcomm', 'NVIDIA', 'Siemens', 'AstraZeneca', 'Goldman Sachs', 'Unilever', 'Daimler', 'AbbVie', 'Linde', 'Danaher', 'L\'Oreal', 'Bristol-Myers Squibb', 'Thermo Fisher Scientific', 'McDonald\'s', 'Honeywell', 'Starbucks', 'General Electric', 'Sony', 'Volkswagen', 'Amgen', 'Mitsubishi', 'IBM', 'L\'Oreal', 'Bayer', 'Nokia', 'Caterpillar', 'Deutsche Telekom', '3M', 'BASF'])
    
    return test_search_categories

def get_dj_fixed_taxonomy():

    dj_fixed_taxonomy={
    
    
        "Author": {
            "search": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-authors/search",
            "definition": "Retrieves a user-filtered collection of authors.",
            "category": "factiva-authors"
            }
        },
        "Company": {
            "search": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-companies/search",
            "definition": "Retrieves a user-filtered collection of companies.",
            "category": "factiva-companies"
            }
        },
        "Language": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-languages",
            "definition": "Retrieves the full taxonomy of languages.",
            "category": "factiva-languages"
        },
        "Industry": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-industries",
            "definition": "Retrieves the full taxonomy of industries.",
            "category": "factiva-industries",
            "children": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-industries/{id}/children",
            "definition": "Retrieves the child industries of an industry, using its Factiva code.",
            "category": "factiva-industries"
            },
            "list": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-industries/list",
            "definition": "Retrieves the plain list of industries.",
            "category": "factiva-industries"
            },
            "lookup": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-industries/lookup",
            "definition": "Retrieves details of an industry using its Factiva code.",
            "category": "factiva-industries"
            },
            "search": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-industries/search",
            "definition": "Retrieves a user-filtered collection of industries.",
            "category": "factiva-industries"
            }
        },
        "Subject": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-news-subjects",
            "definition": "Retrieves the full taxonomy of news subjects.",
            "category": "factiva-news-subjects",
            "children": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-news-subjects/{id}/children",
            "definition": "Retrieves the children news subjects of a news subject, using its Factiva code.",
            "category": "factiva-news-subjects"
            },
            "list": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-news-subjects/list",
            "definition": "Retrieves the plain list of news subjects.",
            "category": "factiva-news-subjects"
            },
            "lookup": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-news-subjects/lookup",
            "definition": "Retrieves details of a news subject using its Factiva code.",
            "category": "factiva-news-subjects"
            },
            "search": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-news-subjects/search",
            "definition": "Retrieves a user-filtered collection of news subjects.",
            "category": "factiva-news-subjects"
            }
        },
        "Region": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-regions",
            "definition": "Retrieves the full taxonomy of regions.",
            "category": "factiva-regions",
            "children": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-regions/{id}/children",
            "definition": "Retrieves the child regions of a region, using its Factiva code.",
            "category": "factiva-regions"
            },
            "list": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-regions/list",
            "definition": "Retrieves the plain list of regions.",
            "category": "factiva-regions"
            },
            "lookup": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-regions/lookup",
            "definition": "Retrieves details of a region, using its Factiva code.",
            "category": "factiva-regions"
            },
            "search": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-regions/search",
            "definition": "Retrieves a user-filtered collection of regions.",
            "category": "factiva-regions"
            }
        },
        "Source": {
            "children": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-sources/{id}/children",
            "definition": "Retrieves the child sources of a source, using its Factiva code.",
            "category": "factiva-sources"
            },
            "list": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-sources/{type}/list",
            "definition": "Retrieves the plain list of sources of a specified type.",
            "category": "factiva-sources"
            },
            "search": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-sources/search",
            "definition": "Retrieves a user-filtered collection of sources.",
            "category": "factiva-sources"
            },
            "title-search": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-sources/title/search",
            "definition": "Retrieves a user-filtered collection of titles from sources.",
            "category": "factiva-sources"
            }
        }
        }
    return dj_fixed_taxonomy

def get_common_dj_codes():
    
    dow_jones_news_codes = {

    "Practice Management & Industry Insight": [
        {"N/PMT": "Practice management news for advisers, including wealth management best practices, industry trends, and compliance issues."},
        {"I/SCR": "News about events in the securities industry and at financial services firms."}
    ],
    "Enhance Client Communication": [
        {"N/PFN": "Getting Personal column and other stories for conversation starters on retirement, college, estate planning, and other personal finance topics."},
        {"N/POV": "Point of View and other columns - Exclusive insights on a wide range of topics affecting the markets and portfolios."},
        {"N/JNL": "Be prepared if a client wants to talk about a particular article from The Wall Street Journal."},
        {"N/BRN": "Articles from Barron's, the premier financial weekly."}
    ],
    "Use News as a Prospecting Source": [
        {"N/LYO": "Prospect 401(k) rollover business using layoff news."},
        {"N/TNM": "Merger and acquisition news may uncover company insiders who have concentrated positions in the company and need diversification."},
        {"N/PER": "News about executive appointments in your area may lead to 401(k) rollover and other planning business."},
        {"N/INI": "Executives and shareholders of companies going public may need help with diversification."},
        {"N/SML": "Small Business"}
    ],
    "Generate Actionable Sales Ideas": [
        {"N/DIV": "Weekly table of the Top Five Dividend Yielding Stocks in Major Industries - runs every Monday 9:15 a.m. ET (use link via DJ NewsPlus)"},
        {"N/SPL": "Table of upcoming stock splits runs daily at 9 a.m."},
        {"N/ISD": "Insider activity may give indications when to advise clients to buy or sell."},
        {"S/FNS": "Mutual fund performance tables that rate the Top and Bottom 10 performers for several fund types."},
        {"N/NYH": "Look for trading opportunities in Hot Stocks to Watch."}
    ],
    "Leverage Financial Planning News in Your Practice": [
        {"N/EPL": "Education Planning - Search on keywords: education planning, 529 plan."},
        {"N/RET": "Retirement Planning - Search on keywords: Roth IRA, 401(k), pension."},
        {"N/EST": "Estate Planning - Reach out to estate planning attorneys in your referral network with news relevant to their field. Keyword search: estate planning."},
        {"N/TAX": "News about corporate and personal taxes, policies, and legislation."}
    ],
    "Respond to Client Calls about Market Activity": [
        {"DJDAY": "One stop for market news, columns, and stats throughout the day."},
        {"N/NYS": "Follow U.S. stock market activity from pre-opening to closing bell."},
        {"N/CAL": "Calendars that help you plan ahead - for the day or next week."},
        {"S/KIR": "Hourly key interest rates from 9 a.m. to 5 p.m."},
        {"G/FED": "Market-moving news on interest rate policy - includes Fed Watch, a column that examines Fed policies and their potential impact on the markets."}
    ],
    "Develop Investing Strategies with Dow Jones Analysis": [
        {"N/TSH": "Tipsheet - Daily fund manager interview. See where the pros are putting money to work in the markets."},
        {"N/TOT": "Focus - An in-depth look at a company or industry and its future prospects."},
        {"N/IMN": "In the Money - Studies company valuation and trading strategies."},
        {"N/DJTA": "Several columns incorporating detailed technical analysis and market trend observations."},
        {"N/SSM": "Taking Stock - A view of developments in the global markets that goes beyond standard analyst commentary."},
        {"N/HRD": "Heard On The Street - Sharp-eyed look at companies and industries from Dow Jones and Wall Street Journal reporters."}
    ],
    "Highlights of Dow Jones News Service": [
        {"N/DJN": "Today's Headlines (All News)"},
        {"N/HOT": "Today's Hot, Market-Moving News"},
        {"DJDAY": "Roundup of Essential News, Comment, and Features"},
        {"N/DJMT": "DJ Market Talk - Streaming Market Commentary"},
        {"N/SUM": "Morning Briefing and News Summaries"},
        {"N/TLK": "Talk Back"}
    ],
    "Stock Market Features": [
        {"N/CAL": "Calendars (Daily, Earnings, Equity, Economic)"},
        {"N/NYS": "U.S. Stock Market Commentary"},
        {"N/NYH": "Today's Hot Stocks to Watch"},
        {"N/MMM": "Major Market-Moving Stocks"},
        {"N/INI": "Initial Public Offerings"},
        {"N/REG": "Stock and Bond Registrations/Pricing"},
        {"N/SOP": "Stock Option Commentary"},
        {"S/ACT": "Most Actives"},
        {"S/STT": "Stock Market Statistics"}
    ],
    "Corporate News": [
        {"N/ERN": "Earnings Reports"},
        {"N/ANL": "Analysts' Comments"},
        {"N/ISD": "Insider Trading/Washington Service"},
        {"N/DIV": "Dividends"},
        {"N/SPL": "Stock Splits"},
        {"N/BBK": "Buybacks"},
        {"N/TNM": "Takeovers, Mergers, Acquisitions"},
        {"N/BCY": "Bankruptcy"},
        {"N/LAB": "Labor/Employment Issues"}
    ],
    "Industry News": [
        {"I/DRG": "Drug Makers and Pharmaceuticals"},
        {"I/HEA": "Health Care Providers"},
        {"I/BNK": "Banking Industry"},
        {"I/RTS": "Retailers"},
        {"I/SEM": "Semiconductors"},
        {"I/CSE": "Consumer Electronics"},
        {"I/MED": "Media"},
        {"I/AUT": "Automobiles"},
        {"I/OIL": "Oil Companies"}
    ],
    "Fund News": [
        {"N/ETF": "Exchange Traded Funds"},
        {"N/FND": "Mutual Fund News"},
        {"S/FNS": "Mutual Fund Performance Tables"},
        {"S/PTF": "Weekly Closed-End Fund Tables"},
        {"N/HGF": "Hedge Fund News"},
        {"N/PEN": "Pension Fund News"}
    ],
    "Dow Jones Publications": [
        {"N/JNL": "The Wall Street Journal"},
        {"N/PAG": "Front Page of The Wall Street Journal"},
        {"N/EDC": "Editorials and Columns"},
        {"N/FRT": "Stories from the first page of each section"},
        {"N/HRD": "Heard on the Street from The Wall Street Journal"},
        {"N/BRN": "Barron's"},
        {"N/SMT": "SmartMoney (selected articles)"}
    ],
    "Credit Market News": [
        {"G/FED": "Federal Reserve"},
        {"G/TRE": "U.S. Treasury Information"},
        {"N/BON": "All Bond News"},
        {"N/TPC": "Treasury Prices and Commentary"},
        {"N/RTG": "Bond Ratings"},
        {"N/COB": "Corporate Bond News"},
        {"S/KIR": "Key Interest Rates"}
    ],
    "Economic & Political News": [
        {"N/EMI": "U.S. Economic Indicators and Data Snap - Summary of number, trend, and consensus"},
        {"N/EMJ": "U.S. Economic Forecasts and Analysis"},
        {"G/SEC": "Securities and Exchange Commission News"},
        {"G/EXE": "White House News"},
        {"G/CNG": "U.S. Congress News"},
        {"N/PLT": "Domestic and International Political News"}
    ],
    "Other Markets & Statistics": [
        {"N/NDX": "Stock and Other Indexes"},
        {"N/WSR": "Global Stock Indexes / World Stock Roundup"},
        {"N/SMC": "Global Stock Market Commentary"},
        {"S/MNR": "Money Rates"},
        {"N/GPC": "Gold Prices and Commentary"},
        {"N/CMD": "Commodities News"},
        {"N/FRX": "Foreign Exchange News"},
        {"S/FXH": "Foreign Exchange Rates - Hourly"},
        {"N/OPC": "OPEC News"}
    ],
    "International & Regional News": [
        {"R/TWO LETTER STATE ABBREVIATION": "News by State"},
        {"R/NY": "New York"},
        {"R/CH": "China"},
        {"R/II": "India"}
    ]
    }
    return dow_jones_news_codes

def run_common_codes():
    common_dict = get_common_dj_codes()
    DJS = DJSearch()

    for key in common_dict.keys():
        list_of_codes = common_dict.get(key, [])
        if len(list_of_codes) > 0:
            for code_dict in list_of_codes:
                codes = code_dict.keys()
                for code in codes:
                    run_examples(code_list=[code], DJS=DJS)
                        
def run_examples(code_list=None, DJS=None):
    # Example of how to use the DJSearch class
    if DJS is None:
        DJS = DJSearch()
        DJS.connect()
    
    # Connect to the Dow Jones API
    
    
    if code_list is None:
        code_list = ['CSCO', 'AA', 'AAPL', 'MSFT']
    
    # Set up a search configuration
    search_config = DJS.create_user_search_config()
    # search_config['config']['includeCodes'] = ['p/pmdm', 'i838']
    search_config['config']['includeCodes'] = code_list
    search_config['config']['excludeCodes'] = []
    search_config['config']['dateRange'] = "Last6Months"
    
    # print("\n\n\nTOKEN:")
    # DJS.display_token()
    
    
    print("\n\n\nSEARCH RESULTS:")
    search_results = DJS.search_by_config(search_config)
    DJS.print_search_results()



if __name__ == "__main__":
    DJS = DJSearch()
    DJS.connect()
    
    # DJS.get_articles_from_test_list()
    # DJS.search_quick()
    formatted_articles = DJS.get_test_rich_articles()
    pass
    # DJS.test_()
    # DJS.run_common_codes()
    # exit()
    