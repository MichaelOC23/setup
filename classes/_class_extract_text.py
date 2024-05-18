# To read PDFs
# import tkinter
import PyPDF2

# To analyze PDF layouts and extract text
from cv2 import log
from pdfminer.high_level import extract_pages, extract_text
from pdfminer.layout import LTTextContainer, LTChar, LTRect, LTFigure

#Office Documents
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain.document_loaders import UnstructuredPowerPointLoader, text
from langchain_community.document_loaders import UnstructuredExcelLoader
import langchain_core as core

# To extract text from tables in PDF
import pdfplumber

# To extract the images from the PDFs
from PIL import Image
from pdf2image import convert_from_path

# To perform OCR to extract text from images 
import pytesseract 

# Standard Python libraries
import os
from pathlib import Path
import re

# from cv2 import log
import math
from collections import Counter

# Add the parent directory to sys.path
import tempfile
import json

#Extraction of text from images
import pytesseract
from PIL import Image
import cv2

from datetime import datetime




class extract_text_from_file:
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
        self.text_structures = ['by_page', 'all_pages', 'useful', 'ignored']
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
            # Handle other possible exceptions (e.g., permission issues)
            print(f"Error while deleting file: {e}")

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
            
            pdf_text['by_page'] = {}

            pdf_text['by_style'] = {}
            for style_item in self.text_styles:
                pdf_text['by_style'][style_item] = {}
                
            pdf_text['by_element_type'] = {}
            for element_type in self.text_element_types:
                pdf_text['by_element_type'][element_type] = []
            
            pdf_text['all_text'] = []

            return pdf_text

        def _add_element_dict_to_json(pdf_text, element_dict):
            if element_dict.get('text', '') == '':
                return pdf_text
            
            pdf_text['all_text'].append(element_dict.get('text', ''))
            
            #structure by_page
            page_str = element_dict['page']
            if element_dict['page'] not in pdf_text['by_page']:
                pdf_text['by_page'][page_str] = []
            pdf_text['by_page'][page_str].append(element_dict)
            
            #structure all_pages
            pdf_text['all_pages'].append(element_dict)
            
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
            
            try:
                pdf_text = _extract_nested_dict_from_pdf(pdf_path=pdf_path)
                save_result, output_path = self.save_json_to_file(pdf_text, output_path=output_path, mode=mode, file_path=pdf_path)
    
                return output_path, save_result, pdf_text
            
            except Exception as e:
                msg = f"Error: {e}"
                self.log_it(msg, "ERROR")
                return pdf_path, False, msg
        
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
            doc_loader = UnstructuredWordDocumentLoader(file_path=file_path, mode="elements")
        if file_extension in ['.pptx', '.ppt']:
            doc_loader = UnstructuredPowerPointLoader(file_path=file_path, mode="elements")
        if file_extension in ['.xlsx', '.xls']:
            doc_loader = UnstructuredExcelLoader(file_path=file_path, mode="elements")
        
        try:
            
            # Open the document and extract the JSON data from the document elements
            doc_doc_objs = doc_loader.load()
            
            if file_extension in ['.pptx', '.ppt']:
                doc_dict = create_dictionary_from_ppt(doc_doc_objs)

            else:    
                # turn the document objects into a dictionary
                doc_dict = core.load.dump.dumpd(doc_doc_objs)
                
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
        pytesseract.pytesseract.tesseract_cmd = self.pytesseract_executable_path

        try:
            # Load the image
            image = Image.open(file_path)
            
            # Use Tesseract to do OCR on the image
            text = pytesseract.image_to_string(image)
            
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
        
        if self.all_extracts_path != '' and self.all_extracts_dict != {}:
            with open(self.all_extracts_path, 'w') as f:
                f.write(json.dumps(self.all_extracts_dict, indent=4))
                f.close()
            
            for key in self.all_extracts_dict.keys():
                file_dict = self.all_extracts_dict[key]
                if isinstance(file_dict, dict):
                    all_text = file_dict.get('all_text', [])
                    all_text = "\n".join(all_text)
                    with open (f"{key}.txt", 'w') as f:
                        f.write(all_text)
                        f.close()
            

if __name__ == '__main__':
    pass
    
    # # pdf_path = 'example.pdf'
    directory_path = '/Users/michasmi/Downloads/pe'
    output_folder = directory_path
    ext_text = extract_text_from_file()
    uid_string = datetime.now().strftime("%Y%m%d%H%M%S")

    
    # directory_path = '/Users/michasmi/code/dow_jones_service/assets/test-images'
    test_doc_list = [os.path.join(directory_path, filename) for filename in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, filename))]
    ext_text.extract_json_from_files(test_doc_list, output_path=f'{output_folder}/extract{uid_string}.json')
    



# def _extract_table(pdf_path, page_num, table_num):
#     # Open the pdf file
#     pdf = pdfplumber.open(pdf_path)
#     # Find the examined page
#     table_page = pdf.pages[page_num]
#     # Extract the appropriate table
#     table = table_page._extract_tables()[table_num]
#     return table


# def _get_first_title(json_data):
#     # Initialize an empty dictionary to store the nested text data
#     nested_text_dict = {}
    
    
#     title_font_size = 0 # This will be the first instance(s) of the max font size in the first 3 pages
#     first_pages = set(['Page_0', 'Page_1', 'Page_2'])
#     title_text = ''
    
#     # Iterate over the first 3 pages and find the max font size
#     text_lines = []
#     for page in first_pages:
#         for text_line in json_data['text_by_page_detailed'][page]:
#             #gather all the text from the first 3 pages
#             text_lines.append(text_line)
#             #track the max font size for later identifying the title
#             title_font_size = max(text_line['max_font_size'], title_font_size)
    
#     found_title = 0 #greater than 0 when the first instance of the max font is found
#     title_complete = 0 #greater than 0 whenever the font changes after finding the max (i.e. end of title)
#     for text_line in text_lines:
#         if title_complete > 0:
#             continue
#         if text_line['max_font_size'] == title_font_size:
#             found_title +=1
#             title_text = f"{title_text} {text_line['text']}"
#         else:
#             if found_title > 0:
#                 title_complete +=1
#                 continue
#     #remove escapted text from JSON
#     title_text = title_text.strip()
#     title_text = title_text.replace('\n', ' ')
#     print(f"Title: {title_text}")
#     return title_text
