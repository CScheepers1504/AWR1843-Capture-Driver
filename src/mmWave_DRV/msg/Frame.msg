# radar frame msg format
std_msgs/Header header
uint32 frame_size
uint8[] frame_data
# DCA1000 stream position of this frame's first byte (bytes since RECORD_START).
# Always a multiple of frame_size; consecutive frames differ by exactly
# frame_size unless frames were dropped.
uint64 stream_offset
# Byte count of the first packet of this stream. 0 = the node saw the stream
# from its first byte; nonzero = it joined late (packets lost before it).
uint64 join_offset
# Bytes zero-filled for dropped packets since this stream started (cumulative).
uint64 zero_filled
# Frame start found by packet timing (first packet after the idle gap between
# frames), as its DCA1000 byte count minus this frame's stream_offset. ~0, or
# down to minus one packet (1456 B), on an aligned take; a multiple of the
# chirp size after a slot slip. -2147483648 = no frame start timed for this frame.
int32 burst_phase
