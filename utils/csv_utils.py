import csv


def filter_tools(tools, to_curate, filter_condition=lambda x: True):
    """Filters tools based on a condition and curate limit."""
    filtered_tools = [tool for tool in tools if filter_condition(tool)]
    if to_curate != 'all':
        filtered_tools = filtered_tools[:int(to_curate)]
    return filtered_tools


def generate_file_name(prefix, file_date):
    """Generates a file name based on a prefix and a date tuple."""
    year, month = file_date[0], file_date[1]
    return f"{prefix}_{year}_{month}.csv"


def generate_csv(tools, to_curate, file_date, include_preprints=True):
    """Generates a CSV file for tools, separating or including preprints based on parameters."""
    file_name = generate_file_name('pub2tools', file_date)
    
    # Filter tools based on 'is_preprint' and 'to_curate'
    publications = filter_tools(tools, to_curate, lambda x: not x['is_preprint'])
    preprints = []

    if include_preprints:
        preprints = filter_tools(tools, to_curate, lambda x: x['is_preprint'])

    print(f"Writing {to_curate} files: {len(publications)} publications and {len(preprints)} preprints to {file_name}")
    
    # Combine lists if including preprints, else just use publications
    combined_tools = publications + (['PREPRINTS'] if preprints else []) + preprints
    
    # Write to CSV, handle 'PREPRINTS' marker
    with open(file_name, 'w', newline='') as fileobj:
        writerobj = csv.writer(fileobj)
        writerobj.writerow(['tool_link', 'tool_name', 'homepage', 'publication_link'])
        for tool in combined_tools:
            if tool == 'PREPRINTS':
                writerobj.writerow([tool])
            else:
                writerobj.writerow([tool['tool_link'], tool['name'], tool['homepage'], tool['publication_link']])
    
    leftover_tools = [tool for tool in tools if tool not in publications and tool not in preprints]
    return publications + preprints, leftover_tools
