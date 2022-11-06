from .editor_tool import EditorTool
from . import shape_editor
import matplotlib
import inspect
import copy

class ArrowEditor(shape_editor.ShapeEditor):

    def __init__(self, arrow_props, **kwargs):
        """
        :param arrow_props: dict with arrow parameters as keys and values in pt
                            possible parameters: width, head_width, head_length
        """
        super().__init__( **kwargs)
        self.element_type = matplotlib.patches.FancyArrow
        self.all_arrows = []

        self.new_arrow = None
        self.arrow_length = arrow_props.get("length",None)
        axis_width_data = max(self.ax.get_xlim()) - min(self.ax.get_xlim())
        if self.arrow_length is None:
            # calculate default length from default value of
            default_length_pt = self.default_in_drawing_arrow_func("size")
            # correct by size_factor as it is done in function that draws erros
            # (figure_panel.draw_on_image)
            default_length_pt *= self.editor_gui.figure_panel.size_factor
            self.arrow_length = default_length_pt

        # get arrow length in axes data
        # first get axes width in data coords
        axis_width_inches = (self.ax.get_position().width *
                             self.ax.figure.get_size_inches()[0])

        # get parameter values from arrow_props dict or
        # from default values when drawing the arrow
        param_names = ["width_factor", "head_width_factor","head_length_factor"]
        param_factors_names = ["arrow_width_factor",
                           "arrow_head_width_factor",
                           "arrow_head_length_factor"]
        for param_name, param_fac_name in zip(param_names, param_factors_names):
            default_factor = self.default_in_drawing_arrow_func(param_fac_name)
            default_value = self.arrow_length * default_factor
            param_value_pt = arrow_props.get(param_name, default_value)
            # set factor that was used
            setattr(self, param_name,
                    param_value_pt/self.arrow_length)
            #scale to axes values
            param_value_inch = param_value_pt / 72
            param_value_data = ((param_value_inch / axis_width_inches) *
                                axis_width_data)
            # set parameter on self
            setattr(self, param_name.replace("_factor", ""), param_value_data)

        self.arrow_label = "___"
        self.arrow_label += str(self.width_factor) + "_"
        self.arrow_label += str(self.head_width_factor)+ "_"
        self.arrow_label += str(self.head_length_factor)

        self.canvas.mpl_connect("pick_event", self.on_pick_event)
        self.canvas.mpl_connect("motion_notify_event", self.drag_arrow)
        self.canvas.mpl_connect("key_press_event", self.move_arrow)

        # get all arrows in current ax and make these zooms pickable
        for child in self.ax.get_children():
            if not isinstance(child, matplotlib.patches.FancyArrow):
                continue
            # now make them pickable and  add them to list
            child.set_picker(True)
            self.all_arrows.append(child)

    def default_in_drawing_arrow_func(self, arg_name):
        signature = inspect.signature(self.editor_gui.figure_panel.draw_on_image)
        default_value = signature.parameters[arg_name].default
        return default_value

    def add_arrow(self, end_position):

        # end_position = self.transform_coords_from_data_to_axes(end_position[0],
        #                                                        end_position[1],
        #                                                        self.ax)
        tool_start_position = copy.copy(self.tool_start_position)
        tool_start_position[1] = 1 - tool_start_position[1]
        tool_start_position = self.transform_coords_from_axes_to_data(tool_start_position[0],
                                                                      tool_start_position[1],
                                                                      self.ax)

        (arrow_end_position,
        d_x, d_y) = self.get_arrow_coords_at_standard_length(tool_start_position,
                                                            end_position,
                                                            self.arrow_length,
                                                            self.ax)

        self.arrow_end_position = arrow_end_position
        self.d_x_arrow = d_x
        self.d_y_arrow = d_y
        if ((self.new_arrow is not None) &
                (isinstance(self.new_arrow, matplotlib.patches.FancyArrow))):
            self.new_arrow.remove()

        # arrow_end_position_data = self.transform_coords_from_axes_to_data(self.arrow_end_position[0],
        #                                                              self.arrow_end_position[1],
        #                                                              self.ax)

        # (d_x_arrow_data,
         # d_y_arrow_data) = self.transform_coords_from_axes_to_data(self.d_x_arrow,
         #                                                           self.d_y_arrow,
         #                                                           self.ax)

        self.new_arrow = self.ax.arrow(self.arrow_end_position[0],
                                       self.arrow_end_position[1],
                                       -self.d_x_arrow,-self.d_y_arrow,
                                         width=self.width,
                                        head_width=self.head_width,
                                         head_length=self.head_length,
                                       picker=True,
                                        transform=self.ax.transData,
                                       color="red",
                                       label=self.arrow_label,
                                 length_includes_head=True,lw=0)
        self.ax._stale_viewlim_x = False
        self.ax._stale_viewlim_y = False
        self.canvas.draw()
        return True

    def get_arrow_coords_at_standard_length(self, head_position,
                                              orig_tail_position,
                                              arrow_length,
                                              ax):
        d_x = orig_tail_position[0] - head_position[0]
        d_y = orig_tail_position[1] - head_position[1]
        x_y_ratio = d_x / d_y
        figure_size_inch = self.editor_gui.figure.get_size_inches()
        axis_width_data = max(self.ax.get_xlim()) - min(self.ax.get_xlim())

        ax_width_inch = (figure_size_inch[0] *
                         ax.get_position().width)
        arrow_length_ax = (arrow_length/72 / ax_width_inch) * axis_width_data
        d_x_arrow = ((arrow_length_ax**2 * x_y_ratio**2)/(x_y_ratio**2 + 1)) ** 0.5
        d_y_arrow = (arrow_length_ax**2 - d_x_arrow**2) ** 0.5

        if d_x < 0:
            d_x_arrow = -d_x_arrow
        if d_y < 0:
            d_y_arrow = -d_y_arrow

        arrow_end_position = [head_position[0] + d_x_arrow,
                              head_position[1] + d_y_arrow]

        return arrow_end_position, d_x_arrow, d_y_arrow

    def end_tool(self, event):
        if not self.active:
            return False
        if self.editor_gui.element_is_picked:
            self.editor_gui.element_is_picked = False
            self.dragged_element = None
            self.tool_start_position = None
            self.editor_gui.tool_start_position = None
            return False
        if self.tool_start_position is None:
            return False

        self.tool_start_position = None
        self.editor_gui.tool_start_position = None
        self.dragged_element = None

        if self.new_arrow is not None:
            self.editor_gui.selected_element = self.new_arrow
            self.all_arrows.append(self.new_arrow)
            self.new_arrow = None
            self.canvas.draw()

    @EditorTool.only_do_for_correct_object
    def drag_arrow(self, event):
        if self.dragged_element is None:
            return False
        if event.xdata is None:
            return False
        if self.editor_gui.moved_out_of_ax:
            return False
        # self.dragged_element.remove()
        x_pos_data = event.xdata
        y_pos_data = event.ydata
        (x_pos_ax,
        y_pos_ax) = self.transform_coords_from_data_to_axes(x_pos_data,
                                                             y_pos_data,
                                                             self.ax)

        d_x = x_pos_ax- self.pick_pos[0]
        d_y = y_pos_ax - self.pick_pos[1]
        self.pick_pos = [x_pos_ax, y_pos_ax]

        position = self.dragged_element.xy

        position[:,0] += d_x
        position[:,1] += d_y
        self.dragged_element.set_xy(position)
        self.canvas.draw()

    @EditorTool.only_do_for_correct_object
    def remove_element(self, event):
        if self.editor_gui.selected_element is None:
            return False
        if event.key not in ["delete", "backspace"]:
            return False
        self.all_arrows.remove(self.editor_gui.selected_element)
        super().remove_element(event)

    @EditorTool.only_do_for_correct_object
    def move_arrow(self, event):
        """
        Move currently selected text element with arrow keys.
        Pressing Control (ctrl) and arrow key increases movement speed 5 fold
        Pressing shift (ctrl) and arrow key reduces movement speed 5 fold
        Pressing control and shift and arrow key increases speed 10 fold
        """
        if self.editor_gui.selected_element is None:
            return False
        if not self.active:
            return False

        (movement_keys,
         modifier_keys) = self.get_movement_and_modifier_keys(event)

        if len(movement_keys) == 0:
            return False

        ax = self.editor_gui.selected_element.axes
        (step_size_x,
        step_size_y) = self.get_step_sizes_for_modifier_keys(modifier_keys, ax)

        arrow_xy = self.editor_gui.selected_element.xy

        new_arrow_xy = self.get_position_after_step(arrow_xy,
                                                     movement_keys,
                                                     step_size_x, step_size_y)

        self.editor_gui.selected_element.set_xy(new_arrow_xy)

        self.canvas.draw()

    def use_tool(self, event):
        if not self.active:
            return False
        if self.tool_start_position is None:
            return False
        if self.editor_gui.moved_out_of_ax:
            return False
        # if an object of a differet type is picked, do not use the arrow tool
        if self.editor_gui.element_is_picked:
            if not isinstance(self.editor_gui.selected_element,
                              self.element_type):
                return False
        end_position = [event.xdata, event.ydata]
        self.add_arrow(end_position)
        return True