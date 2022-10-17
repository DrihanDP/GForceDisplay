#####################################################
# @module    shape.py                               #
# @brief     Tool for drawing basic filled shape    #
# @author    Jamie Bird and Pierre Hasham           #
# @date      June 2020                              #
# @copyright Racelogic Ltd., 2020                   #
# @Version   2.0                                    #
#####################################################

#from time import sleep
import ft8xx as ft
import gui
import math as m
from micropython import const

######## TODO #############
"""
- Add the gradient shape used in Accel Demo but make universal
- optimise instructions to include less display list commands?
- get it to work with gui.redraw() instead of needing to draw entire display list again
- Make item clickable and enable callback (without the tag manager)
"""
#########################

LEFT = const(0)
RIGHT = const(1)

class Shapes():
    """
    Basic shape object that can be filled with a single colour

    Returns:
        obj: shape object
    """

    def __init__(self, coord=[0,0], angle=0, fill=False, outline_colour=gui.RGB(0,0,0), fill_colour=gui.RGB(0,0xFF,0)):
        """
        Args:
            x (int): X_Centre Position (Not Yet Used)
            y (int): Y-Centre Position (Not Yet Used)
            shape (list): display list of points using DL_VERTEX2F (or similar)
            direction (int, optional): Not Yet Used. Defaults to 0.
            fill (bool, optional): Set initial state of object to filled or empty. Defaults to False.
            outline_colour (int, optional): Outline Colour (RGB). Defaults to 0x000000.
            fill_colour (int, optional): Fill Colour (RGB). Defaults to 0x00FF00.
        """

        self.x_start = coord[0]
        self.y_start = coord[1]
        self.start_angle = angle
        self.outline_colour = outline_colour
        self.fill_colour = fill_colour
        self.fill = fill
        self.DL = []

    def __call__(self):
        self.construct_shape()
        print("DL: ")
        print(self.DL)

        self.gui_l = [
            [gui.DL_SAVE_CONTEXT()],
            [gui.DL_LINE_WIDTH(2)],
            [gui.DL_COLOR(self.outline_colour)],
            [gui.DL_BEGIN(gui.PRIM_LINE_STRIP)]] + self.DL + [[gui.DL_END()],
            [gui.DL_STENCIL_OP(ft.STENCILOP_INCR, ft.STENCILOP_INCR)],
            [gui.DL_COLOR_MASK(0, 0, 0, 0)],
            [gui.DL_BEGIN(gui.PRIM_EDGE_STRIP_L)]] + self.DL + [[gui.DL_END()],
            [gui.DL_COLOR_MASK(1, 1, 1, 1)],]
            
        if self.fill:
            self.gui_l.extend([
                gui.DL_COLOR(self.fill_colour),
                gui.DL_STENCIL_FUNC(ft.ALPHAFUNC_EQUAL, 1, 255),
                gui.DL_BEGIN(gui.PRIM_EDGE_STRIP_L),
                gui.DL_VERTEX2F(800, 0),       #0
                gui.DL_VERTEX2F(800, 480),
                gui.DL_END(),
                ])

        self.gui_l.extend([
                gui.DL_STENCIL_FUNC(ft.ALPHAFUNC_ALWAYS, 0, 255),
                gui.DL_CLEAR(0, 1, 0),
                gui.DL_RESTORE_CONTEXT(),
                ])


        return self.gui_l

    def toggle_fill(self, cb=None):
        self.fill = False if self.fill else True
        # draw()

        return self.gui_l

class Custom_Shape(Shapes):
    def __init__(self, coord, angle, fill, outline_colour, fill_colour, *args):
        super().__init__(coord, angle, fill, outline_colour, fill_colour)
        self.points = [] # list of lists
        self.points.append(coord)
        for coord_pair in args:
            self.points.append(coord_pair)

    def rotate_around_start(self, angle_new):
        difference  = angle_new - self.start_angle # change in angle, easier for calculations
        while difference < 0: # accounts for negative rotations
            difference+=360

        for coord_pair in range(1, len(self.points)):
            tempx = self.x_start + ((self.points[coord_pair][0]-self.x_start)*m.cos(m.radians(difference))) - ((self.points[coord_pair][1]-self.y_start)*m.sin(m.radians(difference)))
            self.points[coord_pair][1] = self.y_start + ((self.points[coord_pair][0]-self.x_start)*m.sin(m.radians(difference))) + ((self.points[coord_pair][1]-self.y_start)*m.cos(m.radians(difference)))
            self.points[coord_pair][0] = tempx

        self.start_angle = angle_new # set the start things weith the new ones

    def move(self, new_x, new_y):
        self.x_start = self.x_start+new_x
        self.y_start = self.y_start+new_y
        for coord_pair in range(0, len(self.points)):
            self.points[coord_pair][0] = self.points[coord_pair][0]+new_x
            self.points[coord_pair][1] = self.points[coord_pair][1]+new_y
    
    def rotate_around_point(self, angle_new, new_x, new_y):
        self.rotate_around_start(angle_new)
        self.move(new_x, new_y)

    def construct_shape(self):
        self.DL = []
        print("POINTS: ")
        print(self.points)
        for coord_pair in range(0, len(self.points)):
            self.DL.extend([gui.DL_VERTEX2F(self.points[coord_pair][0], self.points[coord_pair][1])],)
        
        self.DL.extend([gui.DL_VERTEX2F(self.x_start, self.y_start)],)


