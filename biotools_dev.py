import requests
import logging
import json
import time

http_settings = {
    'host_prod':'https://bio-tools-dev.sdu.dk/api',
    'host_local':'http://localhost:8000/api',
    'host_dev':'https://bio-tools-dev.sdu.dk/api',
    'login': '/rest-auth/login/',
    'tool': '/t',
    'validate': '/validate',
    'json': '?format=json',
    'dev':'https://bio-tools-dev.sdu.dk/' 
}

def login_prod(username, password):
    headers_token = {
        'Content-Type': 'application/json'
        }
    user = json.dumps({
        'username': username,
        'password': password
    })

    token_r = requests.post(http_settings['host_prod'] + http_settings['login'] + http_settings['json'], headers = headers_token, data = user)
    logging.info(token_r)
    token = json.loads(token_r.text)['key']
    return token


def validate_tool(tool, token):
    '''Validate a tool using the Biotools API.'''
    url = '{h}{t}{v}{f}'.format(h=http_settings['host_prod'], 
                                t=http_settings['tool'],
                                v=http_settings['validate'],
                                f=http_settings['json'])   
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Token ' + token
    }
    r = requests.post(url, headers=headers, data=json.dumps(tool))
    if r.ok:
        return (True, r.text)
    return (False, r.text)


def insert_tool(tool, url, headers):
    response = requests.post(url, headers=headers, data=json.dumps(tool))
        
    if response.ok:
        print(f"{tool['biotoolsID']} Added {response.status_code}")
        return True, response.text

    print("An Error:",tool['biotoolsID'], response.text)
    return False, response.text


def add_tools(tools, token, WRITE_TO_DB=False):
    if not(WRITE_TO_DB):
        return
        
    url = '{h}{t}{f}'.format(h=http_settings['host_prod'], t=http_settings['tool'], f=http_settings['json'])
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {token}'
    }
    problem_tools = []
    ok_tools = 0
    for tool in tools:
        added, txt = insert_tool(tool, url, headers)
        if added:
            ok_tools += 1
        else:
            problem_tools.append({'tool_id': tool['biotoolsID'], 'error': txt})
        print('--------------')
        time.sleep(2)

            
    print("Total tools added: {added} out of a total of: {total} ".format(added=ok_tools, total=len(tools)))
    if problem_tools:
        print(f"{len(problem_tools)} tools with problems:")
        print(problem_tools)

    print("Finished adding tools")