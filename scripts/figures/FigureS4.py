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

figure = Figure(input_folder,number="S4",dpi=600,width=4.75)


figure.create_panel("A", increase_size_fac=1, hor_alignment="center",
                    padding=[0.1,None])
figure.show_images()
figure.rescale_font_size()

figure.create_panel("B", increase_size_fac=6, hor_alignment="center",
                    padding=[None, None])
inclusion_criteria=[{"time":[0]}]
figure.show_data(hue=None, y="spread", x="condition",
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test="Dunn",
                  x_labels=[("LatA","LatA"),('EtOH','Control')], 
                  x_order=["Control","LatA"],
                  average_columns=["date", "experiment", "cell"],
                    y_tick_interval=2,
                  y_axis_label="Microtubule spread [\u03BCm]",
                  inclusion_criteria=inclusion_criteria,
                    legend_handle_length=1,
                    scale_columns={"spread":0.22}
                  )
figure.get_basic_statistics(show_from_ungrouped_data=True,
                            n_columns=["date", "cell"])
                               

figure.create_panel("C", increase_size_fac=6, hor_alignment="center",
                    padding=[None, None])
figure.show_data(x="condition", y="speed", col="direction",
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test="Dunn",
                  x_labels=[("LatA","LatA"),('EtOH','Control')], 
                  x_order=["Control","LatA"],
                  line_offset=0.02,
                  line_height=0.08,
                  col_labels=[("retrograde", "Retrograde"),
                              ("anterograde", "Anterograde")],
                  average_columns=["date", "experiment", "cell"],
                    y_tick_interval=10,
                  y_axis_label="Speed of microtubule spread [\u03BCm/min]",
                   data_plot_kwds={"swarm_plot_size":1.4},
                    legend_handle_length=1,
                    scale_columns={"spread":0.22}
                  )
figure.get_basic_statistics(show_from_ungrouped_data=True,
                            n_columns=["date", "cell"])


figure.create_panel("D", increase_size_fac=1,vert_alignment="top", 
                    hor_alignment="right")
figure.add_cropping(left=0.05, bottom=0.06, right=0.05, top=0.2)
figure.add_zoom(xy=(271, 204), width=80, height=70, channels=[0],images=[0], label_position_overview="top")
figure.add_zoom(xy=(352, 266), width=80, height=70, channels=[0],images=[0], label_position_overview="top")
figure.add_zoom(xy=(176, 313), width=80, height=70, channels=[0],images=[1], label_position_overview="left")
figure.add_zoom(xy=(224, 213), width=80, height=70, channels=[0],images=[1], label_position_overview="top")
figure.show_images(frames=[0],
                    focus="images",
                    show_focus_in="rows",
                    channels_to_show_first_nonzoomed_timeframe=[1],
                    auto_enlarge=False,                    
                      position_zoom_nb="top-left",
                      use_same_LUTs=False,
                      cmaps="gray")

figure.label_channels(texts=["After\nphotoactivation",
                             "Before\nphotoactivation"], 
                      site="top", label_overlays=False)

figure.annotate_channel_within_image(["Tubulin", "Tubulin"], 
                                      only_show_in_columns=[0],
                                      only_show_in_rows=[0],
                                      position="top-left")

figure.label_channels(texts=["0:30", "-1:00 min"], 
                      site="bottom", label_overlays=False)

figure.label_images(texts=["Control",
                             "LatA"], 
                      site="left", label_orientation="hor")

figure.draw_on_image(targets=[ (269, 204) ], direction="left", size=70, images={"zooms":1,
                                                                              "images":0})
figure.draw_on_image(targets=[ (354, 266)], direction="bottom-right", size=70, images={"zooms":2,
                                                                              "images":0})
figure.draw_on_image(targets=[ (175, 312)], direction="top-left", size=70, images={"zooms":1,
                                                                              "images":1})
figure.draw_on_image(targets=[ (223, 216)], direction="left", size=70, images={"zooms":2,
                                                                              "images":1})
figure.add_scale_bar(um_per_px=0.22, lengths_um=[5,20])

figure.save("png")