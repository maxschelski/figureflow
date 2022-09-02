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
script_figure_folder = os.path.dirname(os.path.abspath(__file__))
scripts_folder = os.path.dirname(script_figure_folder)
figure_folder_name = os.path.basename(script_figure_folder )
data_folder = os.path.join(os.path.dirname(scripts_folder), "data")
input_folder = os.path.join(data_folder,figure_folder_name)

figure = Figure(input_folder,number="S5",dpi=600,width=4.75)

figure.create_panel("A", increase_size_fac=1, hor_alignment="center",
                    padding=[0.1,None])
figure.show_images()
figure.rescale_font_size()

figure.create_panel("B", increase_size_fac=6, hor_alignment="center",
                    padding=[None, None])
figure.show_data_columns()
figure.show_data(hue=None, y="speed", x="type",
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test="Wilcoxon",
                    x_labels=[("proximal","Proximal"),('distal','Distal')], 
                    x_order=["Proximal", "Distal"],
                    pair_unit_columns=["date", "cell"],
                  average_columns=["date", "cell"],
                    y_range = [-0.2, 1],
                  y_tick_interval=0.2,
                  verbose=True,
                  y_axis_label="Microtubule retrograde flow\n[\u03BCm/min]",
                    swarmplot_point_size=1.7,
                  )
figure.get_basic_statistics(show_from_ungrouped_data=True,
                            n_columns=["date", "cell"])
figure.draw_line_on_images(position = 0, line_width=0.5, 
                            orientation="hor", color="black")


figure.create_panel("C", increase_size_fac=1,vert_alignment="top", 
                    hor_alignment="right")
figure.add_cropping(left=0.25, bottom=0.1, right=0.08, top=0.15)
figure.add_zoom(xy=(88, 84), width=32, height=30, channels=[1], label_position_overview="top")
figure.add_zoom(xy=(120, 138), width=32, height=30, channels=[1], label_position_overview="top")
figure.show_images(frames=[0,1,8,15], 
                    channels=[0, 1],
                    channels_to_show_first_nonzoomed_timeframe=[0],
                    auto_enlarge=True,
                    
                      position_zoom_nb="top-left",
                      overlay_cmaps=["Reds", "Blues"])

figure.label_channels(texts=["Not photoconverted","Photoconverted tubulin"], 
                      site="top", label_overlays=False)

figure.annotate_channel_within_image(["Tubulin", "P"], 
                                      only_show_in_columns=[0],
                                      position="top-left",
                                      color="black")#
figure.label_frames(texts=["- 2:00 min", "0:30", "4:00", "8:00"], site="bottom")

figure.draw_on_image(targets=[ (86, 84) ], direction="left", size=50, images={"zooms":1})
figure.draw_on_image(targets=[ (121, 135) ], direction="top", size=50, images={"zooms":2})
figure.add_scale_bar(um_per_px=0.44, lengths_um=[5,20])

figure.save("png")