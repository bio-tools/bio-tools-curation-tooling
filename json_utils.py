import os
from preprints import save_tools_to_json
from csv_utils import check_date

def generate_json(tools, separate_preprints=True):
    file_date = check_date(pub2tools_file)
    output_dir = f"process_scrap_{file_date[0]}_{file_date[1]}"
    os.makedirs(output_dir, exist_ok=True)

    base_file_name = f"low_tools_{file_date[0]}_{file_date[1]}"

    if separate_preprints:
        # Separate tools based on 'is_preprint' attribute
        preprints = [tool for tool in tools if tool['is_preprint']]
        publications = [tool for tool in tools if not tool['is_preprint']]

        # JSON for preprints
        json_prp_file_name = os.path.join(output_dir, f"{base_file_name}_prp.json")
        save_tools_to_json(preprints, json_prp_file_name)

        # JSON for publications
        json_pub_file_name = os.path.join(output_dir, f"{base_file_name}_pub.json")
        save_tools_to_json(publications, json_pub_file_name)

    else:
        # Generate a single JSON file for all tools
        json_all_file_name = os.path.join(output_dir, f"{base_file_name}.json")
        save_tools_to_json(tools, json_all_file_name)

    print(f"JSON files generated in {output_dir}.")
