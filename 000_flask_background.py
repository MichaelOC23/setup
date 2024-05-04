
from flask import Flask, request, jsonify
# from httpx import get
# from numpy import full, isin
import time
from classes import _class_search_web
from io import StringIO
from classes import _class_storage
import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp
import os
import zipfile


import csv

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
# We will collect the is_final=true messages here so we can use them when the person finishes speaking
is_finals = []
deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
deepgram = DeepgramClient(deepgram_api_key)

app = Flask(__name__)

data_directory = os.path.join('data', 'nasdaq')
log_directory = os.path.join(data_directory, 'logs')
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
    
search = _class_search_web.Search()
storage = _class_storage._storage()


def log_it(message, level='info', color='black'):
    with open(os.path.join(log_directory, 'flask.log'), 'a') as f:
        f.write(f"{message}\n")
    print(message)

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

@app.route('/startaudiorec', methods=['POST'])
def startaudiorec():
    try:
        # example of setting up a client config. logging values: WARNING, VERBOSE, DEBUG, SPAM
        # config = DeepgramClientOptions(
        #     verbose=logging.DEBUG, options={"keepalive": "true"}
        # )
        # deepgram: DeepgramClient = DeepgramClient("", config)
        # otherwise, use default config
        deepgram: DeepgramClient = DeepgramClient()

        dg_connection = deepgram.listen.live.v("1")

        def on_open(self, open, **kwargs):
            print(f"Deepgram Connection Open")

        def on_message(self, result, **kwargs):
            global is_finals
            sentence = result.channel.alternatives[0].transcript
            print(f"{result}")
            if len(sentence) == 0:
                return
            else:
                print(f"Deepgram Message: {sentence}")
            if result.is_final:
                # We need to collect these and concatenate them together when we get a speech_final=true
                # See docs: https://developers.deepgram.com/docs/understand-endpointing-interim-results
                is_finals.append(sentence)

                # Speech Final means we have detected sufficent silence to consider this end of speech
                # Speech final is the lowest latency result as it triggers as soon an the endpointing value has triggered
                if result.speech_final:
                    utterance = ' '.join(is_finals)
                    print(f"Speech Final: {utterance}")
                    is_finals = []
                else:
                    # These are useful if you need real time captioning and update what the Interim Results produced
                    print(f"Is Final: {sentence}")
            else:
                # These are useful if you need real time captioning of what is being spoken
                print(f"Interim Results: {sentence}")

        def on_metadata(self, metadata, **kwargs):
            print(f"Deepgram Metadata: {metadata}")

        def on_speech_started(self, speech_started, **kwargs):
            print(f"Deepgram Speech Started")

        def on_utterance_end(self, utterance_end, **kwargs):
            global is_finals
            if len(is_finals) > 0:
                utterance = ' '.join(is_finals)
                print(f"Deepgram Utterance End: {utterance}")
                is_finals = []

        def on_close(self, close, **kwargs):
            print(f"Deepgram Connection Closed")

        def on_error(self, error, **kwargs):
            print(f"Deepgram Handled Error: {error}")

        def on_unhandled(self, unhandled, **kwargs):
            print(f"Deepgram Unhandled Websocket Message: {unhandled}")

        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
        dg_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
        dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
        dg_connection.on(LiveTranscriptionEvents.Close, on_close)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)
        dg_connection.on(LiveTranscriptionEvents.Unhandled, on_unhandled)

        options: LiveOptions = LiveOptions(
            model="nova-2",
            language="en-US",
            # Apply smart formatting to the output
            smart_format=True,
            # Raw audio format details
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            # To get UtteranceEnd, the following must be set:
            interim_results=True,
            utterance_end_ms="1000",
            vad_events=True,
            # Time in milliseconds of silence to wait for before finalizing speech
            endpointing=300
        )

        addons = {
            # Prevent waiting for additional numbers
            "no_delay": "true"
        }

        print("\n\nPress Enter to stop recording...\n\n")
        if dg_connection.start(options, addons=addons) is False:
            print("Failed to connect to Deepgram")
            return

        # Open a microphone stream on the default input device
        microphone = Microphone(dg_connection.send)

        # start microphone
        microphone.start()
        
        with open('stopfile.txt', 'w') as f:
            f.write("Stop Meeting")
        
        def keep_going():
            with open('stopfile.txt', 'r') as f:
                return f.read() != "Stopping Meeting"
        
        while keep_going():
            pass
        
            # Wait for the microphone to close
        microphone.finish()

        # Indicate that we've finished
        dg_connection.finish()

        print("Finished")
        with open('stopfile.txt', 'w') as f:
            f.write("Start Meeting")
        # sleep(30)  # wait 30 seconds to see if there is any additional socket activity
        # print("Really done!")
        return

    except Exception as e:
        print(f"Could not open socket: {e}")
        return

@app.route('/stopaudiorec', methods=['POST'])
def stopaudiorec():
    with open('stopfile.txt', 'w') as f:
        f.write("Stopping Meeting")
    return


if __name__ == "__main__":
    pass
    # download_nasdaq()
    app.run(debug=True)