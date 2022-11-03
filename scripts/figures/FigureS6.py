# -*- coding: utf-8 -*-

from figureflow import figure
import seaborn as sb
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

figure = Figure(input_folder,number="S6", dpi=600, width=4.75)

figure.create_panel("A", increase_size_fac=1.7, vert_alignment= "center", padding=[None,None])
figure.show_images()
figure.rescale_font_size()


figure.create_panel("B", increase_size_fac=5)

figure.show_data(x="neurite", y="speed", col="stage", hue=None,
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test="stats.Wilcoxon",
                  x_labels=[("short","Minor\nneurite"),('long','Axon')], x_order=["Minor\nneurite","Axon"],
                  col_labels=[("3.0","Stage 3")],col_order=["Stage 3"],
                  pair_unit_columns=["date", "experiment","cell"],
                  y_tick_interval=0.3,
                  y_axis_label="Microtubule retrograde flow\n[\u03BCm/min]")
figure.get_representative_data(unit_columns=["date", "cell"])
figure.draw_line_on_images(position = 0, line_width=0.5, 
                            orientation="hor", color="black")
figure.get_basic_statistics(show_from_ungrouped_data=True,
                            n_columns=["date", "experiment", "cell"])


figure.create_panel("C", increase_size_fac=2, vert_alignment="center",
                    hor_alignment="right", padding=[None, 0.05])
figure.add_zoom(xy=(127,114), width=22, height=34, channels=[1], label_position_overview="right")
figure.add_zoom(xy=(138,186), width=22, height=34, channels=[1], label_position_overview="right")
figure.add_cropping(left=0.3, bottom=0.15, right=0.2, top=0)
figure.show_images(frames=[0,1,3,6], order_of_categories=["zooms","frames"], 
                    channels_to_show_first_nonzoomed_timeframe=[0], 
                    position_zoom_nb="top-left", 
                    enlarged_image_site="left",
                    focus="frames",
                    show_focus_in="columns")
figure.label_channels(texts=["Not\nphotoconverted", "Photoconverted tubulin"], site="top", align_all_labels=True)
figure.label_frames(texts=["- 2:00 min", "0:30", "4:30", "10:30"], site="bottom")
figure.draw_on_image(targets=[ (128,113) ], direction="left", images={"zooms":1})
figure.draw_on_image(targets=[ (138,190) ], direction="left", images={"zooms":2})
figure.add_scale_bar(um_per_px=0.44, lengths_um=[5,20])
figure.annotate_channel_within_image(["Tubulin", "Tubulin"], 
                                      only_show_in_columns=[0],
                                      position="top-right")


figure.save("png")