import copy
from inspect import getmembers, isfunction
import matplotlib
import numpy as np

class EditorTool(object):

    def __init__(self, canvas, editor_gui, ax):
        self.canvas = canvas
        self.ax = ax
        self.active = False
        # self.child = child
        # figure gui tracks the current object
        self.editor_gui = editor_gui
        self.color = editor_gui.color

        self.element_type = None
        self.element_label = None
        self.dragged_element = None
        self.tool_start_position = None

        self.step_size_arrow_keys_inch = 0.01
        self.rel_buffer_for_moving_out_of_axes = 0.05

    def only_do_for_correct_object(function):

        def wrapper(self, *args, **kwargs):
            # per default get the current element from kwargs supplied to the
            # function
            selected_element = kwargs.get("selected_element", None)

            # if the function has the parameter event as keyword
            # use artist property of event is it exists
            if selected_element is None:
                event = kwargs.get( "event", None)
                if hasattr(event, "artist"):
                    selected_element = event.artist

            # for several pyqt functions a  parameter of a function
            # (often the second parameter, after the parameter self)
            # is the event and may have the attribute artist
            if selected_element is None:
                for argument in args:
                    if hasattr(argument, "artist"):
                        selected_element = argument.artist
                        break

            # Lastly check whether there is a current element in the gui
            # since the function will likely be executed on the current element
            # if no element is supplied by the function parameters
            if selected_element is None:
                selected_element = self.editor_gui.selected_element

            # check whether the object has the correct object type
            correct_object_type = False
            if (isinstance(selected_element, self.element_type)):
                correct_object_type = True

            # check whether object has correct label, if a label can be set
            # for the object and if the class has not None defined element_label
            correct_label = True
            if (hasattr(selected_element, "get_label") &
                    (self.element_label is not None)):
                label = selected_element.get_label()
                if label != self.element_label:
                    correct_label = False

            # only execute function if the selected ax is the ax used
            # for the tool (otherwise tools from multiple ax are executed)
            selected_ax_label = self.editor_gui.selected_ax.get_label()
            correct_ax_label = self.ax.get_label()
            if selected_ax_label == selected_ax_label:
                correct_ax = True
            else:
                correct_ax = False

            if correct_object_type & correct_label & correct_ax:
                return function(self, *args, **kwargs)

        return wrapper


    def get_movement_and_modifier_keys(self, event):
        all_keys = event.key.split("+")
        keys_that_move = ["up", "down", "left", "right"]
        modifier_keys = []
        movement_keys = []
        for key in all_keys:
            if key in keys_that_move:
                movement_keys.append(key)
            else:
                modifier_keys.append(key)
        return movement_keys, modifier_keys


    def get_step_sizes_for_modifier_keys(self, modifier_keys,
                                         ax):
        figure_size = self.canvas.figure.get_size_inches()
        axes_position = ax.get_position()
        axes_width_inch = axes_position.width * figure_size[0]
        axes_height_inch = axes_position.height * figure_size[1]
        axes_x_lim = ax.get_xlim()
        axes_width_px = max(axes_x_lim) - min(axes_x_lim)
        axes_y_lim = ax.get_ylim()
        axes_height_px = max(axes_y_lim) - min(axes_y_lim)

        step_size_to_use = copy.copy(self.step_size_arrow_keys_inch)
        if ("ctrl" in modifier_keys) & ("shift" not in modifier_keys):
            step_size_to_use *= 5
        if ("shift" in modifier_keys) & ("ctrl" not in modifier_keys):
            step_size_to_use /= 5
        if ("shift" in modifier_keys) & ("ctrl" in modifier_keys):
            step_size_to_use *= 10
        step_size_x = step_size_to_use / axes_width_inch * axes_width_px
        step_size_y = step_size_to_use / axes_height_inch * axes_height_px
        return step_size_x, step_size_y


    def get_position_after_step(self, position, movement_keys,
                                step_size_x, step_size_y):
        position = np.array(position)
        if len(position.shape) == 1:
            position_array = np.expand_dims(position, 0)
        else:
            position_array = position
        position_after_step = copy.copy(position_array)
        if "right" in movement_keys:
            position_after_step[:,0] += step_size_x
        if "left" in movement_keys:
            position_after_step[:,0] -= step_size_x
        if "up" in movement_keys:
            position_after_step[:,1] -= step_size_y
        if "down" in movement_keys:
            position_after_step[:,1] += step_size_y
        if len(position.shape) == 1:
            position_after_step = position_after_step[0,:]
        return position_after_step


    def get_position_in_limits(self, position, ax):
        x_lim = ax.get_xlim()
        y_lim = ax.get_ylim()
        width = max(x_lim) - min(x_lim)
        height = max(y_lim) - min(y_lim)
        buffer_px = min(width, height) * self.rel_buffer_for_moving_out_of_axes
        x_lim = [min(x_lim), max(x_lim) - buffer_px]
        y_lim = [min(y_lim), max(y_lim) - buffer_px]
        new_pos_in_limits = [min(x_lim[1], max(x_lim[0], position[0])),
                             min(y_lim[1], max(y_lim[0], position[1]))]
        return new_pos_in_limits

    @only_do_for_correct_object
    def on_pick_event(self, event):
        #Store which text object was picked and were the pick event occurs.
        # don't allow picking up elements while a tool is activated
        # if self.active_tool is not None:
        #     return False
        # switch color of current selected element back to self.color
        if self.editor_gui.selected_element is not None:
            self.editor_gui.selected_element.set_color(self.color)
        if self.editor_gui.element_is_picked:
            return False
        event.artist.set_color("red")
        self.editor_gui.element_is_picked = True
        self.canvas.setFocus()
        self.editor_gui.selected_element = event.artist
        self.canvas.draw()
        self.dragged_element = event.artist
        self.pick_pos = [event.mouseevent.xdata, event.mouseevent.ydata]
        return True


    def activate(self, ax =None):
        self.active = True

    def deactivate(self):
        self.active = False