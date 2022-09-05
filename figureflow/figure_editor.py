import sys
import copy
import math
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import widgets
import matplotlib
from matplotlib import patches
from matplotlib.text import Text

import numpy as np
import functools
np.random.seed(42)


# first of all implement bliting

# make a general class for "Editor"
# make subclass for "TextAdder" and "ImageEditor" (for arrows and zooms)
# for arrows make resizing possible by keyboard after selecting:
# shift plus arrow left for decreasing size, shift right for increasing size
# for decreasing and increasing keep arrow head at same position but enlarge
# tail of arrow

class FigureEditor(QtWidgets.QDialog):
    def __init__(self, figure_panel=None, font_size=7,
                 arrow_length_inch=0.2):
        super().__init__()

        if figure_panel is not None:
            self.figure = figure_panel.fig
        else:
            # a figure instance to plot on
            self.figure = Figure()

        self.figure_panel = figure_panel
        self.font_size = font_size
        self.arrow_length_inch = arrow_length_inch

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        self.canvas.draw()
        figure_size = self.canvas.figure.get_size_inches() * self.canvas.figure.dpi
        # self.resize(2000, 2000)
        self.canvas.setMinimumSize(self.canvas.size())
        self.resize(2000, 1000)

        qscroll_canvas = QtWidgets.QScrollArea()
        qscroll_canvas.setWidget(self.canvas)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        # self.toolbar = NavigationToolbar(self.canvas, self)

        self.text_input = QtWidgets.QLineEdit()

        self.print_code_button = QtWidgets.QPushButton('Print code')
        self.print_code_button.clicked.connect(self.print_code)

        self.add_text_button = QtWidgets.QPushButton('Add text')
        self.add_text_button.clicked.connect(self.add_text)

        self.qscroll_controls = QtWidgets.QScrollArea()
        self.qscroll_controls.setFixedWidth(600)
        # self.qscroll_controls.setWidgetResizable(True)
        controls_frame = QtWidgets.QFrame(self.qscroll_controls)
        controls_frame.setLayout(QtWidgets.QVBoxLayout())
        self.qscroll_controls.setWidget(controls_frame)
        self.controls_layout = controls_frame.layout()
        self.controls_layout.setAlignment(QtCore.Qt.AlignTop)

        self.all_tool_buttons = []

        self.arrow_tool = QtWidgets.QToolButton(self)
        self.arrow_tool.setText("Arrow")
        self.arrow_tool.setToolTip("Add an arrow to an image")
        # self.arrow_tool.setIcon(self.arrow_tool.style().standardIcon(QtWid
        # gets.QStyle.SP_MediaSeekForward))
        self.arrow_tool.setCheckable(True)
        self.arrow_tool.clicked.connect(self.activate_arrow_tool)
        self.all_tool_buttons.append(self.arrow_tool)

        self.zoom_tool = QtWidgets.QToolButton(self)
        self.zoom_tool.setText("Zoom")
        self.arrow_tool.setToolTip("Add a zoom area to an image")
        self.zoom_tool.setCheckable(True)
        self.zoom_tool.clicked.connect(self.activate_zoom_tool)
        self.all_tool_buttons.append(self.zoom_tool)

        tools = QtWidgets.QFrame()
        tools.setLayout(QtWidgets.QHBoxLayout())
        self.tools_layout = tools.layout()
        self.tools_layout.addWidget(self.arrow_tool)
        self.tools_layout.addWidget(self.zoom_tool)

        self.controls_layout.addWidget(tools )
        self.controls_layout.addWidget(self.print_code_button )
        self.controls_layout.addWidget(self.text_input )
        self.controls_layout.addWidget(self.add_text_button )
        self.controls_layout.setSizeConstraint(self.controls_layout.SetMinAndMaxSize)

        # set the layout
        self.layout = QtWidgets.QGridLayout()
        self.layout.addWidget(qscroll_canvas,0,0)
        self.layout.addWidget(self.qscroll_controls,0,1)

        controls_frame.setFixedWidth(550)

        self.setLayout(self.layout)

        self.change_text_inputs = {}
        self.delete_text_buttons = {}
        self.all_text_fields = {}

        self.all_zoom_rectangles = []

        self.selected_element = None
        self.dragged_element = None
        self.moved_out_of_ax = False
        self.active_tool = None
        self.selected_ax = None
        self.tool_start_position = None
        self.current_zoom_selector = None
        self.new_arrow = None
        self.element_is_picked = False
        self.step_size_arrow_keys_inch = 0.01
        self.rel_buffer_for_moving_out_of_axes = 0.05

        for _, ax in self.figure_panel.all_axs.items():
            selected = self._select_ax(ax)
            if selected:
                break

        self.canvas.mpl_connect("pick_event", self.on_pick_event)
        self.canvas.mpl_connect("button_release_event", self.on_release_event)
        self.canvas.mpl_connect("motion_notify_event", self.move_picked_element)
        self.canvas.mpl_connect("axes_leave_event", self.pause_dragging)
        self.canvas.mpl_connect("axes_enter_event", self.continue_dragging)
        self.canvas.mpl_connect("key_press_event", self.remove_element)

        self.canvas.mpl_connect("key_press_event", self.move_text)
        self.canvas.mpl_connect("pick_event", self.activate_zoom_rectangle)

        self.canvas.mpl_connect("motion_notify_event", self.drag_arrow)
        self.canvas.mpl_connect("key_press_event", self.move_arrow)

        self.canvas.mpl_connect("button_press_event", self.select_ax)

        # self.canvas.mpl_connect("key_press_event", self.move_zoom_rectangle)

        self.canvas.mpl_connect("button_press_event", self.start_tool)
        self.canvas.mpl_connect("motion_notify_event", self.use_tool)
        self.canvas.mpl_connect("button_release_event", self.end_tool)
        self.canvas.mpl_connect("axes_leave_event", self.pause_tool)
        self.canvas.mpl_connect("axes_enter_event", self.continue_tool)

        self.canvas.setFocusPolicy(QtCore.Qt.ClickFocus)

        # get text in current ax and add boxes for it
        for child in self.selected_ax.get_children():
            if not isinstance(child, Text):
                continue
            text = child.get_text()
            if text == "":
                continue
            text_field_number = self.get_next_text_field_number()
            child.set_label("textfield_" + str(text_field_number))
            self.all_text_fields[text_field_number] = child
            self.add_editor_for_text(text, text_field_number)

    def new_zoom_selector(self, ax):
        zoom_selector = widgets.RectangleSelector(ax,
                                                    self.select_rectangle,
                                                    drawtype='box', useblit=False,
                                                    button=[1,2],
                                                    minspanx=5, minspany=5,
                                                    spancoords='data',
                                                    interactive=True,
                                                    maxdist=10,
                                                    rectprops=dict(linestyle='-',
                                                                   color='red',
                                                                   linewidth=0.2,
                                                                   fill=False, alpha=1)
                                                    )
        for tool_handles in [zoom_selector._corner_handles,
                             zoom_selector._edge_handles,
                             zoom_selector._center_handle]:

            tool_handles.artist.set_mfc("grey")
            tool_handles.artist.set_alpha(1)
            tool_handles.artist.set_markersize(1)

        select_rectangle_with_details = functools.partial(self.select_rectangle,
                                                          zoom_selector=zoom_selector
                                                          )
        zoom_selector.onselect = select_rectangle_with_details
        return zoom_selector

    def create_zoom_selector(self, ax):
        zoom_selector = self.new_zoom_selector(ax)
        return zoom_selector

    def activate_zoom_rectangle(self, event):
        # do not allow multiple elements to be picked
        if self.element_is_picked:
            return False
        # only initiate activating new rectangle if the clicked zoom rectangle
        # is different from current zoom rectangle
        if self.selected_element is event.artist:
            return False
        if self.active_tool != "Zoom":
            return False
        zoom_rectangle = event.artist
        if (not isinstance(zoom_rectangle, matplotlib.patches.Rectangle)):
            return False
        # set True to prevent other events from happening until click is ended
        self.element_is_picked = True
        # do not allow interacting with zoom selector while new rect is activated
        self.current_zoom_selector.set_active(False)
        self.current_zoom_selector.set_visible(False)
        self.switch_active_zoom_rectangle(zoom_rectangle)

    def switch_active_zoom_rectangle(self, new_zoom_rectangle):
        if self.selected_element is not None:
                if ((isinstance(self.selected_element, matplotlib.text.Text)) |
                        (isinstance(self.selected_element, matplotlib.patches.FancyArrow))):
                    self.selected_element.set_color("black")
                else:
                    self.selected_element.set_edgecolor("black")
        if new_zoom_rectangle is not None:
            new_zoom_rectangle.set_edgecolor("red")
        self.all_zoom_rectangles.append(new_zoom_rectangle)
        self.selected_element = new_zoom_rectangle
        return True

    def select_rectangle(self, click_event, release_event, zoom_selector=None,
                         zoom_selector_number=None):
        if self.element_is_picked:
            return False
        if self.active_tool != "Zoom":
            return False
        zoom_rect = self.replace_zoom_selector_with_rectangle(self.current_zoom_selector)
        self.switch_active_zoom_rectangle(zoom_rect)
        return True

    def start_tool(self, event):
        if self.active_tool is None:
            return False
        if self.element_is_picked:
            return False
        if self.selected_element is not None:
            if ((isinstance(self.selected_element, matplotlib.text.Text)) |
                    (isinstance(self.selected_element, matplotlib.patches.FancyArrow))):
                self.selected_element.set_color("black")
        self.tool_start_position = [event.xdata, event.ydata]

    def replace_zoom_selector_with_rectangle(self, zoom_selector):
        last_zoom_size = zoom_selector._rect_bbox
        rect = patches.Rectangle((last_zoom_size[0], last_zoom_size[1]),
                                 last_zoom_size[2], last_zoom_size[3],
                                 linewidth=0.2, edgecolor='red',
                                 picker=True,
                                 facecolor='none')
        zoom_selector.ax.add_patch(rect)
        self.canvas.draw()
        return rect

    def use_tool(self, event):
        if self.active_tool is None:
            return False
        if self.tool_start_position is None:
            return False
        if self.moved_out_of_ax:
            return False
        end_position = [event.xdata, event.ydata]
        if self.active_tool == "Zoom":
            if self.element_is_picked:
                return False
            # set edge color of previous zoom rectangle to black
            # so that when drawing a new zoom rectangle, the previous one
            # immediately switches edge color from red to black
            if self.selected_element is not None:
                self.selected_element.set_edgecolor("black")
            if ((self.current_zoom_selector.active_handle is not None) &
                    (self.selected_element is not None)):
                self.all_zoom_rectangles.remove(self.selected_element)
                self.selected_element.remove()
                self.selected_element = None
                self.canvas.draw()

        if self.active_tool == "Arrow":
            self.add_arrow(end_position)
        return True

    def replace_zoom_rectangle_with_selector(self, rect):
        # new_zoom_selector = self.new_zoom_selector(rect.axes)
        zoom_size = rect.get_bbox()
        self.current_zoom_selector.extents = (zoom_size.x0, zoom_size.x1,
                                              zoom_size.y0, zoom_size.y1)
        return True

    def end_tool(self, event):
        if self.active_tool is None:
            return False
        if self.element_is_picked:
            self.element_is_picked = False
            self.replace_zoom_rectangle_with_selector(self.selected_element)
            self.current_zoom_selector.set_active(True)
            self.current_zoom_selector.set_visible(True)
            return False
        if self.tool_start_position is None:
            return False

        if self.active_tool == "Arrow":
            if self.new_arrow is not None:
                self.selected_element = self.new_arrow
                self.new_arrow = None
                self.canvas.draw()

        self.tool_start_position = None

    def pause_tool(self, event):
        if self.tool_start_position is None:
            return False
        self.moved_out_of_ax = True

    def continue_tool(self, event):
        if self.tool_start_position is None:
            return False
        if self.moved_out_of_ax == False:
            return False
        tool_axis_label =  self.selected_element.axes.get_label()
        entered_axis_label = event.inaxes.get_label()
        if tool_axis_label == entered_axis_label:
            self.moved_out_of_ax = False


    def add_arrow(self, end_position):

        (arrow_head_position,
        d_x, d_y) = self.get_arrow_coords_at_standard_length(self.tool_start_position,
                                                            end_position,
                                                            self.arrow_length_inch,
                                                            self.selected_ax)

        self.arrow_head_position = arrow_head_position
        self.d_x_arrow = d_x
        self.d_y_arrow = d_y
        if ((self.new_arrow is not None) &
                (isinstance(self.new_arrow, matplotlib.patches.FancyArrow))):
            self.new_arrow.remove()

        self.new_arrow = self.selected_ax.arrow(self.arrow_head_position[0],
                               self.arrow_head_position[1],
                               -self.d_x_arrow,-self.d_y_arrow,
                                 width=10,
                                head_width=100,
                                 head_length=50,
                               picker=True,
                                transform=self.selected_ax.transData,
                               color="red",
                                 length_includes_head=True,lw=0)

        self.selected_ax._stale_viewlim_x = False
        self.selected_ax._stale_viewlim_y = False
        self.canvas.draw()
        return True

    def get_arrow_coords_at_standard_length(self, head_position,
                                              orig_tail_position,
                                              arrow_length_inch,
                                              ax):
        d_x = orig_tail_position[0] - head_position[0]
        d_y = orig_tail_position[1] - head_position[1]
        x_y_ratio = d_x / d_y
        figure_size_inch = self.figure.get_size_inches()
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

    def activate_zoom_tool(self):
        self.current_zoom_selector = self.create_zoom_selector(self.selected_ax)
        self._activate_tool(self.zoom_tool)

    def activate_arrow_tool(self):
        if self.current_zoom_selector is not None:
            self.current_zoom_selector.set_active(False)
            self.current_zoom_selector.set_visible(False)
        if (isinstance(self.selected_element, matplotlib.patches.Rectangle)):
            self.selected_element.set_edgecolor("black")
        self._activate_tool(self.arrow_tool)

    def _activate_tool(self, clicked_button):
        if clicked_button.isChecked():
            current_label = clicked_button.text()
            for tool_button in self.all_tool_buttons:
                label = tool_button.text()
                if label != current_label:
                    tool_button.setChecked(False)
            self.active_tool = current_label
        else:
            self.active_tool = None

    def select_ax(self, event):
        """
        Select axes, triggered by clicking with the mouse.
        Last selected axes will be deselected before new is selected.
        """
        # only execute function if there was a change in the selected axis
        if self.selected_ax is not None:
            if event.inaxes.get_label() == self.selected_ax.get_label():
                return False
        self._select_ax(event.inaxes)

        if self.active_tool == "Zoom":
            self.create_zoom_selector(self.selected_ax)
        return True

    def _select_ax(self, ax):
        axis_label = ax.get_label()
        if axis_label.find("letter subplot") != -1:
            return False
        # subplots for images have the structure panel_letter-row-column
        # therefore split by "-" should lead to three elements
        if len(axis_label.split("-")) != 3:
            return False
        if self.selected_ax is not None:
            self.selected_ax.patch.set_edgecolor(None)
            self.selected_ax.patch.set_linewidth('0')
        self.selected_ax = ax
        self.selected_ax.patch.set_edgecolor('red')
        self.selected_ax.patch.set_linewidth('0.1')
        self.canvas.draw()
        return True


    def remove_element(self, event):
        if self.selected_element is None:
            return False
        if event.key not in ["delete", "backspace"]:
            return False
        if (isinstance(self.selected_element , matplotlib.text.Text)):
            text_field_number = int(self.selected_element.get_label().split("_")[1])
            self.delete_text("", text_field_number)
        else:
            self.current_zoom_selector.extents = (0,0,0,0)
            self.selected_element.remove()
            self.selected_element = None
            self.canvas.draw()

    def move_text(self, event):
        """
        Move currently selected text element with arrow keys.
        Pressing Control (ctrl) and arrow key increases movement speed 5 fold
        Pressing shift (ctrl) and arrow key reduces movement speed 5 fold
        Pressing control and shift and arrow key increases speed 10 fold
        """
        if self.selected_element is None:
            return False
        if (not isinstance(self.selected_element , matplotlib.text.Text)):
            return False
        (movement_keys,
         modifier_keys) = self.get_movement_and_modifier_keys(event)

        if len(movement_keys) == 0:
            return False

        ax = self.selected_element.axes
        (step_size_x,
        step_size_y) = self.get_step_sizes_for_modifier_keys(modifier_keys, ax)

        text_position = list(self.selected_element.get_position())
        text_position = self.get_position_after_step(text_position,
                                                     movement_keys,
                                                     step_size_x, step_size_y)

        text_position_in_limits = self.get_position_in_limits(text_position,
                                                              ax)

        self.selected_element.set_position(text_position_in_limits)
        self.canvas.draw()

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

    def add_editor_for_text(self, text, text_field_number):

        change_text_function = functools.partial(self.change_text,
                                                 text_field_number=
                                                 text_field_number)
        change_text_input = QtWidgets.QLineEdit(self)
        change_text_input.setText(text)
        change_text_input.resize(280, 40)
        change_text_input.textChanged.connect(change_text_function)
        self.change_text_inputs[text_field_number] = change_text_input

        delete_text_button = QtWidgets.QPushButton('Delete text #' +
                                                   str(text_field_number))

        delete_text_function = functools.partial(self.delete_text,
                                                 text_field_number=
                                                 text_field_number)
        delete_text_button.clicked.connect(delete_text_function)
        self.delete_text_buttons[text_field_number] = delete_text_button

        self.controls_layout.addWidget(change_text_input)
        self.controls_layout.addWidget(delete_text_button)

    def get_next_text_field_number(self):
        if len(list(self.change_text_inputs.keys())) == 0:
            text_field_number = 1
        else:
            text_field_number = max(self.change_text_inputs.keys()) + 1
        return text_field_number

    def add_text(self):

        text_field_number = self.get_next_text_field_number()

        text = self.text_input.text()
        new_text_field = self.selected_ax.text(self.selected_ax.get_xlim()[0],
                                             self.selected_ax.get_ylim()[0],
                                             text, picker=True,
                                             fontsize=self.font_size,
                                               horizontalalignment="left",
                                               verticalalignment="center",
                                             label=("textfield_" +
                                                    str(text_field_number)))
        self.all_text_fields[text_field_number] = new_text_field
        self.text_input.clear()
        self.canvas.draw()

        self.add_editor_for_text(text, text_field_number)

    def change_text(self, event, text_field_number):
        text = self.change_text_inputs[text_field_number].text()
        self.all_text_fields[text_field_number].set_text(text)
        self.canvas.draw()

    def delete_text(self, event_place_holder, text_field_number):
        # if the deleted element is the currently selected element
        # remove this element from being selected
        if self.selected_element is not None:
            text_label = "textfield_" + str(text_field_number)
            if self.selected_element.get_label() == text_label:
                self.selected_element = None
        self.all_text_fields[text_field_number].remove()
        self.change_text_inputs[text_field_number].deleteLater()
        self.delete_text_buttons[text_field_number].deleteLater()
        self.canvas.draw()

    def on_pick_event(self, event):
        print(isinstance(event.artist, matplotlib.patches.FancyArrow))
        #Store which text object was picked and were the pick event occurs.
        if ((not isinstance(event.artist, matplotlib.text.Text)) &
                (not isinstance(event.artist, matplotlib.patches.FancyArrow))):
            return False
        # don't allow picking up elements while a tool is activated
        # if self.active_tool is not None:
        #     return False
        # switch color of current selected element back to black
        if self.selected_element is not None:
            self.selected_element.set_color("black")
        event.artist.set_color("red")
        self.element_is_picked = True
        self.canvas.setFocus()
        self.selected_element = event.artist
        self.canvas.draw()
        self.dragged_element = event.artist
        self.pick_pos = [event.mouseevent.xdata, event.mouseevent.ydata]
        return True

    def pause_dragging(self, event):
        if self.dragged_element is None:
            return False
        self.moved_out_of_ax = True

    def continue_dragging(self, event):
        if self.dragged_element is None:
            return False
        dragged_axis_label =  self.dragged_element.axes.get_label()
        entered_axis_label = event.inaxes.get_label()
        if dragged_axis_label == entered_axis_label:
            self.moved_out_of_ax = False

    def drag_arrow(self, event):
        if self.dragged_element is None:
            return False
        if (not isinstance(self.dragged_element,
                           matplotlib.patches.FancyArrow)):
            return False
        if event.xdata is None:
            return False
        if self.moved_out_of_ax:
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

    def move_arrow(self, event):
        """
        Move currently selected text element with arrow keys.
        Pressing Control (ctrl) and arrow key increases movement speed 5 fold
        Pressing shift (ctrl) and arrow key reduces movement speed 5 fold
        Pressing control and shift and arrow key increases speed 10 fold
        """
        print(self.selected_element)
        if self.selected_element is None:
            return False
        if (not isinstance(self.selected_element,
                           matplotlib.patches.FancyArrow)):
            return False

        (movement_keys,
         modifier_keys) = self.get_movement_and_modifier_keys(event)

        if len(movement_keys) == 0:
            return False

        ax = self.selected_element.axes
        (step_size_x,
        step_size_y) = self.get_step_sizes_for_modifier_keys(modifier_keys, ax)

        arrow_xy = self.selected_element.xy

        new_arrow_xy = self.get_position_after_step(arrow_xy,
                                                     movement_keys,
                                                     step_size_x, step_size_y)

        self.selected_element.set_xy(new_arrow_xy)

        self.canvas.draw()

    def move_picked_element(self, event):
        " Update text position and redraw"
        if self.dragged_element is None:
            return False
        if self.moved_out_of_ax:
            return False
        if (not isinstance(self.dragged_element, matplotlib.text.Text)):
            return False
        old_pos = self.dragged_element.get_position()
        new_pos = (old_pos[0] + event.xdata - self.pick_pos[0],
                   old_pos[1] + event.ydata - self.pick_pos[1])
        new_pos_in_limits = self.get_position_in_limits(new_pos,
                                                        self.dragged_element.axes)

        # only update pick position if element was actually moved
        if new_pos_in_limits[0] == new_pos[0]:
            self.pick_pos[0] = event.xdata
        if new_pos_in_limits[1] == new_pos[1]:
            self.pick_pos[1] = event.ydata
        self.pick_pos = [event.xdata, event.ydata]
        self.dragged_element.set_position(new_pos_in_limits)
        self.canvas.draw()
        return True

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

    def on_release_event(self, event):
        " Update text position and redraw"
        if self.dragged_element is None:
            return False
        self.dragged_element = None
        self.moved_out_of_ax = False
        return True

    def get_code_for_adding_texts(self):
        indent_string = "\t\t\t\t\t\t"
        add_text_string = "figure.add_text_on_image(\n"
        texts_string = indent_string + "texts=[\n"
        target_images_string = indent_string + "images=[\n"
        for text_field in self.all_text_fields.values():
            text = text_field.get_text()
            position = np.round(text_field.get_position(),4)
            texts_string += indent_string + "{"
            texts_string += "'s': '" + text + "',"
            texts_string += "'x': " + str(position[0]) + ","
            texts_string += "'y': " + str(position[1]) + ","
            hor_alignment = text_field.get_horizontalalignment()
            if hor_alignment != "left":
                texts_string += "'horizontalalignment': " + hor_alignment+ ","
            vert_alignment = text_field.get_verticalalignment()
            if vert_alignment != "center":
                texts_string += "'verticalalignment': " + vert_alignment + ","
            texts_string += "},\n"

            axes_label = text_field.axes.get_label()
            axes_position = axes_label.split("-")[1:3]
            axes_position = (int(axes_position[0]), int(axes_position[1]))

            axes_identity = self.figure_panel.pos_to_pre_identity_map[axes_position]
            target_images_string += indent_string + "{"
            identity_map = self.figure_panel.inv_map
            for cat_nb, cat_val in enumerate(axes_identity):
                cat_name = identity_map[cat_nb]
                target_images_string += "'"+cat_name+"': ["+str(cat_val)+"],"
            target_images_string +="},\n"
        texts_string += indent_string + "],"
        target_images_string += indent_string + "],"
        add_text_string += texts_string + "\n" + target_images_string
        add_text_string += ")"
        add_text_string += "\n\n"
        return add_text_string

    def print_code(self):
        """
        Generate string to be copied into figure generating script
        as parameter "texts" to the function "add_texts_in_image".
        The string creates a dictionary containing the details of
        plotting user-defined text at the user-defined positions.
        """
        code_string = ""
        code_string += self.get_code_for_adding_texts()

        print("\nCopy the following text and\n"
              "paste it after the 'show images' function \n"
              "for the target panel:\n\n"+
              code_string)