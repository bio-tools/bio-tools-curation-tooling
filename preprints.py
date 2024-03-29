import requests
import json
import logging
from pathlib import Path

def load_tools_from_json(json_path):
    """Load tools from a JSON file."""
    try:
        with open(json_path, 'r') as file:
            return json.load(file)['list']
    except Exception as e:
        logging.error(f"Error loading JSON from {json_path}: {e}")
        return []


def save_tools_to_json(tools, json_path):
    """Save tools to a JSON file."""
    try:
        with open(json_path, 'w') as file:
            json.dump({"count": len(tools), "list": tools}, file, indent=4)
    except Exception as e:
        logging.error(f"Error saving tools to JSON {json_path}: {e}")


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


def query_for_potential_match(external_id: str, original_doi: str):
    """Query Europe PMC for a potential match based on external ID, excluding the original DOI."""
    query = f'ext_id:"{external_id}" NOT DOI:"{original_doi}"'
    response = search_europe_pmc(query)
    if response and response.get('hitCount', 0) > 0:
        return response['resultList']['result'][0]
    return None


def update_publication_with_match(original_publication, match):
    """Update the original publication information with data from the match if available."""
    return {
        'doi': match.get('doi', original_publication.get('doi', '')),
        'pmid': match.get('pmid', original_publication.get('pmid', '')),
        'pmcid': match.get('pmcid', original_publication.get('pmcid', ''))
    }


def is_preprint_from_response(response):
    if not response or 'resultList' not in response or not response['resultList']['result']:
        logging.error("Invalid response format.")
        return False, {}
    
    original_result = response['resultList']['result'][0]
    original_publication = original_result.get('publication', [{}])[0]
    commentCorrectionList = original_result.get('commentCorrectionList')

    if original_result.get('source') == 'PPR' and not commentCorrectionList:
        return True, original_result
    
    if commentCorrectionList:
        commentCorrection = commentCorrectionList.get('commentCorrection')[0]
        if commentCorrection.get('source') == 'PPR':
            return True, original_result
        
        external_id = commentCorrection.get('id')
        doi = original_publication.get('doi')
        match = query_for_potential_match(external_id, doi)

        if match:
            updated_publication = update_publication_with_match(original_publication, match)
            original_result['publication'] = [updated_publication]

    return False, original_result


def update_tool_with_publication(tool, is_preprint, publication_info):
    """Update the tool with publication information based on preprint status."""
    doi_url = f"https://doi.org/{tool['publication'][0]['doi']}"

    if is_preprint:
        tool['publication_link'] = doi_url
        tool['is_preprint'] = True
    else:
        tool['publication'] = [publication_info]
        tool['publication_link'] = f"https://doi.org/{publication_info[0]['doi']}"
        tool['is_preprint'] = False
  
    return tool


def identify_preprint(tool):
    """Identify if a tool's publication is a preprint and update its information."""
    if 'doi' not in tool['publication'][0]:
        print("No DOI found for this tool.")
        return None, False  # Assuming not a preprint if no DOI

    doi = tool['publication'][0]['doi']
    response = search_europe_pmc(doi)
    is_preprint, result = is_preprint_from_response(response)

    return update_tool_with_publication(tool, is_preprint, result.get('publication'))


def identify_preprints(rerun=True, tools=None, json_pub=None, json_prp=None):
    """Identify preprints from a list of tools and update their publication status."""
    if rerun:
        if not json_pub or not json_prp:
            raise ValueError("JSON file paths must be provided in rerun mode.")

        tools = load_tools_from_json(json_prp)
        publications = load_tools_from_json(json_pub)
        print(f"Loaded {len(tools)} preprints from {json_prp}.")
    else:
        publications = []

    if not tools:
        raise ValueError("No tools to process.")
    
    updated_tools = [identify_preprint(tool) for tool in tools]
    
    # Separate updated tools into preprints and publications
    preprints = [tool for tool in updated_tools if tool['is_preprint']]
    new_publications = [tool for tool in updated_tools if not tool['is_preprint']]
    
    print(f"There are {len(new_publications)} newly published tools. {len(preprints)} preprints remaining.")

    if rerun:
        publications.extend(new_publications)
        save_tools_to_json(publications, json_pub)
        save_tools_to_json(preprints, json_prp)
    else:
        pass

    return updated_tools