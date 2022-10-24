# -*- coding: utf-8 -*-

from figureflow import figure
import seaborn as sb
from matplotlib import pyplot as plt
import importlib
import numpy as np
importlib.reload(figure)
import os

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

figure = Figure(input_folder,number=6,dpi=1000,width=5)


figure.create_panel("A", increase_size_fac=1.5, hor_alignment="center",
                    vert_alignment="bottom",
                    padding=[None,None])
figure.show_images()
figure.rescale_font_size()


figure.create_panel("B", increase_size_fac=4.5,
                    padding=[0.02,None])
inclusion_criteria = []
inclusion_criteria.append({"stage":["2.0"]})
inclusion_criteria.append({"stage":["3.0"], "treatment":["DMSO"], "neurite": ["long"]})
figure.show_data(x="neurite", y="speed", hue="treatment", col="stage",
                    x_labels=(("short","Minor neurite"),("long","Axon")),
                    x_order=["Minor neurite","Axon"],
                    col_labels=(("2.0","No axon"),("3.0", "")), 
                    col_order=["No axon", ""],
                    hue_labels=(("paBlebb","pa-\nBlebb"),
                                ("taxol","Taxol"),
                                ("DMSO","Control")), 
                    hue_order=["Control", "pa-\nBlebb", "Taxol"],
                    average_columns=["date", "experiment", "cell"],
                    plot_colors=sb.color_palette(["white", "silver", "grey"]),
                    y_axis_label = "Microtubule retrograde flow [\u03BCm/min]",
                   data_plot_kwds={"swarm_plot_size":1.4},
                    y_range=[-0.5, 2.0],
                    inclusion_criteria=inclusion_criteria,
                    y_tick_interval=0.3)
figure.draw_line_on_images(position = 0, line_width=0.5, 
                            orientation="hor", color="black")
figure.get_basic_statistics(n_columns=["date", "experiment","cell"])



figure.create_panel("C", hor_alignment="left", padding=[None, 0.3])
figure.add_zoom(xy=(82,105), width=40, height=40, channels=[1], images=[0])
figure.add_zoom(xy=(118,156), width=40, height=40, channels=[1], images=[0], 
                label_position_overview="right")

figure.add_zoom(xy=(137,95), width=40, height=40, channels=[1], images=[1], 
                label_position_overview="right")
figure.add_zoom(xy=(177,159), width=40, height=40, channels=[1], images=[1], 
                label_position_overview="right")

figure.add_zoom(xy=(163,87), width=40, height=40, channels=[1], images=[2], 
                label_position_overview="right")
figure.add_zoom(xy=(182,137), width=40, height=40, channels=[1], images=[2], 
                label_position_overview="right")

figure.add_zoom(xy=(134,177), width=40, height=40, channels=[1], images=[3], 
                label_position_overview="top")
figure.add_zoom(xy=(166,216), width=40, height=40, channels=[1], images=[3], 
                label_position_overview="right")
#
figure.show_images(frames=[0,1,9,19],images=[[0,1,2],[3]],
                    auto_enlarge=True,
                    channels_to_show_first_nonzoomed_timeframe=[0],  
                    show_focus_in="columns")

figure.label_category(category="images_sub", texts=["No\naxon", "With\naxon"], 
                      site="right",
                        label_orientation="hor")
figure.label_category(category="frames", texts=["- 2:00  min", "0:30", "5:00", "10:00"], 
                      site="bottom", label_orientation="hor")
figure.label_category(category="images", 
                      texts=["Control", "pa-\nBlebb", "Taxol", "Control"], 
                      label_orientation="hor",  site="left", plot_line=False)
figure.label_channels(texts=["Not photo-\nconverted", "Photoconverted\ntubulin"], 
                      site="top", label_orientation="hor")
figure.add_scale_bar(um_per_px=0.44, lengths_um=[20,5])

figure.draw_on_image(targets=[(80,107)], direction="bottom-left", images={"images":0,"zooms":1}, size=35)
figure.draw_on_image(targets=[(119,158)], direction="right", images={"images":0,"zooms":2}, size=35)

figure.draw_on_image(targets=[(138,95)], direction="right", images={"images":1,"zooms":1}, size=35)
figure.draw_on_image(targets=[(175,161)], direction="bottom-left", images={"images":1,"zooms":2}, size=35)

figure.draw_on_image(targets=[(166,89)], direction="bottom-right", images={"images":2,"zooms":1}, size=35)
figure.draw_on_image(targets=[(181,140)], direction="bottom", images={"images":2,"zooms":2}, size=35)

figure.draw_on_image(targets=[(132,180)], direction="bottom-left", images={"images":3,"zooms":1}, size=35)
figure.draw_on_image(targets=[(167,218)], direction="bottom-right", images={"images":3,"zooms":2}, size=35)
figure.annotate_channel_within_image(["Tubulin", "Tubulin"], 
                                      only_show_in_columns=[0],
                                      only_show_in_rows=[1],
                                      position="top-left")

figure.draw_on_image(targets=[(140,126)], direction="bottom-right", images={"images":4,"zooms":1})
figure.draw_on_image(targets=[(90,92)], direction="bottom", images={"images":4,"zooms":2})

figure.draw_on_image(targets=[(111,99)], direction="bottom-left", images={"images":5,"zooms":1})
figure.draw_on_image(targets=[(107,173)], direction="bottom-right", images={"images":5,"zooms":2})


figure.save("png")