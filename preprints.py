import logging
from utils.json_utils import load_tools_from_json, save_tools_to_json
from utils.utils import search_europe_pmc


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
    
    if is_preprint:
        doi_url = f"https://doi.org/{tool['publication'][0]['doi']}"
        tool['publication_link'] = doi_url
        tool['is_preprint'] = True
    else:
        if publication_info:
            tool['publication'] = publication_info
        if 'doi' in tool['publication'][0]:
            tool['publication_link'] = f"https://doi.org/{tool['publication'][0]['doi']}"
        else:
            tool['publication_link'] = f"https://pubmed.ncbi.nlm.nih.gov/{tool['publication'][0]['pmid']}"
        
        tool['is_preprint'] = False
  
    return tool


def identify_preprint(tool):
    """Identify if a tool's publication is a preprint and update its information."""
    if 'doi' not in tool['publication'][0]:
        print("No DOI found for this tool.")
        return update_tool_with_publication(tool, False, None)  # Assuming not a preprint if no DOI

    doi = tool['publication'][0]['doi']
    response = search_europe_pmc(doi)
    is_preprint, result = is_preprint_from_response(response)

    return update_tool_with_publication(tool, is_preprint, result.get('publication'))


def identify_preprints(rerun=True, tools=None, json_prp=None):
    """Identify preprints from a list of tools and update their publication status."""
    if rerun:
        if not json_prp:
            raise ValueError("JSON file paths must be provided in rerun mode.")
        if tools:
            raise ValueError("In rerun mode provide only path to preprints file.")
        tools = load_tools_from_json(json_prp)

    # Preprints file needed in both modes
    prp_tools = load_tools_from_json(json_prp)
    print(f"Loaded {len(prp_tools)} preprints from {json_prp}.")
    if not tools:
        raise ValueError("No tools to process.")
            
    updated_tools = [identify_preprint(tool) for tool in tools]
    
    preprints = [tool for tool in updated_tools if tool['is_preprint']]
    publications = [tool for tool in updated_tools if not tool['is_preprint']]
    

    if rerun:
        print(f"There are {len(publications)} newly published tools. {len(preprints)} preprints remaining.")
        save_tools_to_json(preprints,json_prp)
    else:
        print(f"There are {len(publications)} published tools and {len(preprints)} preprints.")
        prp_tools.extend(preprints)
        save_tools_to_json(prp_tools, json_prp)


    return publications