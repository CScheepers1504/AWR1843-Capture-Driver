import os
import yaml

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node

from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.conditions import IfCondition


def generate_launch_description():

    config = os.path.join(get_package_share_directory('mmwave_drv'), 'config', 'radar_config.yaml')

    with open(config, 'r') as f:
        config_params = yaml.safe_load(f)

    use_gui = config_params.get('/**', {}).get('ros__parameters', {}).get('use_gui', True)

    use_gui_lc = LaunchConfiguration('use_gui')
    use_client_lc = LaunchConfiguration('use_client')

    # WHY use_client EXISTS
    #
    # radar_term_cli.py arms the radar ITSELF, unconditionally, from its own
    # __init__:  sleep(3) -> SETUP -> sleep(4) -> START.  There is no flag and
    # no prompt.  That is fine for the inherited interactive workflow, where
    # the client IS the operator, but it makes the client a second, invisible
    # controller: session.sh issues its own SETUP/START and the two race.
    #
    # Observed 29 Aug 2026 (logs/launch_20260829_170310.log): term_cli's START
    # landed first and started the sensor; session.sh's START four seconds
    # later got  Error -54, "Sensor has already been started"  -- and aborted
    # a take whose radar was already running happily at 333 Hz.
    #
    # So: launch with  use_client:=false  whenever something else drives
    # /control_radar.  Default stays true so run.sh is unchanged.
    both = lambda gui: IfCondition(PythonExpression([
        "'", use_client_lc, "'.lower() == 'true' and '",
        use_gui_lc, "'.lower() ", "==" if gui else "!=", " 'true'"]))

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_gui', default_value=str(use_gui).lower(),
            description='true -> radar_gui_cli.py, false -> radar_term_cli.py'),
        DeclareLaunchArgument(
            'use_client', default_value='true',
            description='false -> launch NO client node; the caller drives /control_radar'),
        Node(
            package='mmwave_drv',
            executable='radar_ctrl_node.py',
            name="radar_control",
            parameters=[config],
            ),
        Node(
            package='mmwave_drv',
            executable='radar_gui_cli.py',
            name="radar_client",
            parameters=[config],
            output='screen',
            condition=both(True),
            ),
        Node(
            package='mmwave_drv',
            executable='radar_term_cli.py',
            name="radar_client",
            parameters=[config],
            output='screen',
            condition=both(False),
            ),
        Node(
            package='mmwave_drv',
            executable='radar_data',
            name="radar_data",
            parameters=[config],
            )
  ])
