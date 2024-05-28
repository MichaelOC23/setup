from azure.data.tables import UpdateMode, TransactionOperation, TableEntity, TableTransactionError
from azure.data.tables.aio import TableClient, TableServiceClient

from datetime import date, datetime
from enum import NAMED_FLAGS, unique
import time
from cv2 import log
import torch
import ollama
import chromadb
import argparse
from openai import OpenAI, chat
import asyncio
import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
import json
import os
from googleapiclient.discovery import build
from urllib.parse import urlparse
import urllib.parse
import html2text
import requests
from bs4 import BeautifulSoup
import hashlib

from urllib.parse import urlencode

    
    
##############################################
######    PROSPECT DATA PIPELINE     #########
##############################################



class contact_generation_pipeline:
    def __init__(self):
        self.log_folder = "logs"
        if not os.path.exists(self.log_folder):
            os.makedirs(self.log_folder)
        
        
        #Contact-specific items
        self.SECOrgCRDNum = ""
        self.RegisteredEntity = ""
        self.CCOName = ""
        self.CCOEmail = ""
        self.Website = ""
        self.CCOEmailDomain = ""
        
        #Example of AI Pipeline for RBC for 
        self.LeadershipTitles = ["CEO"]
        self.LeadershipAreas = ["Wealth Management", "Digital Wealth "]
        self.Markets = ["USA", "Canada", "UK", "Europe", "Asia"]
        self.SeedNamesCommoon = ["Smith", "Johnson", "Williams", "Brown"] #"Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        self.leadership_references = ["Leadership", "Founders", "Executive Team", 
                                      "Management Team", "Board of Directors"]
        
        self.log_key = datetime.now().strftime("%Y%m%d%H%M%S")
        
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
    
    def create_email_extraction_prompt(self, name, email, domain, json_str=""):
        prompt = '''Given this text, what are the names and email addresses of the people with an email with ''' + f"{domain}" + "."
        prompt = prompt + ''' Your responses are being systematically integrated. Do not replay with any response other that the names of the people and their emails in this JSON format.  
                    Please extend the data below with the additional records and return the entire new JSON dataset with current and new records in your response.

                    ### JSON Dataset '''
        if json_str == "":
            json_str = json.dumps({ 
                                    "Emails":
                                    [{"Name": name, "Email": email}]
                                    }, indent=4)    
        prompt = prompt + json_str
                    
                    
        return prompt


