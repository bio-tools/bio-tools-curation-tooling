import re

def generate_biotoolsID(name):
    biotoolsID = re.sub('[^a-zA-Z0-9_~ .-]*', '',name)
    biotoolsID = re.sub('[ ]+','-', biotoolsID)
    biotoolsID = 'pub2tools2023__' + biotoolsID

    return biotoolsID.lower()


def process_tools(tools):
    high_tools = []

    for tool in tools:
        tool['editPermission'] = {'type': 'public'}
        tool['biotoolsID'] = generate_biotoolsID(tool['name'])

        if tool['confidence_flag'].lower() == 'high':
            #tool['date']= check_date(pub2tools_file)
            url = '{d}{bt}'.format(d='https://bio-tools-dev.sdu.dk/', bt=tool['biotoolsID'])
            tool['tool_link'] = url
            high_tools.append(tool)

    return high_tools