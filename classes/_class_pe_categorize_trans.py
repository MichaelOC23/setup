import csv
import os
import sys
from datetime import datetime
import re
import shutil
import json

#Create the current Directory Variable
# PE_IO_DIRECTORY = os.path.dirname(os.path.abspath(__file__))



# import functions_sql as sql
# import functions_model_generation as model_gen

#We will be auto-categorizing transacitons.  
#This is the dictionary that will be used to do that
categoryDictionary = {
  'SearchTerm': '',
  'Category': ''
}  

def printProgress(StartTime, TotalRecords, CurrentRecord):
  #Adust for zero based index
  CurrentRecord = CurrentRecord + 1
     
  currentTimeNum = datetime.now()
  elapsedTimeNum = currentTimeNum - StartTime
  avgTimePerRecordNum = elapsedTimeNum / (CurrentRecord)
  percentCompleteNum = (CurrentRecord+ 1) / TotalRecords
  estTimeRemainingNum = avgTimePerRecordNum * (TotalRecords - CurrentRecord)
  
  #format these values to display as hh:mm:ss
  avgTimePerRecord = str(avgTimePerRecordNum).split('.')[0]
  estTimeRemaining = str(estTimeRemainingNum).split('.')[0]
  
  #format as percent % e.g. 20%
  percentComplete = str(percentCompleteNum * 100).split('.')[0] + '%'

  print(f"Record {CurrentRecord} of {TotalRecords} completed. {percentComplete} complete. Avg per record: {avgTimePerRecord}. Time remaining: {estTimeRemaining}")


# transactionFilePath = os.path.join('/Users/michasmi/Library/Mobile Documents/com~apple~CloudDocs/jbi/personal-finance/standardized.csv')
PE_IO_DIRECTORY = '/Users/michasmi/Library/Mobile Documents/com~apple~CloudDocs/jbi/personal-expenses/transaction-files'
fullVocabFilePath = os.path.join(PE_IO_DIRECTORY,'FullVocabForUse.txt')
categoryMapFile = os.path.join(PE_IO_DIRECTORY, '___CategoryMap.csv')
model_file_path = os.path.join(PE_IO_DIRECTORY, 'models.json')
#Working Files for improving category matching
categoryGaps = os.path.join(PE_IO_DIRECTORY, 'CategoryGaps.csv')
categoryGapsByWord = os.path.join(PE_IO_DIRECTORY, 'CategoryGapsByWord.csv')

  

def CreateFileAndFolderPath(FilePath):
  
  # Create parent directories if needed
  fileDirectory = os.path.dirname(FilePath)
  fileName = os.path.basename(FilePath)
  archiveDirectory = os.path.join(fileDirectory, 'Archive')
  fileType = os.path.splitext(FilePath)[1]
  fileNameNoExtension = os.path.splitext(fileName)[0]
  
  completeFilePath = os.path.join(fileDirectory, f'{fileNameNoExtension}{fileType}')
  
  # Create parent directories if they don't exist 
  if not os.path.exists(fileDirectory) and fileDirectory != '':
    os.makedirs(fileDirectory)
  
  # Create archive directories if they don't exist 
  if not os.path.exists(archiveDirectory):
    os.makedirs(archiveDirectory)
  
  #Archive prior files
  if os.path.exists(fileDirectory):
    #Archive prior log file(s)  
    priorLogFiles = os.listdir(fileDirectory)
    for f in priorLogFiles:
      #If the filename begins with fileName and ends with fileType, then move it to the archive folder
      if f.startswith(fileName) and f.endswith(fileType):
        shutil.move(os.path.join(fileDirectory, f), os.path.join(archiveDirectory, f))
      
  # Create the new log file if it doesn't exist
  if not os.path.exists(completeFilePath):
    open(completeFilePath, 'w').close()
    #print(f'Created new file at {FilePath}')
      
  else:
    print(f'Skipping archive of file {fileName}.')
    
  return completeFilePath


