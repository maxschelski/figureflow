from .editor_tool import EditorTool
import matplotlib
from PyQt5 import QtWidgets
import functools

class TextEditor(EditorTool):

    def __init__(self, controls_layout, include_all_labels=False, **kwargs):
        super().__init__( **kwargs)
        self.element_type = matplotlib.text.Text
        self.controls_layout = controls_layout
        self.include_all_labels = include_all_labels

        self.change_text_inputs = {}
        self.delete_text_buttons = {}
        self.all_text_fields = {}

        self.canvas.mpl_connect("pick_event", self.on_pick_event)
        self.canvas.mpl_connect("key_press_event", self.move_text)
        self.canvas.mpl_connect("button_release_event", self.on_release_event)
        self.canvas.mpl_connect("motion_notify_event", self.move_picked_element)
        self.canvas.mpl_connect("key_press_event", self.remove_element)

    def add_text_buttons_for_text_on_ax(self):
        # get text in current ax and add boxes for it
        for child in self.ax.get_children():
            if not isinstance(child, matplotlib.text.Text):
                continue
            # if not all labels should be made changeable
            # do not include any text corresponding to labels
            if self.include_all_labels:
                include_label = True
            else:
                label = child.get_label()
                if label.startswith("label"):
                    include_label = False
                else:
                    include_label = True
            if not include_label:
                continue
            text = child.get_text()
            if text == "":
                continue
            text_field_number = self.get_next_text_field_number()
            child.set_label("textfield_" + str(text_field_number))
            self.all_text_fields[text_field_number] = child
            self.add_editor_for_text(text, text_field_number)


    def add_editor_for_text(self, text, text_field_number):
        """
        Add a text field to edit text that was just added.
        """

        change_text_function = functools.partial(self.change_text,
                                                 text_field_number=
                                                 text_field_number)
        change_text_input = QtWidgets.QLineEdit(self.editor_gui)
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
        new_text_field = self.ax.text(self.ax.get_xlim()[0],
                                             self.ax.get_ylim()[0],
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
        if self.editor_gui.selected_element is not None:
            text_label = "textfield_" + str(text_field_number)
            if self.editor_gui.selected_element.get_label() == text_label:
                self.editor_gui.selected_element = None
        self.all_text_fields[text_field_number].remove()
        self.change_text_inputs[text_field_number].deleteLater()
        self.delete_text_buttons[text_field_number].deleteLater()
        del self.all_text_fields[text_field_number]
        del self.change_text_inputs[text_field_number]
        del self.delete_text_buttons[text_field_number]
        self.canvas.draw()

    @EditorTool.only_do_for_correct_object
    def move_picked_element(self, event):
        """
         Update text position and redraw
        """
        # only allow interaction with text objects when tool is active
        # (which is when no other tool is active)
        if not self.active:
            return False
        if self.dragged_element is None:
            return False
        if self.editor_gui.moved_out_of_ax:
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

    @EditorTool.only_do_for_correct_object
    def remove_element(self, event):
        # only allow interaction with text objects when tool is active
        # (which is when no other tool is active)
        if not self.active:
            return False
        if self.editor_gui.selected_element is None:
            return False
        if event.key not in ["delete", "backspace"]:
            return False
        text_field_number = int(
            self.editor_gui.selected_element.get_label().split("_")[1])
        self.delete_text("", text_field_number)

    @EditorTool.only_do_for_correct_object
    def move_text(self, event):
        """
        Move currently selected text element with arrow keys.
        Pressing Control (ctrl) and arrow key increases movement speed 5 fold
        Pressing shift (ctrl) and arrow key reduces movement speed 5 fold
        Pressing control and shift and arrow key increases speed 10 fold
        """
        # only allow interaction with text objects when no other
        # tool is active
        if not self.active:
            return False
        if self.editor_gui.selected_element is None:
            return False
        (movement_keys,
         modifier_keys) = self.get_movement_and_modifier_keys(event)

        if len(movement_keys) == 0:
            return False

        ax = self.editor_gui.selected_element.axes
        (step_size_x,
        step_size_y) = self.get_step_sizes_for_modifier_keys(modifier_keys, ax)

        text_position = list(self.editor_gui.selected_element.get_position())
        text_position = self.get_position_after_step(text_position,
                                                     movement_keys,
                                                     step_size_x, step_size_y)

        text_position_in_limits = self.get_position_in_limits(text_position,
                                                              ax)

        self.editor_gui.selected_element.set_position(text_position_in_limits)
        self.canvas.draw()

    @EditorTool.only_do_for_correct_object
    def on_pick_event(self, event):
        # only allow picking if the text tool is active
        # (no other tools is active)
        if not self.active:
            return False
        super().on_pick_event(event)

    @EditorTool.only_do_for_correct_object
    def on_release_event(self, event):
        """
        Update text position and redraw
        """
        # only allow interaction with text objects when tool is active
        # (which is when no other tool is active)
        if not self.active:
            return False
        if self.dragged_element is None:
            return False
        self.editor_gui.element_is_picked = False
        self.dragged_element = None
        self.moved_out_of_ax = False
        return True

    def select_ax(self):
        # add previously removed text fields again
        self.add_text_buttons_for_text_on_ax()

    def deselect_ax(self):
        # delete text field editors
        # save them and add them again upon activation
        all_text_field_numbers = list(self.change_text_inputs.keys())
        for text_field_number in all_text_field_numbers:
            self.change_text_inputs[text_field_number].deleteLater()
            del self.change_text_inputs[text_field_number]
            self.delete_text_buttons[text_field_number].deleteLater()
            del self.delete_text_buttons[text_field_number]


