from . import rectangle_editor
from .editor_tool import EditorTool
import matplotlib

class ZoomEditor(rectangle_editor.RectangleEditor):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.line_width = 0.2
        self.canvas.mpl_connect("pick_event", self.on_pick_event)
        self.pick = True
        self.element_label = "Zoom"

    def switch_active_zoom_rectangle(self, new_zoom_rectangle):
        super().switch_active_zoom_rectangle(new_zoom_rectangle)
        self.all_zoom_rectangles.append(new_zoom_rectangle)
        return True

    def use_tool(self, event):
        execute = super().use_tool(event)
        if not execute:
            return False
        if ((self.zoom_selector.active_handle is not None) &
                (self.editor_gui.selected_element is not None)):
            self.all_zoom_rectangles.remove(self.editor_gui.selected_element)
            self.editor_gui.selected_element.remove()
            self.editor_gui.selected_element = None
            self.canvas.draw()
        return True

    @EditorTool.only_do_for_correct_object
    def on_pick_event(self, event):
        if not self.active:
            return False
        # do not allow multiple elements to be picked
        if self.editor_gui.element_is_picked:
            return False
        # only initiate activating new rectangle if the clicked zoom rectangle
        # is different from current zoom rectangle
        if self.editor_gui.selected_element is event.artist:
            return False
        zoom_rectangle = event.artist
        # set True to prevent other events from happening until click is ended
        self.editor_gui.element_is_picked = True
        # do not allow interacting with zoom selector while new rect is activated
        self.zoom_selector.set_active(False)
        self.zoom_selector.set_visible(False)
        self.switch_active_zoom_rectangle(zoom_rectangle)

