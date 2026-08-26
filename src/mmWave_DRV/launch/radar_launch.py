import os
import yaml

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import Node

from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition

def generate_launch_description():

    config = os.path.join(get_package_share_directory('mmwave_drv'), 'config', 'radar_config.yaml')

    with open(config, 'r') as f:
        config_params = yaml.safe_load(f)

    use_gui = config_params.get('/**', {}).get('ros__parameters',{}).get('use_gui', True)

    use_gui_lc = LaunchConfiguration('use_gui', default=use_gui)
    
    return LaunchDescription([
        Node(
            package='mmwave_drv',
            executable='radar_ctrl_node.py',
            name="radar_control",
            parameters = [config],      
            ),
        Node(
            package='mmwave_drv',
            executable='radar_gui_cli.py',
            name="radar_client",
            parameters = [config],
            output='screen',
            condition= IfCondition(use_gui_lc), 
            ),
        Node(
            package='mmwave_drv',
            executable='radar_term_cli.py',
            name="radar_client",
            parameters = [config],
            output='screen',
            condition= UnlessCondition(use_gui_lc),
            ),
        Node(
            package='mmwave_drv',
            executable='radar_data',
            name="radar_data",
            parameters = [config],
            )
  ])
