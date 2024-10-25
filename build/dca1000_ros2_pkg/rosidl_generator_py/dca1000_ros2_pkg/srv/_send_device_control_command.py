# generated from rosidl_generator_py/resource/_idl.py.em
# with input from dca1000_ros2_pkg:srv/SendDeviceControlCommand.idl
# generated code does not contain a copyright notice


# Import statements for member types

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_SendDeviceControlCommand_Request(type):
    """Metaclass of message 'SendDeviceControlCommand_Request'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
        'SETUP': 2,
        'START': 1,
        'STOP': 0,
    }

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('dca1000_ros2_pkg')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'dca1000_ros2_pkg.srv.SendDeviceControlCommand_Request')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__srv__send_device_control_command__request
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__srv__send_device_control_command__request
            cls._CONVERT_TO_PY = module.convert_to_py_msg__srv__send_device_control_command__request
            cls._TYPE_SUPPORT = module.type_support_msg__srv__send_device_control_command__request
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__srv__send_device_control_command__request

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
            'SETUP': cls.__constants['SETUP'],
            'START': cls.__constants['START'],
            'STOP': cls.__constants['STOP'],
        }

    @property
    def SETUP(self):
        """Message constant 'SETUP'."""
        return Metaclass_SendDeviceControlCommand_Request.__constants['SETUP']

    @property
    def START(self):
        """Message constant 'START'."""
        return Metaclass_SendDeviceControlCommand_Request.__constants['START']

    @property
    def STOP(self):
        """Message constant 'STOP'."""
        return Metaclass_SendDeviceControlCommand_Request.__constants['STOP']


class SendDeviceControlCommand_Request(metaclass=Metaclass_SendDeviceControlCommand_Request):
    """
    Message class 'SendDeviceControlCommand_Request'.

    Constants:
      SETUP
      START
      STOP
    """

    __slots__ = [
        '_command',
    ]

    _fields_and_field_types = {
        'command': 'int8',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('int8'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.command = kwargs.get('command', int())

    def __repr__(self):
        typename = self.__class__.__module__.split('.')
        typename.pop()
        typename.append(self.__class__.__name__)
        args = []
        for s, t in zip(self.__slots__, self.SLOT_TYPES):
            field = getattr(self, s)
            fieldstr = repr(field)
            # We use Python array type for fields that can be directly stored
            # in them, and "normal" sequences for everything else.  If it is
            # a type that we store in an array, strip off the 'array' portion.
            if (
                isinstance(t, rosidl_parser.definition.AbstractSequence) and
                isinstance(t.value_type, rosidl_parser.definition.BasicType) and
                t.value_type.typename in ['float', 'double', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']
            ):
                if len(field) == 0:
                    fieldstr = '[]'
                else:
                    assert fieldstr.startswith('array(')
                    prefix = "array('X', "
                    suffix = ')'
                    fieldstr = fieldstr[len(prefix):-len(suffix)]
            args.append(s[1:] + '=' + fieldstr)
        return '%s(%s)' % ('.'.join(typename), ', '.join(args))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.command != other.command:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @property
    def command(self):
        """Message field 'command'."""
        return self._command

    @command.setter
    def command(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'command' field must be of type 'int'"
            assert value >= -128 and value < 128, \
                "The 'command' field must be an integer in [-128, 127]"
        self._command = value


# Import statements for member types

# already imported above
# import rosidl_parser.definition


class Metaclass_SendDeviceControlCommand_Response(type):
    """Metaclass of message 'SendDeviceControlCommand_Response'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
        'DONE': True,
        'ERROR': False,
    }

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('dca1000_ros2_pkg')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'dca1000_ros2_pkg.srv.SendDeviceControlCommand_Response')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__srv__send_device_control_command__response
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__srv__send_device_control_command__response
            cls._CONVERT_TO_PY = module.convert_to_py_msg__srv__send_device_control_command__response
            cls._TYPE_SUPPORT = module.type_support_msg__srv__send_device_control_command__response
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__srv__send_device_control_command__response

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
            'DONE': cls.__constants['DONE'],
            'ERROR': cls.__constants['ERROR'],
        }

    @property
    def DONE(self):
        """Message constant 'DONE'."""
        return Metaclass_SendDeviceControlCommand_Response.__constants['DONE']

    @property
    def ERROR(self):
        """Message constant 'ERROR'."""
        return Metaclass_SendDeviceControlCommand_Response.__constants['ERROR']


class SendDeviceControlCommand_Response(metaclass=Metaclass_SendDeviceControlCommand_Response):
    """
    Message class 'SendDeviceControlCommand_Response'.

    Constants:
      DONE
      ERROR
    """

    __slots__ = [
        '_status',
    ]

    _fields_and_field_types = {
        'status': 'boolean',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.status = kwargs.get('status', bool())

    def __repr__(self):
        typename = self.__class__.__module__.split('.')
        typename.pop()
        typename.append(self.__class__.__name__)
        args = []
        for s, t in zip(self.__slots__, self.SLOT_TYPES):
            field = getattr(self, s)
            fieldstr = repr(field)
            # We use Python array type for fields that can be directly stored
            # in them, and "normal" sequences for everything else.  If it is
            # a type that we store in an array, strip off the 'array' portion.
            if (
                isinstance(t, rosidl_parser.definition.AbstractSequence) and
                isinstance(t.value_type, rosidl_parser.definition.BasicType) and
                t.value_type.typename in ['float', 'double', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']
            ):
                if len(field) == 0:
                    fieldstr = '[]'
                else:
                    assert fieldstr.startswith('array(')
                    prefix = "array('X', "
                    suffix = ')'
                    fieldstr = fieldstr[len(prefix):-len(suffix)]
            args.append(s[1:] + '=' + fieldstr)
        return '%s(%s)' % ('.'.join(typename), ', '.join(args))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.status != other.status:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @property
    def status(self):
        """Message field 'status'."""
        return self._status

    @status.setter
    def status(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'status' field must be of type 'bool'"
        self._status = value


class Metaclass_SendDeviceControlCommand(type):
    """Metaclass of service 'SendDeviceControlCommand'."""

    _TYPE_SUPPORT = None

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('dca1000_ros2_pkg')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'dca1000_ros2_pkg.srv.SendDeviceControlCommand')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._TYPE_SUPPORT = module.type_support_srv__srv__send_device_control_command

            from dca1000_ros2_pkg.srv import _send_device_control_command
            if _send_device_control_command.Metaclass_SendDeviceControlCommand_Request._TYPE_SUPPORT is None:
                _send_device_control_command.Metaclass_SendDeviceControlCommand_Request.__import_type_support__()
            if _send_device_control_command.Metaclass_SendDeviceControlCommand_Response._TYPE_SUPPORT is None:
                _send_device_control_command.Metaclass_SendDeviceControlCommand_Response.__import_type_support__()


class SendDeviceControlCommand(metaclass=Metaclass_SendDeviceControlCommand):
    from dca1000_ros2_pkg.srv._send_device_control_command import SendDeviceControlCommand_Request as Request
    from dca1000_ros2_pkg.srv._send_device_control_command import SendDeviceControlCommand_Response as Response

    def __init__(self):
        raise NotImplementedError('Service classes can not be instantiated')
