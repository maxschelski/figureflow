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

figure = Figure(input_folder,number=8, dpi=600, width=5)


figure.create_panel("A", increase_size_fac=1, hor_alignment="right",
                    vert_alignment="center",
                    padding=[0.1, None])
figure.show_images()
figure.rescale_font_size(linespacing=1)


inclusion_criteria = [{"stage":["2.0"]}]
figure.create_panel("B", increase_size_fac=7, hor_alignment="center")
figure.show_data(x="treatment", y="speed", hue=None, col=None, 
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test=["stats.kruskal","posthocs.posthoc_dunn"],
                    x_labels=[("DMSO2x","Control"),("cilA50-30m", "Ciliobrevin"),
                              ("cilA50-60m", "Ciliobrevin")],
                    x_order=["Control", "Ciliobrevin"],
                  y_range = [-0.3, 1.8], 
                  y_tick_interval=0.5,
                  inclusion_criteria=inclusion_criteria,
                    average_columns=["date","experiment", "cell"],
                  y_axis_label="Microtubule\nretrograde flow\n[\u03BCm/min]",
                  )
figure.draw_line_on_images(position = 0, line_width=0.5, 
                            orientation="hor", color="black")
figure.get_basic_statistics(n_columns=["date", "experiment","cell"])
figure.get_representative_data(["date", "experiment", "cell"])



inclusion_criteria = [{"stage":["2.0"],  "expression":">400"}]
figure.create_panel("C", increase_size_fac=6, hor_alignment="center")
figure.show_data(x="treatment", y="speed", col="neurite", hue=None,
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test=["stats.kruskal","posthocs.posthoc_dunn"],
                  col_labels=[("short","Minor\nneurite")], col_order=["Minor\nneurite"],
                    x_labels=[("baseline2x","Control"),("baseline","Control"),("IC2", "IC2N")],
                    x_order=["Control", "IC2N"],
                  y_range = [-1.05, 1.8], 
                    y_tick_interval=0.5,
                    average_columns=["date","experiment", "cell"],
                  inclusion_criteria=inclusion_criteria,
                  y_axis_label="Microtubule\nretrograde flow\n[\u03BCm/min]",
                  )
figure.draw_line_on_images(position = 0, line_width=0.5, 
                            orientation="hor", color="black")
figure.get_basic_statistics(n_columns=["date", "experiment","cell"])
figure.get_representative_data(["date", "experiment","cell"])


figure.create_panel("D", hor_alignment="center", padding=[None, None])
figure.add_zoom(xy=(181,90), width=45, height=35, channels=[1], images=[0], 
                label_position_overview="top")
figure.add_zoom(xy=(102,150), width=45, height=35, channels=[1], images=[0], 
                label_position_overview="bottom")

figure.add_zoom(xy=(132,74), width=45, height=35, channels=[1], images=[1], 
                label_position_overview="right")
figure.add_zoom(xy=(137,176), width=45, height=35, channels=[1], images=[1], 
                label_position_overview="right")
figure.show_images(frames=[0,1,9,19],images=[0,1],
                    auto_enlarge=True,
                    channels_to_show_first_nonzoomed_timeframe=[0],  
                    show_focus_in="columns",
                use_same_LUTs=False)

figure.label_category(category="frames", texts=["- 2:00  min", "0:30", "5:00", "10:00"], 
                      site="bottom", label_orientation="hor")
figure.label_category(category="images", 
                      texts=["Control", "Cilio-\nbrevin"], 
                      label_orientation="hor",  site="left", plot_line=False)
figure.label_channels(texts=["Not photo-\nconverted", "Photoconverted\ntubulin"], 
                      site="top", label_orientation="hor")
figure.add_scale_bar(um_per_px=0.44, lengths_um=[20,5])

figure.draw_on_image(targets=[(181,90)], direction="bottom-right", images={"images":0,"zooms":1}, size=35)
figure.draw_on_image(targets=[(102,150)], direction="bottom-right", images={"images":0,"zooms":2}, size=35)

figure.draw_on_image(targets=[(132,74)], direction="right", images={"images":1,"zooms":1}, size=35)
figure.draw_on_image(targets=[(137,176)], direction="right", images={"images":1,"zooms":2}, size=35)

figure.annotate_channel_within_image(["Tubulin", "Tubulin"], 
                                      only_show_in_columns=[0],
                                      only_show_in_rows=[1],
                                      position="top-left")


figure.create_panel("E", hor_alignment="center", padding=[None, None])
figure.add_zoom(xy=(162,107), width=45, height=35, channels=[1], images=[0])
figure.add_zoom(xy=(135,180), width=45, height=35, channels=[1], images=[0], 
                label_position_overview="right")

figure.add_zoom(xy=(119,105), width=45, height=35, channels=[1], images=[1], 
                label_position_overview="left")
figure.add_zoom(xy=(134,165), width=45, height=35, channels=[1], images=[1], 
                label_position_overview="left")

figure.show_images(frames=[0,1,9,19],images=[0,1],
                    auto_enlarge=True,
                    channels_to_show_first_nonzoomed_timeframe=[0],  
                    show_focus_in="columns",
                use_same_LUTs=False)

figure.label_category(category="frames", texts=["- 2:00  min", "0:30", "5:00", "10:00"], 
                      site="bottom", label_orientation="hor")
figure.label_category(category="images", 
                      texts=["Control", "IC2N"], 
                      label_orientation="hor",  site="left", plot_line=False)
figure.label_channels(texts=["Not photo-\nconverted", "Photoconverted\ntubulin"], 
                      site="top", label_orientation="hor")
figure.add_scale_bar(um_per_px=0.44, lengths_um=[20,5])

figure.draw_on_image(targets=[(162,107)], direction="left", images={"images":0,"zooms":1}, size=35)
figure.draw_on_image(targets=[(135,180)], direction="bottom-right", images={"images":0,"zooms":2}, size=35)

figure.draw_on_image(targets=[(119,105)], direction="top-right", images={"images":1,"zooms":1}, size=35)
figure.draw_on_image(targets=[(134,165)], direction="bottom-right", images={"images":1,"zooms":2}, size=35)

figure.annotate_channel_within_image(["Tubulin", "Tubulin"], 
                                      only_show_in_columns=[0],
                                      only_show_in_rows=[1],
                                      position="top-left")


figure.save("png")