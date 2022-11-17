from . import rectangle_editor
from .editor_tool import EditorTool
import matplotlib

class CropEditor(rectangle_editor.RectangleEditor):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.line_width = 0.8
        self.pick = False
        self.element_label = "Crop"
        self.crop_element = None

        axes_position = self.get_position_of_axes(self.ax)
        # if cropping should be done, it has the followings structure:
        # [x0, x1, y0, y1]
        cropping = self.figure_panel.cropped_positions.get(axes_position,
                                                           None)
        if cropping is not None:
            # add rectangle for cropping
            x0, x1, y0, y1 = tuple(cropping)

            x0_ax, y0_ax = self.transform_coords_from_data_to_axes(x0, y0,
                                                                   self.ax)
            x1_ax, y1_ax = self.transform_coords_from_data_to_axes(x1, y1,
                                                                   self.ax)

            width = x1_ax - x0_ax
            y_positions = [y0_ax, y1_ax]
            height = max(y_positions) - min(y_positions)

            mpl_rectangle = matplotlib.patches.Rectangle

            self.crop_element = mpl_rectangle((x0_ax, y1_ax),width, height,
                                              linewidth=self.line_width,
                                              edgecolor=self.color,
                                              transform=self.ax.transAxes,
                                              picker=self.pick,
                                              label=self.element_label,
                                              facecolor='none')

            self.ax.add_patch(self.crop_element)
            self.canvas.draw()


    def switch_active_rectangle(self, new_rectangle):
        super().switch_active_rectangle(new_rectangle)
        self.crop_element = new_rectangle

    @EditorTool.only_do_for_correct_object
    def remove_element(self, event):
        execute = super().remove_element(event)
        if not execute:
            return False
        self.crop_element = None

    def select_rectangle(self, start_event=None, end_event=None):
        if self.crop_element is not None:
            self.crop_element.remove()
        super().select_rectangle()

    def use_tool(self, event):
        execute = super().use_tool(event)
        if not execute:
            return False
        # remove the last crop element
        if self.crop_element is not None:
            self.crop_element.remove()
            self.crop_element = None
            # also set the selected element to None if the
            # gui element is the selected element
            if self.crop_element is self.editor_gui.selected_element:
                self.editor_gui.selected_element = None

        self.canvas.draw()
        return True

    def activate(self):
        super().activate()
        if self.crop_element is not None:
            self.replace_rectangle_with_selector(self.crop_element)
            self.change_color_of_selected_element_to_default()
            # self.editor_gui.selected_element = self.crop_element
            self.crop_element.set_edgecolor("red")
            self.canvas.draw()


    @EditorTool.only_do_for_correct_object
    def on_pick_event(self, event):
        pass