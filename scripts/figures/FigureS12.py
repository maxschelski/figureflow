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

figure = Figure(input_folder,number="S12",dpi=600,width=4.75)


figure.create_panel("A", increase_size_fac=1, hor_alignment="center",
                    padding=[0,0.05])
figure.show_images()
figure.rescale_font_size()


figure.create_panel("B", increase_size_fac=6, hor_alignment="center",
                    padding=[None, None])
figure.show_data(col="type", y="MT-RFmed", x="manipulation",
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test="Dunn",
                  x_labels=[("before","Before"),('early','After')], 
                  x_order=["Before","After"],
                  col_labels=[("axon", "Axon"), ("dendrite", "Dendrites")],
                  average_columns=["date", "neuron"],
                    y_range = [-1, 3.05],
                  y_tick_interval=0.5,
                  y_axis_label="Microtubule retrograde flow [\u03BCm/min]",
                   data_plot_kwds={"swarm_plot_point_size":1.6},
                  line_height=0.08,
                    legend_handle_length=1,
                    scale_columns={"MT-RFmed":-1}
                  )
figure.get_basic_statistics(show_from_ungrouped_data=True,
                            n_columns=["date", "neuron"])


figure.create_panel("C", increase_size_fac=6, hor_alignment="center",
                    padding=[None, None])
figure.show_data(col="type", y="rel_intensity", x="manipulation",
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test="Dunn",
                  x_labels=[("before","Before"),('between','After')], 
                  x_order=["Before","After"],
                  col_labels=[("axon", "Axon"), ("dendrite", "Dendrites")],
                  average_columns=["date", "neuron"],
                    y_range = [-0.05, 2.05],
                  y_tick_interval=0.2,
                  y_axis_label="Relative microtubule density",
                   data_plot_kwds={"swarm_plot_point_size":1.6},
                    legend_handle_length=1,
                  )
figure.get_basic_statistics(show_from_ungrouped_data=True,
                            n_columns=["date", "neuron"])


figure.create_panel("D", increase_size_fac=1,vert_alignment="center", 
                    hor_alignment="center")
figure.add_cropping(left=0.15, bottom=0, right=0.35, top=0)
figure.add_zoom(xy=(202, 209 ), width=93, height=88, channels=[0,1], label_position_overview="top")
figure.add_zoom(xy=(263, 405 ), width=93, height=88, channels=[0,1], label_position_overview="top")
figure.add_zoom(xy=(173, 392), width=93, height=88, channels=[0,1], label_position_overview="left")
figure.show_images(frames=[1,25,49,65], 
                   order_of_categories=["frames", "zooms", "channels"],
                    channels=[0, 1],
                    channels_to_show_first_nonzoomed_timeframe=[0],
                    auto_enlarge=True,
                    focus="zooms",
                    show_focus_in="rows",
                    cmaps=["viridis", "gray"],
                    
                      position_zoom_nb="top-left")

figure.label_channels(texts=["Not photoconverted tubulin","Photoconverted tubulin"], 
                      site="top", label_overlays=False)


figure.current_panel._add_label("-36:00 min", 2,2,0,0,"bottom")
figure.current_panel._add_label("0:00", 2,2,1,1,"bottom")
figure.current_panel._add_label("72:00", 2,2,2,2,"bottom")
figure.current_panel._add_label("84:00", 2,2,3,3,"bottom")
figure.current_panel._add_label("-36:00", 2,2,7,7,"bottom")
figure.current_panel._add_label("0:00", 2,2,8,8,"bottom")
figure.current_panel._add_label("72:00", 2,2,9,9,"bottom")
figure.current_panel._add_label("84:00", 2,2,10,10,"bottom")

figure.add_colorbars(site="left", only_show_in_rows = [0],
                     font_size_factor=1)
figure.draw_on_image(targets=[ (202, 209 ) ], direction="right", 
                     size=50, images={"zooms":1,"channels":1})
figure.draw_on_image(targets=[ (284, 432 ) ], direction="top-right", 
                     size=50, images={"zooms":2,"channels":1})
figure.draw_on_image(targets=[ (163, 402) ], direction="top-left", 
                     size=50, images={"zooms":3, "channels":1})
figure.add_scale_bar(um_per_px=0.33, lengths_um=[10,20])

figure.save("png")