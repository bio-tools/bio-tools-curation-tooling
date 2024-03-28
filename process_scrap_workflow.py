import json, re, requests
from getpass import getpass
import sys
import os
import copy
import time
import csv
from datetime import date
from preprints_new import identify_preprints
from settings import http_settings, file_settings


WRITE_TO_DB = False
to_curate = 100 #how many of high_tools to write to csv file to be manually curated (int or str) ('all')

def login_prod(http_settings):
    headers_token = {
        'Content-Type': 'application/json'
        }
    user = json.dumps({
        'username': http_settings['username'],
        'password': http_settings['password']
    })

    token_r = requests.post(http_settings['host_prod'] + http_settings['login'] + http_settings['json'], headers=headers_token, data=user)
    token = json.loads(token_r.text)['key']
    return token

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

def validate_tools(tools, token, http_settings):
    tools_count = len(tools)
    to_add = []
    problem_tools = []    
    for tool in tools: 
        print(tool['confidence_flag'])
        (valid, txt) = validate_tool(tool, token, http_settings)
        #valid=True   #For testing
        if valid:  
            to_add.append(tool)            
            print("Tool with name {name} is valid.".format(name=tool['name']))
        else:
            print("Tool with name:{name} has the errors: {errors}".format(name=tool['name'],errors=txt))
            print('Checking if there is an error with the name {name} ... '.format(name=tool['name']))
            if (is_html_error(txt)):
                print("It's an html error message ... ")
            else:
                e = json.loads(txt)
                if type(e) is dict and e.get('name') != None:
                    print('There is an error with the name {name}'.format(name=tool['name']))
                    tool_temp = copy.deepcopy(tool)
                    tool_temp['name'] = tool_temp['name'] + '_autogenerated'
                    print('Trying to fix problem by changing tool name to {name}'.format(name=tool_temp['name']))
                    (valid, txt) = validate_tool(tool_temp, token, http_settings)
                    if valid:
                        print('The error was fixed by changing the name to {name}'.format(name=tool_temp['name']))
                        tool['name'] = tool_temp['name']
                        to_add.append(tool)            
                    else:
                        print('The error could not be fixed')
                        problem_tools.append({'tool_name':tool['name'],'error':txt})
                else:
                    print('There was a different error')
                    problem_tools.append({'tool_name':tool['name'],'error':txt})
        print('-----------------')       
    print("Total tools validated: {added} out of a total of: {total} ".format(added=len(to_add), total=tools_count))
    if len(problem_tools) > 0:
        print("{problem} tools with problems:".format(problem=len(problem_tools)))
        print(problem_tools)
    else:
        print("No tools with problems")
    return to_add


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
    
        


def generate_json(tools, separate_preprints= True):
    file_date=check_date(pub2tools_file)  #function to return date
    output_dir='process_scrap_{year}_{month}'.format(year=file_date[0],month=file_date[1])
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if separate_preprints:
        json_prp='low_tools_prp_{year}_{month}.json'.format(year=file_date[0],month=file_date[1]) #name .json file
        preprints=[tool for tool in tools if tool['is_preprint'] == True]
        json_dat_prp={"count":len(preprints),"list":preprints}
        with open(os.path.join(output_dir,json_prp), 'w') as json_f_prp:
            json.dump(json_dat_prp, json_f_prp, indent=4)
        json_pub='low_tools_pub_{year}_{month}.json'.format(year=file_date[0],month=file_date[1]) #name .json file
        pubs=[tool for tool in  tools if tool['is_preprint'] == False]
        json_dat_pub={"count":len(pubs),"list":pubs}
        with open(os.path.join(output_dir,json_pub), 'w') as json_f_pub:
            json.dump(json_dat_pub, json_f_pub, indent=4)
    else:
        json_all='low_tools_{year}_{month}.json'.format(year=file_date[0],month=file_date[1]) #name .json file
        json_dat_all={"count":len(tools),"list":tools}
        with open(os.path.join(output_dir,json_all), 'w') as json_f_all:
            json.dump(json_dat_all, json_f_all, indent=4)




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
        
            biotoolsID = re.sub('[^a-zA-Z0-9_~ .-]*', '',tool['name'])
            biotoolsID = re.sub('[ ]+','-', biotoolsID)
            biotoolsID = 'pub2tools2023__' + biotoolsID
            tool['biotoolsID'] = biotoolsID.lower()

            if tool['confidence_flag'].lower() == 'high':
                #tool['date']= check_date(pub2tools_file)
                url_d='{d}{bt}'.format(d=http_settings['dev'],bt=tool['biotoolsID'])  #create tool_link
                tool['tool_link']=url_d
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


def check_date(pub2tools_file):     #function to generate date
    log_file=open(pub2tools_file,'r')
    textfile=log_file.read()
    log_file.close()
    date=re.findall("--month (\d+)-(\d+)",textfile)  #from command for pub2tools
    return date[0] 
    


def search_europe_pmc(query):
    """Search Europe PMC and return the JSON response."""
    api_endpoint = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {
        'query': query,
        'format': 'json',
        'resultType': 'core'
    }
    response = requests.get(api_endpoint, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

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
tools_to_add, tools_left = generate_csv_pub(tools_prp,to_curate) #STEP 5. GENERATE CSV FROM TO_CURATE FIRST PUBLICATIONS. Alternative function - generate_csv_prp will use TO_CURATE first publications and identified preprints (that might be useful in case of coming back to old curation schema (curating all validated tools))
generate_json(tools_left)                                        # STEP 6. GEENRATE TWO JSON FILES FROM TOOLS THAT WON'T BE CURATED. (leftover tools = all tools - to_curate tools). Generates file with preprints and file with publications. File with preprints can be used as input to identify_preprints later. 
add_tools(tools_to_add, token, http_settings, WRITE_TO_DB)       # STEP 7. ADD TO_CURATE TOOLS TO DEV
