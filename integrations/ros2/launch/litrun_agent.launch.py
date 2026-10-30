from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="litrun_ros",
            executable="edge_agent_node",
            name="litrun_edge_agent",
            output="screen",
            parameters=[
                {"model_id": "qwen2.5-0.5b"},
                {"quant": "Q4_K_M"},
                {"threads": 4},
                {"demo_mode": False},
            ],
        ),
    ])

