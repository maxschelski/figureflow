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

from . import arrow_editor
from . import crop_editor
from . import text_editor
from . import zoom_editor


# first of all implement bliting

# make a general class for "Editor"
# make subclass for "TextAdder" and "ImageEditor" (for arrows and zooms)
# for arrows make resizing possible by keyboard after selecting:
# shift plus arrow left for decreasing size, shift right for increasing size
# for decreasing and increasing keep arrow head at same position but enlarge
# tail of arrow

class FigureEditorGUI(QtWidgets.QDialog):
    def __init__(self, figure_panel=None, font_size=7,
                 arrow_length_inch=0.2):
        super().__init__()

        self.selected_element = None
        self.dragged_element = None
        self.tool_start_position = None
        self.moved_out_of_ax = False
        self.active_tool = "Text"
        self.element_is_picked = False
        self.tools_for_all_axs = {}
        self.tools = {}

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
        self.arrow_length_inch = arrow_length_inch

        self.initialize_layout()

        self.selected_ax = None
        for _, ax in self.figure_panel.all_axs.items():
            selected = self._select_ax(ax)
            if selected:
                break

        self.canvas.draw()
        # figure_size = self.canvas.figure.get_size_inches() * self.canvas.figure.dpi
        self.canvas.setMinimumSize(self.canvas.size())
        self.resize(2000, 1000)

        # make sure that the button that activates a tool
        # has the same label as the key in the tools dictionary
        # that refers to the respective editor object
        self.add_buttons_to_layout()


        self.canvas.mpl_connect("axes_leave_event", self.pause_dragging)
        self.canvas.mpl_connect("axes_enter_event", self.continue_dragging)
        self.canvas.mpl_connect("button_release_event", self.on_release_event)
        self.canvas.mpl_connect("axes_leave_event", self.pause_tool)
        self.canvas.mpl_connect("axes_enter_event", self.continue_tool)


        self.canvas.mpl_connect("button_press_event", self.select_ax)

        # self.canvas.mpl_connect("key_press_event", self.move_zoom_rectangle)

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


    def add_buttons_to_layout(self):

        self.add_text_button = QtWidgets.QPushButton('Add text')
        self.add_text_button.clicked.connect(self.tools["Text"].add_text)

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

        if self.active_tool == "Zoom":
            self.tools["Zoom"].activate(ax=self.selected_ax)
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
        self.selected_ax.patch.set_linewidth('0.1')
        self.canvas.draw()

        # select tools for currently selected ax
        if ax_label in self.tools_for_all_axs:
            self.tools = self.tools_for_all_axs[ax_label]
        else:
            # if the tools for the ax has not been generated, do that now
            self.tools = {}
            self.tools["Text"] = text_editor.TextEditor(self.controls_layout,
                                                        canvas=self.canvas,
                                                       editor_gui=self)
            self.tools["Arrow"] = arrow_editor.ArrowEditor(canvas=self.canvas,
                                                       editor_gui=self,
                                                           arrow_length_inch=
                                                           self.arrow_length_inch)
            self.tools["Zoom"] = zoom_editor.ZoomEditor(canvas=self.canvas,
                                                       editor_gui=self)
            self.tools["Crop"] = crop_editor.CropEditor(canvas=self.canvas,
                                                       editor_gui=self)

            self.tools_for_all_axs[ax_label] = self.tools

        # activate the same tool that was active before the axes switch
        if active_tool is not None:
            self.tools[active_tool].activate()

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