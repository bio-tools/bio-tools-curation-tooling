import json, re, requests
from getpass import getpass
import sys
import os
import copy
import time
import csv
from pathlib import Path
from datetime import date
from preprints_new import identify_preprints
from settings import http_settings, file_settings

# Settings
# @WRITE_TO_DB - flag to write tools to the database (bool)
# @num_to_curate - number of high_tools to write to csv file to be manually curated (int or str) ('all')
WRITE_TO_DB = False
num_to_curate = 100

# Authentication

def login_prod(http_settings):
    headers_token = {
        'Content-Type': 'application/json'
        }
    user = json.dumps({
        'username': http_settings['username'],
        'password': http_settings['password']
    })

    token_r = requests.post(http_settings['host_prod'] + http_settings['login'] + http_settings['json'], headers = headers_token, data = user)
    token = json.loads(token_r.text)['key']
    return token

# Validation

def validate_tool(tool, token, http_settings):
    url = '{h}{t}{v}{f}'.format(h=http_settings['host_prod'], t=http_settings['tool'],v=http_settings['validate'], f=http_settings['json'])   
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Token ' + token
    }

    r = requests.post(url, headers=headers, data=json.dumps(tool))
    if r.status_code >= 200 and r.status_code <= 299:
        return (True, r.text)
    return (False, r.text)

def validate_tool_2(tool, url, headers):
    response = requests.post(url, headers=headers, data=json.dumps(tool))
    return response.ok, response.text

def attempt_fix_tool(tool, token, url, headers):
    tool_temp = copy.deepcopy(tool)
    tool_temp['name'] = tool_temp['name'] + '_autogenerated'
    print('Trying to fix problem by changing tool name to {name}'.format(name=tool_temp['name']))
    valid, txt = validate_tool_2(tool_temp, url, headers)
    if valid:
        print('Error fixed by changing the name to {name}'.format(name=tool_temp['name']))
        tool['name'] = tool_temp['name']
        return True, tool
    else:
        print('Error could not be fixed')
        return False, {'tool_name': tool['name'], 'error': txt}

def validate_tools_2(tools, token, http_settings):
    url = f"{http_settings['host_prod']}{http_settings['tool']}{http_settings['validate']}{http_settings['json']}"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {token}'
    }
    
    to_add, problem_tools = [], []

    for tool in tools:
        valid, txt = validate_tool_2(tool, url, headers)
        if valid:
            to_add.append(tool)
        else:
            print(f"Tool with name:{tool['name']} has the errors: {txt}")
            print(f"Checking if there is an error with the name {tool['name']} ... ")
            try:
                e = json.loads(txt)
                if isinstance(e, dict) and e.get('name') is not None:
                    valid, result = attempt_fix_tool(tool, token, url, headers)
                    if valid:
                        to_add.append(tool)
                    else:
                        problem_tools.append(result)
                else:
                    problem_tools.append({'tool_name': tool['name'], 'error': txt})
            except json.JSONDecodeError:
                print("Error parsing JSON from the response.")
                problem_tools.append({'tool_name': tool['name'], 'error': 'Invalid JSON response'})

    print(f"Total tools validated: {len(to_add)} out of a total of: {len(tools)}")
    if problem_tools:
        print(f"{len(problem_tools)} tools with problems: {problem_tools}")
    else:
        print("No tools with problems")
    return to_add, problem_tools


def generate_csv_pre(val_tools, to_curate):
    preprints = []
    publications = []
    if to_curate=='all':
        for tool in tools:
            if tool['is_preprint']:
                preprints.append(tool)
            else:
                publications.append(tool)
    else:
        for tool in tools[:to_curate]:
            if tool['is_preprint']:
                preprints.append(tool)
            else:
                publications.append(tool)        
    file_date=check_date(pub2tools_file)  #function to return date
    file_name='pub2tools_{year}_{month}.csv'.format(year=file_date[0],month=file_date[1]) #name .csv file
    print(" Writing {to_curate} files which is {pubs} publications and {pre} preprints to a {filename} ".format(to_curate=to_curate,pubs=len(publications), pre=len(preprints), filename=file_name))
    with open(file_name,'w') as fileobj: #write to .csv file
        writerobj=csv.writer(fileobj)
        writerobj.writerow(['tool_link','tool_name','homepage','publication_link'])
        for tool in publications:
            writerobj.writerow([tool['tool_link'],tool['name'],tool['homepage'],tool['publication_link']])
        writerobj.writerow(['PREPRINTS'])
        for tool in preprints:
            writerobj.writerow([tool['tool_link'],tool['name'],tool['homepage'],tool['publication_link']])
    leftover_tools=[tool for tool in tools if tool not in publications and tool not in preprints]
    tools_to_add=preprints+publications
    return tools_to_add, leftover_tools

