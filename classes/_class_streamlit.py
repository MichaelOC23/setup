
import streamlit as st
import uuid
import os
import asyncio
from openai import OpenAI
from typing import List
from pathlib import Path
import pandas as pd

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from langchain.schema import StrOutputParser
from langchain_community.document_loaders import (PyMuPDFLoader,)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.chroma import Chroma
from langchain.indexes import SQLRecordManager, index
from langchain.schema import Document
from langchain.schema.runnable import Runnable, RunnablePassthrough, RunnableConfig
from langchain.callbacks.base import BaseCallbackHandler

def initialize_session_state_variable(variable_name, variable_value):
    if variable_name not in st.session_state:
        st.session_state[variable_name] = variable_value

def set_up_page(page_title_text="[TITLE NEEDED FOR PAGE]", jbi_or_cfy="jbi", light_or_dark="dark", session_state_variables=[], connect_to_dj=False, hideResultGridButton=False):  
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
    
    # if show_chatbot and st.session_state.show_results:
    #     if not st.session_state.chat_has_started:
    #         asyncio.run(on_chat_start(prompt="You are an always-helpful and cheerful AI Assistant.", pdf_storage_path=None, api_response=None, chunk_size=1024, chunk_overlap=50))
            
    #     def show_simple_chatbot():
    #         viewer_col.subheader('Chatbot', divider='gray')

    #         # Set OpenAI API key from Streamlit secrets
    #         client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    #         if "messages" not in st.session_state:
    #             st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

    #         for msg in st.session_state.messages:
    #             viewer_col.chat_message(msg["role"]).write(msg["content"])

    #         if prompt := viewer_col.chat_input():
    #             st.session_state.messages.append({"role": "user", "content": prompt})
    #             response = client.chat.completions.create(model="gpt-3.5-turbo", messages=st.session_state.messages)
    #             msg = response.choices[0].message.content
    #             st.session_state.messages.append({"role": "assistant", "content": msg})
    #             viewer_col.chat_message("assistant").write(msg)
    #             viewer_col.chat_message("user").write(prompt)
    #     show_simple_chatbot()
        