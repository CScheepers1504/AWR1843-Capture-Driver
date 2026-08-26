#!/usr/bin/env bash

set -e

IMAGE_NAME="mmwave_image"
CONTAINER_NAME="mmwave"

# Allow X11 access (needed for GUI apps)

xhost +local:root

echo "Building Docker image..."
docker build -t $IMAGE_NAME -f Dockerfile .

# Remove existing container if it exists

if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
echo "Removing existing container..."
docker rm -f $CONTAINER_NAME
fi

echo "Starting container..."

docker run -it --rm
--name $CONTAINER_NAME 
--privileged 
--network host 
--device=/dev/ttyACM0 
--device=/dev/ttyACM1 
--device=/dev/i2c-1 
-e DISPLAY=$DISPLAY 
-v /tmp/.X11-unix:/tmp/.X11-unix:rw 
-v ../src/:/home/ros2_ws/src/ 
--gpus '"device=0"' 
--stdin_open 
--tty 
$IMAGE_NAME 
bash -c "source /opt/ros/humble/setup.bash && /bin/bash"

