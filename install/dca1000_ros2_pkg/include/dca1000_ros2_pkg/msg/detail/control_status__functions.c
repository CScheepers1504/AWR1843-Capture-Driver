// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from dca1000_ros2_pkg:msg/ControlStatus.idl
// generated code does not contain a copyright notice
#include "dca1000_ros2_pkg/msg/detail/control_status__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `dev_name`
#include "rosidl_runtime_c/string_functions.h"

bool
dca1000_ros2_pkg__msg__ControlStatus__init(dca1000_ros2_pkg__msg__ControlStatus * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    dca1000_ros2_pkg__msg__ControlStatus__fini(msg);
    return false;
  }
  // dev_name
  if (!rosidl_runtime_c__String__init(&msg->dev_name)) {
    dca1000_ros2_pkg__msg__ControlStatus__fini(msg);
    return false;
  }
  // pwron
  // setup
  // recrd
  return true;
}

void
dca1000_ros2_pkg__msg__ControlStatus__fini(dca1000_ros2_pkg__msg__ControlStatus * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // dev_name
  rosidl_runtime_c__String__fini(&msg->dev_name);
  // pwron
  // setup
  // recrd
}

bool
dca1000_ros2_pkg__msg__ControlStatus__are_equal(const dca1000_ros2_pkg__msg__ControlStatus * lhs, const dca1000_ros2_pkg__msg__ControlStatus * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__are_equal(
      &(lhs->header), &(rhs->header)))
  {
    return false;
  }
  // dev_name
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->dev_name), &(rhs->dev_name)))
  {
    return false;
  }
  // pwron
  if (lhs->pwron != rhs->pwron) {
    return false;
  }
  // setup
  if (lhs->setup != rhs->setup) {
    return false;
  }
  // recrd
  if (lhs->recrd != rhs->recrd) {
    return false;
  }
  return true;
}

bool
dca1000_ros2_pkg__msg__ControlStatus__copy(
  const dca1000_ros2_pkg__msg__ControlStatus * input,
  dca1000_ros2_pkg__msg__ControlStatus * output)
{
  if (!input || !output) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__copy(
      &(input->header), &(output->header)))
  {
    return false;
  }
  // dev_name
  if (!rosidl_runtime_c__String__copy(
      &(input->dev_name), &(output->dev_name)))
  {
    return false;
  }
  // pwron
  output->pwron = input->pwron;
  // setup
  output->setup = input->setup;
  // recrd
  output->recrd = input->recrd;
  return true;
}

dca1000_ros2_pkg__msg__ControlStatus *
dca1000_ros2_pkg__msg__ControlStatus__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dca1000_ros2_pkg__msg__ControlStatus * msg = (dca1000_ros2_pkg__msg__ControlStatus *)allocator.allocate(sizeof(dca1000_ros2_pkg__msg__ControlStatus), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(dca1000_ros2_pkg__msg__ControlStatus));
  bool success = dca1000_ros2_pkg__msg__ControlStatus__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
dca1000_ros2_pkg__msg__ControlStatus__destroy(dca1000_ros2_pkg__msg__ControlStatus * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    dca1000_ros2_pkg__msg__ControlStatus__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
dca1000_ros2_pkg__msg__ControlStatus__Sequence__init(dca1000_ros2_pkg__msg__ControlStatus__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dca1000_ros2_pkg__msg__ControlStatus * data = NULL;

  if (size) {
    data = (dca1000_ros2_pkg__msg__ControlStatus *)allocator.zero_allocate(size, sizeof(dca1000_ros2_pkg__msg__ControlStatus), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = dca1000_ros2_pkg__msg__ControlStatus__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        dca1000_ros2_pkg__msg__ControlStatus__fini(&data[i - 1]);
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
dca1000_ros2_pkg__msg__ControlStatus__Sequence__fini(dca1000_ros2_pkg__msg__ControlStatus__Sequence * array)
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
      dca1000_ros2_pkg__msg__ControlStatus__fini(&array->data[i]);
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

dca1000_ros2_pkg__msg__ControlStatus__Sequence *
dca1000_ros2_pkg__msg__ControlStatus__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dca1000_ros2_pkg__msg__ControlStatus__Sequence * array = (dca1000_ros2_pkg__msg__ControlStatus__Sequence *)allocator.allocate(sizeof(dca1000_ros2_pkg__msg__ControlStatus__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = dca1000_ros2_pkg__msg__ControlStatus__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
dca1000_ros2_pkg__msg__ControlStatus__Sequence__destroy(dca1000_ros2_pkg__msg__ControlStatus__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    dca1000_ros2_pkg__msg__ControlStatus__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
dca1000_ros2_pkg__msg__ControlStatus__Sequence__are_equal(const dca1000_ros2_pkg__msg__ControlStatus__Sequence * lhs, const dca1000_ros2_pkg__msg__ControlStatus__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!dca1000_ros2_pkg__msg__ControlStatus__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
dca1000_ros2_pkg__msg__ControlStatus__Sequence__copy(
  const dca1000_ros2_pkg__msg__ControlStatus__Sequence * input,
  dca1000_ros2_pkg__msg__ControlStatus__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(dca1000_ros2_pkg__msg__ControlStatus);
    dca1000_ros2_pkg__msg__ControlStatus * data =
      (dca1000_ros2_pkg__msg__ControlStatus *)realloc(output->data, allocation_size);
    if (!data) {
      return false;
    }
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!dca1000_ros2_pkg__msg__ControlStatus__init(&data[i])) {
        /* free currently allocated and return false */
        for (; i-- > output->capacity; ) {
          dca1000_ros2_pkg__msg__ControlStatus__fini(&data[i]);
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
    if (!dca1000_ros2_pkg__msg__ControlStatus__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
