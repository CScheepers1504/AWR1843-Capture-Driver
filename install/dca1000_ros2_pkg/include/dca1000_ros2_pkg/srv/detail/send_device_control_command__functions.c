// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from dca1000_ros2_pkg:srv/SendDeviceControlCommand.idl
// generated code does not contain a copyright notice
#include "dca1000_ros2_pkg/srv/detail/send_device_control_command__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

bool
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__init(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request * msg)
{
  if (!msg) {
    return false;
  }
  // command
  return true;
}

void
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__fini(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request * msg)
{
  if (!msg) {
    return;
  }
  // command
}

bool
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__are_equal(const dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request * lhs, const dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // command
  if (lhs->command != rhs->command) {
    return false;
  }
  return true;
}

bool
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__copy(
  const dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request * input,
  dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // command
  output->command = input->command;
  return true;
}

dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request *
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request * msg = (dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request *)allocator.allocate(sizeof(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request));
  bool success = dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__destroy(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence__init(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request * data = NULL;

  if (size) {
    data = (dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request *)allocator.zero_allocate(size, sizeof(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence__fini(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence *
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence * array = (dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence *)allocator.allocate(sizeof(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence__destroy(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence__are_equal(const dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence * lhs, const dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence__copy(
  const dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence * input,
  dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request);
    dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request * data =
      (dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request *)realloc(output->data, allocation_size);
    if (!data) {
      return false;
    }
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__init(&data[i])) {
        /* free currently allocated and return false */
        for (; i-- > output->capacity; ) {
          dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__fini(&data[i]);
        }
        free(data);
        return false;
      }
    }
    output->data = data;
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


bool
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__init(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response * msg)
{
  if (!msg) {
    return false;
  }
  // status
  return true;
}

void
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__fini(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response * msg)
{
  if (!msg) {
    return;
  }
  // status
}

bool
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__are_equal(const dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response * lhs, const dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // status
  if (lhs->status != rhs->status) {
    return false;
  }
  return true;
}

bool
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__copy(
  const dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response * input,
  dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // status
  output->status = input->status;
  return true;
}

dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response *
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response * msg = (dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response *)allocator.allocate(sizeof(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response));
  bool success = dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__destroy(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence__init(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response * data = NULL;

  if (size) {
    data = (dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response *)allocator.zero_allocate(size, sizeof(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence__fini(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence *
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence * array = (dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence *)allocator.allocate(sizeof(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence__destroy(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence__are_equal(const dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence * lhs, const dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence__copy(
  const dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence * input,
  dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response);
    dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response * data =
      (dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response *)realloc(output->data, allocation_size);
    if (!data) {
      return false;
    }
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__init(&data[i])) {
        /* free currently allocated and return false */
        for (; i-- > output->capacity; ) {
          dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__fini(&data[i]);
        }
        free(data);
        return false;
      }
    }
    output->data = data;
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
