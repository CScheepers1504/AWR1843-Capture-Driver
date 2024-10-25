# generated from rosidl_generator_py/resource/_idl.py.em
# with input from dca1000_ros2_pkg:msg/ControlStatus.idl
# generated code does not contain a copyright notice


# Import statements for member types

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_ControlStatus(type):
    """Metaclass of message 'ControlStatus'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
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
                'dca1000_ros2_pkg.msg.ControlStatus')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__control_status
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__control_status
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__control_status
            cls._TYPE_SUPPORT = module.type_support_msg__msg__control_status
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__control_status

            from std_msgs.msg import Header
            if Header.__class__._TYPE_SUPPORT is None:
                Header.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class ControlStatus(metaclass=Metaclass_ControlStatus):
    """Message class 'ControlStatus'."""

    __slots__ = [
        '_header',
        '_dev_name',
        '_pwron',
        '_setup',
        '_recrd',
    ]

    _fields_and_field_types = {
        'header': 'std_msgs/Header',
        'dev_name': 'string',
        'pwron': 'boolean',
        'setup': 'boolean',
        'recrd': 'boolean',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.NamespacedType(['std_msgs', 'msg'], 'Header'),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        from std_msgs.msg import Header
        self.header = kwargs.get('header', Header())
        self.dev_name = kwargs.get('dev_name', str())
        self.pwron = kwargs.get('pwron', bool())
        self.setup = kwargs.get('setup', bool())
        self.recrd = kwargs.get('recrd', bool())

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
        if self.header != other.header:
            return False
        if self.dev_name != other.dev_name:
            return False
        if self.pwron != other.pwron:
            return False
        if self.setup != other.setup:
            return False
        if self.recrd != other.recrd:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @property
    def header(self):
        """Message field 'header'."""
        return self._header

    @header.setter
    def header(self, value):
        if __debug__:
            from std_msgs.msg import Header
            assert \
                isinstance(value, Header), \
                "The 'header' field must be a sub message of type 'Header'"
        self._header = value

    @property
    def dev_name(self):
        """Message field 'dev_name'."""
        return self._dev_name

    @dev_name.setter
    def dev_name(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'dev_name' field must be of type 'str'"
        self._dev_name = value

    @property
    def pwron(self):
        """Message field 'pwron'."""
        return self._pwron

    @pwron.setter
    def pwron(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'pwron' field must be of type 'bool'"
        self._pwron = value

    @property
    def setup(self):
        """Message field 'setup'."""
        return self._setup

    @setup.setter
    def setup(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'setup' field must be of type 'bool'"
        self._setup = value

    @property
    def recrd(self):
        """Message field 'recrd'."""
        return self._recrd

    @recrd.setter
    def recrd(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'recrd' field must be of type 'bool'"
        self._recrd = value
