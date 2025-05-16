import json
from collections import defaultdict

def extract_sensors_objects(json_data):
    # Parse JSON data if it's a string, otherwise assume it's already a dict
    if isinstance(json_data, str):
        data = json.load(json_data)
    else:
        data = json_data
    
    # Initialize a dictionary to store objects by timestamp
    result = defaultdict(list)
    
    # Iterate through each entry in the JSON data
    for entry in data:
        timestamp = entry.get('timestamp', 0)  # Default to 0 if timestamp is missing
        objects = entry.get('result', [])
        
        # Add each object to the corresponding timestamp
        for obj in objects:
            result[timestamp].append(obj)
    
    return dict(result)

def extract_steps_objects(json_data):
    # Parse JSON data if it's a string, otherwise assume it's already a dict
    if isinstance(json_data, str):
        data = json.load(json_data)
    else:
        data = json_data
    
    # Initialize a dictionary to store objects by obj_id and timestamp
    result = defaultdict(dict)
    
    # Iterate through each entry in the JSON data
    for entry in data:
        timestamp = entry.get('timestamp', 0)  # Default to 0 if timestamp is missing
        obj_id = entry.get('obj_id')
        result_data = entry.get('result', {})
        
        if obj_id is not None:
            result[obj_id][timestamp] = result_data
    
    return dict(result)

def update_objects_with_scenario_info(timestamp_objects, scenario_data):
    # Create a mapping of obj_id to flattened fields
    scenario_map = {}
    exclude_fields = {'obj_id', 'obj_name', 'generate_type', 'obj_type'}  # Fields to exclude
    valid_obj_ids = set()  # Track valid obj_ids from scenario_data
    for obj in scenario_data:
        obj_id = obj.get('obj_id')
        if obj_id is not None:
            valid_obj_ids.add(obj_id)
            # Initialize flattened dictionary
            flattened_info = {}
            # Copy all fields except excluded ones
            for key, value in obj.items():
                if key not in exclude_fields:
                    if isinstance(value, dict):
                        # Flatten dictionary fields into top-level keys
                        flattened_info.update(value)
                    else:
                        # Copy non-dictionary fields as-is
                        flattened_info[key] = value
            scenario_map[obj_id] = flattened_info
    
    # Update timestamp_objects with scenario information, only for matching obj_ids
    updated_timestamp_objects = {}
    for timestamp, objects in timestamp_objects.items():
        updated_objects = []
        for obj in objects:
            obj_id = obj.get('id')
            if obj_id in valid_obj_ids:  # Only include objects with matching obj_id
                updated_obj = obj.copy()  # Preserve original object
                # Merge scenario fields, overwriting duplicate keys
                updated_obj.update(scenario_map[obj_id])
                updated_objects.append(updated_obj)
        if updated_objects:  # Only add timestamp if there are matching objects
            updated_timestamp_objects[timestamp] = updated_objects
    
    return updated_timestamp_objects

def merge_sensors_with_steps(sensors_objects, steps_objects):
    # Merge steps data into sensors objects by id and timestamp
    merged_objects = defaultdict(list)
    
    for timestamp, objects in sensors_objects.items():
        for obj in objects:
            obj_id = obj.get('id')
            merged_obj = obj.copy()
            # Add steps data if available
            if obj_id in steps_objects and timestamp in steps_objects[obj_id]:
                merged_obj.update(steps_objects[obj_id][timestamp])
            merged_objects[timestamp].append(merged_obj)
    
    return dict(merged_objects)

# Example usage
if __name__ == "__main__":
    # Load sensors.json
    with open('sensors.json', 'r', encoding='utf-8') as file:
        sensors_data = json.load(file)
    
    # Load steps.json
    with open('steps.json', 'r', encoding='utf-8') as file:
        steps_data = json.load(file)
    
    # Load scenario_objs.json
    with open('scenario_objs.json', 'r', encoding='utf-8') as file:
        scenario_data = json.load(file)
    
    # Extract objects from sensors.json and steps.json
    sensors_objects = extract_sensors_objects(sensors_data)
    steps_objects = extract_steps_objects(steps_data)
    
    # Merge sensors objects with steps data
    timestamp_objects = merge_sensors_with_steps(sensors_objects, steps_objects)
    
    # Update timestamp_objects with scenario information
    timestamp_objects = update_objects_with_scenario_info(timestamp_objects, scenario_data)
    
    # Save the updated result to a JSON file with the new structure
    output_data = {"object": timestamp_objects}
    with open('timestamp_objects_updated.json', 'w', encoding='utf-8') as outfile:
        json.dump(output_data, outfile, indent=4)
    
    # Print completion message
    print("文件已生成")