#!################################################################
#! OLLAMA EMBEDDING FUNCTIONS ####################################
#!################################################################
    def chromadb_collection_exists(self, client, collection_name):
        collections = client.list_collections()
        for collection in collections:
            if collection.name == collection_name:
                return True
            else:
                return False
        
    
    def prepare_text_for_embedding(self, any_text_list_or_dict):
        
        if any_text_list_or_dict is None or any_text_list_or_dict == "":
            return []
        
        if isinstance(any_text_list_or_dict, str):
            any_text_list_or_dict = [any_text_list_or_dict]
        
        # Flatten the JSON data into a single string
        text = json.dumps(any_text_list_or_dict, ensure_ascii=False)
        
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

    def embed_text_chroma(self, documents, collection_name):
        client = chromadb.Client()
        if not self.chromadb_collection_exists(client, collection_name):
            collection = client.create_collection(name=collection_name)
        
        # store each document in a vector embedding database
        for i, d in enumerate(documents):
            response = ollama.embeddings(model="mxbai-embed-large", prompt=d)
            embedding = response["embedding"]
            collection.add(
                ids=[str(i)],
                embeddings=[embedding],
                documents=[d]
            )

    def get_relevant_embeddings(self, prompt, collection_name, n_results=10):
        client = chromadb.Client()
        collection = client.get_or_create_collection(name=collection_name)

        # generate an embedding for the prompt and retrieve the most relevant doc
        response = ollama.embeddings(
        prompt=prompt,
        model=self.embeddings_model
        )
        results = collection.query(
        query_embeddings=[response["embedding"]],
        n_results=n_results
        )
        data = results['documents'][0]
        return data

    def query_ollama_with_embedding(self, prompt, embeddings):

        output = ollama.generate(
            model="llama2",
            prompt=f"Using this data:\n {embeddings}. Respond to this prompt: \n{prompt}")
        
        return output['response']



           
    def log_it(self, message, color='black', data="", print_it=True):
        color_dict = {        
            "BLACK":"\033[0;30m",
            "RED":"\033[0;31m",
            "RED_U":"\033[4;31m",
            "RED_BLINK":"\033[5;31m",
            "GREEN":"\033[0;32m",
            "GREEN_BLINK":"\033[5;32m",
            "YELLOW":"\033[0;33m",
            "YELLOW_BOLD":"\033[1;33m",
            "PURPLE":"\033[1;34m",
            "PURPLE_U":"\033[4;34m",
            "PURPLE_BLINK":"\033[5;34m",
            "PINK":"\033[0;35m",
            "PINK_U":"\033[4;35m",
            "PINK_BLINK":"\033[5;35m",
            "LIGHTBLUE":"\033[0;36m",
            "LIGHTBLUE_BOLD":"\033[1;36m",
            "GRAY":"\033[0;37m",
            "ORANGE":"\033[1;91m",
            "BLUE":"\033[1;94m",
            "CYAN":"\033[1;96m",
            "WHITE":"\033[1;97m",
            "MAGENTA":"\033[1;95m",
            "BOLD":"\033[1m",
            "UNDERLINE":"\033[4m",
            "BLINK":"\033[5m",
            "NC":"\033[0m'"} # No Colo"}
                
        if color.upper() in color_dict:
            color_code = color_dict[color.upper()]
            terminal_message = f"{color_code}{message}{color_dict['NC']} \n {data}"
        
        def got_dict(input_value):
            if isinstance(input_value, dict):
                return True, input_value
            try:
                type_value = type(input_value)
                input_value = json.loads(input_value)
            except Exception as e:
                return False, f"Type is: {type_value}.  Could not convert input to dictionary: {e}"
            return True, input_value
        
        is_dict, dict_value = got_dict(message)
        
        
        if is_dict:
            message = json.dumps(dict_value, indent=4)
        else:
            message = f"{message}"
            
        with open(os.path.join(self.log_folder, f"Contact_Gen_log_{self.log_key}.txt"), 'a') as f:
            f.write(message)
            print(terminal_message)
    
    def get_domain_from_email(self, email_address):
            try:
                return email_address.split('@')[1]
            except IndexError:
                return "Invalid email address"

    def get_url_domain(self, url):
        try: 
            parsed_url = urlparse(url)        
            domain_parts = parsed_url.netloc.split('.')
            domain = '.'.join(domain_parts[-2:]) if len(domain_parts) > 1 else parsed_url.netloc

            return domain
            
        except:
            return ""
    
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
    
    def generate_unique_key_for_url(self, url):
        # Create a SHA-256 hash object
        hash_object = hashlib.sha256()
        
        # Encode the URL to bytes and update the hash object
        hash_object.update(url.encode('utf-8'))
        
        # Get the hexadecimal representation of the hash
        unique_key = hash_object.hexdigest()
        
        return unique_key
     
    def extract_N_urls_from_markdown(self, markdown, N=5):
        # Split the markdown into lines
        lines = markdown.split('\n')
        
        # Find lines that start with '### '
        h3_lines = [line for line in lines if line.startswith('### ')]
        
        # Regular expression to match the URL
        pattern = r"/url\?q=(https?://[^\s&]+)"

        # Search for the pattern in the text
        

        urls = []
        urls_found = 0
        
        # Search for the URL
        for result in h3_lines:
            match = re.search(pattern, result)
            if match is not None and self.is_valid_url(match.group(1)):
                urls_found += 1
                urls.append(f"{match.group(1)}")
            if urls_found >= N:
                break
        
        return urls
    
    def get_markdown_from_google_search(self, search_query):
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
            
            time.sleep(1)
            
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
                    h.skip_internal_links = True  # Skip internal links
                    
                    # Configure options (optional)
                    h.ignore_links = False  # Ignore links 
                    h.ignore_images = True # Ignore images
                    h.body_width = 0  # Don't wrap lines

                    markdown_text = h.handle(body_html)
                    unique_key = self.generate_unique_key_for_url(url)
                    with open(f"/Users/michasmi/Downloads/{unique_key}test_markdown.md", "w") as f:
                        f.write(markdown_text)
                    return markdown_text
                else:
                    print("No body tag found.")
            else:
                print(f"Failed to retrieve the page. Status code: {response.status_code}")
        except Exception as e:
            print(f"An error occurred: {e}")

    async def async_scrape_single_url(self, url):
            def extract_text_from_html(html_body):
                soup = BeautifulSoup(html_body, 'html.parser')
                return soup.get_text(separator=' ', strip=True)

            def is_a_valid_url(may_be_a_url):
                try:
                    result = urlparse(may_be_a_url)
                    return all([result.scheme, result.netloc])
                except Exception as e:
                    self.log_it(f"Error: URL |{url}|is invalid: {str(e)}", color="RED")
                    return ""
            
            if url == "" or not is_a_valid_url(url):
                return ""
            
            unique_key = self.generate_unique_key_for_url(url)
            if os.path.exists(f"scrapes/{unique_key}_site_markdown.md"):
                with open(f"scrapes/{unique_key}_site_markdown.md", "r") as f:
                    return f.read()
            
            else:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    try:
                        await page.goto(url)
                        await page.wait_for_selector('body')
                        body = await page.content()
                        body_text = extract_text_from_html(body)
                        self.log_it(f"Successfully got full webpage for {url} with {len(body_text)} characters.")
                        
                        
                        with open(f"scrapes/{unique_key}_site_markdown.md", "w") as f:
                            f.write(body_text)
                            
                        return body_text
                    
                    except Exception as e:
                        error_message = f"Error getting full webpage for {url}: {str(e)}"
                        self.log_it(error_message, color="RED")
                        return error_message
                    
                    finally:
                        await browser.close()
    
    async def generate_contact_ollama_rag(self, contact_data):
        def step_0_setup(contact_data):
            self.SECOrgCRDNum = contact_data.get('SECOrgCRDNum')
            self.RegisteredEntity = contact_data.get('RegisteredEntity')
            self.CCOName = contact_data.get('CCOName')
            self.CCOEmail = contact_data.get('CCOEmail')
            self.CCOEmailDomain = self.get_domain_from_email(self.CCOEmail)
            self.Website = contact_data.get('Website')
            contact_data["EmailUrlList"] = []
            
        def step_1_search(contact_data, url_list):

            for title in self.LeadershipTitles:
                for market in self.Markets:
                    # Define the search query
                    search_query = f' {title} at {self.CCOEmailDomain} in {market}?'

                    #Search google, get results page in markdown
                    google_web_scrape_results = self.get_markdown_from_google_search(search_query)
                    
                    self.log_it(f"Searched for {search_query}", color="PINK")
                    
                    #Get the URLs from the markdown
                    contact_data["EmailUrlList"].extend(self.extract_N_urls_from_markdown(google_web_scrape_results, N=3))
                
            for leadership_reference in self.leadership_references: 
                # Define the search query
                search_query = f' {leadership_reference} at {self.CCOEmailDomain} in {market}?'

                #Search google, get results page in markdown
                google_web_scrape_results = self.get_markdown_from_google_search(search_query)
                
                self.log_it(f"Searched for {search_query}", color="PINK")
                
                #Get the URLs from the markdown
                contact_data["EmailUrlList"].extend(self.extract_N_urls_from_markdown(google_web_scrape_results, N=3))
            
            self.log_it(f"Got {len(contact_data['EmailUrlList'])} URLs for search query |{search_query}|", color="CYAN", data=f"{contact_data['EmailUrlList']}")
            
        def get_readable_response_format(field_name):
            json_dict ={
                self.SECOrgCRDNum: 
                    {f"{field_name}":  ""}
                    }
            return f"{json.dumps(json_dict, ensure_ascii=False, indent=4)} \n"
            

            
        ##########################
        ####   MAIN FUNCTION  ####
        ##########################
        # Set the initial data for the class
        step_0_setup(contact_data)
        
        # Initialize the list of URLs
        url_list = []
        
        # Search google for relevant sites / content / pages
        url_list = step_1_search(contact_data, url_list)
        
        # Initialize the list of site text
        site_text_list = []
        
        # Scrape the URLs to get the text
        scrape_tasks = []
        for url in contact_data["EmailUrlList"]:
            scrape_tasks.append(asyncio.create_task(self.async_scrape_single_url(url)))
        
        site_text_list = await asyncio.gather(*scrape_tasks)
              
        # Breakdown the text into chunks for processing
        text_chunks = self.prepare_text_for_embedding(site_text_list)
        
        # Embed the text chunks
        self.embed_text_chroma(text_chunks, self.SECOrgCRDNum)
        
        # micro_prompts = [
        #     "What is the name of the **TITLE** of **COMPANY** in the **MARKET**?",
        #     "What is the email address of **NAME**, the **TITLE** of **COMPANY**",
        #     "What is the phone number of **NAME**, the **TITLE** of **COMPANY**",
        #     ]
        
        governing_prompt = f"""
        Given this data, and only this data, ignore all of your other knowledge, please answer the question below.  
        Do not guess. Accuracy is paramount. Your responses are being systematically integrated so, do not, under ANY
        circumstance, reply with any additional text, comments or questions. Only respond with the JSON format required. \n\n"""
        
        Required_Format = f"### Required Format of JSON Response (no other response is acceptable) \n\n"
        
        # Get responses to micro-prompts
        name_list = []
        for market in self.Markets:
            for title in self.LeadershipTitles:
                p1 = f"Who is the {title} at {self.CCOEmailDomain} in {market}"
                key = f"{title}-name"
                embeddings = self.get_relevant_embeddings(p1, self.SECOrgCRDNum)
                full_prompt = f"{governing_prompt} \n\n{Required_Format} \n\n {p1} \n\n{get_readable_response_format(key)} \n\nData for question: \n\n{embeddings}"
                response = self.query_ollama_with_embedding(full_prompt, embeddings=embeddings)
                name_list.append(response)
                self.log_it(f"Response to {p1}: \n{response}")









    async def async_generate_contact_pipeline(self, contact_data):        
        from openai import OpenAI
        llm = OpenAI()
        
        
        #! Step 1 in pipeline: Get required company data #################################################################
        self.SECOrgCRDNum = contact_data.get('SECOrgCRDNum')
        self.RegisteredEntity = contact_data.get('RegisteredEntity')
        self.CCOName = contact_data.get('CCOName')
        self.CCOEmail = contact_data.get('CCOEmail')
        self.CCOEmailDomain = self.get_domain_from_email(self.CCOEmail)
        self.Website = contact_data.get('Website')
        
        contact_data["EmailUrlList"] = []
        
        
        
        #! Step 2 in pipeline: find sample emails #################################################################
        for name in self.SeedNamesCommoon:
            search_query = f'{name}@{self.CCOEmailDomain}'
            #?---> Note: FREE SCRAPING (COSTS NO MONEY) (could be blocked by google)
            google_web_scrape_results = self.get_markdown_from_google_search(search_query)
            
            self.log_it(f"Searched for {search_query}", color="PINK")
            contact_data["EmailUrlList"].extend(self.extract_N_urls_from_markdown(google_web_scrape_results, N=3))
        self.log_it(f"Got {len(contact_data['EmailUrlList'])} URLs for search query |{search_query}|", color="CYAN", data=f"{contact_data['EmailUrlList']}")
        
        
        scrape_tasks = []
        for url in contact_data["EmailUrlList"]:
            scrape_tasks.append(self.async_scrape_single_url(url))
        text_with_real_emails = await asyncio.gather(*scrape_tasks)
        
        prompt = self.create_email_extraction_prompt(self.CCOName, self.CCOEmail, self.CCOEmailDomain)
        for site_text in text_with_real_emails:
            prompt = f"{prompt} \n\n {site_text}"
            chat_completion = llm.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], temperature=0.2)
            prompt = self.create_email_extraction_prompt(self.CCOName, self.CCOEmail, self.CCOEmailDomain, chat_completion.choices[0].message.content)

        
        example_email = json.loads(chat_completion.choices[0].message.content)
        contact_data["ExampleEmails"] = example_email   
        #! Step 2 in pipeline: Get all relevant search results #################################################################

        contact_data["ExecutiveURLs"] = []
        for title in self.LeadershipTitles:
            for market in self.Markets:
                search_query = f' {title} at {self.CCOEmailDomain} in {market}?'
                #?---> Note: FREE SCRAPING (COSTS NO MONEY) (could be blocked by google)
                md_google_results = self.get_markdown_from_google_search(search_query)
                
                self.log_it(f"Searched for {search_query}", color="PINK")
                contact_data["ExecutiveURLs"].extend(self.extract_N_urls_from_markdown(md_google_results, N=3))
        self.log_it(f"Got {len(contact_data['ExecutiveURLs'])} URLs for search query |{search_query}|", color="CYAN", data=f"{contact_data['ExecutiveURLs']}")

                        
        #! Step 3 in pipeline: Scrape all search results #################################################################
        new_scrape_tasks = []
        for url in contact_data["ExecutiveURLs"]:
            new_scrape_tasks.append(self.async_scrape_single_url(url))
        text_with_executive_names_list = await asyncio.gather(*new_scrape_tasks)
        
        executive_text = "\n".join(text_with_executive_names_list)
        
        def get_executive_emails( executive_text, market, executives_dict=""):

            # Get the name and email of the CEO
            prompt = f'''Given this text, what are the names and email addresses of the {" and ".join(self.LeadershipTitles)} from {self.CCOEmailDomain} for the {market} market'''
            
            prompt = prompt + f''' \n Your responses are being systematically integrated. Do not replay with any response other that the names of the people and their emails in this JSON format.  
                        Please extend the data below with the additional records and return the entire new JSON dataset (only removing duplicates) with current and new records in your response.

                        ### JSON Dataset \n''' 
            if executives_dict == {}:
                json_str = json.dumps({ 
                                        "Emails":
                                        [{"NameExecutive": "<Put Name Here>", 
                                        "Email": "<Put Email Here>",
                                        "Title": "<Put Title Here>"
                                        }]
                                        }, indent=4)
            else: 
                json_str = json.dumps(executives_dict)
               
            
            prompt = prompt + f"""\n\n For the email addres, use an email address if there is one for the executive in the text. 
            If there is not an email address do your best to create an email address that would be likely to be used by the executive given these EXAMPLES:
            EXAMPLES
            {json.dumps(example_email, indent=4)}"""
            
            
            
            prompt = prompt + f"\n\n {executive_text} \n\n remember to get name, title and email for all markets and don't use the data from the EXAMPLES in your response {" and ".join(self.Markets)}"
            self.log_it(f"Prompt for executive emails: {prompt}", color="LIGHTBLUE")
            
            executive_emails = llm.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}],temperature=0.2)
            
            json_str = json.loads(executive_emails.choices[0].message.content)
            

            return json_str

        executives_dict = {}
        for market in self.Markets:
            contact_data["Executives"] = get_executive_emails(executive_text, executives_dict)
        self.log_it(f"Executives: {contact_data['Executives']}", color="MAGENTA")
        
        with open(f"{self.CCOName}_contact.json", "w") as f:
            f.write(json.dumps(contact_data, indent=4))
        
        return contact_data
        
            

