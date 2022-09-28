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

figure = Figure(input_folder,number=4,dpi=600,width=5)

figure.create_panel("A", increase_size_fac=1, hor_alignment="right",
                    vert_alignment="center",
                    padding=[0.03, None])
figure.show_images()
figure.rescale_font_size()


figure.create_panel("B", increase_size_fac=4, hor_alignment="center", 
                    vert_alignment="center",
                    padding=[0.09,None])
figure.show_images()
figure.rescale_font_size()


figure.create_panel("C", increase_size_fac=6, hor_alignment="center")
inclusion_criteria= [{"stage":["2.0"]}]
figure.show_data(hue=None, y="speed", x="accumulation",
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test="Wilcoxon",
                  x_labels=[("yes","caKIF5C"),('no','No\ncaKIF5C')], 
                  x_order=["No\ncaKIF5C","caKIF5C"],
                   pair_unit_columns=["date", "cell"],
                  y_tick_interval=0.4,
                  y_axis_label="Microtubule retrograde flow [\u03BCm/min]",
                    swarmplot_point_size=2.3,
                    inclusion_criteria=inclusion_criteria,
                  )
figure.draw_line_on_images(position = 0, line_width=0.5, 
                            orientation="hor", color="black")
figure.get_basic_statistics(show_from_ungrouped_data=True,
                            n_columns=["date", "experiment", "cell"])


figure.create_panel("D", increase_size_fac=1, hor_alignment="center",
                    vert_alignment="center")

figure.add_zoom(xy=(166,85), width=25, height=30, channels=[1], images=[0], 
                label_position_overview="right")
figure.add_zoom(xy=(64,148), width=25, height=30, channels=[1], images=[0], 
                label_position_overview="left") 
figure.add_cropping(left=0, bottom=0.1, right=0.1, top=0.1, row=0)
figure.add_cropping(left=0, bottom=0.1, right=0.1, top=0.1, row=1)
repositioning_map = {}
repositioning_map[("images_sub",0,"images",0,"channels",0,"zooms",0)] = ("images_sub",0,"images",0,"channels",1,"zooms",1)
repositioning_map[("images_sub",0,"images",1,"channels",0,"zooms",0)] = ("images_sub",0,"images",0,"channels",1,"zooms",2)
figure.show_images(frames=[0,9,19], images=[[0,1]],
                    repositioning_map=repositioning_map,
                    auto_enlarge=False,
                    order_of_categories=["zooms"],
                    focus="frames", channels_to_show_first_nonzoomed_timeframe=[0], 
                    position_zoom_nb="top-left", 
                    simple_remapping=True, show_focus_in="columns")
figure.label_channels(texts=["Not\nphotoconverted", "Photoconverted tubulin"], site="top")
figure.label_frames(texts=["0:30 min\n", "5:00", "10:00"], site="bottom")
figure.annotate_channel_within_image(["caKIF5C",""], images=[1,3])
figure.annotate_channel_within_image(["Tubulin",""], images=[0,2])
figure.add_scale_bar(um_per_px=0.44, lengths_um=[20,5])
figure.draw_on_image(targets=[(60,149 )], direction="top-left", 
                      images={"images":0,"zooms":2}, size=50)
figure.draw_on_image(targets=[(167,84)], direction="top-left", 
                      images={"images":0,"zooms":1}, size=50)
#mark growth cones with caKIF5C accumulation
figure.draw_on_image(targets=[(36,165)], direction="top", images={"images":1}, size=50)


figure.save("png")