def get_model_entity_definition(model_name, table_name=None):
    try:
        with open(model_file_path) as json_file:
            models = json.load(json_file)
        
        entities = models['models'][model_name]['entities']
        if table_name:
            return entities[table_name]['attributes']
        else:
            return entities
    except Exception as e:
        print(f"Error in get_model_definition. Value of modelname/tablename is: {model_name}/{table_name} \n Error below:")
        print(e)
        return False



def create_standardized_transactions_file():
  
  #Create the log file_paths
  # #The log where we shall put important things that happened
  logFile = os.path.join(PE_IO_DIRECTORY, 'Logs', 'Log.txt')
  CreateFileAndFolderPath(logFile)

  #<< This is the model for the transactions table in the database  
  entity = get_model_entity_definition('outercircles', 'transaction')
  transaction_fields = []
  for attribute_dict in entity:
    transaction_fields.append(list(attribute_dict.keys())[0])
  
  #This is the main consolidated and normalized output file
  outputTransactionsCSV = os.path.join(PE_IO_DIRECTORY, "Output", 'standardized.csv' )#<< This is the output file that will be created. All of the transactions will be in MY standard model format
  CreateFileAndFolderPath(outputTransactionsCSV) 
  open(outputTransactionsCSV, 'w').close() #Makes sure the file is empty to start
  with open(outputTransactionsCSV, 'a') as f:
    writer = csv.DictWriter(f, fieldnames=transaction_fields)
    writer.writeheader() # Populate the header row
    
  #This is where we put records that fell out of the process and were not put into the standardized file.
  skippedTransactionsCSV = os.path.join(PE_IO_DIRECTORY, "Output", 'skipped.csv' )#<< This is the output file that will be created. All of the transactions will be in MY standard model format
  CreateFileAndFolderPath(skippedTransactionsCSV) 
  open(skippedTransactionsCSV, 'w').close() #Makes sure the file is empty to start
  with open(skippedTransactionsCSV, 'a') as f:
    writer = csv.DictWriter(f, fieldnames=transaction_fields)
    writer.writeheader() # Populate the header row

  
  #Get the FullVocab Set 
  #Note this is a static file that is created by the pVocabCategiry.py script
  # Open the file and read its content
  
  with open(fullVocabFilePath, 'r') as f:
    content = f.read()
    content = content.replace('{', '').replace('}', '').replace("'", '').replace('\n', '').replace(' ', '') #Remove unnecessary characters
    content_list = content.split(',')
    # Convert the list into a set
    full_vocab = set(content_list)
  
  #Load up the category map
  categories = getCategories(categoryMapFile)

  open(categoryGaps, 'w').close() #Makes sure the file is empty to start
  open(categoryGapsByWord, 'w').close() #Makes sure the file is empty to start

  #This gets all the CSV and TXT files from the Transactions directory
  file_paths = get_file_paths('transaction-files/')
    
  #Now we process each file and standardize it and output it to the output file
  for inputTransactionFile in file_paths:
      
    # # Read CSV and get type
    with open(inputTransactionFile, 'r', encoding='utf-8-sig') as f: #<< This is loading the transactions from the input file
      reader = csv.reader(f)
      headers = next(reader)
      TotalRecords = len(list(reader))
      # Get field mappings for this type
      # I decided that I think it is safe to unqiue define each input CSV type as the concatenation of the first two columns
      # I know this to be different for Chase, Apple,  RocketMoney and American Express
      csv_type = headers[0] + ',' + headers[1]
      
    mappings = typeMap.get(csv_type)

    # Initialize output list
    outputs = []
    skips = []

    #These fields are used to print the progress of the script
    StartTime = datetime.now()
    CurrentRecord = 0     

    # Create a set to hold the unique values for each column
    #! FIX ME REACTIVATE THIS
    Tran_Bus_Key_Set = set() #!!<< Remove this line, reactivate the code below and remove the line after that
    # current_business_keys = sql.getDISTINCTValue(tablename='transaction', fieldname='txtUniqueBusinessKey')
    # if isinstance(current_business_keys, bool):
    #     Tran_Bus_Key_Set = set()
    # else:  
    #     Tran_Bus_Key_Set =  set(result[0] for result in current_business_keys)
    
    #Create an empty dictionary to store the normalized transaction field data for each row
    empty_output = {}
    for attribute_dict in entity:
      empty_output.update(attribute_dict)

  
    # Read data from the CSV and normalize it so it can be in the same format as all the other files.
    #Look in the table Definitions file to see the model for each file type
    with open(inputTransactionFile, 'r', encoding='utf-8-sig') as f:   
      reader = csv.reader(f)
      next(reader) # Skip header row

      for row in reader:
        row = [field.replace('\r', ' ') for field in row]
        row = [field.replace('\n', ' ') for field in row]

        output = empty_output.copy()
        
        # Get current row index number of the row of the CSV file in reader
        CurrentRecord = CurrentRecord + 1    
                
        if output['fltAmount'] == None or output['fltAmount'] == '':
          output['fltAmount'] = 0
        
        # Apply mappings 
        for key, value in mappings.items():
          if '||HARDCODE->' in value:  # Check if the value contains 'Hardcoded Value'
            output[key] = value.replace('||HARDCODE->', '')  # Replace 'Hardcoded Value' with an empty string
          else:
            try:
              output[key] = row[headers.index(value)]
            except (ValueError, IndexError):
              continue #This means there may be a corrupt row or an emepty row.
        
        # Set Ignore field 
        if output['txtIgnore']:
          output['txtIgnore'] = 0
          
        # Set TaxDeductible field
        if output['txtTaxDeductible']:
          output['txtTaxDeductible'] = 1
        
        output['txtTransactionOriginalNameClean'] = cleanUpText(output['txtTransactionOriginalName'].lower(), full_vocab).upper() 
        output['txtTranName'] = cleanUpText(output['txtTranNameOrig'].lower(), full_vocab).upper()  
        
        newCategory = getCatoryForTransaction(categories, output)
        output['txtCategory'] = newCategory  
        
        #Label the category if it is a small charge
        if output['fltAmount'] != '' and output['fltAmount'] != None and output['txtCategory'] == '' and  abs(float(output['fltAmount']) < 20):
        #if output['txtCategory'] == '' and  float(output['fltAmount']) < 0:
          output['txtCategory'] = '#Small Charge'
        
        #Label the category if it is a Check
        if output['txtCategory'] == '' and output['txtTransactionOriginalNameClean'].lower().find('check') != -1:
          output['txtCategory'] = '#Check'
        
        # Parse dates
        date_formats = ['%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%m-%d-%Y', '%d.%m.%Y', '%Y%m%d']

        transactionDate = output['datTransactionDate']
        parsed_transactionDate = None
        for fmt in date_formats:
            try:
                parsed_transactionDate = datetime.strptime(transactionDate, fmt)
                break
            except ValueError:
                pass  
        output['datTransactionDate'] = parsed_transactionDate
        output['fltCashFlowMultiplier'] = 1

        if output['fltAmount'] == None or output['fltAmount'] == '' or output['fltAmount'] == 0 or parsed_transactionDate == None :
          skips.append(output)
        else:
          #Assign Key
          output['txtUniqueBusinessKey'] = round(((abs(float(output['fltAmount'])) * parsed_transactionDate.timestamp()) + parsed_transactionDate.timestamp() ) * 10000)
          # Add to output
          if output['txtUniqueBusinessKey'] in Tran_Bus_Key_Set:
              skips.append(output)
          else:
              outputs.append(output)
              Tran_Bus_Key_Set.add(output['txtUniqueBusinessKey'])
        
        #Print Progress every 100 records
        if CurrentRecord / 100 == round(CurrentRecord /100):
          printProgress(StartTime, TotalRecords, CurrentRecord)
        
      ## Write CSV output 
      with open(outputTransactionsCSV, 'a') as f:
        writer = csv.DictWriter(f, fieldnames=transaction_fields)
        writer.writerows(outputs)
                
      with open(skippedTransactionsCSV, 'a') as f:
        writer = csv.DictWriter(f, fieldnames=transaction_fields)
        writer.writerows(skips)
        
    print(f'Processing complete! for {inputTransactionFile}')

