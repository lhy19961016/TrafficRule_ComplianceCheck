import json
from collections import defaultdict


'''
 /* 从tracks中读取主车和环境车的轨迹信息
'''
def track_extract(tracks_path):
    with open(tracks_path, 'r', encoding='utf-8') as f:
        track_data = json.load(f)

    tracks = defaultdict(dict)
    for entry in track_data:
        obj_id = entry.get('obj_id')
        timestamp = entry.get('timestamp', 0)
        result = entry.get('result')
        obj_track = tracks[obj_id]
        obj_track[timestamp] = result
        tracks[obj_id] = obj_track
    return tracks


'''
 /* 从paths中读取主车的轨迹信息
'''
def ego_trajectory_extract(ego_id_list, paths_path):
    with open(paths_path, 'r', encoding='utf-8') as f:
        path_data = json.load(f)

    all_trajectories = defaultdict(dict)
    for entry in path_data:
        if entry['obj_id'] in ego_id_list:
            ego_trajectory = all_trajectories[entry['obj_id']]
            timestamp = entry.get('timestamp', 0)

            # 查找主轨迹（标记为choose或第一条）
            main_path = None
            for path in entry['result']:
                if path.get('choose', False):
                    main_path = path
                    break
            if main_path is None and entry['result']:
                main_path = entry['result'][0]

            if main_path and main_path['points']:
                # 取第一个点作为该时间点的位置
                first_point = main_path['points'][0]
                ego_trajectory[timestamp] = first_point
                all_trajectories[entry['obj_id']] = ego_trajectory

    return all_trajectories


'''
 /* 从steps中读取主车的基本信息
'''
def ego_base_info_extract(ego_id_list, steps_path):
    with open(steps_path, 'r', encoding='utf-8') as f:
        step_data = json.load(f)

    base_data = defaultdict(dict)
    for entry in step_data:
        if entry['obj_id'] in ego_id_list:
            ego_base_data = base_data[entry['obj_id']]
            timestamp = entry.get('timestamp', 0)
            result = entry.get('result', {})
            property_list = ['speed', 'acc', 'mileage', 'ste_wheel', 'turn_signal', 'v', 'w', 'w_acc', 'reference_speed',
                             'u', 'u_acc', 'distance_to_front', 'front_obj_id', 'distance_to_center']
            for property in property_list:
                if property not in result:
                    result[property] = None
            ego_base_data[timestamp] = result
            base_data[entry['obj_id']] = ego_base_data
    return base_data


if __name__ == '__main__':
    step_path = 'steps.json'
    paths_path = 'paths.json'
    tracks_path = 'tracks.json'
    ego_id_list = ['测试车辆1']

    # path_data = ego_trajectory_extract(ego_id_list, paths_path)
    # print(path_data)
    # data = ego_base_info_extract(ego_id_list, step_path)
    # print(data)
    # with open('base_data.json', 'w')as json_file:
    #     json.dump(data, json_file)
    data = track_extract(tracks_path)
    print(data)
    with open('track_data.json', 'w')as json_file:
        json.dump(data, json_file)




