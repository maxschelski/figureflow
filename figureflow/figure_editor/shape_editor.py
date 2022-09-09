from .editor_tool import EditorTool
import matplotlib

class ShapeEditor(EditorTool):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.canvas.mpl_connect("key_press_event", self.remove_element)

        self.canvas.mpl_connect("button_press_event", self.start_tool)
        self.canvas.mpl_connect("motion_notify_event", self.use_tool)
        self.canvas.mpl_connect("button_release_event", self.end_tool)



    def start_tool(self, event):
        if not self.active:
            return False
        if self.editor_gui.element_is_picked:
            return False
        if self.editor_gui.selected_element is not None:
            if ((isinstance(self.editor_gui.selected_element, matplotlib.text.Text)) |
                    (isinstance(self.editor_gui.selected_element, matplotlib.patches.FancyArrow))):
                self.editor_gui.selected_element.set_color("black")
        self.tool_start_position = [event.xdata, event.ydata]
        self.editor_gui.tool_start_position = self.tool_start_position
        return True


    @EditorTool.only_do_for_correct_object
    def remove_element(self, event):
        if self.editor_gui.selected_element is None:
            return False
        if event.key not in ["delete", "backspace"]:
            return False
        self.current_zoom_selector.extents = (0,0,0,0)
        self.editor_gui.selected_element.remove()
        self.editor_gui.selected_element = None
        self.canvas.draw()
