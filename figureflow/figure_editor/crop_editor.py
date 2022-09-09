from . import rectangle_editor
from .editor_tool import EditorTool

class CropEditor(rectangle_editor.RectangleEditor):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.line_width = 0.8
        self.pick = False
        self.element_label = "Crop"
        self.crop_element = None
        # self.canvas.mpl_connect("pick_event", self.on_pick_event)

    # def start_tool(self, event):
    #     execute = super().start_tool(event)
    #     if not execute:
    #         return False

    def switch_active_zoom_rectangle(self, new_zoom_rectangle):
        super().switch_active_zoom_rectangle(new_zoom_rectangle)
        self.crop_element = new_zoom_rectangle

    def use_tool(self, event):
        execute = super().use_tool(event)
        if not execute:
            return False
        print(self.crop_element)
        # remove the last crop element
        if self.crop_element is not None:
            print("remove!")
            self.crop_element.remove()
            self.crop_element = None
            # also set the selected element to None if the
            # gui element is the selected element
            if self.crop_element is self.editor_gui.selected_element:
                self.editor_gui.selected_element = None

        self.canvas.draw()
        return True

    def activate(self, ax):
        super().activate(ax)
        print("activate")
        print(self.crop_element)
        if self.crop_element is not None:
            self.replace_zoom_rectangle_with_selector(self.crop_element)
            self.crop_element.set_edgecolor("red")
            self.reset_edge_color_of_selected_element()
            self.canvas.draw()

    @EditorTool.only_do_for_correct_object
    def on_pick_event(self, event):
        pass