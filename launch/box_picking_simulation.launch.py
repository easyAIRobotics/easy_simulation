from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution, FindExecutable

import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    # ------------------
    # Launch Arguments
    # ------------------
    use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use simulation time",
    )

    world_file = os.path.join(
        get_package_share_directory("easy_simulation"), "worlds", "box_picking_desk.sdf"
    )

    robot_description_file = os.path.join(
        get_package_share_directory("easy_simulation"), "urdf", "kinova_g3l_box_picker.urdf.xacro"
    )

    # ------------------
    # Load Robot Description
    # ------------------
    robot_description_content = Command([
        FindExecutable(name="xacro"),
        " ",
        robot_description_file,
        " name:=kinova_arm"
    ])

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[
            {"robot_description": robot_description_content},
            {"use_sim_time": LaunchConfiguration("use_sim_time")}
        ],
    )

    # ------------------
    # Launch Gazebo
    # ------------------
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py"
            )
        ]),
        launch_arguments={
            "gz_args": [" -r -v 4 ", world_file],
        }.items(),
    )

    # ------------------
    # Spawn Robot in Gazebo
    # ------------------
    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            '-topic', 'robot_description',
            "-name", "kinova_g3_lite_box_picker",
        ],
    )

    # ------------------
    # Spawn ros2_control
    # ------------------
    controller_manager = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            {"robot_description": robot_description_content}
        ],
        output="screen",
    )

    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "controller_manager"],
        output="screen",
    )

    kinova_arm_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["kinova_arm_controller", "--controller-manager", "controller_manager"],
        output="screen",
    )

    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name=f'ros_gz_bridge',
        parameters= [{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }],
        arguments=[
            f'/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            f'joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
        ],
    )

    return LaunchDescription([
        use_sim_time,

        # robot_state_publisher,
        gazebo,
        # controller_manager,
        # joint_state_broadcaster,
        # kinova_arm_controller,
        spawn_entity,
        ros_gz_bridge,
    ])
