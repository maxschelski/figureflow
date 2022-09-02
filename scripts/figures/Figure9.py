# -*- coding: utf-8 -*-

from figureflow import figure
import seaborn as sb
import numpy as np

import importlib
importlib.reload(figure)

Figure = figure.Figure

# get the path to the data of the respective figure or movie
# the data is in the data folder in a folder with the same
# name as the folder that the script is in
# the input_folder can also just be the folder in which the script is
# in which case you would just need the following:
# input_folder = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.abspath(__file__)
figureflow_folder = os.path.dirname(os.path.dirname(os.path.dirname(script_path)))
figure_folder_name = os.path.basename(script_path).replace(".py", "")
data_folder = os.path.join(figureflow_folder, "data")
input_folder = os.path.join(data_folder,figure_folder_name)

figure = Figure(input_folder,number=9, dpi=600, width=7.3)

figure.create_panel("A", increase_size_fac=1, hor_alignment="left",
                    padding=[None, 0.18])
figure.show_images()
figure.rescale_font_size()


figure.create_panel("B", increase_size_fac=1, hor_alignment="left",
                    vert_alignment="center",
                    padding=[0.12, None])
figure.show_images()
figure.rescale_font_size()


figure.create_panel("C", increase_size_fac=4, hor_alignment = "center",
                    padding=[0.11, 0.03])
figure.show_data_columns()
inclusion_criteria = [{"bicd":"<1000", "caax":">200"}]
figure.show_data(x="manipulation", y="MT-RFmed", col="condition",hue=None,
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test="Dunn",
                    col_labels=[("bicd", "With bicDN"), ("control", "Control")],
                    col_order = ["Control", "With bicDN"],
                    always_show_col_label=True,
                    x_labels=[("after","After"),("before", "Before")], x_order=["Before", "After"],
                    average_columns=["date", "neuron"],
                  y_axis_label="Microtubule\nretrograde flow\n[\u03BCm/min]",
                  swarmplot_point_size=1.9, y_range=[-0.55,2],
                  y_tick_interval=0.5,
                  scale_columns = {"MT-RFmed":-1},
                  inclusion_criteria= inclusion_criteria)
figure.draw_line_on_plots(positions = 0, axis="y", line_width=0.5, 
                            color="black")
figure.get_basic_statistics(n_columns=["date", "neuron"])


figure.create_panel("D", increase_size_fac=1, hor_alignment="left", 
                    vert_alignment="top",
                    padding=[None, 0.03])
figure.add_cropping(right=0.15, row=0)
figure.set_image_scaling(x_scale = 0.22, y_scale = 1/60)
additional_padding = {"images":1}
figure.show_images( 
                    additional_padding=additional_padding, 
                    use_same_LUTs=False, scale_images=False,
                    make_image_size_equal=["width", "right",65536])

figure.add_y_axis(show_in_rows=[1],
                    axis_padding=1, site="right",
                    axis_title="Time [h]",
                    tick_values=[0.5,1.0,1.5],
                    show_title_in_rows=[0],
                    tick_length=3, tick_width=1,
                    tick_color="black")

figure.add_y_axis(show_in_rows=[0],
                    axis_padding=1, site="right",
                    axis_title="Time [h]",
                    tick_values=[0.5,1.0,1.5],
                    show_title_in_rows=[0],
                    tick_length=3, tick_width=1,
                    tick_color="white")

figure.label_category(category="images", texts=["Control", "With\nbicDN", 
                                                "\n3", "\n4", "\n5"], 
                      site="left", label_orientation="vert")

figure.add_x_axis(show_in_rows=[1],
                    axis_padding=1,
                    axis_title="Soma distance [\u03BCm]",
                    tick_values=[0,10,20,30],
                    tick_length=3, tick_width=1,
                    tick_color="white")

figure.draw_line_on_images(position = 24, line_width=0.8,
                            line_style=(0, (3,1)), color="white")



figure.create_panel("E", increase_size_fac=1, hor_alignment="center",
                    padding=[None, [0.13,None]])
figure.show_images()
figure.rescale_font_size()



figure.create_panel("F", increase_size_fac=6, hor_alignment = "center",
                    padding=[0.02,0.05])
figure.show_data(x="manipulation", y="MT-RFmed", col="stage", hue="condition",
                  plot_colors=sb.xkcd_palette(["white","grey"]),
                    perform_stat_test=True, test="Dunn",
                    always_show_col_label=True,
                    line_height=0.3,
                    hue_labels=[("Dync1h1K2599T", "Motor\ndeficient"),("Dync1h1", "Wildtype")],
                    x_labels=[("early","After"),("before", "Before")], x_order=["Before", "After"],
                    col_labels = [("2.0", "Membrane recruitment of dynein motor"),
                                  ("2.5", "Membrane recruitment of dynein motor")],
                    col_order = ["Membrane recruitment of dynein motor"],
                  y_axis_label="Microtubule retrograde flow\n[\u03BCm/min]",
                  show_data_points=True,
                  show_legend=True,
                    average_columns=["date", "neuron"],
                  y_tick_interval=0.5,
                  swarmplot_point_size=1.8,
                  legend_handle_length=1,fliersize=1.5,
                  y_range=[-0.05, 2],
                  scale_columns = {"MT-RFmed":-1},
                  )
figure.draw_line_on_images(position = 0, line_width=0.5, 
                            orientation="hor", color="black")
figure.get_basic_statistics(n_columns=["date", "neuron"])
figure.get_representative_data(["date", "neuron"])


figure.create_panel("G", increase_size_fac=1, hor_alignment="left", 
                    vert_alignment="center",
                    padding=[None, 0.02])
figure.add_cropping(right=0.5, bottom=0.7, column=0)
figure.add_cropping(right=0.4, bottom=0.3, column=1)
figure.set_image_scaling(x_scale = 0.22, y_scale = 1/60)

figure.show_images( 
                    use_same_LUTs=False, scale_images=False,
                    make_image_size_equal=["height", "bottom",65536])

figure.add_y_axis(show_in_rows=[0],
                  show_title_in_columns=[1],
                    axis_padding=1, site="right",
                    axis_title="Time [h]",
                    tick_values=[0.5,1.5],
                    tick_length=3, tick_width=1,
                    tick_color="white")

figure.label_category(category="images", texts=["Wildtype", "Motor\ndeficient", 
                                                "\n3", "\n4", "\n5"], 
                      site="top")

figure.add_x_axis(show_title_in_columns=[0],
                    axis_padding=1,
                    axis_title="Soma\ndistance [\u03BCm]",
                    tick_values=[0,10],
                    tick_length=3, tick_width=1,
                    tick_color="white")

figure.draw_line_on_images(position = 37, line_width=0.8,
                            line_style=(0, (3,1)), color="white",
                            only_show_in_columns=[0])

figure.draw_line_on_images(position = 43, line_width=0.8,
                            line_style=(0, (3,1)), color="white",
                            only_show_in_columns=[1])


figure.save("png")