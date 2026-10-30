import os
from glob import glob
from setuptools import setup

package_name = "litrun_ros"

setup(
    name=package_name,
    version="0.4.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools", "litrun>=0.3.0"],
    zip_safe=True,
    maintainer="litrun Contributors",
    maintainer_email="dev@litrun.dev",
    description="ROS 2 Node powered by litrun for edge robotics reasoning and actuator commands.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "edge_agent_node = litrun_ros.edge_agent_node:main",
        ],
    },
)

