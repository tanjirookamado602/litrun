# VHS Tape Configuration for litrun Terminal Demo
# Output: assets/demo.gif
Output assets/demo.gif

Set FontSize 15
Set Width 1024
Set Height 640
Set Theme "Dracula"
Set Padding 16

# 1. Inspect Hardware, NPU & Jetson Accelerators
Type "litrun inspect"
Enter
Sleep 3s

# 2. Local Offline RAG: Ingest Industrial Manual
Type "litrun embed --text 'Alert Code E-04: Hydraulic pressure dropped below 15 PSI. Action: Inspect secondary seal and intake valve.'"
Enter
Sleep 2.5s

# 3. Edge Reasoning with Augmented Context
Type "litrun run qwen2.5-0.5b --rag -p 'What action is required for alert code E-04?'"
Enter
Sleep 3.5s

# 4. Industrial IoT MQTT Autonomous Telemetry Daemon
Type "litrun mqtt --demo"
Enter
Sleep 4s

# 5. Vision-Language Model Edge Inspection
Type "litrun see --demo"
Enter
Sleep 3.5s
