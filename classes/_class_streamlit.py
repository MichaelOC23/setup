from multiprocessing import process
import streamlit as st
import uuid
import os
import nltk
import base64
import asyncio
from datetime import date
import requests
from urllib.parse import urlencode


from langchain_openai import OpenAIEmbeddings

########################################
#######    STORAGE MANAGEMENT    #######
########################################
#Make sure there is a parameter table to store state
from _class_storage import az_storage as cs
storage = cs()
asyncio.run(storage.create_table_safely(storage.parameter_table_name))

def get_parameter_value(parameter_name):
    parameter_value = asyncio.run(storage.get_one_parameter(parameter_name))
    return parameter_value

def set_parameter_value(parameter_name, parameter_value):
    asyncio.run(storage.create_parameter(parameter_name, parameter_value))

def initialize_session_state_variable(variable_name, variable_value):
    if variable_name not in st.session_state:
        st.session_state[variable_name] = variable_value

def set_up_page(page_title_text="[TITLE NEEDED FOR PAGE]", jbi_or_cfy="jbi", light_or_dark="dark", session_state_variables=[], connect_to_dj=False, hideResultGridButton=False):  
        
    def initialize_session_state_variable(variable_name, variable_value):
        if variable_name not in st.session_state:
            st.session_state[variable_name] = variable_value

    
    initialize_session_state_variable("DevModeState", False) 
    initialize_session_state_variable("settings", {"divider-color": "gray",}) 
    initialize_session_state_variable("djsession", None)
    initialize_session_state_variable("djtoken", {})
    initialize_session_state_variable("djtoken_status_message", "") 
    initialize_session_state_variable("search_result_cache", "") 
    initialize_session_state_variable("viewed_article_cache", "") 
    initialize_session_state_variable("show_results", False)
    initialize_session_state_variable("show_article", False) 
    initialize_session_state_variable("chat_has_started", False)
    initialize_session_state_variable("show_session_state", False)
    initialize_session_state_variable("show_search_results", False)
    initialize_session_state_variable("current_search_summary", "")
    
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
        
        message_col.markdown(st.session_state.djtoken_status_message, unsafe_allow_html=True)
        if refresh_col.button('DJ ♾️', use_container_width=True):
            get_new_token()
    
    
    
    

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
    
    border_color = "#FFFFFF"
    text_color = "#FFFFFF"
    background_color = "#1D1D1D"
    
    message_col, refresh_col, ss_col, view_results = st.columns([8.5, 2,2,2])    
    with ss_col:

        view_ss = st.sidebar.button(f"Ses. State", use_container_width=True)
        if view_ss:
            if st.session_state.show_session_state:
                st.session_state.show_session_state = False
            else:
                st.session_state.show_session_state = True
    if st.session_state.show_session_state:
        ss = st.expander("Session State Value", expanded=False)
        ss.write(st.session_state)
    if not hideResultGridButton:
        with view_results:
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
            
  
        

    st.markdown(f"""
            <div style="display: flex; align-items: start; width: 100%; padding: 10px; border: 1px solid {border_color}; border-radius: 10px; 
            height: 80px; background-color: {background_color}; margin-bottom: 20px;"> 
            <img src="{LOGO_URL}" alt="{PAGE_TITLE}" style="width: 80px; height: auto; margin: 10px 40px 5px 20px;">  
            <span style="flex: 1; font-size: 30px; margin: 2px 0px 10px 10px; font-weight: 400; text-align: top; align: right; white-space: nowrap; 
            overflow: hidden; color: {text_color}; text-overflow: ellipsis;">{PAGE_TITLE}</span>  </div>""", unsafe_allow_html=True)
    
    
    # Apply standard mardown to the page
    # st.markdown("<hr style='margin: 0.5em 0; border-top: 1px solid #ABABAB;'>", unsafe_allow_html=True)

    # Enable the below to see border around the page and all the columns
    # st.markdown("""<code style="background-color: #FFFFFF; padding: 30px; border-radius: 6px;color: red;">Your HTML content here</code>""", unsafe_allow_html=True)

    
    if connect_to_dj:
        display_dj_connection_status()
    
def display_dj_search_results(simple_search_string = "", search_date_range="Last6Months", page_offset=0, search_results=None, show_chatbot=False):
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
    
class research_libaray():
    def __init__(self ):
        self.azure_storage_connection_string = os.environ.get('PERSONAL_STORAGE_CONNECTION_STRING', 'No Key or Connection String found')
        # self.local_chromadb = None
        self.CACHE_DIR = "cache"
        if not os.path.exists(self.CACHE_DIR):
            os.makedirs(f"{self.CACHE_DIR}/")
        
        self.sec_bert_base_model = "nlpaueb/sec-bert-base"
        self.general_model = "roberta-base"
        self.supported_file_types = ["pdf", "txt", "mp3", "mp4", 'mpeg', 'doc', 'docx', "txt"]
        self.model_dict = {
            "Finance": self.sec_bert_base_model, 
            "General": self.general_model,
            "ChatGPT-3.5": "gpt-3.5-turbo",
            "ChatGPT-4": "gpt-4-turbo",
            
            }
        
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
        
        initialize_session_state_variable("model_type_value", self.model_dict["Finance"])
        initialize_session_state_variable("temperature", .1)
        
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
              