def generate_csv_pub(tools,to_curate):
    publications = []
    if to_curate=='all':
        for tool in tools:
            if not tool['is_preprint']:
                publications.append(tool)
    else:
        counter = 0
        for tool in tools:
            if not tool['is_preprint']:
                publications.append(tool)
                counter += 1
                if counter == to_curate:
                    break
    file_date=check_date(pub2tools_file)  #function to return date
    file_name='pub2tools_{year}_{month}.csv'.format(year=file_date[0],month=file_date[1]) #name .csv file
    print(" Writing {to_curate} files which is {pubs} publications to a {filename} ".format(to_curate=to_curate, pubs=len(publications), filename=file_name))
    with open(file_name,'w') as fileobj: #write to .csv file
        writerobj=csv.writer(fileobj)
        writerobj.writerow(['tool_link','tool_name','homepage','publication_link'])
        for tool in publications:
            writerobj.writerow([tool['tool_link'],tool['name'],tool['homepage'],tool['publication_link']])
    leftover_tools=[tool for tool in tools if tool not in publications]
    tools_to_add=publications
    return tools_to_add, leftover_tools
    

# Write json files
def check_date(pub2tools_file):
    log_file = open(pub2tools_file,'r')
    textfile = log_file.read()
    log_file.close()
    date = re.findall("--month (\d+)-(\d+)", textfile)
    return date[0] 

def write_json(data, file_path):
    """Helper function to write data to a JSON file."""
    with file_path.open('w') as json_file:
        json.dump(data, json_file, indent=4)

def generate_json(tools, separate_preprints= True):
    file_date = check_date(pub2tools_file)
    output_dir = Path(f'process_scrap_{file_date[0]}_{file_date[1]}')
    output_dir.mkdir(exist_ok=True)

    if separate_preprints:
        preprints = [tool for tool in tools if tool['is_preprint']]
        pubs = [tool for tool in tools if not tool['is_preprint']]

        preprints_file = output_dir / f'preprints_{file_date[0]}_{file_date[1]}.json'
        write_json({"count": len(preprints), "list": preprints}, preprints_file)

        pubs_file = output_dir / f'low_tools_pub_{file_date[0]}_{file_date[1]}.json'
        write_json({"count": len(pubs), "list": pubs}, pubs_file)
    else:
        all_tools_file = output_dir / f'low_tools_{file_date[0]}_{file_date[1]}.json'
        write_json({"count": len(tools), "list": tools}, all_tools_file)



def add_tools(tools, token, http_settings, WRITE_TO_DB):
    print(WRITE_TO_DB)
    if not(WRITE_TO_DB):
        print("Write flag is False, exiting...")
        return    
    url = '{h}{t}{f}'.format(h=http_settings['host_prod'], t=http_settings['tool'], f=http_settings['json'])
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Token ' + token
    }
    tools_count = len(tools)
    problem_tools = []
    ok_tools = 0
    for tool in tools:
        r = requests.post(url, headers=headers, data=json.dumps(tool))
        
        if r.status_code >= 200 and r.status_code <= 299:
            print(tool['biotoolsID'], 'Added', r.status_code)
            ok_tools += 1
        else:
            print("An Error:",tool['biotoolsID'], r.text)
            problem_tools.append({'tool_id':tool['biotoolsID'],'error':r.text})
        print('--------------')
        time.sleep(2)

            
    print("Total tools added: {added} out of a total of: {total} ".format(added=ok_tools, total=tools_count))
    if len(problem_tools) > 0:
        print("{problem} tools with problems:".format(problem=len(problem_tools)))
        print(problem_tools)
    else:
        print("No tools with problems")

