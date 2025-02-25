import json

def load_metadata(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)