def get_file_paths(directory):
    IO_Directory = os.environ.get('PERSONAL_EXPENSES_IO_FOLDER_PATH')
    directory_path = os.path.join(IO_Directory, directory)
    file_paths = [os.path.join(directory_path, file) for file in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, file)) and (file.endswith('.txt') or file.endswith('.csv'))]
    return file_paths

def getAllColumnDataFromFile(input_file_path, output_file_path, column_number, column_number2, skip_column_number, file_type, full_vocab):
    #Increase the CSV column size limit for this function 
    csv.field_size_limit(10485760)
    
    # Define delimiters for different file types
    delimiters = {'CSV': ',', 'PIPE': '|'}
    delimiter = delimiters[file_type]

    # Initialize an empty list to store the column values
    column_values = []

    # Open the input file
    with open(input_file_path, 'r') as input_file:
        # Create a CSV reader object with the appropriate delimiter
        reader = csv.reader(input_file, delimiter=delimiter)

        # Iterate over each row in the file
        for row in reader:
          textToCheck = ''
          skipCheckVal = ''
          if skip_column_number > 0 and skip_column_number < len(row):
            if row[skip_column_number]:
              skipCheckVal = row[skip_column_number]
            else:
              skipCheckVal = ''
          
          if skipCheckVal == '':  
            # Check if the column number is within the range of columns for this row
            if column_number < len(row):
                # If there is a value in the specified column, add it to the list
                if row[column_number]: 
                  textToCheck = row[column_number]
                          
            if column_number2 >0:
              if column_number2 < len(row):
                  # If there is a value in the specified column, add it to the list
                  if row[column_number2]: 
                    textToCheck = textToCheck+  " " + row[column_number]

            
            cleanValue = cleanUpText(textToCheck.lower(), full_vocab).lower()
            column_values.append(cleanValue)

    # Open the output file
    with open(output_file_path, 'w') as output_file:
        # Create a CSV writer object
        writer = csv.writer(output_file)

        # Write the column values to the output file
        for value in column_values:
            writer.writerow([value])
    return column_values

