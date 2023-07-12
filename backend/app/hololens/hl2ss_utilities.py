
import fractions
import numpy as np
import time
import av
from ..hololens import hl2ss
from ..hololens import hl2ss_io


#------------------------------------------------------------------------------
# Microphone
#------------------------------------------------------------------------------

def microphone_planar_to_packed(array):
    data = np.zeros((1, array.size), dtype=array.dtype)
    data[0, 0::2] = array[0, :]
    data[0, 1::2] = array[1, :]
    return data


def microphone_packed_to_planar(array):
    data = np.zeros((2, array.size // 2), dtype=array.dtype)
    data[0, :] = array[0, 0::2]
    data[1, :] = array[0, 1::2]
    return data


#------------------------------------------------------------------------------
# SI
#------------------------------------------------------------------------------

class SI_Hand:
    def __init__(self, poses, orientations, positions, radii, accuracies):
        self.poses = poses
        self.orientations = orientations
        self.positions = positions
        self.radii = radii
        self.accuracies = accuracies


def si_unpack_hand(hand):
    poses = [hand.get_joint_pose(joint) for joint in range(0, hl2ss.SI_HandJointKind.TOTAL)]
    orientations = np.array([pose.orientation for pose in poses])
    positions = np.array([pose.position for pose in poses])
    radii = np.array([pose.radius for pose in poses])
    accuracies = np.array([pose.accuracy for pose in poses])
    return SI_Hand(poses, orientations, positions, radii, accuracies)


def si_head_pose_rotation_matrix(head_pose):
    y = head_pose.up
    z = -head_pose.forward
    x = np.cross(y, z)
    return np.hstack((x, y, z)).reshape((3, 3)).transpose()


#------------------------------------------------------------------------------
# Unpack to MP4
#------------------------------------------------------------------------------

def get_av_codec_name(reader):
    if (reader.header.port == hl2ss.StreamPort.RM_VLC_LEFTFRONT):
        return hl2ss.get_video_codec_name(reader.header.profile)
    if (reader.header.port == hl2ss.StreamPort.RM_VLC_LEFTLEFT):
        return hl2ss.get_video_codec_name(reader.header.profile)
    if (reader.header.port == hl2ss.StreamPort.RM_VLC_RIGHTFRONT):
        return hl2ss.get_video_codec_name(reader.header.profile)
    if (reader.header.port == hl2ss.StreamPort.RM_VLC_RIGHTRIGHT):
        return hl2ss.get_video_codec_name(reader.header.profile)
    if (reader.header.port == hl2ss.StreamPort.RM_DEPTH_AHAT):
        return hl2ss.get_video_codec_name(reader.header.profile)
    if (reader.header.port == hl2ss.StreamPort.PERSONAL_VIDEO):
        return hl2ss.get_video_codec_name(reader.header.profile)
    if (reader.header.port == hl2ss.StreamPort.MICROPHONE):
        return hl2ss.get_audio_codec_name(reader.header.profile)
    

def get_av_framerate(reader):
    if (reader.header.port == hl2ss.StreamPort.RM_VLC_LEFTFRONT):
        return hl2ss.Parameters_RM_VLC.FPS
    if (reader.header.port == hl2ss.StreamPort.RM_VLC_LEFTLEFT):
        return hl2ss.Parameters_RM_VLC.FPS
    if (reader.header.port == hl2ss.StreamPort.RM_VLC_RIGHTFRONT):
        return hl2ss.Parameters_RM_VLC.FPS
    if (reader.header.port == hl2ss.StreamPort.RM_VLC_RIGHTRIGHT):
        return hl2ss.Parameters_RM_VLC.FPS
    if (reader.header.port == hl2ss.StreamPort.RM_DEPTH_AHAT):
        return hl2ss.Parameters_RM_DEPTH_AHAT.FPS
    if (reader.header.port == hl2ss.StreamPort.PERSONAL_VIDEO):
        return reader.header.framerate
    if (reader.header.port == hl2ss.StreamPort.MICROPHONE):
        return hl2ss.Parameters_MICROPHONE.SAMPLE_RATE


def unpack_to_mp4(input_filenames, output_filename):
    readers = [hl2ss_io.create_rd(False, input_filename, hl2ss.ChunkSize.SINGLE_TRANSFER, None) for input_filename in input_filenames]
    [reader.open() for reader in readers]

    container = av.open(output_filename, mode='w')
    streams = [container.add_stream(get_av_codec_name(reader), rate=get_av_framerate(reader)) for reader in readers]
    codecs = [av.CodecContext.create(get_av_codec_name(reader), "r") for reader in readers]

    base = hl2ss._RANGEOF.U64_MAX

    for reader in readers:
        data = reader.read()
        if ((data is not None) and (data.timestamp < base)):
            base = data.timestamp

    [reader.close() for reader in readers]
    [reader.open() for reader in readers]

    time_base = fractions.Fraction(1, hl2ss.TimeBase.HUNDREDS_OF_NANOSECONDS)

    for i in range(0, len(input_filenames)):
        while (True):
            data = readers[i].read()
            if (data is None):
                break
            for packet in codecs[i].parse(data.payload):
                packet.stream = streams[i]
                packet.pts = data.timestamp - base
                packet.dts = packet.pts
                packet.time_base = time_base
                container.mux(packet)

    container.close()
    [reader.close() for reader in readers]


#------------------------------------------------------------------------------
# Math
#------------------------------------------------------------------------------

def clamp(v, min, max):
    return min if (v < min) else max if (v > max) else v


#------------------------------------------------------------------------------
# Timing
#------------------------------------------------------------------------------

class continuity_analyzer:
    def __init__(self, period):
        self._period = period
        self._ub = 1.5 * self._period
        self._lb = 0.5 * self._period
        self._last = None

    def push(self, timestamp):
        if (self._last is None):
            status = (0, -1)
        else:
            delta = timestamp - self._last
            status = (1, delta) if (delta > self._ub) else (-1, delta) if (delta < self._lb) else (0, delta)
        self._last = timestamp
        return status


class framerate_counter:
    def reset(self):
        self._count = 0
        self._start = time.perf_counter()

    def increment(self):
        self._count += 1
        return self._count

    def delta(self):
        return time.perf_counter() - self._start

    def get(self):
        return self._count / self.delta()


class stream_report:
    def __init__(self, notify_period, stream_period):
        self._np = notify_period
        self._ca = continuity_analyzer(stream_period)
        self._fc = framerate_counter()
        self._fc.reset()

    def _report_continuity(self, timestamp):
        status, delta = self._ca.push(timestamp)
        if (status != 0):
            print('Discontinuity detected with delta time {delta}'.format(delta=delta))

    def _report_framerate_and_pose(self, timestamp, pose):
        self._fc.increment()
        if (self._fc.delta() >= self._np):
            print('FPS: {fps}'.format(fps=self._fc.get()))
            print('Pose at {timestamp}'.format(timestamp=timestamp))
            print(pose)
            self._fc.reset()

    def push(self, data):
        self._report_continuity(data.timestamp)
        self._report_framerate_and_pose(data.timestamp, data.pose)

