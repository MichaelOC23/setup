from bs4 import BeautifulSoup  # Correct import
from playwright.async_api import async_playwright
from urllib.parse import urlparse, urljoin
import asyncio
import os
import json



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
                
async def scrape_list_of_urls(url_list):
    full_url_list = []
    
    
    #crawl the site and get all the urls if it is a top level domain
    for url in url_list:
        full_url_list.append(url.strip())
        if url.count("/") == 3:
            more_urls = await crawl_site(url)
            if len(more_urls) > 0:
                full_url_list.extend(more_urls)
                
    scrape_tasks = []
    for url in full_url_list:
        scrape_tasks.append(async_scrape_single_url(url))
    return await asyncio.gather(*scrape_tasks)

#create a string from a url that is safe for a file name
def url_to_filename(url):
    return url.replace("://", "_").replace("/", "_").replace(".", "_").replace(":", "_")

async def get_all_links(page, base_url):
    content = await page.content()
    soup = BeautifulSoup(content, 'html.parser')
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        url = urljoin(base_url, href)
        parsed_url = urlparse(url)
        if parsed_url.netloc == urlparse(base_url).netloc:
            links.add(url)
    return links

async def crawl_site(base_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(base_url)
        
        # Use a set to store unique URLs
        visited_urls = set()
        urls_to_visit = {base_url}
        
        while urls_to_visit:
            current_url = urls_to_visit.pop()
            if current_url in visited_urls:
                continue
            
            print(f"Crawling: {current_url}")
            visited_urls.add(current_url)
            await page.goto(current_url)
            new_links = await get_all_links(page, base_url)
            
            urls_to_visit.update(new_links - visited_urls)
        
        await browser.close()
        return visited_urls




folder_path = os.environ.get("TFOLDER", None)
with open("folder_path.txt", "w") as f:
    f.write(folder_path)
    



# folder_path = "/Users/michasmi/Library/CloudStorage/OneDrive-SharedLibraries-JBIHoldingsLLC/Just Build It - Documents/Clients/Sageview/research"

if folder_path is None or not os.path.exists(folder_path):
    raise ValueError(f"Folder path {folder_path} does not exist")

url_file = f"{folder_path}/url_list.txt"
scrape_folder = f"{folder_path}/scraped_data"

print(f"Scraping URLs from {url_file} with data saved to {scrape_folder}")

url_list = []
with open(url_file, "r") as f:
    url_list = f.readlines()

scraped_text_list = asyncio.run(scrape_list_of_urls(url_list))

if not os.path.exists(scrape_folder):
    os.makedirs(scrape_folder)

for url, text in zip(url_list, scraped_text_list):
    with open(f"{scrape_folder}/{url_to_filename(url)}.json", "w") as f:
        out_dict = {"url": url, "text": text}   
        f.write(json.dumps(out_dict, indent=4))