def tupleToString(varTuple):

  if isinstance(varTuple, tuple):
    returnVal = " ".join(varTuple)
  else: returnVal = varTuple
  
  if not isinstance(returnVal, str):
    try:
      returnVal = str(returnVal)
    except:
      print(f'Error: Issue with CategoryMap Value. {returnVal} is a {type(returnVal)} not a string')
      sys.exit()
  return returnVal

#! Function imports the category dictionary
def getCategories(categoryMapFile):
  categories = []
  with open(categoryMapFile) as f:  
    reader = csv.DictReader(f)
    for row in reader:
        pair = {}
        #pair['Category'] = tupleToString(row['Category'])
        #pair['TranNameCont'] = tupleToString(row['TranNameCont'])
        pair['Category'] = row['Category'].title()
        pair['TranNameCont'] = row['TransactionSubtring']
        pair['AmountIs'] = row.get('AmountIs')
        
        categories.append(pair)   
    return categories  ## This is the categories ... we will load it later (but only once)

def getCatoryForTransaction(categories, output): 
    ## This is the function that will be used to categorize the transactions
    ## It will be called for each transaction and will return the first category for that transaction that matches
    for category in categories:
        #if category['SearchTerm'].lower() in tran_name.lower():
        if checkTranMatch(output, category['TranNameCont'], category['AmountIs']):
            return category['Category'].lower()
    else:
        return ''

