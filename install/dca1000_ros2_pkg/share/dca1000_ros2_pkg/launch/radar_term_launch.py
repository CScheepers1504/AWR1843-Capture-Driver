import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import Node

# from m2s2_pydevclass.m2s2_device import M2S2Device

# device = M2S2Device("RADAR")
device_dev_name = "RADAR"

def generate_launch_description():

    config = os.path.join(get_package_share_directory('dca1000_ros2_pkg'), 'config', 'radar_config.yaml')
    
    return LaunchDescription([
        Node(
            package='dca1000_ros2_pkg',
            executable='radar_ctrl_node.py',
            name="radar_controller",
            parameters = [config],      
            # emulate_tty=True
            ),

        Node(
            package='dca1000_ros2_pkg',
            executable='radar_term_cli.py',
            name="radar_client",
            parameters = [config],
            # emulate_tty=True, 
            output='screen'
            ),

        Node(
            package='dca1000_ros2_pkg',
            executable='radar_data',
            name="data_node",
            parameters = [config],
            # emulate_tty=True
            ),
  ])
