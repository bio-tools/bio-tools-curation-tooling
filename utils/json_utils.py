import os, logging, json

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


def generate_json(tools, file_date):
    output_dir = os.path.join(os.getcwd(), "data")
    os.makedirs(output_dir, exist_ok=True)
    output_name = f"low_tools_{file_date[0]}_{file_date[1]}"
    
    json_all_file_name = os.path.join(output_dir, f"{output_name}.json")
    save_tools_to_json(tools, json_all_file_name)

    print(f"JSON files generated in {output_dir}.")