class Reg_Shape(Shapes):
    def __init__(self, coord, angle, fill, outline_colour, fill_colour, radius = 20, num_sides=3):
        super().__init__(coord, angle, fill, outline_colour, fill_colour)
        self.num_sides = num_sides
        self.radius = radius
        self.flipx_bol = False
        self.flipy_bol = False
    
    def rotate(self, angle_new):
        self.start_angle = self.start_angle+angle_new
        self.construct_shape()
    
    def move(self, x_new, y_new):
        self.x_start = self.x_start+x_new
        self.y_start = self.y_start+y_new
        self.construct_shape()
    
    def rotate_around_point(self, angle_new, x_new, y_new):
        self.rotate(angle_new)
        self.move(x_new, y_new)

    def flip(self, x_plane, y_plane):
        self.flipx(x_plane)
        self.flipy(y_plane)
        self.construct_shape()

    def flipx(self, x_plane):
        if (self.flipx_bol == True) and (self.x_plane == x_plane):
            self.flipx_bol = False
        
        else:
            self.x_plane = x_plane
            self.flipx_bol = True

        self.construct_shape()

    def flipy(self, y_plane):
        if (self.flipy_bol == True) and (self.y_plane == y_plane):
            self.flipy_bol = False
        else:
            self.y_plane = y_plane
            self.flipy_bol = True
        self.construct_shape()

    def construct_shape(self):
        self.DL = []
        self.angle = self.start_angle-(360/self.num_sides)

        for i in range(0,self.num_sides+1):
            self.angle = self.angle+(360/self.num_sides)
            self.x = self.x_start + self.radius*m.cos(m.radians(self.angle))
            self.y = self.y_start + self.radius*m.sin(m.radians(self.angle))

            if self.flipx_bol == True:
                self.x = self.x_plane+(self.x_plane-self.x)
            if self.flipy_bol == True:
                self.x = self.x_plane+(self.x_plane-self.x)
            
            self.DL.extend([gui.DL_VERTEX2F(self.x, self.y)],)

if __name__ == "__main__":
    #Demo Use
    shape_example = Reg_Shape([300, 250], 45, True, gui.RGB(0,0,0), gui.RGB(255,0,0), 50, 3)
    shape_example2 = Reg_Shape([300, 250], 90, True, gui.RGB(0,0,0), gui.RGB(0,255,0), 50, 3)
    shape_example3 = Reg_Shape([300, 250], 45, True, gui.RGB(0,0,0), gui.RGB(255,0,255), 50, 3)
    shape_example3.flipx(400)
    cstm_shape_example = Custom_Shape([100, 100], 0, True, gui.RGB(0,0,0), gui.RGB(0,0,0), [140, 160], [100,160], [60, 100])
    cstm_shape_example2 = Custom_Shape([100, 100], 0, True, gui.RGB(0,0,0), gui.RGB(0,0,0), [140, 160], [100,160], [60, 100])
    cstm_shape_example2.rotate_around_start(167)
    cstm_shape_example3 = Custom_Shape([100, 100], 0, True, gui.RGB(0,0,0), gui.RGB(0,0,0), [140, 160], [100,160], [60, 100])
    cstm_shape_example3.move(100,100)
    cstm_shape_example4 = Custom_Shape([100, 100], 0, True, gui.RGB(0,0,0), gui.RGB(0,0,0), [140, 160], [100,160], [60, 100])
    cstm_shape_example4.rotate_around_point(167, 100, 100)

    gui_l = [
            [gui.DL_SAVE_CONTEXT()],
            [gui.DL_CLEAR_COLOR_RGB(0, 41, 66)],
            [gui.DL_CLEAR(1, 1, 1)],
            [gui.DL_SCISSOR_SIZE(800, 350)],
            [gui.DL_SCISSOR_XY(0, 65)],
            [gui.DL_CLEAR_COLOR_RGB(255, 255, 255)],
            [gui.DL_CLEAR(1, 1, 1)],
            [gui.DL_RESTORE_CONTEXT()],
            [gui.DL_COLOR_RGB(255, 255, 255)],
            [gui.CTRL_TEXT, 30, 30, 28, 0, 'SHAPES EXAMPLE'],
            [gui.DL_COLOR_RGB(0, 0, 0)],
            [gui.CTRL_TEXT, 400, 240, 32, gui.OPT_CENTER, '0.5'],
            shape_example(),
            shape_example2(),
            shape_example3(),
            cstm_shape_example(),
            cstm_shape_example2(),
            cstm_shape_example3(),
            cstm_shape_example4(),
        ]

    gui.show(gui_l)
