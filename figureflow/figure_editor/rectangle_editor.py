from .editor_tool import EditorTool
from . import shape_editor
import matplotlib
from matplotlib import widgets
import functools

class RectangleEditor(shape_editor.ShapeEditor):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.element_type = matplotlib.patches.Rectangle

        self.all_zoom_rectangles = []
        self.zoom_selector = None

    def activate(self, ax=None):
        self.active = True
        if self.zoom_selector is None:
            self.create_zoom_selector(ax)
        self.zoom_selector.set_active(True)
        self.zoom_selector.set_visible(True)

    def deactivate(self):
        self.active = False
        if self.zoom_selector is None:
            return False
        self.zoom_selector.set_active(False)
        self.zoom_selector.set_visible(False)
        return True

    def new_zoom_selector(self, ax):
        zoom_selector = widgets.RectangleSelector(ax,
                                                  self.select_rectangle,
                                                  drawtype='box', useblit=False,
                                                  button=[1, 2],
                                                  minspanx=5, minspany=5,
                                                  spancoords='data',
                                                  interactive=True,
                                                  maxdist=10,
                                                  rectprops=dict(linestyle='-',
                                                                 color='red',
                                                                 linewidth=self.line_width,
                                                                 fill=False,
                                                                 alpha=1)
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
        self.zoom_selector = self.new_zoom_selector(ax)

    def replace_zoom_selector_with_rectangle(self, zoom_selector):
        last_zoom_size = zoom_selector._rect_bbox
        rect = matplotlib.patches.Rectangle((last_zoom_size[0], last_zoom_size[1]),
                                 last_zoom_size[2], last_zoom_size[3],
                                 linewidth=self.line_width, edgecolor='red',
                                 picker=self.pick,label=self.element_label,
                                 facecolor='none')
        zoom_selector.ax.add_patch(rect)
        self.canvas.draw()
        return rect


    def replace_zoom_rectangle_with_selector(self, rect):
        # new_zoom_selector = self.new_zoom_selector(rect.axes)
        zoom_size = rect.get_bbox()
        self.zoom_selector.extents = (zoom_size.x0, zoom_size.x1,
                                              zoom_size.y0, zoom_size.y1)
        return True


    def select_rectangle(self, click_event, release_event,
                         zoom_selector=None,
                         zoom_selector_number=None):
        if self.editor_gui.element_is_picked:
            return False
        zoom_rect = self.replace_zoom_selector_with_rectangle(self.zoom_selector)
        self.switch_active_zoom_rectangle(zoom_rect)
        return True

    def use_tool(self, event):
        if not self.active:
            return False
        if self.tool_start_position is None:
            return False
        if self.editor_gui.moved_out_of_ax:
            return False
        end_position = [event.xdata, event.ydata]
        # set edge color of previous zoom rectangle to black
        # so that when drawing a new zoom rectangle, the previous one
        # immediately switches edge color from red to black
        if self.editor_gui.selected_element is not None:
            if hasattr(self.editor_gui.selected_element, "set_edgecolor"):
                self.editor_gui.selected_element.set_edgecolor("black")
            elif hasattr(self.editor_gui.selected_element, "set_color"):
                self.editor_gui.selected_element.set_color("black")
        return True


    def end_tool(self, event):
        if not self.active:
            return False
        if self.editor_gui.element_is_picked:
            self.editor_gui.element_is_picked = False
            if self.editor_gui.selected_element is None:
                return False
            self.replace_zoom_rectangle_with_selector(self.editor_gui.selected_element)
            self.zoom_selector.set_active(True)
            self.zoom_selector.set_visible(True)
            return False
        if self.tool_start_position is None:
            return False

        self.tool_start_position = None
        self.editor_gui.tool_start_position = None


    @EditorTool.only_do_for_correct_object
    def switch_to_other_tool(self):
        if self.zoom_selector is None:
            return False
        self.replace_zoom_rectangle_with_selector(
            self.editor_gui.selected_element)
        self.zoom_selector.set_active(True)
        self.zoom_selector.set_visible(True)

    def reset_edge_color_of_selected_element(self):
        if self.editor_gui.selected_element is not None:
            if ((isinstance(self.editor_gui.selected_element, matplotlib.text.Text)) |
                    (isinstance(self.editor_gui.selected_element,
                                matplotlib.patches.FancyArrow))):
                self.editor_gui.selected_element.set_color("black")
            else:
                self.editor_gui.selected_element.set_edgecolor("black")

    def switch_active_zoom_rectangle(self, new_zoom_rectangle):
        self.reset_edge_color_of_selected_element()
        if new_zoom_rectangle is not None:
            new_zoom_rectangle.set_edgecolor("red")
            self.editor_gui.selected_element = new_zoom_rectangle
            self.canvas.draw()


