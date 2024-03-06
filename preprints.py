from datetime import date
import requests
import json

# This function can be used for the first time on to_biotools.json output from Pub2tools
# as well as it can be rerun on the preprints json in the future to check for new publications
# if there are new publications in low_tools_prp_date.json file, they will be removed from this file
# and moved to the publications file


json_pub = '/work/Pub2tools/low_tools_pub_2023_10.json'     # For testing
json_prp = '/work/Pub2tools/low_tools_prp_2023_10.json'



def identify_preprints(rerun = True, tools = None, json_pub = None, json_prp= None):
    """
    This function is used to identify preprints in a list of tools and update their publication status based on their DOI or PMID. It can operate in two modes depending on the `rerun` parameter:

    Parameters:
    - rerun (bool): Indicates whether the function should operate in rerun mode (True) or not (False). Default is True.
    - tools (list): List of dictionaries representing tools. Required if rerun is False.
    - json_pub (str): Path to a JSON file containing a list of publications. Required if rerun is True.
    - json_prp (str): Path to a JSON file containing a list of preprints. Required if rerun is True.

    Returns:
    - list: Updated list of tools with their publication links and updated preprint flags.

    Functionality:
    1. If rerun is False:
    - Processes the list of tools provided, identifies preprints, updates their publication status, and returns the updated list.

    2. If rerun is True:
    - Loads the JSON files containing lists of publications and preprints.
    - Identifies preprints, updates their publication status, and writes the changes back to the JSON files.
    - Outputs the updated list of tools with their publication links and updated preprint flags.

    """
    if rerun == False:
        if tools is None:
            raise ValueError("Pass list of tools as input to function.")
        else:
            for tool in tools:
                url_pub,is_preprint=identify_preprint(tool)
                tool['publication_link']=url_pub
                tool['is_preprint']=is_preprint
    else:
        if json_pub is None and json_prp is None:
            raise ValueError("If you want to rerun, pass json with publications and preprints.")
        else:
            with open(json_pub, 'r') as publications_json_file:
                publications_json = json.load(publications_json_file)
            pubs = publications_json['list']
            with open(json_prp,'r') as preprint_json_file:
                preprints_json = json.load(preprint_json_file)
            tools = preprints_json['list']
            checked_before = all('is_preprint' in tool for tool in tools)
            if checked_before:
                number_of_pp=sum(1 for tool in tools if tool.get('is_preprint') == True)
                print("Preprints were already identified. There are {preprints} preprints in the file. Checking if something was published.....".format(preprints=number_of_pp))
            updated_pubs=[]
            for tool in tools:
                url_pub,is_preprint=identify_preprint(tool)
                tool['publication_link']=url_pub
                tool['is_preprint']=is_preprint
                if not is_preprint:
                    updated_pubs.append(tool)
        print(updated_pubs)
        print("Updating json.....")
        pubs.extend(updated_pubs)
        pub_json = {"count":len(pubs),"list":pubs}
        with open(json_pub, 'w') as publications_json_file:
            json.dump(pub_json, publications_json_file, indent=4)

        preprints_data = [preprint for preprint in tools if preprint not in updated_pubs]
        pp_json = {"count":len(preprints_data),"list":preprints_data}
        with open(json_prp, 'w') as preprints_json_file:
            json.dump(pp_json, preprints_json_file, indent=4)
    number_of_pp=sum(1 for tool in tools if tool.get('is_preprint') == True)
    print("There are {preprints} preprints in the file after identification".format(preprints=number_of_pp))
    return tools



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




def identify_preprint(tool):
    """
    Identify if a publication associated with a tool is a preprint.
    Args:
    - tool (dict): A dictionary containing tool metadata (Pub2Tools output).
    Returns:
    - pub_link (str): A link to the publication.
    - is_preprint (bool): True if the publication is a preprint, False otherwise.
    """
    if 'doi' in tool['publication'][0]:
        # Extract DOI from publication metadata if exists
        doi=tool['publication'][0]['doi']
        print(tool['name'])
        data = search_europe_pmc(f'DOI:"{doi}"')        
        if data.get('hitCount', 0) != 0:  # If DOI is found in Europe PMC database
            result=data['resultList']['result'] 
            if (result[0].get('source')=='PPR' and result[0].get('commentCorrectionList') is None): # Check if the source is PPR and there are no comment corrections
                is_preprint=True
                pub_link= f"https://doi.org/{doi}"
            elif (result[0].get('source')=='PPR' and result[0].get('commentCorrectionList') is not None): 
                if (result[0].get('commentCorrectionList').get('commentCorrection')[0].get('source')=='PPR'): # Check if the first comment correction source is PPR
                    is_preprint=True
                    pub_link= f"https://doi.org/{doi}"
                else:  # Extract external ID and search for potential match
                    ext_id=result[0].get('commentCorrectionList').get('commentCorrection')[0].get('id')
                    potential_match=search_europe_pmc(f'ext_id:"{ext_id}" NOT DOI:"{doi}"')
                    if potential_match or potential_match.get('hitCount', 0) != 0:
                        if ('doi' in potential_match['resultList']['result'][0].keys()):
                            new_doi=potential_match['resultList']['result'][0]['doi']
                            pub_link= f"https://doi.org/{new_doi}"
                            print("Tool {name} has a published version. Changing from {doi} to {new_doi} ".format(name=tool['name'], doi=doi, new_doi=new_doi))
                        else:  
                            pmid=potential_match['resultList']['result'][0]['pmid']
                            pub_link= f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" 
                            print("Tool {name} has a published version. Changing from {doi} to {pmid} ".format(name=tool['name'], doi=doi, pmid=pmid))                
                        is_preprint=False
                    else:  # If there is no match in a database (even though there is correction list), we can't say much about it
                        is_preprint=True
                        pub_link= f"https://doi.org/{doi}"
            else:   # Source is other than preprint, that's always publication (?)
                pub_link= f"https://doi.org/{doi}"
                is_preprint=False
                 
        else:  #No result in Europe PMC database
            pub_link= f"https://doi.org/{doi}"
            is_preprint=False  #Is it better to assume that this is preprint or not preprint? 
    else:
        print("There is no DOI for this tool")
        pmid=tool['publication'][0]['pmid']
        pub_link= f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" 
        # It can still be preprint, but it's safer to assume it's not and double-check it with curation.  
        is_preprint=False
    return pub_link, is_preprint


