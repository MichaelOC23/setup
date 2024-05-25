


from flask import Flask, request, jsonify, redirect, url_for, session
from datetime import datetime

import torch
import ollama
import argparse
from openai import OpenAI


from openai import chat
from langchain.retrievers.you import YouRetriever 
import asyncio



import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright


import json
import os
import threading

from googleapiclient.discovery import build
from urllib.parse import urlparse
import urllib.parse

import html2text
import requests




import time
from io import StringIO

from bs4 import BeautifulSoup

import aiohttp

import zipfile
import csv
import uuid 

import base64
import hashlib

import setproctitle
import pyaudio
import subprocess
import threading
import queue
import websocket

#import urlencode
from urllib.parse import urlencode

yr = YouRetriever()


import _class_search_web
import _class_storage

#Deepgram
from dotenv import load_dotenv
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    FileSource,
    LiveOptions,
    LiveTranscriptionEvents,
    PrerecordedOptions,
    Microphone,)
load_dotenv()

print_it = False

def log_it(message, print_it=True, color='black'):
    is_dict, dict_value = got_dict(message)
    if is_dict:
        message = json.dumps(dict_value, indent=4)
    else:
        message = f"{message}"
        
    with open(os.path.join(log_directory, 'flask1.log'), 'a') as f:
        f.write(message)
        print(message)

# We will collect the is_final=true messages here so we can use them when the person finishes speaking
is_finals = []
API_KEY = os.getenv("DEEPGRAM_API_KEY")
LOG_FOLDER = "logs"


app = Flask(__name__)

state_parameters = {
    "DeepgramComnection": {
                "Open": "Open",
                "Closed": "Closed",
                "Error": "Error",
                "Unhandled": "Unhandles Websocket Message",
                "Default": "Closed"},
    "DeepgramErrorMessage": { 
                "ErrorMessage": "",
                "Default": "None"
                        }  
    }

data_directory = os.path.join('data', 'nasdaq')
log_directory = "logs"

if not os.path.exists(log_directory):
    os.makedirs(log_directory)
    
search = _class_search_web.Search()
storage = _class_storage.az_storage()

asyncio.run(storage.create_parameter("StartStopButton", "Start Meeting"))

#Make sure there is a parameter table to store state
asyncio.run(storage.create_table_safely(storage.parameter_table_name))

#Set default state parameters
for key in state_parameters.keys():
    asyncio.run(storage.create_parameter(key, state_parameters[key]["Default"]))

def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}".replace("channel_alternatives_","alt") if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, (dict, list)):
                    items.extend(flatten_dict({f"{i}": item}, new_key, sep=sep).items())
                else:
                    items.append((f"{new_key}{sep}{i}", item))
        else:
            items.append((new_key, v))
        
        flat_dict = dict(items)
        log_it(flat_dict)
    return flat_dict

@app.route('/isup', methods=['GET'])
def isup():
    return jsonify({"status": "SUCCESS! Background Flask is up and running"})

def got_dict(input_value):
    if isinstance(input_value, dict):
        return True, input_value
    try:
        type_value = type(input_value)
        input_value = json.loads(input_value)
    except Exception as e:
        return False, f"Type is: {type_value}.  Could not convert input to dictionary: {e}"
    
    
    
    return True, input_value

@app.route("/", methods=["GET"])
def test():
    # Insert your default code or parameter setup here
    
    search_query = '("Darryl Burns" OR  ("Darryl" AND "Burns"))  AND ()'
    
    search_results = asyncio.run(search.get_stored_search_results(search_query=search_query))
    resp = asyncio.run(scrape_all_results_async(search_results))
    
    return_value = ""
    if resp is not None:
        if isinstance(resp, list) or isinstance(resp, dict):
            return_value = jsonify(resp)
        else:
            return_value = resp
    return return_value


##############################################
####    SEARCH AND SCRAPE WEB FUNCTIONS    ####
##############################################

@app.route('/searchweb', methods=['POST'])
def searchweb():
    data = request.json
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    other = data.get('other', '')
    
    search.search_web_async_with_assemble(first_name, last_name, other)

@app.route('/scrape', methods=['POST'])
def scrape():
    
    data = request.json
    search_query = data.get('search_query', '')
    if not search_query:
        return jsonify({"error": "Search Query is required"}), 400

   
    search_results = asyncio.run(search.get_stored_search_results(search_query=search_query))
    resp = asyncio.run(scrape_all_results_async(search_results))
    
    return_value = ""
    if resp is not None:
        if isinstance(resp, list) or isinstance(resp, dict):
            return_value = jsonify(resp)
        else:
            return_value = resp
    return return_value

async def get_web_page_async(result):
    try:
        url = result.get('Orig_RowKey', '')
        
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            body = soup.body.get_text(separator=' ', strip=True)

            result['full_text_blob']= body
            result['full_html_blob']=response.text

            resp = await storage.add_update_or_delete_some_entities(storage.url_results_table_name, [result])
            return True
        else:
            print(f"Failed to retrieve {result.get('Orig_RowKey', '')}: Status code {response.status_code}")
            return ""
    except Exception as e:
        print(f"Error getting full webpage for {result.get('Orig_RowKey', '')}: {e}")
        return ""

async def scrape_all_results_async(search_results):
    search_tasks = []
    for result in search_results:
        search_tasks.append(get_web_page_async(result))
    scrape_success_list = await asyncio.gather(*search_tasks)
    return search_results


    
    
##############################################
######    PROSPECT DATA PIPELINE     #########
##############################################



