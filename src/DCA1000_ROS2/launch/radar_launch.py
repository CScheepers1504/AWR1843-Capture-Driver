import os
import yaml

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    config = os.path.join(get_package_share_directory('dca1000_ros2_pkg'), 'config', 'radar_config.yaml')

    with open(config, 'r') as f:
        config_params = yaml.safe_load(f)

    use_gui = config_params.get('use_gui', True)
    
    return LaunchDescription([
        Node(
            package='dca1000_ros2_pkg',
            executable='radar_ctrl_node.py',
            name="radar_control",
            parameters = [config],      
            ),
        Node(
            package='dca1000_ros2_pkg',
            executable='radar_gui_cli.py',
            name="radar_client",
            parameters = [config],
            output='screen',
            condition= use_gui, 
            ),
        Node(
            package='dca1000_ros2_pkg',
            executable='radar_term_cli.py',
            name="radar_client",
            parameters = [config],
            output='screen',
            condition = not use_gui

            ),
        Node(
            package='dca1000_ros2_pkg',
            executable='radar_data',
            name="radar_data",
            parameters = [config],
            ),
  ])
