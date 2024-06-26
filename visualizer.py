from OpenGL.GLUT import *
from OpenGL.GL import *
# from OpenGL.GLU import *

import numpy as np
import matplotlib.pyplot as plt
from shader import Shader

from bin import Bin

class Visualizer():
    def __init__(self, audio_stream: np.array, sample_rate: float, x_origin = 0., y_origin = 0., window_width = 500, window_height = 500, width = 500, height= 500, spectrum_bins = 5, depth=0., shader = None, padding=0.002):
        
        self.audio_stream = audio_stream
        self.sample_rate = sample_rate
        self.fps = 30.
        self.spectrum_bins = spectrum_bins
        self.z = depth
        self.padding = padding
        self.x = x_origin
        self.y = y_origin
        self.width = width
        self.height = height
        self.window_width = window_width
        self.window_height = window_height

        self.origin_offset_x = (window_width / 2) / self.window_width
        self.origin_offset_y = (window_height / 2) / self.window_height

        if shader == None:
            self.shader = Shader("./shaders/default.frag")
        else:
            self.shader = shader

        self.samples_per_frame = self.sample_rate / self.fps

        self.fft_size = 0
        i = 0
        # Choose the smallest power of two that can incapsulate all frames for a fast fft and free smoothing
        while self.fft_size < self.samples_per_frame:
            self.fft_size = 2**i
            i+=1

        self.transport_pos = 0.

        self.bins = [Bin(0) for i in range(0,spectrum_bins)]

        self.transform = np.identity(4)
        self.build_transform_matrix()

        verts = self.vertices()

        self.vao = GLuint(0)
        glGenVertexArrays(1, self.vao)
        
        self.vbo = GLuint(0)
        glGenBuffers(1, self.vbo)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER,  verts, GL_STATIC_DRAW)

        glBindVertexArray(self.vao)

        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, float_size(3), 0)
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

        self.fill_bins()

        print(f'Initialized Visualizer using audio stream with {len(audio_stream)} samples and {self.fps} FPS resulting in {self.samples_per_frame} samples/frame. \nUsing a fft buffer size of {self.fft_size} samples. \nWith a sample rate of {self.sample_rate} its duration is {len(self.audio_stream) / self.sample_rate} seconds')

    def set_fps(self, fps: float):
        self.fps = fps
        self.samples_per_frame = self.sample_rate / self.fps

    def set_sample_rate(self, sample_rate: float):
        self.sample_rate = sample_rate
        self.samples_per_frame = self.sample_rate / self.fps

    def tick(self):
        self.transport_pos += self.samples_per_frame
        self.fill_bins()

    def fill_bins(self):
        # Run fft and pad remaining space with 0s
        # data_slice = np.zeros(int(self.fft_size))
        # data_slice[:int(self.samples_per_frame)] = self.audio_stream[int(self.transport_pos):int(self.transport_pos) + int(self.samples_per_frame)]
        
        # # Due to the mirrored nature we just need half the output
        # complex_fft_data: np.array[complex] = np.fft.fft(data_slice)[:len(data_slice) // 2 + 1]
        # fft_magnitude: np.array[float] = complex_fft_data.real ** 2 + complex_fft_data.imag ** 2

        # # Convert the magnitudes to dB
        # # TODO: Check if this is the correct dB formula
        # fft_magnitude = 10 * np.log10(fft_magnitude)
        # fft_magnitude[fft_magnitude < -90.] = -90.


        # Slice magnitudes into equal bins
        bin_width = 1092 // self.spectrum_bins #len(fft_magnitude) // self.spectrum_bins
        for i in range(0, self.spectrum_bins):
            start = i * bin_width
            # bin_sum = sum(fft_magnitude[start:start+bin_width]) / bin_width

            # self.bins[i].update(bin_sum) 
            self.bins[i].update(i / self.spectrum_bins)

    def vertices(self):
        vertices = []
        # x and y go from -1 to 1 so the full width is 2
        bin_width = 2 / self.spectrum_bins

        for i in range(0, self.spectrum_bins):
            x = -1 + i * bin_width
            y = -1 + 2 * self.bins[i].linear_val()

            bar_rect = [
                [x + self.padding, y, self.z], # top left
                [x + self.padding, -1, self.z], # bottom left
                [x - self.padding + bin_width, -1, self.z], # bottom right
                [x + self.padding, y, self.z], # top left
                [x - self.padding + bin_width, -1, self.z], # bottom right
                [x - self.padding + bin_width, y, self.z] # top right
                        ]
            vertices += bar_rect


        return np.array(vertices)
    
    def bind_shader(self, shader: Shader):
        self.shader = shader

    def draw(self):
        self.shader.bind()
        # TODO: Bind transformation matrix
        transform_location = glGetUniformLocation(self.shader.program, 'transform')
        pos_location = glGetUniformLocation(self.shader.program, 'pos')


        glUniformMatrix4fv(transform_location,1,False,self.transform)
        # print(self.x, self.y)
        # print(self.x - self.origin_offset_x, self.y - self.origin_offset_y)
        glUniform2fv(pos_location, 1, [self.x + self.origin_offset_x, self.y + self.origin_offset_y])
        glBegin(GL_TRIANGLES)
        for vert in self.vertices():
            glVertex3f(*vert)
        glEnd()

        # TODO: Figure out vertex arrays later
        # glBindVertexArray(self.vao)
        # glDrawArrays(GL_TRIANGLES, 0, len(self.vertices()))

    def set_position(self, x, y):
        self.x = 2 * (x / self.window_width)
        self.y = 2 * ((y / self.window_height) * -1)

    def set_width(self, width):
        self.width = width / self.window_width
        self.origin_offset_x = -(1 - self.width)
        print(self.origin_offset_x)
        self.build_transform_matrix()

    def set_height(self, height):
        self.height = height / self.window_height
        self.origin_offset_y = (1 - self.height)
        self.build_transform_matrix()

    def build_transform_matrix(self):

        self.transform =  np.array([[self.width, 0, 0, 0],
                                   [0,self.height, 0, 0],
                                   [0,0,1,0],
                                   [0,0,0,1]])
    

def float_size(n=1):
    return sizeof(ctypes.c_float) * n

