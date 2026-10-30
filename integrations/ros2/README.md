# 🤖 litrun ROS 2 Robotics Integration

Deploy deterministic on-device LLM reasoning and autonomous navigation decisions directly onto ROS 2 robotics platforms (TurtleBot 4, autonomous rovers, robotic arms) powered by `litrun`.

---

## 🌟 Why Use litrun on Robots?

- **Deterministic Actions via GBNF Schema**: Never hallucinates malformed JSON or unexecutable velocity commands. Outputs strictly match the robot's action schema (`move_forward`, `turn_left`, `stop`, `dock`).
- **RAM Governor Protection**: Probes Linux memory cgroups so high-context prompts never trigger kernel OOM panics on your robot's onboard SBC (Raspberry Pi 4/5, Jetson Orin Nano).
- **Sub-50ms Reaction Times**: Keeps quantized weights pinned in RAM across continuous sensor topic evaluations.

---

## 📦 Building the ROS 2 Package

In your ROS 2 workspace (e.g. `colcon_ws/`):

```bash
cd ~/colcon_ws/src
git clone https://github.com/assassinaj602/litrun.git
cd ~/colcon_ws

# Install litrun dependencies
pip3 install -e litrun/

# Build package
colcon build --packages-select litrun_ros
source install/setup.bash
```

---

## 🚀 Running the Node

Launch the edge agent node:

```bash
ros2 launch litrun_ros litrun_agent.launch.py
```

---

## 📡 Topics

| Topic | Type | Direction | Description |
|---|---|---|---|
| `/robot/task_query` | `std_msgs/String` | Subscribed | Natural language task or sensor telemetry prompt |
| `/robot/action_decision` | `std_msgs/String` | Published | Strict JSON action decision payload |
| `/cmd_vel` | `geometry_msgs/Twist` | Published | Extracted linear and angular velocity commands |

### Testing with ROS 2 CLI:

Publish an operator query or sensor telemetry:
```bash
ros2 topic pub --once /robot/task_query std_msgs/msg/String '{data: "Obstacle detected 0.3 meters ahead"}'
```

Echo the autonomous robot action:
```bash
ros2 topic echo /robot/action_decision
```

Output:
```json
{
  "action": "stop",
  "linear_speed": 0.0,
  "angular_speed": 0.0,
  "reason": "Immediate obstacle detected within safe stopping threshold."
}
```
