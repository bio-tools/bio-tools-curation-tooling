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


def generate_csv(pub_tools, pub_preprints, to_curate, file_date):
    """Generates a CSV file for published tools and newly published preprints."""
    file_name = generate_file_name('pub2tools', file_date)
    tu_curate_tools = filter_tools(pub_tools, to_curate)
    # Use to_curate publications and previously identified preprints
    combined_tools = to_curate_tools + pub_preprints    
    # Write to CSV
    with open(file_name, 'w', newline='') as fileobj:
        writerobj = csv.writer(fileobj)
        writerobj.writerow(['tool_link', 'tool_name', 'homepage', 'publication_link'])
        for tool in combined_tools[:to_curate]:
            writerobj.writerow([tool['tool_link'], tool['name'], tool['homepage'], tool['publication_link']])
        writerobj.writerow(['NEWLY PUBLISHED PREPRINTS'])
        for tool in combined_tools[to_curate:]:
            writerobj.writerow([tool['tool_link'], tool['name'], tool['homepage'], tool['publication_link']])
    
    leftover_tools = [tool for tool in tools if tool not in combined_tools]
    return combined_tools, leftover_tools

