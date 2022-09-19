import sys
import copy
import math
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets
import inspect

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

import math

from . import arrow_editor
from . import crop_editor
from . import text_editor
from . import zoom_editor

class FigureEditorGUI(QtWidgets.QDialog):
    def __init__(self, figure_panel=None, font_size=7,
                 include_all_labels=False,
                 arrow_props=None, coord_decimals=2, color="white"):
        """
        :param include_all_labels: Boolean, whether all text labels will be made
                                    changeable, this also includes
                                    channels, timesteps and zoom numbers.
                                     Also code for plotting them will be
                                     printed, therefore be aware to only take
                                     the code for labels you want to change
                                     to prevent duplication and remove
                                     the original function that added the label.
                                     This however, will make the labels static
                                     and not change with a different timestamp
                                     etc.
        :param arrow_props: Dictionary of properties of arrow added.
                            key is the property
                            (allowed properties:
                            length, width_factor, head_length_factor,
                            head_width_factor)
                            values are float of the size in pt (length)
                            or the factor that is multiplied with the length
                            to obtain the respective value (e.g. width_factor
                            will be multiplied with length to obtain the width
        :param coord_decimals: For printing code for generating objects
                                number of decimals plotted
                                for each number (e.g. coordinates, width etc)
        """
        super().__init__()

        self.selected_element = None
        self.dragged_element = None
        self.tool_start_position = None
        self.moved_out_of_ax = False
        self.active_tool = "Text"
        self.element_is_picked = False
        self.tools_for_all_axs = {}
        self.tools = {}
        self.color = color
        self.round = functools.partial(np.round, decimals=coord_decimals)
        self.include_all_labels = include_all_labels

        if arrow_props is None:
            self.arrow_props = {}
        else:
            self.arrow_props = arrow_props

        if figure_panel is not None:
            self.figure = figure_panel.fig
        else:
            # a figure instance to plot on
            self.figure = Figure()

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        self.figure_panel = figure_panel
        self.font_size = font_size

        self.initialize_layout()

        # make sure that the button that activates a tool
        # has the same label as the key in the tools dictionary
        # that refers to the respective editor object
        self.add_buttons_to_layout()

        self.selected_ax = None
        for ax in self.figure_panel.all_axs.values():
            selected = self._select_ax(ax)
            if selected:
                break

        self.canvas.draw()
        # figure_size = self.canvas.figure.get_size_inches() * self.canvas.figure.dpi
        self.canvas.setMinimumSize(self.canvas.size())
        self.resize(2000, 1000)


        self.canvas.mpl_connect("axes_leave_event", self.pause_dragging)
        self.canvas.mpl_connect("axes_enter_event", self.continue_dragging)
        self.canvas.mpl_connect("button_release_event", self.on_release_event)
        self.canvas.mpl_connect("axes_leave_event", self.pause_tool)
        self.canvas.mpl_connect("axes_enter_event", self.continue_tool)

        self.canvas.mpl_connect("button_press_event", self.select_ax)

        self.canvas.setFocusPolicy(QtCore.Qt.ClickFocus)

    def pick_object(self, type):
        if type != "Zoom":
            self.tools["Zoom"].switch_to_other_object()

    def initialize_layout(self):
        self.text_input = QtWidgets.QLineEdit()

        self.print_code_button = QtWidgets.QPushButton('Print code')
        self.print_code_button.clicked.connect(self.print_code)


        self.qscroll_controls = QtWidgets.QScrollArea()
        self.qscroll_controls.setFixedWidth(600)
        controls_frame = QtWidgets.QFrame(self.qscroll_controls)
        controls_frame.setLayout(QtWidgets.QVBoxLayout())
        self.qscroll_controls.setWidget(controls_frame)
        self.controls_layout = controls_frame.layout()
        self.controls_layout.setAlignment(QtCore.Qt.AlignTop)

        # set general layout
        qscroll_canvas = QtWidgets.QScrollArea()
        qscroll_canvas.setWidget(self.canvas)

        # set the layout
        self.layout = QtWidgets.QGridLayout()
        self.layout.addWidget(qscroll_canvas,0,0)
        controls_frame.setFixedWidth(550)

    def add_text(self):
        self.tools["Text"].add_text()

    def add_buttons_to_layout(self):

        self.add_text_button = QtWidgets.QPushButton('Add text')
        self.add_text_button.clicked.connect(self.add_text)

        self.all_tool_buttons = []

        self.arrow_tool_switch = QtWidgets.QToolButton(self)
        self.arrow_tool_switch.setText("Arrow")
        self.arrow_tool_switch.setToolTip("Add an arrow to an image")
        # self.arrow_tool_switch.setIcon(self.arrow_tool_switch.style().standardIcon(QtWid
        # gets.QStyle.SP_MediaSeekForward))
        self.arrow_tool_switch.setCheckable(True)
        self.arrow_tool_switch.clicked.connect(self.activate_arrow_tool)
        self.all_tool_buttons.append(self.arrow_tool_switch)

        self.zoom_tool_switch = QtWidgets.QToolButton(self)
        self.zoom_tool_switch.setText("Zoom")
        self.zoom_tool_switch.setToolTip("Add a zoom area to an image")
        self.zoom_tool_switch.setCheckable(True)
        self.zoom_tool_switch.clicked.connect(self.activate_zoom_tool)
        self.all_tool_buttons.append(self.zoom_tool_switch)


        self.crop_tool_switch = QtWidgets.QToolButton(self)
        self.crop_tool_switch.setText("Crop")
        self.crop_tool_switch.setToolTip("Change the crop area to an image")
        self.crop_tool_switch.setCheckable(True)
        self.crop_tool_switch.clicked.connect(self.activate_crop_tool)
        self.all_tool_buttons.append(self.crop_tool_switch)

        tools = QtWidgets.QFrame()
        tools.setLayout(QtWidgets.QHBoxLayout())
        self.tools_layout = tools.layout()
        self.tools_layout.addWidget(self.arrow_tool_switch)
        self.tools_layout.addWidget(self.zoom_tool_switch)
        self.tools_layout.addWidget(self.crop_tool_switch)

        self.controls_layout.addWidget(tools )
        self.controls_layout.addWidget(self.print_code_button)
        self.controls_layout.addWidget(self.text_input)
        self.controls_layout.addWidget(self.add_text_button)
        self.controls_layout.setSizeConstraint(self.controls_layout.SetMinAndMaxSize)

        self.layout.addWidget(self.qscroll_controls,0,1)


        self.setLayout(self.layout)

    def pause_tool(self, event):
        if self.tool_start_position is None:
            return False
        self.moved_out_of_ax = True

    def continue_tool(self, event):
        if self.tool_start_position is None:
            return False
        if self.moved_out_of_ax == False:
            return False
        if self.selected_element is not None:
            tool_axis_label =  self.selected_element.axes.get_label()
            entered_axis_label = event.inaxes.get_label()
            if tool_axis_label == entered_axis_label:
                self.moved_out_of_ax = False

    def activate_zoom_tool(self):
        self._activate_tool(self.zoom_tool_switch, ax=self.selected_ax)

    def activate_crop_tool(self):
        self._activate_tool(self.crop_tool_switch, ax=self.selected_ax)

    def activate_arrow_tool(self):
        if (isinstance(self.selected_element, matplotlib.patches.Rectangle)):
            self.selected_element.set_edgecolor("black")
        self._activate_tool(self.arrow_tool_switch)

    def _activate_tool(self, clicked_button, ax=None):
        current_label = clicked_button.text()
        if clicked_button.isChecked():
            for tool_button in self.all_tool_buttons:
                label = tool_button.text()
                if label != current_label:
                    tool_button.setChecked(False)
                    self.tools[label].deactivate()
            self.active_tool = current_label
            self.tools[current_label].activate(ax)
            self.tools["Text"].deactivate()
        else:
            self.active_tool = "Text"
            self.tools[current_label].deactivate()
            self.tools["Text"].activate()

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

        return True

    def _select_ax(self, ax):
        axis_label = ax.get_label()
        # do not select subplots only made for the letter
        if axis_label.find("letter subplot") != -1:
            return False
        # subplots for images have the structure panel_letter-row-column
        # therefore split by "-" should lead to three elements
        if len(axis_label.split("-")) != 3:
            return False
        if self.selected_ax is not None:
            self.selected_ax.patch.set_edgecolor(None)
            self.selected_ax.patch.set_linewidth('0')
        # deactivate all current tools
        # and find out which tool was active (if any)
        active_tool = "Text"
        for tool_name, tool in self.tools.items():
            if tool.active:
                active_tool = tool_name
            tool.deactivate()
        self.selected_ax = ax
        ax_label = ax.get_label()
        self.selected_ax.patch.set_edgecolor('red')
        self.selected_ax.patch.set_linewidth('0.8')
        self.canvas.draw()

        # when the editor is initialized, there are no tools yet
        # therefore also no text tool
        if "Text" in self.tools:
            # remove edit and delete text buttons
            self.tools["Text"].deselect_ax()

        # select tools for currently selected ax
        if ax_label in self.tools_for_all_axs:
            self.tools = self.tools_for_all_axs[ax_label]
        else:
            # if the tools for the ax has not been generated, do that now
            self.tools = {}
            self.tools["Text"] = text_editor.TextEditor(self.controls_layout,
                                                        canvas=self.canvas,
                                                       editor_gui=self,
                                                        ax = self.selected_ax,
                                                        include_all_labels=
                                                        self.include_all_labels)
            self.tools["Arrow"] = arrow_editor.ArrowEditor(canvas=self.canvas,
                                                       editor_gui=self,
                                                           arrow_props=
                                                           self.arrow_props,
                                                        ax = self.selected_ax)
            self.tools["Zoom"] = zoom_editor.ZoomEditor(canvas=self.canvas,
                                                       editor_gui=self,
                                                        ax = self.selected_ax)
            self.tools["Crop"] = crop_editor.CropEditor(canvas=self.canvas,
                                                       editor_gui=self,
                                                        ax = self.selected_ax)

            self.tools_for_all_axs[ax_label] = self.tools

        # activate the same tool that was active before the axes switch
        if active_tool is not None:
            self.tools[active_tool].activate()

        # show edit and delete text buttons
        self.tools["Text"].select_ax()

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

    def on_release_event(self, event):
        if self.dragged_element is None:
            return False
        self.dragged_element = None
        self.moved_out_of_ax = False
        return True

    def get_size_of_arrow(self, arrow, ax):
        # set size for each arrow
        arrow_path_array = arrow.get_path().vertices
        # the actual d_x/d_y used for drawing the arrow
        # is the mean between the fifth and sixth row
        d_x = (((arrow_path_array[3, 0] - arrow_path_array[0, 0]) +
                      (arrow_path_array[4, 0] - arrow_path_array[0, 0]))/2)
        d_y = (((arrow_path_array[3, 1] - arrow_path_array[0, 1]) +
                      (arrow_path_array[4, 1] - arrow_path_array[0, 1]))/2)
        # calculate size from d_x and d_y of arrow
        # first convert d_x and d_y from data to inches
        ax_width_data = max(ax.get_xlim()) - min(ax.get_xlim())
        d_x_rel = d_x / ax_width_data
        ax_width_inches = (ax.get_position().width *
                           ax.figure.get_size_inches()[0])
        d_x_inches = d_x_rel * ax_width_inches

        ax_height_data = max(ax.get_ylim()) - min(ax.get_ylim())
        d_y_rel = d_y / ax_height_data
        ax_height_inches = (ax.get_position().height *
                            ax.figure.get_size_inches()[1])
        d_y_inches = d_y_rel * ax_height_inches

        # then get length of hypothenus in inches
        size_inches = np.sqrt(d_x_inches**2 + d_y_inches**2)

        # multiply length by 72 to get length in pt
        size_pt = size_inches * 72
        return size_pt, d_x, d_y

    def get_code_for_adding_zooms(self, zoom_tool, ax):
        indent_string = "\t\t\t\t"
        add_all_zooms_string = ""
        function_call_string = "figure.add_zoom(\n"
        target_images_string_start = indent_string + "images=[\n"
        #(xy=(181, 110), width=32, height=30, channels=[1], label_position_overview="top")
        for zoom_rect in zoom_tool.all_zoom_rectangles:
            add_zoom_string = function_call_string
            # get mid point and width and height
            zoom_dimensions = zoom_rect.get_bbox()
            width = (zoom_dimensions.x1 - zoom_dimensions.x0)
            height = (zoom_dimensions.y1 - zoom_dimensions.y0)
            x_mid = zoom_dimensions.x0 + width/2
            y_mid = zoom_dimensions.y0 + height/2
            add_zoom_string += (indent_string +
                                "xy=("+str(self.round(x_mid))+","
                                +str(self.round(y_mid))+"),\n")
            add_zoom_string += (indent_string +
                                "width="+str(self.round(width))+
                                ", height="+str(self.round(height))+",\n")

            rect_label = zoom_rect.get_label()
            rect_properties_string = rect_label.split("___")
            if len(rect_properties_string) > 1:
                rect_properties_string = rect_properties_string[1]
                rect_properties = rect_properties_string.split("_")
                label_position_overview = rect_properties[0]
                if label_position_overview != "":
                    add_zoom_string += (indent_string +
                                        "label_position_overview="+
                                        label_position_overview+",\n")

            # get target images for arrow
            target_images_string = (target_images_string_start +
                                    self.get_image_identity_string(zoom_rect.axes,
                                                                   indent_string))
            target_images_string += indent_string+"]"

            add_zoom_string += target_images_string
            add_zoom_string += ")"
            add_zoom_string += "\n"

            add_all_zooms_string += add_zoom_string

        add_all_zooms_string += "\n\n"
        return add_all_zooms_string

    def get_code_for_adding_arrows(self, arrow_tool, ax):
        indent_string = "\t\t\t\t\t"
        add_all_arrows_string = ""
        function_call_string = "figure.draw_on_image(\n"
        target_images_string_start = indent_string + "images=[\n"

        for arrow in arrow_tool.all_arrows:
            add_arrow_string = function_call_string
            # get and set target for each arrow
            target = arrow.get_path().vertices[0,:]
            target = [str(self.round(coord)) for coord in target]
            add_arrow_string += (indent_string +
                                 "target=["+",".join(target)+"],\n")

            # get size of arrow and d_x and d_y
            size_pt, d_x, d_y = self.get_size_of_arrow(arrow, ax)
            add_arrow_string += (indent_string +
                                 "size="+str(self.round(size_pt))+",")

            # get and set direction for each arrow
            # get direction in degrees from d_x and d_y of arrow
            direction = np.rad2deg(np.arctan2(d_x, d_y) % (2*np.pi))
            add_arrow_string += "direction="+str(self.round(direction))+",\n"
            color = arrow.get_edgecolor()
            # if the color is a tuple, it would be an RGB color code
            # otherwise just a string
            if type(color) == tuple:
                color = str(color)
            else:
                color = "'"+color+"'"
            add_arrow_string += "color=" + color + ",\n"

            # get and set several parameters from label of arrow:
            # width_factor (first)
            # head_width_factor (second)
            # head_length_factor (third)
            # starting after "___" and separated by _
            # e.g. LABEL___0.125_0.625_0.625
            arrow_label = arrow.get_label()
            arrow_params_string = arrow_label.split("___")[1]
            arrow_params = arrow_params_string.split("_")
            width_factor = float(arrow_params[0])
            head_width_factor = float(arrow_params[1])
            head_length_factor = float(arrow_params[2])
            # check if each of the parameters is different from the default
            default_in_function = self.figure_panel.default_in_function
            function_object = self.figure_panel.draw_on_image

            default_factor = default_in_function(function_object,
                                                 "arrow_width_factor")
            if default_factor != width_factor:
                add_arrow_string += (indent_string +
                                     "arrow_width_factor="+
                                     str(self.round(width_factor))+",\n")
            default_factor = default_in_function(function_object,
                                                 "arrow_head_width_factor")
            if default_factor != head_width_factor:
                add_arrow_string += (indent_string + "arrow_head_width_factor="+
                                     str(self.round(head_width_factor)))+",\n"
            default_factor = default_in_function(function_object,
                                                 "arrow_head_length_factor")
            if default_factor != head_length_factor:
                add_arrow_string += (indent_string +
                                     "arrow_head_length_factor="+
                                     str(self.round(head_length_factor))+",\n")

            # get target images for arrow
            target_images_string = (target_images_string_start +
                                    self.get_image_identity_string(arrow.axes,
                                                                   indent_string))
            target_images_string += indent_string+"]"

            add_arrow_string += target_images_string
            add_arrow_string += ")"
            add_arrow_string += "\n"

            add_all_arrows_string += add_arrow_string

        add_all_arrows_string += "\n\n"
        return add_all_arrows_string

    def get_code_for_adding_texts(self, text_tool):
        indent_string = "\t\t\t\t\t\t"
        add_text_string = "figure.add_text_on_image(\n"
        texts_string = indent_string + "texts=[\n"
        target_images_string = indent_string + "images=[\n"
        for text_field in text_tool.all_text_fields.values():
            text = text_field.get_text()
            position = np.round(text_field.get_position(),4)
            texts_string += indent_string + "{"
            texts_string += "'s': '" + text + "',"
            texts_string += "'x': " + str(self.round(position[0])) + ","
            texts_string += "'y': " + str(self.round(position[1])) + ","
            color = text_field.get_color()
            if type(color) == tuple:
                color = str(color)
            else:
                color = "'"+color+"'"
            texts_string += indent_string + "color=" + color + ",\n"
            hor_alignment = text_field.get_horizontalalignment()
            if hor_alignment != "left":
                texts_string += (indent_string+
                                 "'horizontalalignment': " + hor_alignment+ ",")
            vert_alignment = text_field.get_verticalalignment()
            if vert_alignment != "center":
                texts_string += (indent_string+
                                 "'verticalalignment': " + vert_alignment + ",")
            texts_string += "},\n"

        target_images_string += self.get_image_identity_string(text_field.axes,
                                                              indent_string)

        texts_string += indent_string + "],"
        target_images_string += indent_string + "],"
        add_text_string += texts_string + "\n" + target_images_string
        add_text_string += ")"
        add_text_string += "\n\n"
        return add_text_string

    def get_image_identity_string(self, ax, indent_string):
        axes_label = ax.get_label()
        axes_position = axes_label.split("-")[1:3]
        axes_position = (int(axes_position[0]), int(axes_position[1]))

        axes_identity = self.figure_panel.pos_to_pre_identity_map[axes_position]
        identity_string = indent_string + "{"
        identity_map = self.figure_panel.inv_map
        for cat_nb, cat_val in enumerate(axes_identity):
            cat_name = identity_map[cat_nb]
            identity_string += "'"+cat_name+"': ["+str(self.round(cat_val))+"],"
        identity_string +="},\n"
        return identity_string

    def print_code(self):
        """
        Generate string to be copied into figure generating script
        as parameter "texts" to the function "add_texts_in_image".
        The string creates a dictionary containing the details of
        plotting user-defined text at the user-defined positions.
        """
        code_string = ""
        add_texts_string = ""
        add_arrows_string = ""
        add_zooms_string = ""
        for ax in self.figure_panel.all_axs.values():
            axis_label = ax.get_label()
            if axis_label not in self.tools_for_all_axs:
                continue
            axis_tools = self.tools_for_all_axs[axis_label]
            add_texts_string += self.get_code_for_adding_texts(axis_tools["Text"])
            add_arrows_string += self.get_code_for_adding_arrows(axis_tools["Arrow"],
                                                                 ax)
            add_zooms_string += self.get_code_for_adding_zooms(axis_tools["Zoom"],
                                                               ax)

        code_string += (add_zooms_string +
                        add_arrows_string +
                        add_texts_string)

        print("\nCopy the following text and\n"
              "paste it after the 'show images' function \n"
              "for the target panel:\n\n"+
              code_string)