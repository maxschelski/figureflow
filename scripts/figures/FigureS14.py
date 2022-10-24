# -*- coding: utf-8 -*-

from figureflow import figure
import seaborn as sb
import numpy as np
import os

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

figure = Figure(input_folder,number="S14",dpi=600,width=4.75)

figure.create_panel("A", increase_size_fac=1, hor_alignment="center",
                    vert_alignment="center",
                    padding=[0.1,None])
figure.show_images()
figure.rescale_font_size()


figure.create_panel("B", increase_size_fac=6, hor_alignment="center",
                    padding=[None, None])
figure.show_data(hue=None, y="MT-RFmed", x="manipulation",
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test="Wilcoxon",
                  x_labels=[("before","Before"),('early','After')], 
                  x_order=["Before","After"],
                  pair_unit_columns=["date", "neuron"],
                  average_columns=["date", "neuron"],
                  y_axis_label="Microtubule retrograde\nflow [\u03BCm/min]",
                   data_plot_kwds={"swarm_plot_point_size":2.3},
                    legend_handle_length=1,
                    scale_columns={"MT-RFmed":-1}
                  )
figure.get_basic_statistics(show_from_ungrouped_data=True,
                            n_columns=["date", "neuron"])
figure.draw_line_on_images(position = 0, line_width=0.5, 
                            orientation="hor", color="black")


figure.create_panel("C", increase_size_fac=1, hor_alignment="center", 
                    vert_alignment="center",
                    padding=[None, None])
figure.set_image_scaling(x_scale = 0.2, y_scale = 1/40)
additional_padding = {"images":1}
figure.show_images(additional_padding=additional_padding, 
                    use_same_LUTs=False, scale_images=False,
                    )

figure.add_y_axis(show_title_in_rows=[0],show_title_in_columns=[0],
                    axis_padding=1, site="right",
                    axis_title="Time [h]",
                    tick_values=[0.5,1,1.5,2,2.5, 3, 3.5],
                    tick_length=3, tick_width=1,
                    tick_color="white")

figure.label_category(category="images", texts=["CAMSAP3", "Photoconverted tubulin"], 
                        site="top", label_orientation="hor")

figure.add_x_axis(show_title_in_rows=[0],show_title_in_columns=[0],
                    axis_padding=1,
                    axis_title="Soma distance [\u03BCm]",
                    tick_values=[0,10,20,30,40])

figure.draw_line_on_images(position = 71, line_width=1,
                            only_show_in_rows=[0],
                            line_style=(0, (3,1)), color="white")


figure.create_panel("D", increase_size_fac=6, hor_alignment="center",
                    padding=[None, None])
inclusion_criteria=[{"time":[2,3]}]
figure.show_data(x="interval", y="tubb_frac", col="region",
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test="Wilcoxon",
                    x_labels=[("0","Before"),("1","After")],
                    x_order=["Before", "After"],
                    col_labels=[("retrograde","Retrograde"),
                              ('anterograde','Anterograde'),
                              ('stationary','Stationary')],
                    box_pairs=[["Before", "After"]],
                    col_order=["Retrograde",'Anterograde','Stationary'],
                  pair_unit_columns=["date", "cell"],
                    y_range = [-2, 105],
                    y_axis_label="Fraction of\nmicrotubule mass [%]",
                  average_columns=["date", "cell"],
                   data_plot_kwds={"swarm_plot_point_size":1.6},
                    inclusion_criteria=inclusion_criteria,
                    legend_handle_length=1,
                    scale_columns={"tubb_frac":100},
                  add_background_lines=False,
                  group_padding=.16
                  )
figure.get_basic_statistics(show_from_ungrouped_data=True,
                            n_columns=["date", "cell"])

                               
figure.create_panel("E", increase_size_fac=6, hor_alignment="center",
                    padding=[None, None])
