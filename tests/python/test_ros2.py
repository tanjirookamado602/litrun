"""
Unit tests for litrun ROS 2 Robotics Integration.
"""

import os
import sys

# Ensure integrations/ros2 is accessible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "integrations", "ros2")))

from litrun_ros.edge_agent_node import LitrunEdgeAgentNode, ROBOT_ACTION_SCHEMA


def test_ros2_robot_action_schema():
    assert "properties" in ROBOT_ACTION_SCHEMA
    assert "action" in ROBOT_ACTION_SCHEMA["properties"]
    assert "linear_speed" in ROBOT_ACTION_SCHEMA["properties"]
    assert "angular_speed" in ROBOT_ACTION_SCHEMA["properties"]


def test_ros2_edge_agent_node_reasoning():
    node = LitrunEdgeAgentNode()

    # Test stop on obstacle
    res_obstacle = node.reason_task("Obstacle detected 0.3 meters ahead in forward path")
    assert isinstance(res_obstacle, dict)
    assert "action" in res_obstacle
    assert "linear_speed" in res_obstacle
    assert "angular_speed" in res_obstacle
    assert res_obstacle["action"] in ["stop", "turn_left", "turn_right"]

    # Test move forward
    res_clear = node.reason_task("Path clear, navigate to waypoint Alpha")
    assert isinstance(res_clear, dict)
    assert "action" in res_clear
