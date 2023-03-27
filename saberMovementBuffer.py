from typing import *
from typeDefs import SaberMovementData
from bsor.Bsor import VRObject
from Geometry import Vector3, Quaternion

BUFFER_SIZE = 500


class SaberMovementBuffer:
    data: List[SaberMovementData]
    nextAddIndex: int

    def __init__(self):
        data = [None] * BUFFER_SIZE
        nextAddIndex = 0

    def get_curr(self):
        return self.data[(self.nextAddIndex - 1) % BUFFER_SIZE]

    def get_prev(self):
        return self.data[(self.nextAddIndex - 2) % BUFFER_SIZE]

    def add_saber_data(self, hand_object: VRObject, time: float):
        new_data = SaberMovementData()
        curr_data = self.get_curr()
        self.data[self.nextAddIndex] = new_data
        self.nextAddIndex = (self.nextAddIndex + 1) % BUFFER_SIZE

        new_data.hiltPos = Vector3(hand_object.x, hand_object.y, hand_object.z)
        new_data.tipPos = Vector3(0, 1, 0).rotate(
            Quaternion(hand_object.x, hand_object.y, hand_object.z, hand_object.w)
        )
        new_data.time = time

        if curr_data is None:
            new_data.cutPlaneNormal = 0
            return
        new_data.cutPlaneNormal = (new_data.hiltPos - new_data.tipPos).cross(
            new_data.hiltPos - (curr_data.tipPos + curr_data.hiltPos) / 2
        ).normal()

    class BufferIterator:
        def __init__(self, buffer):
            self.buffer = buffer
            self.relativeIndex = 0

        def __next__(self):
            if self.relativeIndex >= BUFFER_SIZE:
                raise StopIteration

            output = self.buffer.data[(self.buffer.nextAddIndex - self.relativeIndex) % BUFFER_SIZE]

            if output is None:
                raise StopIteration

            self.relativeIndex += 1
            return output

    def __iter__(self):
        return self.BufferIterator(self)