class prospect_data_pipeline:
    def __init__(self):
        self.log_folder = LOG_FOLDER
        self.company =""
        self.location = ""
        self.CRD = ""
        self.llm_model = 'llama3'
        self.llm_base_url='http://localhost:11434/v1'
        self.llm_model_api_key='Local-None-Needed'
        
        self.embeddings_model = 'mxbai-embed-large'
        self.embeddings_base_url='http://localhost:11434/v1'
        self.embeddings_model_api_key='Local-None-Needed'
        
        self.scrape_session_history = {}

        self.embeddings_model='mxbai-embed-large'
        self.google_api_key = os.environ.get('GOOGLE_API_KEY', 'No Key or Connection String found')
        self.google_general_cx = os.environ.get('GOOGLE_GENERAL_CX', 'No Key or Connection String found')
        self.titles_list = [
                # "Founder",
                # "Managing Partner",
                # "Chairman",
                # "Chief Executive Officer (CEO)"
                "Wealth Management CEO",
                "Head of Wealth Management",
                # "Head of Private Banking",
                # "Head of Client Services",
                # "Head of Client Relations",
                # "Head of Client Experience",
                # "Head of Client Engagement",
                # "Head of Client Success",
                # "Chief Investment Officer (CIO)",
                # "Chief Financial Officer (CFO)",
                # "President",
                # "Managing Director",
                # "Partner",
                # "Executive Vice President (EVP)",
                # "Chief Strategy Officer (CSO)",
                # "Regional Managing Director",
                "Principal"]
    
    def process_prospect_main(self, propsect_data):
        
        new_prospect_dict = asyncio.run(self.async_process_prospect(propsect_data))
        asyncio.run(storage.add_update_or_delete_some_entities("prospects", [new_prospect_dict], alternate_connection_string=storage.jbi_connection_string))
    
    def is_valid_url(self, may_be_a_url):
        try:
            result = urlparse(may_be_a_url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False    
    
    def get_base_url(self, url):
        try: 
            parsed_url = urlparse(url)            
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            return base_url
        except:
            return ""
    
    def get_domain(self, url):
        try: 
            parsed_url = urlparse(url)        
            domain_parts = parsed_url.netloc.split('.')
            domain = '.'.join(domain_parts[-2:]) if len(domain_parts) > 1 else parsed_url.netloc

            return domain
            
        except:
            return ""

    def generate_unique_key_for_url(self, url):
        # Create a SHA-256 hash object
        hash_object = hashlib.sha256()
        
        # Encode the URL to bytes and update the hash object
        hash_object.update(url.encode('utf-8'))
        
        # Get the hexadecimal representation of the hash
        unique_key = hash_object.hexdigest()
        
        return unique_key
    
    # Enable override of default values for configuration options that are set in __init__
    def optional_config(self, log_folder=None, llm_model=None, llm_base_url=None, llm_model_api_key=None, embeddings_model=None, embeddings_base_url=None, embeddings_model_api_key=None, google_api_key=None, google_general_cx=None):
        if log_folder:
            self.log_folder = log_folder
        if llm_model:
            self.llm_model = llm_model
        if llm_base_url:
            self.llm_base_url = llm_base_url
        if llm_model_api_key:
            self.llm_model_api_key = llm_model_api_key
        if embeddings_model:
            self.embeddings_model = embeddings_model
        if embeddings_base_url:
            self.embeddings_base_url = embeddings_base_url
        if embeddings_model_api_key:
            self.embeddings_model_api_key = embeddings_model_api_key
        if google_api_key:
            self.google_api_key = google_api_key
        if google_general_cx:
            self.google_general_cx = google_general_cx
    
    async def async_process_prospect(self, propsect_data):
        def extract_N_urls_from_markdown(markdown, N=5):
            # Split the markdown into lines
            lines = markdown.split('\n')
            
            # Find lines that start with '### '
            h3_lines = [line for line in lines if line.startswith('### ')]
            
            # Regular expression to extract URLs from markdown links
            url_pattern = re.compile(r'\(https*://[^\s\)]+')
            
            # List to store the extracted URLs
            urls = []
            urls.append({"Type":"Markdown", "all-google-results": markdown})
            
            # Extract URLs from the first 5 H3 lines
            for line in h3_lines[:N]:
                # Find all URLs in the line
                found_urls = url_pattern.findall(line)
                # If a URL is found, clean it and add to the list
                if found_urls:
                    # Remove the opening parenthesis from the URL
                    clean_url = found_urls[0][1:]
                    clean_dict = {"Type":"google", "Link": clean_url}
                    urls.append(clean_dict)
            
            return urls
        
        
        def scrape_google_web(search_query):
            try:
                def clean_search_string(search_query):
                    # Remove characters that are not suitable for a URL search query
                    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.~ ")
                    cleaned_string = ''.join(c for c in search_query if c in allowed_chars)
                    return cleaned_string
                
                def create_google_search_url(search_string):
                    # Clean the search string
                    cleaned_string = clean_search_string(search_string)
                    # Encode the search string for use in a URL
                    encoded_string = urllib.parse.quote_plus(cleaned_string)
                    # Construct the final Google search URL
                    google_search_url = f"https://www.google.com/search?q={encoded_string}"
                    return google_search_url
                
                url = create_google_search_url(search_query)
                
                response = requests.get(url)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract the HTML content of the body
                    body_html = soup.find('body')
                    if body_html:
                        body_html = str(body_html)
                        # Convert HTML to Markdown
                        h = html2text.HTML2Text()
                        # Configure options (optional)
                        h.ignore_links = False  # Ignore links 
                        h.ignore_images = True # Ignore images
                        h.body_width = 0  # Don't wrap lines

                        markdown_text = h.handle(body_html)
                        return markdown_text
                    else:
                        print("No body tag found.")
                else:
                    print(f"Failed to retrieve the page. Status code: {response.status_code}")
            except Exception as e:
                print(f"An error occurred: {e}")
        
        def search_google_api(query):
            # Uses the configured (non image) CSE to search for results. Returns page 1
            service = build("customsearch", "v1", developerKey=self.google_api_key)
            search_results = (service.cse().list(q=query,cx=f"{self.google_general_cx}",).execute())
            
            
            
            results = []
            for result in search_results.get('items', []):
                thumb_list = result.get('pagemap', {}).get('cse_thumbnail', [])
                image_list = result.get('pagemap', {}).get('cse_image', [])
                metatag_list = result.get('pagemap', {}).get('metatags', [])
                
                #Below is my view on prioritizing images and content
                primary_result_image = ""
                primary_site_image = ""
                for image in image_list:
                    if 'src' in image:
                        if self.is_valid_url(image.get('src', '')):
                            primary_result_image = image.get('src', '')
                            
                if primary_result_image == "":
                    for thumb in thumb_list:
                        if primary_result_image != "":
                            continue
                        else:
                            if 'src' in thumb:
                                if self.is_valid_url(thumb.get('src', '')):
                                    primary_result_image = thumb.get('src', '')
                                    
                
                if primary_result_image =="":
                    for meta in metatag_list:
                        if primary_result_image != "":
                            continue
                        else:
                            if 'og:image' in meta:
                                if self.is_valid_url(meta.get('og:image', '')):
                                    primary_result_image = meta.get('og:image', '')
                    
                if primary_site_image == "":
                    if result.get('link', '') != "":
                        base_url = self.get_base_url(result.get('link', ''))
                        if base_url != "":
                            primary_site_image = f"{base_url}/favicon.ico"
                    primary_site_image = f"https://www.google.com/s2/favicons?domain_url={self.get_domain(result.get('link', ''))}"
                    
                    if primary_site_image == "":                
                        for meta in metatag_list:
                            if primary_site_image != "":
                                continue
                            else:
                                if 'og:url' in meta:
                                    if self.is_valid_url(meta.get('og:url', '')):
                                        base_url = self.get_base_url(meta.get('og:url', ''))
                                        if base_url != "":
                                            primary_site_image = f"{base_url}/favicon.ico"
                
                
                result_dict = {
                    "Type" : "google",
                    "Query" : query,
                    "Site" : base_url,
                    "Summary" : result.get('htmlSnippet', result.get('snippet', '')),
                    "Page_Content": "",
                    "Link" : result.get('link', ''),
                    "Title": result.get('title', ''),
                    "primary_result_image" : primary_result_image,
                    "primary_site_image" : primary_site_image
                }
                
                results.append(result_dict)
            
            return results
            
        def search_you_rag_content_api(query):
            ydc_list = []
            for doc in yr.get_relevant_documents(query):
                text_val = f"<strong>{doc.type}</strong>: {doc.page_content}"
                ydc_list.append(text_val)
            return ydc_list
        
        #! Step 1 in pipeline: Get the company and location #################################################################
        self.company = propsect_data.get('Legal_Name''')
        self.location = f"{propsect_data.get('Main_Office_City', '')}, {propsect_data.get('Main_Office_State', '')}"
        self.CRD = propsect_data.get('Organization_CRD', '')
        
        #! Step 2 in pipeline: Get all relevant search results #################################################################
        search_results = []
        for title in self.titles_list:
            
            search_query = f'person {title} at {self.company} in {self.location}?'
            
            #?---> Note: FREE SCRAPING (COSTS NO MONEY) (could be blocked by google)
            google_web_scrape_results = scrape_google_web(search_query)
            url_list = extract_N_urls_from_markdown(google_web_scrape_results)
            search_results.extend(url_list)
            

            #?---> Note: THESE TWO LINES OF CODE !WORK! (THEY JUST COST MONEY)
            # google_results = search_google_api(search_query)
            # search_results.extend(google_results)
            
            print(f"Successfully got google search results for query '{search_query}'")
            
            you_results = search_you_rag_content_api(search_query)
            search_results.extend(you_results)
            print(f"Successfully got you.com results for query '{search_query}'")
            
            with open(f"{self.CRD}{title}search_results.json", "w") as f:
                f.write(json.dumps(search_results, indent=4))
        
        #! Step 3 in pipeline: Scrape all search results #################################################################
        async def async_scrape_single_url(url):
            def extract_text_from_html(html_body):
                soup = BeautifulSoup(html_body, 'html.parser')
                return soup.get_text(separator=' ', strip=True)

            def is_a_valid_url(may_be_a_url):
                try:
                    result = urlparse(may_be_a_url)
                    return all([result.scheme, result.netloc])
                except ValueError:
                    return False
            
            if url == "" or not is_a_valid_url(url):
                return "Invalid or missing URL"
                
            
            else:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    try:
                        await page.goto(url)
                        await page.wait_for_selector('body')
                        body = await page.content()
                        body_text = extract_text_from_html(body)
                        
                        return body_text
                    
                    except Exception as e:
                        error_message = f"Error getting full webpage for {url}: {str(e)}"
                        return error_message
                    
                    finally:
                        await browser.close()
        
        search_results_for_llm = []
        for result in search_results:            
            if isinstance(result, dict):
                type = result.get('Type', '')   
                if type == 'google':
                    url = result.get('Link', '')
                    
                    # Check if the URL has already been scraped
                    url_key = self.generate_unique_key_for_url(url)
                    if url_key in self.scrape_session_history:
                        body_text = self.scrape_session_history[url_key]
                    else:
                        # Scrape the URL and store the result
                        body_text = await async_scrape_single_url(url)
                        
                        # Store the result in the session history
                        self.scrape_session_history[url_key] = body_text
                    
                    result['Page_Content'] = body_text
                    search_results_for_llm.append(result)
                    print(f"Successfully scraped {url}")
                    
                    
        
        #! Step 4 in pipeline: prepare embeddings #################################################################
        def prepare_text(data):
            
            # Flatten the JSON data into a single string
            text = json.dumps(data, ensure_ascii=False)
            
            # Normalize whitespace and clean up text
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Split text into chunks by sentences, respecting a maximum chunk size
            sentences = re.split(r'(?<=[.!?]) +', text)  # split on spaces following sentence-ending punctuation
            chunks = []
            current_chunk = ""
            for sentence in sentences:
                
                # Check if the current sentence plus the current chunk exceeds the limit
                if len(current_chunk) + len(sentence) + 1 < 1000:  # +1 for the space
                    current_chunk += (sentence + " ").strip()
                else:
                    # When the chunk exceeds 1000 characters, store it and start a new one
                    chunks.append(current_chunk)
                    current_chunk = sentence + " "
            if current_chunk:  # Don't forget the last chunk!
                chunks.append(current_chunk)
            
            text_to_embed_list = []
            for chunk in chunks:
                # Write each chunk to its own line
                text_to_embed_list.append(chunk.strip() + "\n")  # Two newlines to separate chunks
            
            return text_to_embed_list
        
        #! Step 5 in pipeline: organize everything into a package #################################################################
        package = {}
        package['Prospect']= propsect_data
        package['Search_Results'] = search_results_for_llm
        package['Text_To_Embed'] = prepare_text(search_results_for_llm)
        
        #! Step 6 in pipeline: get the embeddings #################################################################
        # Parse command-line arguments
        parser = argparse.ArgumentParser(description="Ollama Chat")
        parser.add_argument("--model", default=self.llm_model, help="Ollama model to use (default: llama3)")
        args = parser.parse_args()

        # Configuration for the Ollama API client
        client = OpenAI(
            base_url=self.llm_base_url,
            api_key=self.llm_model_api_key
        )

        # Generate embeddings for the vault content using Ollama
        vault_embeddings = []
        for content in package['Text_To_Embed']:
            response = ollama.embeddings(model=self.embeddings_model, prompt=content)
            vault_embeddings.append(response["embedding"])

        # Convert to tensor and print embeddings
        vault_embeddings_tensor = torch.tensor(vault_embeddings) 
        print(f"Successfully got embeddings for the vault content for {self.company}.")
        print("Embeddings for each line in the vault:")
        print(vault_embeddings_tensor)
        
        
        #! Step 7 in pipeline: get the prompt, get relevant embeddings and ask Ollama #################################################################
        
        def get_relevant_context(rewritten_input, vault_embeddings, vault_content, top_k=3):
            if vault_embeddings.nelement() == 0:  # Check if the tensor has any elements
                return []
            # Encode the rewritten input
            input_embedding = ollama.embeddings(model='mxbai-embed-large', prompt=rewritten_input)["embedding"]
            
            # Compute cosine similarity between the input and vault embeddings
            cos_scores = torch.cosine_similarity(torch.tensor(input_embedding).unsqueeze(0), vault_embeddings)
            
            # Adjust top_k if it's greater than the number of available scores
            top_k = min(top_k, len(cos_scores))
            
            # Sort the scores and get the top-k indices
            top_indices = torch.topk(cos_scores, k=top_k)[1].tolist()
            
            # Get the corresponding context from the vault
            relevant_context = [vault_content[idx].strip() for idx in top_indices]
            
            return relevant_context

           #! Step 7 in pipeline: get the prompt         
        
        # Function to interact with the Ollama model
        def ollama_chat(user_input, system_message, vault_embeddings, vault_content, ollama_model, conversation_history):
           
            # Get relevant context from the vault
            relevant_context = get_relevant_context(user_input, vault_embeddings_tensor, vault_content, top_k=3)
            if relevant_context:
                # Convert list to a single string with newlines between items
                context_str = "\n".join(relevant_context)
                print("Context Pulled from Documents: \n\n" + CYAN + context_str + RESET_COLOR)
            else:
                print(CYAN + "No relevant context found." + RESET_COLOR)
            
            # Prepare the user's input by concatenating it with the relevant context
            user_input_with_context = user_input
            if relevant_context:
                user_input_with_context = context_str + "\n\n" + user_input
            
            # Append the user's input to the conversation history
            conversation_history.append({"role": "user", "content": user_input_with_context})
            
            # Create a message history including the system message and the conversation history
            messages = [
                {"role": "system", "content": system_message},
                *conversation_history
            ]
            
            
            # Send the completion request to the Ollama model
            response = client.chat.completions.create(
                model=self.llm_model,
                messages=messages
            )
            
            # Append the model's response to the conversation history
            conversation_history.append({"role": "assistant", "content": response.choices[0].message.content})
            
            # Return the content of the response from the model
            return response.choices[0].message.content
            
        def get_prompt(PersonTitle, Company):
            prompts = {"GetInfo": ''' {

                    "Instructions": [
                        "Below is an Example_JSON_Data_Record for a contact at a wealth management firm. Use the Example_JSON_Data_Record as a guide to populate the Empty_JSON_Data_Template with information about the person holding the RoleTitle specified in the Empty_JSON_Data_Template.",
                        "Use only the information provided with this prompt. Do not use any external sources. If you are not able to populate a value, leave it as an empty string.",
                        "Return only the Empty_JSON_Data_Template in your response. Do not return any other commentary or text. Your response is being systematically integrated and the assumption is that the Empty_JSON_Data_Template is the only output of your code.",
                        "Your response must be in valid JSON format beginning with: {\"Contact_JSON_Data\": {<The template you populate>} }"
                    ],
                    "Example_and_Template": {
                        "Example_JSON_Data_Record": {
                            "RoleTitle": "Chief Investment Officer (CIO)"
                            "PersonName": "John Doe",
                            "Company": "XYZ Wealth Management",
                            "Email": "John@xyzwealth.com",
                            "Phone": "555-555-5555",
                            "LinkedIn": "https://www.linkedin.com/in/johndoe",
                            "Background": "John Doe is the Chief Investment Officer at XYZ Wealth Management. He has over 20 years of experience in the financial services industry and specializes in investment management and portfolio construction. John holds a CFA designation and is a graduate of the University of ABC with a degree in Finance. He is passionate about helping clients achieve their financial goals and is committed to providing personalized investment solutions tailored to their needs.",
                            "PhotoURLs": ["https://www.xyzwealth.com/johndoe.jpg", "https://www.xyzwealth.com/johndoe2.jpg"],
                            "Location": "New York, NY",
                            "Interests": ["Cars", "Golf", "Travel"],
                            "OtherInfo": ["John is an avid golfer and enjoys spending time with his family and friends.", "He is also a car enthusiast and loves to travel to new destinations."]
                        },
                        
                        "Empty_JSON_Data_Template": {
                            "RoleTitle": " ''' + PersonTitle + ''' ",
                            "PersonName": "",
                            "Company": " ''' + Company + ''' ",
                            "Email": "",
                            "Phone": "",
                            "LinkedIn": "",
                            "Background": "",
                            "PhotoURLs": ["", ""],
                            "Location": "",
                            "Interests": ["", "", ""],
                            "OtherInfo": ["", "", ""]
                        }
                    }
                    }

                    Critical reminder: "Your response must be in valid JSON format beginning with: 
                    {
                        \"Contact_JSON_Data\": {<The populated template>}
                    }'''
                    
            }
            return prompts


            # @st.cache
        
        # ANSI escape codes for colors
        PINK = '\033[95m'
        CYAN = '\033[96m'
        YELLOW = '\033[93m'
        NEON_GREEN = '\033[92m'
        RESET_COLOR = '\033[0m'
        
        # Conversation loop
        conversation_history = []
        system_message = "You are a helpful assistant that is an expert at extracting the most useful information from a given text."

        key_contacts  = []
        for title in self.titles_list:
            user_input = get_prompts(title, self.company)
            response = ollama_chat(user_input, system_message, vault_embeddings_tensor, package['Text_To_Embed'], args.model, conversation_history)
            print(NEON_GREEN + "Response: \n\n" + response + RESET_COLOR)
            key_contacts.append(response)
        
        current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")    
        package['Prospect'][key_contacts] = json.dumps(key_contacts)
        package['Prospect']['pipeline_version'] = "1"
        package['Prospect']['pipeline_as_of'] = current_date_time
        
        #! Step 8 in pipeline: return the package
        return package['Prospect']
            
@app.route('/prospectpipeline', methods=['POST'])
def process_pipeline_all_prospects():
    
    storage = _class_storage.az_storage()
    prospect_list = asyncio.run(storage.get_all_prospects())
    print(f"Successfully got prospect list with count '{len(prospect_list)}'")
    
    pipeline = prospect_data_pipeline()
    
    for prospect in prospect_list:
        FIXME = pipeline.process_prospect_main(prospect)
        
        
        


##############################################
####    Audio Transcription Functions     ####
##############################################

 
is_finals = queue.Queue()
stop_event = threading.Event()

asyncio.run(storage.create_parameter("StartStopButton", "Start Meeting"))

#Make sure there is a parameter table to store state
asyncio.run(storage.create_table_safely(storage.parameter_table_name))

#Set default state parameters
for key in state_parameters.keys():
    asyncio.run(storage.create_parameter(key, state_parameters[key]["Default"]))


def capture_audio(device_index, channels, q):
    command = [
        'ffmpeg',
        '-f', 'avfoundation',  # Use avfoundation for macOS
        '-i', f':{1}',
        '-ac', str(channels),
        '-f', 'wav',
        'pipe:1'
    ]
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    while not stop_event.is_set():
        data = proc.stdout.read(4096)
        if not data:
            if proc.poll() is not None:
                break
            else:
                continue
        q.put(data)

    # Capture stderr to log errors
    stderr_output, _ = proc.communicate()
    print(f"ffmpeg stderr: {stderr_output.decode('utf-8')}")

# Global variable to control the loop
keep_running = True

@app.route('/startaudiorec', methods=['GET'])
def startaudiorec():
    global keep_running
    keep_running = True

    # Set the button to stop the meeting
    asyncio.run(storage.create_parameter("StartStopButton", "Starting ..."))
    
    # Queue to hold audio data
    audio_queue = queue.Queue()

    def on_open(ws):
        print("WebSocket connection established.")
        def keep_alive():
            while keep_running:
                keep_alive_msg = json.dumps({"type": "KeepAlive"})
                ws.send(keep_alive_msg)
                print("Sent KeepAlive message")
                time.sleep(7)  # Send every 7 seconds
        keep_alive_thread = threading.Thread(target=keep_alive)
        keep_alive_thread.daemon = True
        keep_alive_thread.start()

    def store_result(result):
        log_it(f"Deepgram Result: {result}")
        
        transcription_dict = result  # Directly use the result as it's already a dictionary
        if transcription_dict.get('is_final', False):
            transcription_dict["Transcript"] = ' '.join(list(is_finals.queue))
            is_finals.queue.clear()
        transcription_dict["PartitionKey"] = transcription_dict['metadata']['request_id']
        #create a unique datetime string
        unique_time_in_ms_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        row_key = f"{unique_time_in_ms_string}--{uuid.uuid4()}"
        transcription_dict["RowKey"] = row_key
        
        flat_transcription_dict = flatten_dict(transcription_dict)
        asyncio.run(storage.add_update_or_delete_some_entities(table_name="Transcriptions", entities_list=[flat_transcription_dict], instruction_type="UPSERT_MERGE", attempt=1))

    def on_message(ws, message):
        global is_finals
        result = json.loads(message)
        try:
            sentence = result['channel']['alternatives'][0]['transcript']
        except (IndexError, KeyError):
            sentence = ""

        if sentence is None or sentence == "":
            return 
        else:
            print(f"Transcription: {sentence}")

        if result.get('is_final'):
            is_finals.put(sentence)
            store_result(result)

            if result.get('speech_final'):
                utterance = ' '.join(list(is_finals.queue))
                is_finals.queue.clear()

    def on_metadata(ws, metadata):
        print(f"Deepgram Metadata: {metadata}")

    def on_close(ws, close_status_code, close_msg):
        asyncio.run(storage.create_parameter("DeepgramComnection", state_parameters["DeepgramComnection"]["Closed"]))
        print(f"Deepgram Connection Closed")

    def on_error(ws, error):
        asyncio.run(storage.create_parameter("DeepgramComnection", state_parameters["DeepgramComnection"]["Error"]))
        asyncio.run(storage.create_parameter("DeepgramErrorMessage", f"{error}"))
        print(f"Deepgram Handled Error: {error}")

    def on_unhandled(ws, unhandled):
        asyncio.run(storage.create_parameter("DeepgramComnection", state_parameters["DeepgramErrorMessage"]["Unhandled"]))
        asyncio.run(storage.create_parameter("DeepgramErrorMessage", f"{unhandled}"))
        print(f"Deepgram Unhandled Websocket Message: {unhandled}")

    # Prepare query parameters for WebSocket URL
    options = {
        "model": "nova-2",
        "language": "en-US",
        "encoding": "linear16",
        "channels": 1,
        "sample_rate": 16000,
        "multichannel": "true",
        "endpointing": 300,
        "interim_results": "true",
        "utterance_end_ms": "1000",
        "vad_events": "true",
        "punctuate": "true",
        "smart_format": "true",
        "diarize": "true",
        "no_delay": "true"
    }
    
    # Convert options dictionary to query string
    options_query = '&'.join([f"{key}={value}" for key, value in options.items()])

    # Connect to Deepgram WebSocket API with options
    ws_url = f"wss://api.deepgram.com/v1/listen?{options_query}"
    headers = {"Authorization": f"Token {API_KEY}"}
    ws = websocket.WebSocketApp(ws_url,
                                on_open=on_open,
                                on_message=on_message,
                                on_close=on_close,
                                on_error=on_error,
                                header=headers)

    def send_audio(ws):
        while keep_running:
            try:
                if not audio_queue.empty():
                    data = audio_queue.get_nowait()
                    # print(f"Sending audio data: {data[:20]}...")  # Print first few bytes for debug
                    ws.send(data, websocket.ABNF.OPCODE_BINARY)
            except Exception as e:
                print(f"Error sending audio data: {e}")

    audio_thread = threading.Thread(target=send_audio, args=(ws,))
    audio_thread.daemon = True
    audio_thread.start()

    def run_ws():
        ws.run_forever()
    
    ws_thread = threading.Thread(target=run_ws)
    ws_thread.daemon = True
    ws_thread.start()
    
    # Start thread to capture audio from the microphone (MacBook Pro Microphone)
    mic_thread = threading.Thread(target=capture_audio, args=(0, 1, audio_queue))
    mic_thread.daemon = True
    mic_thread.start()

    asyncio.run(storage.create_parameter("StartStopButton", "Stop Meeting"))
    
    while keep_running:
        pass
    
    stop_event.set()

    # Wait for the threads to finish
    mic_thread.join()
    audio_thread.join()
    ws_thread.join()

    # Indicate that we've finished
    ws.close()

    return jsonify({"status": "Transcription Complete"})

@app.route('/stopaudiorec', methods=['GET'])
def stopaudiorec():
    global keep_running
    # Set the stop event to stop the threads
    keep_running = False
    stop_event.set()
    
    #Sets the button value to "Start Meeting" <Read as opposite of meaning>
    asyncio.run(storage.create_parameter("StartStopButton", "Start Meeting"))
    
    # Return a response indicating the recording has stopped
    return jsonify({"status": "Recording Stopped"})





#########################################
####    NASDAQ DOWNLOAD FUNCTIONS    ####
#########################################

async def download_file(session, url, destination):
    """
    Asynchronous function to download a file from a URL.
    """
    start_time = time.time()
    log_it(f"Starting download of {destination} at {start_time}")
    async with session.get(url) as response:
        # Ensure the response is successful
        response.raise_for_status()
        
        # Write the content to a destination file
        with open(destination, 'wb') as f:
            while True:
                chunk = await response.content.read(1024)  # Read chunks of 1KB
                if not chunk:
                    break
                f.write(chunk)
        # if the file is a zip file, extract it
        if destination.endswith('.zip'):
            with zipfile.ZipFile(destination, 'r') as zip_ref:
                filenames = zip_ref.extractall(data_directory)
            os.remove(destination)
        log_it(f"Completed download of {destination} in {time.time() - start_time} seconds")

async def dowload_list_of_files_async(download_status):
    
    waiting_on = []
    download_next_list = []
    # Create a session and download files concurrently
    
    async with aiohttp.ClientSession() as session:

        for file in download_status:
            if 'downloaded' not in file or 'file.status' not in file:
                continue
            if file["downloaded"] == 0 and file['file.status'] == "fresh":
                download_next_list.append(download_file(session, file["file.link"], f"{data_directory}/{file['name']}.zip"))
                file["downloaded"] == 1
            elif file["downloaded"] == 1:
                continue
            else:
                waiting_on.append(file)
                
        await asyncio.gather(*download_next_list)
        
        return download_status, waiting_on

@app.route('/downloadnasdaq', methods=['POST'])
def download_nasdaq():


    nasdaq_tables = ['SF1', 'SFP', 'DAILY', 'TICKERS', 'INDICATORS', 'METRICS', 'ACTIONS', 'SP500', 'EVENTS', 
                    'SF3', 'SF3A', 'SF3B', 'SEP']
    log_it("Beginning download of NASDAQ files")
    
    log_it("Getting status of NASDAQ files")
    download_list = []
    
    def create_download_item(table):
        url = f"https://data.nasdaq.com/api/v3/datatables/SHARADAR/{table}.csv?qopts.export=true&api_key=6X82a45M1zJPu2ci4TJP"
        response = requests.get(url)
        status_dict = {}
        status_dict["name"] = table
        status_dict["status"] = response.status_code
        status_dict["link"] = url
        status_dict["downloaded"] = 0
        if response.status_code == 200:
            reader = csv.DictReader(StringIO(response.text))
            for row in reader:
                for column_name in reader.fieldnames:
                    status_dict[column_name] = row[column_name]
            return status_dict
        else:
            status_dict["status"] = "Failed"
            status_dict["error"] = response.text
            log_it(Exception(f"ERROR ... Failed to get a download link for table {table}: {response.text}"))
            return None
    
    
    for table in nasdaq_tables: 
        item = create_download_item(table)
        if item is not None:
            download_list.append(item)
    
    log_it("Beginning download of files that are ready")

    download_list, waiting_on = asyncio.run(dowload_list_of_files_async(download_list))
    while len(waiting_on) > 0:
        download_list, waiting_on = asyncio.run(dowload_list_of_files_async(download_list))
        log_it(f"Still waiting on: waiting_on {waiting_on}")
        time.sleep(5)






#########################################
####      OFFICE 365  FUNCTIONS      ####
#########################################

CLIENT_ID = os.environ.get('AZURE_APP_CLIENT_ID', 'No Key or Connection String found')
TENANT_ID = os.environ.get('AZURE_APP_TENANT_ID', 'No Key or Connection String found') 

# OAuth Endpoints
AUTH_ENDPOINT = f'https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize'
TOKEN_ENDPOINT = f'https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token'

app.secret_key = os.urandom(24)

@app.route('/')
def homepage():
        
    def generate_code_verifier():
        return base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('utf-8')

    def generate_code_challenge(code_verifier):
        code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(code_challenge).rstrip(b'=').decode('utf-8')
    
    
    
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    session['code_verifier'] = code_verifier
    
    auth_params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': url_for('auth_redirect', _external=True),
        'scope': 'openid profile User.Read Mail.Read',
        'response_mode': 'query',
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    auth_url = f'{AUTH_ENDPOINT}?{urlencode(auth_params)}'
    return redirect(auth_url)

@app.route('/redirect')
def auth_redirect():
    # Microsoft Graph Endpoint
    GRAPH_ENDPOINT = 'https://graph.microsoft.com/v1.0'

    code = request.args.get('code')
    if not code:
        return "No code provided"
    
    code_verifier = session.pop('code_verifier', None)
    if not code_verifier:
        return "Missing code verifier"
    
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': url_for('auth_redirect', _external=True),
        'client_id': CLIENT_ID,
        'code_verifier': code_verifier
    }

    token_response = requests.post(TOKEN_ENDPOINT, data=token_data)
    token_json = token_response.json()

    if 'access_token' in token_json:
        access_token = token_json['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        with open('office_token.json', 'w') as f:
            f.write(json.dumps(token_json))

        response = requests.get(f'{GRAPH_ENDPOINT}/me/messages', headers=headers)
        if response.status_code == 200:
            messages = response.json()
            return json.dumps(messages, indent=2)
        else:
            return f"Failed to fetch messages: {response.status_code} {response.text}"
    else:
        return f"Failed to obtain access token: {token_response.status_code} {token_json}"


if __name__ == "__main__":
    # Set the process title
    process_pipeline_all_prospects()
    # download_nasdaq()
    setproctitle.setproctitle("MyTechFlaskBackground")    
    app.run(port=5005, debug=True)









#! Code not in use
    # is_finals = []
    # stop_event = threading.Event()


    # @app.route('/startaudiorec', methods=['GET'])
    # def startaudiorec():
        
    #     # Set the button to stop the meeting
    #     asyncio.run(storage.create_parameter("StartStopButton", "Starting ..."))
        
    #     # Queues to hold audio data
    #     mic_queue = queue.Queue()
    #     teams_queue = queue.Queue()
        
    #     # Start the Deepgram connection
    #     deepgram: DeepgramClient = DeepgramClient()
    #     dg_connection = deepgram.listen.live.v("1")

    #     def capture_audio(device_index, channels, q):
    #         command = [
    #             'ffmpeg',
    #             '-f', 'dshow',
    #             '-i', f'audio={device_index}',
    #             '-ac', str(channels),
    #             '-f', 'wav',
    #             'pipe:1'
    #         ]
    #         proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
    #         while True:
    #             data = proc.stdout.read(4096)
    #             if not data:
    #                 break
    #             q.put(data)

    #     def on_open(self, open, **kwargs):
    #         asyncio.run(storage.create_parameter("DeepgramComnection", state_parameters["DeepgramComnection"]["Open"]))

    #     def store_result(result):
            
    #         log_it(f"Deepgram Result: {result}")
            
    #         transcription_dict = {}
    #         transcription_dict = result.to_dict()
    #         transcription_dict["PartitionKey"] = transcription_dict['metadata']['request_id']
            
    #         #Create a string that represents the current time in milliseconds in the format YYYY.DD.MM.HH.mm.SS.mmm
    #         unique_time_in_ms_string = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M.%S.%f")
    #         row_key = f"{unique_time_in_ms_string}--{uuid.uuid4()}"
    #         transcription_dict["RowKey"] = row_key
            
    #         # Flatten the dictionary so it can be stored in Azure Table Storage
    #         flat_transcription_dict = flatten_dict(transcription_dict)
            
    #         # Store the transcription in Azure Table Storage
    #         asyncio.run(storage.add_update_or_delete_some_entities(table_name ="Transcriptions", entities_list=[flat_transcription_dict], instruction_type="UPSERT_MERGE", attempt=1))

    #     def on_message(self, result, **kwargs):
    #         global is_finals
    #         # print(f"Deepgram Message: {result}")
    #         sentence = result.channel.alternatives[0].transcript
            
    #         if sentence != "": 
    #             print(f"{sentence}")
    #             # print(f"result")
    #         else:
    #             pass
    #             # print("Empty result")
            
    #         if result.is_final:
    #             # We need to collect these and concatenate them together when we get a speech_final=true
    #             # See docs: https://developers.deepgram.com/docs/understand-endpointing-interim-results
    #             is_finals.append(sentence)
    #             store_result(result)

    #             # Speech Final means we have detected sufficent silence to consider this end of speech
    #             # Speech final is the lowest latency result as it triggers as soon an the endpointing value has triggered
    #             if result.speech_final:
    #                 utterance = ' '.join(is_finals)
    #                 # print(f"Speech Final: {utterance}")
    #                 with open('meeting.txt', 'a') as f:
    #                     f.write(utterance)
    #                 is_finals = []
    #             else:
    #                 # These are useful if you need real time captioning and update what the Interim Results produced
    #                 pass
    #         else:
    #             pass
    #             # These are useful if you need real time captioning of what is being spoken
    #             # print(f"Interim Results: {sentence}")

    #     def on_metadata(self, metadata, **kwargs):
    #         print(f"Deepgram Metadata: {metadata}")

    #     def on_speech_started(self, speech_started, **kwargs):
    #         pass
    #         # print(f"Deepgram Speech Started")

    #     def on_utterance_end(self, utterance_end, **kwargs):
    #         global is_finals
    #         if len(is_finals) > 0:
    #             utterance = ' '.join(is_finals)
    #             # print(f"Deepgram Utterance End: {utterance}")
    #             is_finals = []

    #     def on_close(self, close, **kwargs):
    #         asyncio.run(storage.create_parameter("DeepgramComnection", state_parameters["DeepgramComnection"]["Closed"]))
    #         print(f"Deepgram Connection Closed")

    #     def on_error(self, error, **kwargs):
    #         asyncio.run(storage.create_parameter("DeepgramComnection", state_parameters["DeepgramErrorMessage"]["Error"]))
    #         asyncio.run(storage.create_parameter("DeepgramErrorMessage", f"{error}"))
    #         print(f"Deepgram Handled Error: {error}")

    #     def on_unhandled(self, unhandled, **kwargs):
    #             asyncio.run(storage.create_parameter("DeepgramComnection", state_parameters["DeepgramErrorMessage"]["Unhandled"]))
    #             asyncio.run(storage.create_parameter("DeepgramErrorMessage", f"{unhandled}"))
    #             print(f"Deepgram Unhandled Websocket Message: {unhandled}")

    #     dg_connection.on(LiveTranscriptionEvents.Open, on_open)
    #     dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    #     dg_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
    #     dg_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
    #     dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
    #     dg_connection.on(LiveTranscriptionEvents.Close, on_close)
    #     dg_connection.on(LiveTranscriptionEvents.Error, on_error)
    #     dg_connection.on(LiveTranscriptionEvents.Unhandled, on_unhandled)

        
    #     """            
    #     Please see the documentation for more information on each option:
    #     https://developers.deepgram.com/reference/streaming
    #     """
    #     options: LiveOptions = LiveOptions(
    #             model= "nova-2",
    #             language= "en-US",
    #             # alternatives=,
    #             # callback=,
    #             # callback_method=,
    #             # version=,
                
    #             encoding="linear16",
    #             channels=1,
    #             sample_rate=16000,
    #             multichannel=False ,
                
    #             endpointing=300 ,           # Time in milliseconds of silence to wait for before finalizing speech
                
    #             interim_results=True ,      # Return interim results
    #             utterance_end_ms="1000",    # To get UtteranceEnd, these must be set.
    #             vad_events=True ,           # To get UtteranceEnd, these must be set.
                
    #             punctuate=True ,
    #             smart_format= True,         # Apply smart formatting to the output
    #             diarize=True ,              # Identify the speaker
    #             # diarize_version=,
    #             # extra=,
    #             # filler_words=,
    #             # keywords=,
    #             # profanity_filter=,
    #             # redact=,
    #             # replace=,
    #             # numerals=,
    #             # search=,
    #             # tag=,
    #             # tier=,
    #     )
            
    #     addons = {
    #         # Prevent waiting for additional numbers
    #         "no_delay": "true"
    #     }

    #     if dg_connection.start(options, addons=addons) is False:
    #         print("Failed to connect to Deepgram")
    #         return

        
    #     # Start threads to capture audio from the microphone and Microsoft Teams
    #     threading.Thread(target=capture_audio, args=(1, 1, mic_queue)).start()
    #     threading.Thread(target=capture_audio, args=(2, 1, teams_queue)).start()

        
    #     # Open a microphone stream on the default input device
    #     microphone = Microphone(dg_connection.send)

    #     # start microphone
    #     microphone.start()
        
    #     with open('stopfile.txt', 'w') as f:
    #         f.write("Meeting Started")
        
    #     # Set the button to stop the meeting
    #     asyncio.run(storage.create_parameter("StartStopButton", "Stop Meeting"))
        
        
    #     def keep_going():
    #         with open('stopfile.txt', 'r') as f:
    #             return f.read() != "Stopping Meeting"
        
    #     while keep_going():
    #         pass
        
    #         # Wait for the microphone to close
    #     microphone.finish()

    #     # Indicate that we've finished
    #     dg_connection.finish()

    #     print("Finished")
    #     with open('stopfile.txt', 'w') as f:
    #         f.write("Start Meeting")
        
    #     asyncio.run(storage.create_parameter("StartStopButton", "Start Meeting"))


    #     return jsonify({"status": "Transcription Complete"})


    #         # print(f"Could not open socket: {e}")
    #         # return  jsonify({"status": "Transcription Failed"})








    # def capture_audio(device_index, channels, q):
    #     command = [
    #         'ffmpeg',
    #         '-f', 'dshow',
    #         '-i', f'audio={device_index}',
    #         '-ac', str(channels),
    #         '-f', 'wav',
    #         'pipe:1'
    #     ]
    #     proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
    #     while not stop_event.is_set():
    #         data = proc.stdout.read(4096)
    #         if not data:
    #             break
    #         q.put(data)

    # @app.route('/startaudiorec1', methods=['GET'])
    # def startaudiorec1():
        
    #     # Set the button to stop the meeting
    #     asyncio.run(storage.create_parameter("StartStopButton", "Starting ..."))
        
    #     # Queues to hold audio data
    #     mic_queue = queue.Queue()
    #     teams_queue = queue.Queue()

    #     def on_open(ws):
    #         print("WebSocket connection established.")
    #         def keep_alive():
    #             while not stop_event.is_set():
    #                 keep_alive_msg = json.dumps({"type": "KeepAlive"})
    #                 ws.send(keep_alive_msg)
    #                 print("Sent KeepAlive message")
    #                 time.sleep(7)  # Send every 7 seconds
    #         keep_alive_thread = threading.Thread(target=keep_alive)
    #         keep_alive_thread.daemon = True
    #         keep_alive_thread.start()

    #     def store_result(result):
    #         log_it(f"Deepgram Result: {result}")
            
    #         transcription_dict = result.to_dict()
    #         transcription_dict["PartitionKey"] = transcription_dict['metadata']['request_id']
    #         unique_time_in_ms_string = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M.%S.%f")
    #         row_key = f"{unique_time_in_ms_string}--{uuid.uuid4()}"
    #         transcription_dict["RowKey"] = row_key
            
    #         flat_transcription_dict = flatten_dict(transcription_dict)
    #         asyncio.run(storage.add_update_or_delete_some_entities(table_name="Transcriptions", entities_list=[flat_transcription_dict], instruction_type="UPSERT_MERGE", attempt=1))

    #     def on_message(ws, message):
    #         global is_finals
    #         result = json.loads(message)
    #         sentence = result['channel']['alternatives'][0]['transcript']
            
    #         if sentence:
    #             print(f"{sentence}")

    #         if result['is_final']:
    #             is_finals.put(sentence)
    #             store_result(result)

    #             if result['speech_final']:
    #                 utterance = ' '.join(list(is_finals.queue))
    #                 with open('meeting.txt', 'a') as f:
    #                     f.write(utterance)
    #                 is_finals.queue.clear()

    #     def on_metadata(ws, metadata):
    #         print(f"Deepgram Metadata: {metadata}")

    #     def on_close(ws, close_status_code, close_msg):
    #         asyncio.run(storage.create_parameter("DeepgramComnection", state_parameters["DeepgramComnection"]["Closed"]))
    #         print(f"Deepgram Connection Closed")

    #     def on_error(ws, error):
    #         asyncio.run(storage.create_parameter("DeepgramComnection", state_parameters["DeepgramErrorMessage"]["Error"]))
    #         asyncio.run(storage.create_parameter("DeepgramErrorMessage", f"{error}"))
    #         print(f"Deepgram Handled Error: {error}")

    #     def on_unhandled(ws, unhandled):
    #         asyncio.run(storage.create_parameter("DeepgramComnection", state_parameters["DeepgramErrorMessage"]["Unhandled"]))
    #         asyncio.run(storage.create_parameter("DeepgramErrorMessage", f"{unhandled}"))
    #         print(f"Deepgram Unhandled Websocket Message: {unhandled}")

    #     # Connect to Deepgram WebSocket API
    #     ws_url = "wss://api.deepgram.com/v1/listen"
    #     headers = {"Authorization": f"Token {API_KEY}"}
    #     ws = websocket.WebSocketApp(ws_url,
    #                                 on_open=on_open,
    #                                 on_message=on_message,
    #                                 on_close=on_close,
    #                                 on_error=on_error,
    #                                 header=headers)

    #     def send_audio(ws):
    #         while not stop_event.is_set():
    #             try:
    #                 if not mic_queue.empty():
    #                     data = mic_queue.get_nowait()
    #                     ws.send(data, websocket.ABNF.OPCODE_BINARY)
    #                 if not teams_queue.empty():
    #                     data = teams_queue.get_nowait()
    #                     ws.send(data, websocket.ABNF.OPCODE_BINARY)
    #             except Exception as e:
    #                 print(f"Error sending audio data: {e}")

    #     audio_thread = threading.Thread(target=send_audio, args=(ws,))
    #     audio_thread.daemon = True
    #     audio_thread.start()

    #     def run_ws():
    #         ws.run_forever()
        
    #     ws_thread = threading.Thread(target=run_ws)
    #     ws_thread.daemon = True
    #     ws_thread.start()

    #     options = LiveOptions(
    #         model="nova-2",
    #         language="en-US",
    #         encoding="linear16",
    #         channels=1,
    #         sample_rate=16000,
    #         multichannel=True,
    #         endpointing=300,
    #         interim_results=True,
    #         utterance_end_ms="1000",
    #         vad_events=True,
    #         punctuate=True,
    #         smart_format=True,
    #         diarize=True,
    #     )
            
    #     addons = {
    #         "no_delay": "true"
    #     }

    #     # This part is not used since we have direct WebSocket handling now
    #     # if dg_connection.start(options, addons=addons) is False:
    #     #     print("Failed to connect to Deepgram")
    #     #     return
        
    #     # Start threads to capture audio from the microphone and Microsoft Teams
    #     mic_thread = threading.Thread(target=capture_audio, args=(1, 1, mic_queue))
    #     mic_thread.daemon = True
    #     mic_thread.start()

    #     teams_thread = threading.Thread(target=capture_audio, args=(2, 1, teams_queue))
    #     teams_thread.daemon = True
    #     teams_thread.start()

    #     with open('stopfile.txt', 'w') as f:
    #         f.write("Meeting Started")
        
    #     asyncio.run(storage.create_parameter("StartStopButton", "Stop Meeting"))
        
    #     def keep_going():
    #         with open('stopfile.txt', 'r') as f:
    #             return f.read() != "Stopping Meeting"
        
    #     while keep_going():
    #         pass
        
    #     stop_event.set()

    #     # Wait for the threads to finish
    #     mic_thread.join()
    #     teams_thread.join()
    #     audio_thread.join()
    #     ws_thread.join()

    #     # Indicate that we've finished
    #     ws.close()

    #     print("Finished")
    #     with open('stopfile.txt', 'w') as f:
    #         f.write("Start Meeting")
        
    #     asyncio.run(storage.create_parameter("StartStopButton", "Start Meeting"))

    #     return jsonify({"status": "Transcription Complete"})






    # async def async_scrape_single_url_old(search_result):
    #     from pyppeteer import launch
        
    #     def extract_text_from_html(html_body):    
    #         soup = BeautifulSoup(html_body, 'html.parser')
    #         return soup.get_text(separator=' ', strip=True)
        
    #     def is_a_valid_url(may_be_a_url):
    #         try:
    #             result = urlparse(may_be_a_url)
    #             return all([result.scheme, result.netloc])
    #         except ValueError:
    #             return False  
        
    #     url = search_result.get('Link', '')
        
    #     if url == "" or not is_a_valid_url(url):
    #         search_result['Page_Content'] = "Invalid or missing URL"
    #         return search_result
        
    #     else:
    #         browser = None
            
    #         try:
    #             browser = await launch(headless=True)
    #             page = await browser.newPage()
    #             await page.goto(url)
    #             await page.waitForSelector('body')
    #             body = await page.content()
    #             body_text = extract_text_from_html(body)
    #             search_result['Page_Content'] = body_text
                
    #             return search_result
            
    #         except Exception as e:
                
    #             error_message = f"Error getting full webpage for {url}: {str(e)}"
    #             search_result['Page_Content'] = error_message
    #             return search_result
            
    #         finally:
    #             if browser:
    #                 await browser.close()   
        
            
        
    #     step1_submit = tc.form_submit_button(label="Submit", type="primary", on_click=create_search_query, use_container_width=True) 

    #     if step1_submit:
    #         st.session_state["MODE"] = 'EXECUTE_SEARCH'


    #     async def get_search_results_for_prospect(self, Company, Location):
            
    #         company_results = []
            
    #         for title in self.titles_list:
                
    #             search_query = f'person {title} at {Company} in {Location}?'
                
    #             google_results = await self.async_search_google_api(search_query)
                
    #             add_you_results = await self.async_search_you_rag_content_api(search_query)
                
    #             for rslt in add_you_results:
    #                 google_results.append(rslt)
                
    #             with open(f"{title}search_results.json", "w") as f:
    #                 f.write(json.dumps(google_results, indent=4))
                
    #             company_results.append(google_results)
            
    #         return company_results

    # pros = prospect_data_pipeline()
    
   