def contact_pipeline_test(contact_info):
    gen_contact = contact_generation_pipeline()
    complete_contact_info = asyncio.run(gen_contact.async_generate_contact(contact_info))
    print(f"Successfully got contact {complete_contact_info}")
    
    with open(f"{complete_contact_info.get('Legal_Name', '')}_contact.json", "w") as f:
        f.write(json.dumps(complete_contact_info, indent=4))

contact_info = {
"SECOrgCRDNum":	"107173",
"RegisteredEntity":	"RBC GLOBAL ASSET MANAGEMENT (U.S.) INC.",
"CCOName":	"CHRISTINA M. WEBER",
"CCOEmail":	"CHRISTI.WEBER@RBC.COM",
"Website":	f"{'HTTPS://WWW.LINKEDIN.COM/COMPANY/RBC-GLOBAL-ASSET-MANAGEMENT/'}"
}

gen_contact = contact_generation_pipeline()



asyncio.run(gen_contact.generate_contact_ollama_rag(contact_info))

# contact_pipeline_test(contact_info)

def process_pipeline_all_prospects():
    import _class_storage 
    storage = _class_storage.az_storage()
    prospect_list = asyncio.run(storage.get_all_prospects())
    print(f"Successfully got prospect list with count '{len(prospect_list)}'")
    
    for prospect in prospect_list:
        contact_pipeline_test(prospect)
        
# process_pipeline_all_prospects()


async def update_batch_1():
    csv_file_name = "/Users/michasmi/Downloads/smallprospects.csv"
    import pandas as pd
    prospect_df = pd.read_csv(csv_file_name)
    prospect_list = prospect_df.to_dict(orient='records')
    print(f"Successfully got prospect list with count '{len(prospect_list)}'")
    
    jbi_connection_string = os.environ.get('JBI_CONNECTION_STRING', 'No Key or Connection String found')
    
    async with TableClient.from_connection_string(conn_str=jbi_connection_string, table_name="prospects") as table_client:
        try:
            for prospect in prospect_list:
        
                resp = await table_client.upsert_entity(mode=UpdateMode.MERGE, entity=prospect)
                print(resp)
        except Exception as e:
            print(f"Error: {str(e)}")

# asyncio.run(update_batch_1())