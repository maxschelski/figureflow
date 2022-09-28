from .editor_tool import EditorTool
from . import shape_editor
import matplotlib
from matplotlib import widgets
import functools

class RectangleEditor(shape_editor.ShapeEditor):

    def __init__(self, max_dist_resize_rect=20, **kwargs):
        super().__init__(**kwargs)
        self.element_type = matplotlib.patches.Rectangle
        self.max_dist_resize_rect = max_dist_resize_rect
        self.rectangle_selector = None

    def activate(self):
        self.active = True
        if self.rectangle_selector is None:
            self.create_rectangle_selector(self.ax)
        self.rectangle_selector.set_active(True)
        self.rectangle_selector.set_visible(True)

    def deactivate(self):
        self.active = False
        if self.rectangle_selector is None:
            return False
        self.rectangle_selector.set_active(False)
        self.rectangle_selector.set_visible(False)
        return True

    @EditorTool.only_do_for_correct_object
    def remove_element(self, event):
        if self.editor_gui.selected_element is None:
            return False
        if event.key not in ["delete", "backspace"]:
            return False
        self.rectangle_selector.extents = (0,0,0,0)
        super().remove_element(event)

    def new_rectangle_selector(self, ax):
        rectangle_selector = widgets.RectangleSelector(ax,
                                                  self.select_rectangle,
                                                  drawtype='box', useblit=False,
                                                  button=[1, 2],
                                                  minspanx=0.01, minspany=0.01,
                                                  spancoords='data',
                                                  interactive=True,
                                                  maxdist=self.max_dist_resize_rect,
                                                  rectprops=dict(linestyle='-',
                                                                 color='red',
                                                                 linewidth=self.line_width,
                                                                 fill=False,
                                                                 alpha=1)
                                                  )
        for tool_handles in [rectangle_selector._corner_handles,
                             rectangle_selector._edge_handles,
                             rectangle_selector._center_handle]:
            tool_handles.artist.set_mfc("grey")
            tool_handles.artist.set_alpha(1)
            tool_handles.artist.set_markersize(1)

        # select_rectangle_with_details = functools.partial(self.select_rectangle,
        #                                                   rectangle_selector=rectangle_selector
        #                                                   )
        # rectangle_selector.onselect = select_rectangle_with_details
        return rectangle_selector

    def create_rectangle_selector(self, ax):
        self.rectangle_selector = self.new_rectangle_selector(ax)

    def replace_rectangle_selector_with_rectangle(self, rectangle_selector):
        last_zoom_size = rectangle_selector._rect_bbox
        x0, y0 = (last_zoom_size[0], last_zoom_size[1])
        x1, y1 = (x0 + last_zoom_size[2], y0 + last_zoom_size[3])
        x0, y0 = self.transform_coords_from_data_to_axes(x0,y0, self.ax)
        x1, y1 = self.transform_coords_from_data_to_axes(x1,y1, self.ax)
        width = x1 - x0
        height = y1 - y0

        rect = matplotlib.patches.Rectangle((x0, y0), width, height,
                                 linewidth=self.line_width, edgecolor='red',
                                        transform=self.ax.transAxes,
                                 picker=self.pick,label=self.element_label,
                                 facecolor='none')

        rectangle_selector.ax.add_patch(rect)
        self.canvas.draw()
        return rect


    def replace_rectangle_with_selector(self, rect):
        # new_rectangle_selector = self.new_rectangle_selector(rect.axes)
        zoom_size = rect.get_bbox()
        x0, y0 = (zoom_size.x0, zoom_size.y0)
        x1, y1 = (zoom_size.x1, zoom_size.y1)
        x0, y0 = self.transform_coords_from_axes_to_data(x0,y0, self.ax)
        x1, y1 = self.transform_coords_from_axes_to_data(x1,y1, self.ax)
        y_lim = self.ax.get_ylim()
        ax_height_px = max(y_lim) - min(y_lim)
        self.rectangle_selector.extents = (x0, x1,
                                           ax_height_px-y0, ax_height_px-y1)
        return True


    def select_rectangle(self, start_event=None, end_event=None):
        if self.editor_gui.element_is_picked:
            return False
        zoom_rect = self.replace_rectangle_selector_with_rectangle(self.rectangle_selector)
        self.switch_active_rectangle(zoom_rect)
        return True

    def use_tool(self, event):
        if not self.active:
            return False
        if self.tool_start_position is None:
            return False
        if self.editor_gui.moved_out_of_ax:
            return False
        end_position = [event.xdata, event.ydata]
        # set edge color of previous zoom rectangle to self.color
        # so that when drawing a new zoom rectangle, the previous one
        # immediately switches edge color from red to self.color
        self.change_color_of_selected_element_to_default()
        return True


    def end_tool(self, event):
        if not self.active:
            return False
        if self.editor_gui.element_is_picked:
            self.editor_gui.element_is_picked = False
            if self.editor_gui.selected_element is None:
                return False
            self.replace_rectangle_with_selector(self.editor_gui.selected_element)
            self.rectangle_selector.set_active(True)
            self.rectangle_selector.set_visible(True)
            return False
        if self.tool_start_position is None:
            return False

        self.tool_start_position = None
        self.editor_gui.tool_start_position = None


    @EditorTool.only_do_for_correct_object
    def switch_to_other_tool(self):
        if self.rectangle_selector is None:
            return False
        self.replace_rectangle_with_selector(
            self.editor_gui.selected_element)
        self.rectangle_selector.set_active(True)
        self.rectangle_selector.set_visible(True)

    def reset_edge_color_of_selected_element(self):
        if self.editor_gui.selected_element is not None:
            if ((isinstance(self.editor_gui.selected_element, matplotlib.text.Text)) |
                    (isinstance(self.editor_gui.selected_element,
                                matplotlib.patches.FancyArrow))):
                self.editor_gui.selected_element.set_color(self.color)
            else:
                self.editor_gui.selected_element.set_edgecolor(self.color)

    def switch_active_rectangle(self, new_rectangle):
        self.reset_edge_color_of_selected_element()
        if new_rectangle is not None:
            new_rectangle.set_edgecolor("red")
            self.editor_gui.selected_element = new_rectangle
            self.canvas.draw()


