"""googlesearch is a Python library for searching Google, easily."""
from pyppeteer import launch
import os
import threading
from langchain.retrievers.you import YouRetriever
from googleapiclient.discovery import build
from urllib.parse import urlparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
import requests
import cv2
import urllib
import numpy as np
from PIL import Image
import imagehash
import requests
from io import BytesIO

import _class_storage as azstr

yr = YouRetriever()

# This class builds a service object for interacting with the API. Visit
# the Google APIs Console <http://code.google.com/apis/console>
# Create Custom Search Engines at https://programmablesearchengine.google.com/controlpanel/all



class Search:
    def __init__(self):

        self.google_api_key = os.environ.get('GOOGLE_API_KEY')
        self.google_general_cx = os.environ.get('GOOGLE_GENERAL_CX')
        self.google_image_cx = os.environ.get('GOOGLE_IMAGE_CX')
        self.hash_list = []
        self.flask_url = "http://127.0.0.1:5005/"
        self.storage = azstr._storage()
    
    async def search_images_fast(self, query, require_a_face=False):
        
        img_log = []
        service = build("customsearch", "v1", developerKey=self.google_api_key)
        search_results = (service.cse().list(q=query,cx=f"{self.google_image_cx}",).execute())
        
        msg = f"Internet search found {len(search_results.get('items', []))} possible image results."
        print(msg)
        img_log.append(msg)
        
        candidate_image_urls = []
        
        #get every candidate uRL that might be an image
        for item in search_results.get('items', []):
            candidate_image_urls.extend(self.find_image_urls(item))
        
        # eliminate duplicate URLs from the candidate list
        unique_candidate_image_urls = list(set(candidate_image_urls))
        msg = f"Found a total of {len(unique_candidate_image_urls)} image urls."
        
        # Async: Validate the URL, test for faces, and return hash if (has face) and is hashable
        all_tasks = []
        for url in unique_candidate_image_urls:
            task = asyncio.create_task(self.get_hash_if_human(url))
            all_tasks.append(task)
        all_results = await asyncio.gather(*all_tasks)
        
        return all_results, query
        
    async def get_hash_if_human (self, url):
        
        # kick out if url is invalid
        if not self.is_valid_url(url):
            return False, None, url
        
        if not await self.image_has_face(url):
            return False, None, url
        
        img_hash = self.image_url_to_hash(url)
        
        if img_hash is None:
            return False, None, url
        
        return True, img_hash, url
        
    def is_valid_url(self, may_be_a_url):
        try:
            result = urlparse(may_be_a_url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False
        
    def url_to_image(self, url):
        try:
            # Download the image, convert it to a NumPy array, and then read it into OpenCV format
            resp = urllib.request.urlopen(url)
            image = np.asarray(bytearray(resp.read()), dtype="uint8")
            image = cv2.imdecode(image, cv2.IMREAD_COLOR)
            return image
        except:
            return None
    
    def image_url_to_hash(self, url):
        try:
            # Download the image from URL
            response = requests.get(url)
            image = Image.open(BytesIO(response.content))
        
            # Calculate the hash
            hash_value = imagehash.average_hash(image)
        except:
            return None
    
        return hash_value
    
    def find_image_urls(self, d, image_urls=None):
        # Return none if empty results
        if image_urls is None:
            image_urls = []

        # Check if the input is a dictionary
        if isinstance(d, dict):
            for value in d.values():
                self.find_image_urls(value, image_urls)
            for key in d.keys():
                if 'image' in key.lower() or 'src' in key.lower():
                    if isinstance(d[key], list):
                        for item in d[key]:
                            if isinstance(item, str):
                                image_urls.append(item)
                            if isinstance(item, dict):
                                self.find_image_urls(item, image_urls)
                    if isinstance(d[key], str):
                        image_urls.append(d[key])
                    if isinstance(d[key], dict):
                        self.find_image_urls(d[key], image_urls)
                    
        # Check if the input is a list or a tuple
        elif isinstance(d, (list, tuple)):
            for item in d:
                self.find_image_urls(item, image_urls)
        # Check if the input is a string, starts with http, and matches the URL pattern
        elif isinstance(d, str) and d.startswith('http') and d.endswith(('.jpg', '.png', '.gif')):
            image_urls.append(d)
        

        return image_urls

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
    
    def assemble_web_query(self, first_name, last_name, other_details=''):
        qry = f' ("{first_name} {last_name}" OR '
        qry+= f' ("{first_name}" AND "{last_name}")) '
        if other_details != "":
            qry+= f' AND ({other_details})'
        return qry
    
    # @st.cache
    def search_web(self, query):
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
                "Type" : "web",
                "Query" : query,
                "Site" : base_url,
                "Summary" : result.get('htmlSnippet', result.get('snippet', '')),
                "Link" : result.get('link', ''),
                "Title": result.get('title', ''),
                "primary_result_image" : primary_result_image,
                "primary_site_image" : primary_site_image
            }
            
            results.append(result_dict)
        
        return results
    
    def search_web_async_with_assemble(self, first_name, last_name, other_details):
        qry = self.assemble_web_query(first_name, last_name, other_details)
        asyncio.run(self.search_web_async(qry))
        return qry
    
    async def search_web_async(self, query):
        search_results = self.search_web(query)
        Res_tasks = []
        for result in search_results:
            if result.get('Link', '') != None  and result.get('Link', '') != "" and result.get('Query', '') is not None and result.get('Query', '') != "":
                Res_tasks.append(
                    self.storage.save_url(search_type=result.get('Type', ''),
                                          search_query=query, 
                                          result_name=result.get('Title', ''), #
                                          site = result.get('Site', ''),
                                          page_snippet=result.get('Summary', ''),
                                          url=result.get('Link', ''), 
                                          primary_result_image=result.get('primary_result_image', ''),
                                          primary_site_image=result.get('primary_site_image', ''),
                                          
                                          ))
            else:
                continue
                
        #Async: Save the results to the database
        response = await asyncio.gather(*Res_tasks)
        
        #kick off Scraping
        # all_raw = await self.scrape_results(query)
        
        return query

    def try_to_scrape_search_results(self, search_results):        
        threads = []
        for result in search_results:
            url = result.get('result_url', "")
            if url:
                t = threading.Thread(target=self.sync_wrapper, args=(url,))
                t.start()
                threads.append(t)
            
    def sync_wrapper(self, url):
        return asyncio.run(self.async_get_web_page(url))

    async def async_get_web_page(self, url):
        browser = None
        try:
            browser = await launch(headless=True)
            page = await browser.newPage()
            await page.goto(url)
            await page.waitForSelector('body')
            body = await page.content()
            return body
        except Exception as e:
            print(f"Error getting full webpage for {url}: {str(e)}")
        finally:
            if browser:
                await browser.close()

    # @st.cache
    def search_images(self, query, require_a_face=False):
        
        img_log = []
        service = build("customsearch", "v1", developerKey=self.google_api_key)
        search_results = (service.cse().list(q=query,cx=f"{self.google_image_cx}",).execute())
        
        msg = f"Internet search found {len(search_results.get('items', []))} possible image results."
        print(msg)
        img_log.append(msg)
        
        
        complete_list = []
        hash_list = []
        vald_and_truly_unique_list = []
        vald_and_truly_unique_face_list = []
        
        
        #get every candidate uRL that might be an image
        for item in search_results.get('items', []):
            complete_list.extend(self.find_image_urls(item))
        
        msg = f"Found a total of {len(complete_list)} image urls."
        print(msg)
        img_log.append(msg)
        
        
        # kick out duplicate URLs from the candidate lisst
        complete_unique_list = list(set(complete_list))

        
        msg = f"Of the {len(complete_list)} URLs, {len(complete_unique_list)} were unique."
        print(msg)
        img_log.append(msg)
        
        # kick out candidates that are not valid URLs
        complete_valid_list = [i for i in complete_unique_list if self.is_valid_url(i)]
        msg = f"Of the {len(complete_unique_list)} unique URLs, {len(complete_valid_list)} were valid URLs."
        print(msg)
        img_log.append(msg)
        
        # Kick out duplicate images and NEAR-DUPLICATES
        for cu_image in complete_valid_list:
            
            #Download and hash the image for comparison
            img_hash = self.image_url_to_hash(cu_image)
            
            #Skip any url where the image could not be hashed
            if img_hash is None:
                continue
            
            #If the hash list is empty, add the image to the unique list
            if len(hash_list) == 0:
                hash_list.append(img_hash)
                vald_and_truly_unique_list.append(cu_image)
                continue
            
            # If the hash list is not empty, compare this hash to each hash in the hash list
            # using the index of the list to compare the most recent images first 
            # (as they are the most likely to be similar to the current image)
            x=len(hash_list)-1
            
            #Assume the image is unique util proven similar
            is_similar = False
            
            # Using a threshold to determine similarity,
            # declare the image as similar if the hash difference is less than the hash threshold
            while x>=0 and is_similar == False:
                hi = hash_list[x]
                if abs(img_hash - hi) < 4: ## << Hash Threshold
                    is_similar = True
                x-=1
            
            # If the image is not similar to any other image, add it to the vald_and_truly_unique_list list
            if not is_similar:
                vald_and_truly_unique_list.append(cu_image)
            

        # Tracking progress ....
        # Any image that has reached this point:
        # 1. Has a valid URL
        # 2. Has a different URL from all other images
        # 3. Is hashable
        # 4. Is not similar to any other image (based on the hash threshold)
        
        msg = f"After removing duplicates AND NEAR-DUPLICATES {len(vald_and_truly_unique_list)} valid, hashable and unique urls remain."
        print(msg)
        img_log.append(msg)
                    
        # Return results unless require_a_face is True
        # If require_a_face is True, return only images with faces
        # Note this is the slowest part of the process which is why it is not the default
        if not require_a_face:
            return vald_and_truly_unique_list
        
        # Test images for having at least 1 face
        for candidate_face_image in vald_and_truly_unique_list:
            if self.image_has_face(candidate_face_image):
                vald_and_truly_unique_face_list.append(candidate_face_image)
        
        msg = f"After removing images without faces {len(vald_and_truly_unique_face_list)} valid, hashable and unique urls  (with faces) remain."
        print(msg)
        img_log.append(msg)
        
        # Return the list of images with faces
        return vald_and_truly_unique_face_list, img_log        
                
    async def image_has_face(self, image_url):
        try:
            # Use the function to convert the image URL to an OpenCV image and hash the image
            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor() as pool:
                image = await loop.run_in_executor(pool, self.url_to_image, image_url) 
            if image is None:
                return False
            
            # image = self.url_to_image(image_url)
            # if image is None:
            #     return False

            # Load the pre-trained Haar Cascade model for face detection
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

            # Convert the image to grayscale (necessary for face detection)
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Detect faces in the image
            faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))


            # Print the number of faces found
            print(f"Found {len(faces)} faces in the image.")
            
            if len(faces) > 0:
                return True
            else:
                return False
        except:
            return False
    
    def search_rag_content(self, query):
        ydc_list = []
        for doc in yr.get_relevant_documents(query):
            text_val = f"<strong>{doc.type}</strong>: {doc.page_content}"
            ydc_list.append(text_val)
        return ydc_list

    async def get_stored_search_results(self, search_query):
        entities = await self.storage.get_some_entities(table_name=self.storage.url_results_table_name, PartitionKey=search_query, re_sanitize_keys=True)
        if isinstance(entities, list):
            return entities
        else:
            return []
        
    def request_scrape_for_query(self, params=None):
        """Make an asynchronous GET request to the specified URL."""
        def request_thread(url, params):
            """The thread function that performs the request."""
            try:
                requests.get(url, params=params)
                print("Request sent successfully!")
            except Exception as e:
                print(f"Failed to send request: {e}")

        # Create and start a thread to make the request
        thread = Thread(target=request_thread, args=(self.flask_url, params))
        thread.start()


if __name__ == "__main__":
    pass
    # search = Search()

    



