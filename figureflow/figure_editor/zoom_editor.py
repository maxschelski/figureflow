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
        self.all_zoom_rectangles = []

        # get all zoom windows in current ax and make these zooms pickable
        for child in self.ax.get_children():
            if not isinstance(child, matplotlib.patches.Rectangle):
                continue
            rect_dimensions = child.get_bbox()
            # for some reason there is a rectangle with width and height of 1
            # starting at position (0,0)
            # this is not a zoom rectangle and therefore don't include it
            if ((rect_dimensions.x0 == 0) &
                    (rect_dimensions.y0 == 0) &
            (rect_dimensions.width == 1) &
            (rect_dimensions.height == 1)):
                continue

            # now make them pickable and  add them to list
            child.set_picker(True)
            self.all_zoom_rectangles.append(child)

    @EditorTool.only_do_for_correct_object
    def remove_element(self, event):
        if self.editor_gui.selected_element is None:
            return False
        if event.key not in ["delete", "backspace"]:
            return False
        self.all_zoom_rectangles.remove(self.editor_gui.selected_element)
        super().remove_element(event)

    def switch_active_rectangle(self, new_rectangle):
        super().switch_active_rectangle(new_rectangle)
        if new_rectangle is not None:
            self.all_zoom_rectangles.append(new_rectangle)
        return True

    def use_tool(self, event):
        execute = super().use_tool(event)
        if not execute:
            return False
        if ((self.rectangle_selector.active_handle is not None) &
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
        rectangle = event.artist
        # set True to prevent other events from happening until click is ended
        self.editor_gui.element_is_picked = True
        # do not allow interacting with zoom selector while new rect is activated
        self.rectangle_selector.set_active(False)
        self.rectangle_selector.set_visible(False)
        self.switch_active_rectangle(rectangle)

