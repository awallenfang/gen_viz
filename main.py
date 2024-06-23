from OpenGL.GLUT import *
from OpenGL.GL import *
# from OpenGL.GLU import *
import numpy as np

from visualizer import Visualizer
from renderer import Renderer




if __name__ == "__main__":
    visualizers = []

    renderer = Renderer()
        

    x = np.linspace(0,400 * np.pi, 2000000)
    audio = 0.2 * np.sin(x) * (1/(x+0.000000000001))
    # audio += np.sin(2*x)
    # audio += 2*np.sin(8*x)
    # audio += 5*np.sin(100*x)

    audio /= 4.

    vis = Visualizer(audio, 48000)
    visualizers.append(vis)

    renderer.bind_visualizers(visualizers)

    renderer.render()