def stringContains(string, substring):
    #This function checks if a string contains a substring (with additional logic)
    #perform the test
    if substring != None:
      
      if isinstance(substring, tuple):
        substring = " ".join(substring)      
      #Check for bad description
      if string == None:
        return False

      #standardize case and search for match
      if substring.lower() in string.lower():
        return True
    
    #Passes the test as there is no criteria to test against
    else: 
      return True
  
def cleanUpText(text, full_vocab):
  #This function removes garbage from the transaction string by 
  # 1. Removing all non alpha numeric characters
  # 2. Removing all words that are not in the full vocab set
  # 3. Joining the words back together with a space
  words = re.findall(r"\w+", text)
  cleaned_words = []
  for word in words:
    if word in full_vocab:
        cleaned_words.append(word)
  cleaned_text = " ".join(cleaned_words)
  return cleaned_text

def checkTranMatch(output, trannameCont=None, amountIs=None, institutionCont=None, accounttypeCont=None, accountNameCont=None, accountNumCont=None):
  #This function checks if a transaction matches the criteria provided, and if it does, it is assigned the category provided by the parent function
  #Assume there is a mtach until a test proves otherwise
  tranMatches = True
  tranString = output['txtTranName'] + " " + output['txtTransactionOriginalNameClean']
  tranMatches = stringContains(tranString, trannameCont)
  if tranMatches: tranMatches = stringContains(output['txtInstitutionName'], institutionCont) 
  if tranMatches: tranMatches = stringContains(output['txtAccountType'], accounttypeCont) 
  if tranMatches: tranMatches = stringContains(output['txtAccountName'], accountNameCont) 
  if tranMatches: tranMatches = stringContains(output['txtAccountNumber'], accountNumCont)
  
  if tranMatches: 
    if amountIs == None or amountIs == '' or amountIs.strip() == '': #skip this test, no test value supplied
        return tranMatches
    
    else:  #Continue with test
      if output['fltAmount'] == None: #Bad Data
        return False
      
      else: 
        if float(output['fltAmount']) == float(amountIs):
          tranMatches = tranMatches
    
  else: return tranMatches #Some other test failed so we can return False

