cmake_minimum_required(VERSION 3.5)
project(mmwave_drv)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

# Find dependencies for C++
find_package(ament_cmake REQUIRED)
find_package(ament_index_cpp REQUIRED)
find_package(rclcpp REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(std_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

#find_package(jsoncpp REQUIRED)
pkg_check_modules(JSONCPP jsoncpp)
link_libraries(${JSONCPP_LIBRARIES})

# Find dependencies for Python
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Frame.msg"
  "msg/ControlStatus.msg"
  "srv/SendDeviceControlCommand.srv"
  DEPENDENCIES std_msgs
)

# --------------------
# C++ Nodes
# --------------------

# find include direcotires
include_directories(
	include
	${rclcpp_INCLUDE_DIRS}
	${std_msgs_INCLUDE_DIRS}
	${CMAKE_CURRENT_BINARY_DIR}/$<BUILD_INTERFACE:${PROJECT_NAME}>/msg
)
# Add C++ executables. The inherited RingBuffer class was compiled in and
# instantiated but never used; the node keeps its own aligned ring.
add_executable(radar_data
  src/cpp/radar_data_node.cpp
  )

ament_target_dependencies(radar_data rclcpp builtin_interfaces rosidl_default_runtime ament_index_cpp)

target_link_libraries(radar_data ${JSONCPP_LIBRARIES})

rosidl_target_interfaces(radar_data ${PROJECT_NAME} "rosidl_typesupport_cpp")

# --------------------
# Messages, Services, Actions
# --------------------


# Install C++ executables
install(TARGETS
  radar_data
  DESTINATION lib/${PROJECT_NAME}
)

# --------------------
# Python Nodes
# --------------------

# Install Python modules
# ament_python_install_package(${PROJECT_NAME})

# Install Python executables (scripts)
install(PROGRAMS
  src/python/radar_gui_cli.py
  src/python/radar_term_cli.py
  src/python/radar_ctrl_node.py
  src/python/radar_proc_node.py
  src/python/mmwave_config_class.py
  DESTINATION lib/${PROJECT_NAME}
)

# --------------------
# Install Launch Files
# --------------------

install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}/
)

# --------------------
# Install Configuration and Parameter Files
# --------------------

install(DIRECTORY
  config
  DESTINATION share/${PROJECT_NAME}/
)

# --------------------
# Export Dependencies
# --------------------

ament_export_dependencies(
  ament_cmake
  rclcpp
  builtin_interfaces
  std_msgs
  rosidl_default_generators
  jsoncpp
)

ament_export_dependencies(
  ament_cmake_python
  rclpy
  std_msgs
)

ament_export_dependencies(rosidl_default_generators)

# --------------------
# Package
# --------------------

ament_package()