def process_tools(json_file):
    high_tools = []
    with open(json_file) as jf:
        data = json.load(jf)
        tools = data['list']
        for tool in tools:
        #    tool['confidence_flag'] = confidence_dict[tool['name']].replace('_',' ')
            tool['editPermission'] = {'type': 'public'}
        
            biotoolsID = re.sub('[^a-zA-Z0-9_~ .-]*', '', tool['name'])
            biotoolsID = re.sub('[ ]+','-', biotoolsID)
            biotoolsID = 'pub2tools2023__' + biotoolsID
            tool['biotoolsID'] = biotoolsID.lower()

            if tool['confidence_flag'].lower() == 'high':
                #tool['date']= check_date(pub2tools_file)
                url_d = '{d}{bt}'.format(d = http_settings['dev'], bt = tool['biotoolsID'])  # Create tool_link
                tool['tool_link'] = url_d
                high_tools.append(tool)
    return high_tools
        
def fix_name_errors(tools, errors):
    if len(errors) == 0:
        return tools    
    for error in errors:
        if error.get('name') != None:
            error_name = error['name']
            for tool in tools:
                if tool['name'] == error_name:
                    print('changing', tool['name'], ' to::', tool['name'] + '_autogenerated')
                    break



###    
def check_if_name_exists(tool_name):
    url_get='{h}{t}{f}'.format(h=http_settings['host_prod'], t=http_settings['tool'], f=http_settings['json'])
    tool_data=requests.get(url_get+ f"&name='{tool_name}'").json()
    if (tool_data['count']!=0):
        print("Tool with this name already exists")
        return False
    else:
        return True  

def is_html_error(message):
    return '<html' in message.lower() or '<body' in message.lower()  

###

if len(sys.argv) != 2:
    print ("Usage: python process_scraped.py <path_to_pub2tools_output_folder>")
    quit()

root_dir = sys.argv[1]
if not os.path.exists(root_dir):
    print("path to pub2tools output folder does not exist")
    quit()


json_file = (root_dir + '/' + file_settings['json_tools']).replace('//', '/')
if not(os.path.exists(json_file) and os.path.isfile(json_file)):
    print("can't find json tools file")
    quit()

pub2tools_file=(root_dir + '/' + file_settings['pub2tools_log']).replace('//', '/')  #check if log file exists in output folder
if not(os.path.exists(pub2tools_file) and os.path.isfile(pub2tools_file)):
    print("can't find pub2tools log file")
    quit()

tools = process_tools(json_file)                        # STEP 1. READ PUB2TOOLS OUTPUT JSON FILE
token = login_prod(http_settings)                       # STEP 2. GET TOKEN
#tools_v = validate_tools(tools, token, http_settings)   # STEP 3. VALIDATE TOOLS FROM PUB2TOOLS OUTPUT
tools_prp = identify_preprints(rerun = False, tools = tools)    #STEP 4. FROM THOSE VALIDATED, IDENTIFY PREPRINTS. RERUN = FALSE - it's first time we add "is_preprint" flag. More about it in preprints.py file.
tools_to_add, tools_left = generate_csv_pub(tools_prp,num_to_curate) #STEP 5. GENERATE CSV FROM TO_CURATE FIRST PUBLICATIONS. Alternative function - generate_csv_prp will use TO_CURATE first publications and identified preprints (that might be useful in case of coming back to old curation schema (curating all validated tools))
generate_json(tools_left)                                        # STEP 6. GEENRATE TWO JSON FILES FROM TOOLS THAT WON'T BE CURATED. (leftover tools = all tools - to_curate tools). Generates file with preprints and file with publications. File with preprints can be used as input to identify_preprints later. 
add_tools(tools_to_add, token, http_settings, WRITE_TO_DB)       # STEP 7. ADD TO_CURATE TOOLS TO DEV
