#do not use desktop full image, not compiled for arm
# FROM osrf/ros:humble-desktop-full-jammy

FROM ros:humble-ros-core-jammy

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    python3-pip \
    git \
    cmake \
    gdb \
    curl \
    vim \
    libjsoncpp-dev \
    iputils-ping \
    nmap \
    qtbase5-dev \
    qtbase5-dev-tools \
    python3-pyqt5 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install numpy \
    && pip3 install scipy \
    && pip3 install matplotlib \
    && pip3 install h5py \
    && pip3 install pyserial \
    && pip3 install pyqtgraph

#RUN pip3 install PyQt5

RUN apt-get update && apt-get install --no-install-recommends -y \
    python3-colcon-common-extensions \
    python3-colcon-mixin \
    python3-rosdep \
    python3-vcstool\
    && rm -rf /var/lib/apt/lists/*

# bootstrap rosdep
RUN rosdep init && \
  rosdep update --rosdistro $ROS_DISTRO

# setup colcon mixin and metadata
RUN colcon mixin add default https://raw.githubusercontent.com/colcon/colcon-mixin-repository/master/index.yaml && \
    colcon mixin update && \
    colcon metadata add default https://raw.githubusercontent.com/colcon/colcon-metadata-repository/master/index.yaml && \
    colcon metadata update

# install ros2 packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-ros-base=0.10.0-1* \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-cv-bridge \
    ros-humble-pcl-conversions \
    ros-humble-xacro \
    ros-humble-robot-state-publisher\
    ros-humble-rviz2 \
    ros-humble-image-transport \
    ros-humble-image-transport-plugins \
    ros-humble-pcl-ros \
    ros-humble-imu-tools \
    ros-humble-sensor-msgs-py \
    && rm -rf /var/lib/apt/lists/*

# expose port 22 to enable ssh connections from other devices
EXPOSE 22

RUN echo 'source /opt/ros/humble/setup.bash' >> ~/.bashrc
RUN echo 'source /home/ros2_ws/install/setup.bash' >> ~/.bashrc