# Map of CSV types to field mappings
typeMap = {
  'Date,Original Date': { #Rocket Money#
    'txtFileSource': '||HARDCODE->ROCKETMONEY',
    'txtUniqueBusinessKey': '||Calculate->UniqueBusinessKey',
    'datTransactionDate': 'Date',
    # 'datOriginalTransactionDate': 'Original Date',
    'txtAccountType': 'Account Type',
    'txtAccountName': 'Account Name',
    'txtAccountNumber': 'Account Number',
    'txtInstitutionName': 'Institution Name',
    'txtTransactionOriginalName': 'Name',
    'txtTranNameOrig': 'Description',
    'fltAmount': 'Amount',
    'txtCategoryOld': 'Category',
    'txtNote': 'Note',
    'txtIgnore': 'Ignored From',
    'txtTaxDeductible': 'Tax Deductible'
  },
  
  'Date,Description': { #AMEX#
    'txtFileSource': '||HARDCODE->AMEX',
    'txtUniqueBusinessKey': '||Calculate->UniqueBusinessKey',
    'datTransactionDate': 'Date',
    # 'txtUniqueBusinessKey': '',
    'txtInstitutionTransactionId': 'Reference',
    # 'datOriginalTransactionDate': '',  
    # 'txtAccountType': '',
    'txtAccountName': 'Card Member',
    'txtAccountNumber': 'Account #',
    # 'txtInstitutionName': '',
    # 'txtMerchantName': '',
    # 'txtMerchantCategory': '',
     'txtMerchantStreetAddress': 'Address',
     'txtMerchantCity': 'City/State',
    # 'txtMerchantState': '',
    'txtMerchantZip': 'Zip Code',
    'txtMerchantCountry': 'Country',
    # 'txtTransactionOriginalName': '',
    # 'txtTransactionOriginalNameClean': '',
    # 'txtTranNameOrig': '',
    'txtTranName': 'Description',
    'txtTranName2': 'Appears On Your Statement As',
    'fltAmount': 'Amount',
    # 'txtCategory': '',
    # 'fltCashFlowMultiplier': '', 
    'txtCategoryOld': 'Category',
    'txtNote': 'Extended Details',
    # 'txtIgnore': '',
    # 'txtTaxDeductible': ''
  },
  
  'Transaction Date,Clearing Date': { #Apple#
    'txtFileSource': '||HARDCODE->AppleCard',
    'txtUniqueBusinessKey': '||Calculate->UniqueBusinessKey',
    'datTransactionDate': 'Transaction Date',
    # 'txtUniqueBusinessKey': '',
    # 'txtInstitutionTransactionId': '',
    # 'datOriginalTransactionDate': '',  
    # 'txtAccountType': '',
    'txtAccountName': 'Purchased By',
    # 'txtAccountNumber': '',
    # 'txtInstitutionName': '',
    'txtMerchantName': 'Merchant',
    # 'txtMerchantCategory': '',
    # 'txtMerchantStreetAddress': '',
    # 'txtMerchantCity': '',
    # 'txtMerchantState': '',
    # 'txtMerchantZip': '',
    # 'txtMerchantCountry': '',
    # 'txtTransactionOriginalName': '',
    # 'txtTransactionOriginalNameClean': '',
    # 'txtTranNameOrig': '',
    'txtTranName': 'Description',
    # 'txtTranName2': '',
    'fltAmount': 'Amount (USD)',
    'txtTransactionType': 'Type',
    # 'txtCategory': '',
    # 'fltCashFlowMultiplier': '', 
    'txtCategoryOld': 'Category',
    # 'txtNote': '',
    # 'txtIgnore': '',
    # 'txtTaxDeductible': ''
  },
  
  'Trade Date,Post Date': { #CHASE# 
    'txtFileSource': '||HARDCODE->CHASE',
    'txtUniqueBusinessKey': '||Calculate->UniqueBusinessKey',
    'datTransactionDate': 'Trade Date',
    # 'txtUniqueBusinessKey': '',
    # 'txtInstitutionTransactionId': '',
    # 'datOriginalTransactionDate': '',  
    'txtAccountType': 'Account Type',
    'txtAccountName': 'Account Name',
    'txtAccountNumber': 'Account Number',
    # 'txtInstitutionName': '',
    # 'txtMerchantName': '',
    # 'txtMerchantCategory': '',
    # 'txtMerchantStreetAddress': '',
    # 'txtMerchantCity': '',
    # 'txtMerchantState': '',
    # 'txtMerchantZip': '',
    # 'txtMerchantCountry': '',
    # 'txtTransactionOriginalName': '',
    # 'txtTransactionOriginalNameClean': '',
    # 'txtTranNameOrig': '',
    'txtTranName': 'Description',
    'txtTranName2': 'Tran Code Description',
    'fltAmount': 'Amount USD',
    'txtTransactionType': 'Type',
    # 'txtCategory': '',
    # 'fltCashFlowMultiplier': '', 
    'txtCheckNumber': 'Check Number',
    # 'txtCategoryOld': '',
    # 'txtNote': '',
    # 'txtIgnore': '',
    # 'txtTaxDeductible': ''
        }
}

if __name__ == "__main__":
    
    #!Recreate all tables (We are in start over mode on each run)
    # sql.DELETE_ALL_TABLES()
    # create_table_statements = generate_model_for_database('models.json', 'outercircles', 'postgresql')
    # for statement in create_table_statements:
    #     sql.execute_sql(statement)
    
    #Process the business logic (main function at the top of this file)
    #Looks through the transaction files and creates a standardized file
    #Detects duplicates so can be run anytime
    create_standardized_transactions_file() 



    print("Personal Expense DB Load Completed")



