from .editor_tool import EditorTool
from . import shape_editor
import matplotlib

class ArrowEditor(shape_editor.ShapeEditor):

    def __init__(self, arrow_length_inch, **kwargs):
        super().__init__( **kwargs)
        self.element_type = matplotlib.patches.FancyArrow

        self.new_arrow = None
        self.arrow_length_inch = arrow_length_inch

        self.canvas.mpl_connect("pick_event", self.on_pick_event)
        self.canvas.mpl_connect("motion_notify_event", self.drag_arrow)
        self.canvas.mpl_connect("key_press_event", self.move_arrow)


    def add_arrow(self, end_position):

        (arrow_head_position,
        d_x, d_y) = self.get_arrow_coords_at_standard_length(self.tool_start_position,
                                                            end_position,
                                                            self.arrow_length_inch,
                                                            self.editor_gui.selected_ax)

        self.arrow_head_position = arrow_head_position
        self.d_x_arrow = d_x
        self.d_y_arrow = d_y
        if ((self.new_arrow is not None) &
                (isinstance(self.new_arrow, matplotlib.patches.FancyArrow))):
            self.new_arrow.remove()

        self.new_arrow = self.editor_gui.selected_ax.arrow(self.arrow_head_position[0],
                               self.arrow_head_position[1],
                               -self.d_x_arrow,-self.d_y_arrow,
                                 width=10,
                                head_width=100,
                                 head_length=50,
                               picker=True,
                                transform=self.editor_gui.selected_ax.transData,
                               color="red",
                                 length_includes_head=True,lw=0)

        self.editor_gui.selected_ax._stale_viewlim_x = False
        self.editor_gui.selected_ax._stale_viewlim_y = False
        self.canvas.draw()
        return True

    def get_arrow_coords_at_standard_length(self, head_position,
                                              orig_tail_position,
                                              arrow_length_inch,
                                              ax):
        d_x = orig_tail_position[0] - head_position[0]
        d_y = orig_tail_position[1] - head_position[1]
        x_y_ratio = d_x / d_y
        figure_size_inch = self.editor_gui.figure.get_size_inches()
        ax_x_lim = ax.get_xlim()
        ax_width_px = max(ax_x_lim) - min(ax_x_lim)
        ax_width_inch = (figure_size_inch[0] *
                         ax.get_position().width)
        arrow_length_px = (arrow_length_inch / ax_width_inch *
                           ax_width_px)
        d_x_arrow = ((arrow_length_px**2 * x_y_ratio**2)/(x_y_ratio**2 + 1)) ** 0.5
        d_y_arrow = (arrow_length_px**2 - d_x_arrow**2) ** 0.5

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
        d_x = event.xdata - self.pick_pos[0]
        d_y = event.ydata - self.pick_pos[1]
        self.pick_pos = [event.xdata, event.ydata]
        position = self.dragged_element.xy
        position[:,0] += d_x
        position[:,1] += d_y
        self.dragged_element.set_xy(position)
        self.canvas.draw()

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