figure.show_data(x="manipulation", y="int_change", col="region",
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test="Wilcoxon",
                    x_labels=[("before","Before"),("early","After"),
                              ("late","Late\nafter")],
                    x_order=["Before", "After"],
                    col_labels=[("proximal","Proximal neurite"),
                              ('distal','Distal neurite')],
                    box_pairs=[["Before", "After"]],
                    col_order=["Distal neurite",'Proximal neurite'],
                  pair_unit_columns=["date", "neuron"],
                    connect_paired_data_points=False,
                    y_range = [0, 7.8],
                    y_tick_interval=1,
                    y_axis_label="Relative microtubule density",
                  average_columns=["date", "neuron"],
                   data_plot_kwds={"swarm_plot_point_size":1.6},
                    legend_handle_length=1,
                  add_background_lines=False,
                  group_padding=.16
                  )
figure.get_basic_statistics(show_from_ungrouped_data=True,
                            n_columns=["date", "neuron"])

                               
figure.create_panel("F", increase_size_fac=6, hor_alignment="center",
                    padding=[None, None])
inclusion_criteria=[{"int_change":"<40"}]
figure.show_data(x="manipulation", y="growth_rate", col=None,
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test="Wilcoxon",
                    x_labels=[("before","Before"),("early","After"),
                              ("late","Late\nafter")],
                    x_order=["Before", "After"],
                    box_pairs=[["Before", "After"]],
                    y_axis_label="Neurite growth rate [\u03BCm/h]",
                  average_columns=["date", "neuron"],
                   data_plot_kwds={"swarm_plot_point_size":1.6},
                    inclusion_criteria=inclusion_criteria,
                    legend_handle_length=1,
                    scale_columns={"growth_rate":60}
                  )
figure.get_basic_statistics(show_from_ungrouped_data=True,
                            n_columns=["date", "neuron"])



figure.create_panel("G", increase_size_fac=1,vert_alignment="top", 
                    hor_alignment="right")
figure.add_cropping(left=0.1, bottom=0, right=0, top=0.1)
figure.show_images(frames=[[0,16],[50,109]], 
                    channels=[0],
                    channels_to_show_first_nonzoomed_timeframe=[0],
                    auto_enlarge=True,                    
                      position_zoom_nb="top-left",
                      cmaps="viridis")


figure.label_category(category="frames_sub", texts=["Before\ndimerization",
                                                    "After\ndimerization"],
                      label_orientation="vert")

figure.annotate_channel_within_image(["Tubulin"],
                                      position="top-right",
                                      only_show_in_columns=[0],
                                      only_show_in_rows=[0],
                                      channel_colors=["white"])

figure.add_timestamp(time_per_frame="90s",position="bottom-left",
                      format="hh:mm",show_unit=True,
                      padding=[0.015, 0.03],
                      start_time=0, first_time_difference=0)


figure.add_scale_bar(um_per_px=0.22, lengths_um=[20])

figure.add_colorbars(site="bottom", only_show_in_columns=[0],
                      size=0.05, font_size_factor=1)


figure.create_panel("H", increase_size_fac=1, hor_alignment="center", 
                    vert_alignment="center",
                    padding=[None, None])
figure.add_cropping(bottom=0, right=0.1)
figure.set_image_scaling(x_scale = 0.22, y_scale = 1/40)
additional_padding = {"images":1}
figure.show_images(additional_padding=additional_padding, 
                    use_same_LUTs=False, scale_images=False,
                    cmaps=["viridis"]
                    )

figure.add_y_axis(show_title_in_rows=[0],show_title_in_columns=[0],
                    axis_padding=1, site="right",
                    axis_title="Time [h]",
                    tick_values=[0.5,1,1.5,2,2.5],
                    tick_length=3, tick_width=1,
                    tick_color="white")

figure.label_category(category="images", texts=["Photo-\nconverted\ntubulin", 
                                                "Not \nphoto-\nconverted\ntubulin"], 
                        site="left", label_orientation="hor")

figure.add_x_axis(show_title_in_rows=[1],show_title_in_columns=[0],
                  show_in_rows=[1],
                    axis_padding=1,
                    axis_title="Soma distance [\u03BCm]",
                    tick_values=[0,10,20,30,40,50],
                    tick_length=3, tick_width=1,
                    tick_color="white")

figure.add_colorbars(site="top", only_show_in_columns=[0],
                     size=0.05, font_size_factor=1)
figure.draw_line_on_images(position = 16, line_width=1,
                            only_show_in_rows=[0,1],
                            line_style=(0, (3,1)), color="white")

figure.save("png")