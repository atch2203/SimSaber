# As of this commit, a lot needs to change in this code. A lot of
# function and variable definitions are incorrect or not filled in.
# Also, special care should be taken to cast between C# floats and doubles
# (in numpy 'single' and 'double') in the same way that the source does.

from typeDefs import *
from typing import *
from math import cos, sin, pi as π
from numpy import single
from Geometry import Vector3, Quaternion
from bsor.Bsor import Bsor


def lerp_unclamped(a, b, t):
    return a + (b - a) * t


def lerp(a, b, t):
    if t < 0:
        t = 0
    if t > 1:
        t = 1
    return a + (b - a) * t


def quadratic_in_out(t):
    if t < 0.5:
        return 2 * t * t
    return (4 - 2 * t) * t - 1


def move_towards_head(a, b, q, t):
    return a


def quat_slerp(p, q, t):
    return lerp(p, q, t)   # This is incorrect


def look_rotation(forwards, up):
    return Quaternion(0, 0, 0, 1)


class NoteData:
    COLOR_A = 0
    COLOR_B = 1

    def __init__(self, map: Map, note: Note):
        self.time = note.time * map.beatsPerMinute
        self.line_index = note.lineIndex
        self.flip_line_index = note.lineIndex
        self.flip_y_side = 0
        self.cut_direction_angle_offset = 0
        self.line_layer = note.lineLayer
        self.before_line_layer = note.lineLayer
        self.note_type = note.type


class MovementData:
    BEAT_OFFSET = 0
    JUMP_DURATION = 1
    move_speed = 200
    move_duration = 1
    center_pos = Vector3(0, 0, 0.65)

    def __init__(self, map: Map, note_data: NoteData, bsor: Bsor):
        self.note_lines_count = 4
        start_NJS = 0  # Called startNoteJumpMovementSpeed
        start_bpm = map.beatsPerMinute
        self.jump_duration = bsor.info.jumpDistance / start_NJS  # Notably NOT the same way the game calculates it
        self.right_vec = Vector3(1, 0, 0)
        forward_vec = Vector3(0, 0, 1)
        self.move_distance = self.move_duration * self.move_duration
        self.jump_distance = start_NJS * self.jump_duration
        self.move_end_pos = self.center_pos + forward_vec * (self.jump_distance * 0.5)
        self.jump_end_pos = self.center_pos - forward_vec * (self.jump_distance * 0.5)
        self.move_start_pos = self.center_pos + forward_vec * (self.move_distance + self.jump_distance * 0.5)
        self.spawn_ahead_time = self.move_duration + self.jump_duration * 0.5

        note_offset_1 = self.get_note_offset(note_data.line_index, note_data.line_layer)
        self.jump_gravity = self.get_gravity()

    def get_note_offset(self, line_index, before_note_line_layer):
        return self.right_vec * ((-(self.note_lines_count - 1) * 0.5 + line_index) * 0.6) + Vector3(
            0, self.get_y_pos_from_layer(before_note_line_layer), 0)

    def get_y_pos_from_layer(self, layer):
        return 0

    def get_gravity(self):
        return 9.8


def create_note_position_function(map: Map, note: Note, bsor: Bsor):
    note_data = NoteData(map, note)
    movement_data = MovementData(map, note_data, bsor)
    movement_start_time = note_data.time - movement_data.move_duration - movement_data.jump_duration / 2
    jump_start_time = note_data.time - movement_data.jump_duration / 2
    move_duration = movement_data.move_duration
    jump_duration = movement_data.jump_duration
    floor_movement_start_pos = movement_data.move_start_pos
    floor_movement_end_pos = movement_data.move_end_pos
    jump_end_pos = movement_data.jump_end_pos
    gravity = movement_data.jump_gravity
    start_vertical_velocity = gravity * movement_data.jump_duration / 2
    y_avoidance = note_data.flip_y_side * 0.15 if note_data.flip_y_side <= 0 else note_data.flip_y_side * 0.45
    end_rotation = note_data.cut_direction + note_data.cut_direction_angle_offset
    middle_rotation = end_rotation
    if note_data.gameplay_type == NoteData.GameplayType.NORMAL:
        pass   # This is useRandomRotation. Needs Euler angles caulculations
    start_rotation = Quaternion(0, 0, 0, 1)
    rotate_towards_player = note_data.gameplay_type == NoteData.GameplayType.NORMAL
    world_rotation = Quaternion(0, 0, 0, 1)  # TBD how iportant this is yet
    inverse_world_rotation = Quaternion(0, 0, 0, 1)  # TBD how iportant this is yet
    world_to_player_rotation = Quaternion(0, 0, 0, 1)  # TBD how iportant this is yet
    rotated_object_up = Vector3(0, 1, 0)  # ###
    end_distance_offset = 500

    def position(time: float) -> Union(Vector3, None):
        relative_time = time - movement_start_time  # Called num1 in source

        # Called floor movement in code
        if relative_time < move_duration:
            return lerp(floor_movement_start_pos, floor_movement_end_pos, relative_time / move_duration)

        relative_time = time - jump_start_time  # Called num1 in source
        start_pos = floor_movement_end_pos
        end_pos = jump_end_pos
        percentage_of_jump = relative_time / jump_duration  # Called t in source

        local_pos = Vector3(0, 0, 0)  # Called localPosition in source

        if start_pos.x == end_pos.x:
            local_pos.x = start_pos.x
        elif percentage_of_jump >= 0.25:
            local_pos.x = end_pos.x
        else:
            local_pos.x = lerp_unclamped(start_pos, end_pos, quadratic_in_out(percentage_of_jump * 4))

        local_pos.y = start_pos.y + start_vertical_velocity * relative_time - gravity * relative_time * relative_time
        local_pos.z = move_towards_head(start_pos.z, end_pos.z, inverse_world_rotation, percentage_of_jump)

        if y_avoidance != 0 and percentage_of_jump < 0.25:
            local_pos.y += (0.5 - cos(percentage_of_jump * 8 * π)) * y_avoidance

        if percentage_of_jump < 0.5:
            if percentage_of_jump >= 0.25:
                a = quat_slerp(middle_rotation, end_rotation, sin((percentage_of_jump - 0.125) * π * 2))
            else:
                a = quat_slerp(start_rotation, middle_rotation, sin((percentage_of_jump * π * 4)))

            if rotate_towards_player:
                head_pseudo_location = Vector3(0, 0, 0)  # ###
                head_pseudo_location.y = lerp(head_pseudo_location.y, local_pos.y, 0.8)
                normalized = (local_pos - inverse_world_rotation * head_pseudo_location)
                vector3 = world_to_player_rotation * rotated_object_up
                b = look_rotation(normalized, inverse_world_rotation * vector3)
                rotated_object_local_rotation = lerp(a, b, percentage_of_jump * 2)
            else:
                rotated_object_local_rotation = a

        if percentage_of_jump >= 0.75:
            num2 = (percentage_of_jump - 0.75) / 0.25
            local_pos.z -= lerp_unclamped(0, end_distance_offset * num2 * num2 * num2)

        return world_rotation * local_pos

    return position
