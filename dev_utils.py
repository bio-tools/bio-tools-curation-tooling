import requests
import json
import time

def insert_tool(tool, url, headers):
    response = requests.post(url, headers=headers, data=json.dumps(tool))
        
    if response.ok:
        print(f'{tool['biotoolsID']} Added {response.status_code}')
        return True, response.text

    print("An Error:",tool['biotoolsID'], response.text)
    return False, response.text


def add_tools(tools, token, http_settings, WRITE_TO_DB=False):
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