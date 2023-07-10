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

figure = Figure(input_folder,number=5,dpi=600,width=5)
figure.show_panels("D")

figure.create_panel("A", increase_size_fac=1, hor_alignment="right",
                    vert_alignment="center",
                    padding=[[0.01,0.03], [0.05,None]])
figure.show_images()
figure.rescale_font_size()


figure.create_panel("B", increase_size_fac=6, hor_alignment="right")
renaming_dicts = [{}]
renaming_dicts[-1]["__from__"] = "Axon"
renaming_dicts[-1]["__to__"] = "Future\naxon"
renaming_dicts[-1]["__target-column__"] = "axon"
renaming_dicts[-1]["stage"] = ["No axon"]
inclusion_criteria = [{}]
inclusion_criteria[0]["cycle_threshold"] = [0.2]
figure.show_data(x="axon", y="cycles/h", col="stage", hue=None,
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test="stats.wilcoxon",
                    col_labels=[("2.0", "No axon"), ("3.0", "With axon")],
                    box_pairs=[["Minor\nneurites","Axon"]],#,
                    pair_unit_columns=["date", "neuron"],
                    average_columns=["date", "neuron"],
                    verbose=True,
                    x_labels=[("0.0","Minor\nneurites"), ("1.0", "Axon")],
                  y_axis_label="Microtubule density cycles [1/h]",
                    y_range=[-0.05,1.8], 
                  y_tick_interval = 0.3,
                  inclusion_criteria=inclusion_criteria,
                  show_data_points=True,
                  renaming_dicts = renaming_dicts,
                  add_background_lines=False,
                  group_padding=.16
                  )
figure.get_basic_statistics()


figure.create_panel("C", increase_size_fac = 1, hor_alignment="center", padding=[None, None])
figure.add_cropping(bottom=0.2, left=0, right=0.15)
figure.show_images(frames=[0,1,2],
                    cmaps="viridis")
figure.add_colorbars(site="right",font_size_factor=1)

figure.add_text_within_at_coords("Axon",x=209, y=73, only_show_in_columns=[2])#Axon
figure.add_text_within_at_coords("1",x=326, y=171, only_show_in_columns=[2])#1
figure.add_text_within_at_coords("2",x=319, y=285, only_show_in_columns=[2])#2
figure.add_text_within_at_coords("3",x=172, y=140, only_show_in_columns=[2])#7

figure.annotate_channel_within_image(channel_names=["Tubulin"], 
                                      position="top-left",
                                      only_show_in_columns=[0])
figure.add_scale_bar(um_per_px=0.22, lengths_um=[20], position="bottom-left")

inclusion_criteria = []
inclusion_criteria.append({
                            "neuron" : [9],
                            "date" : [200529],
                            "neurite": [0,1,2,7]
                            })
figure.create_panel("D",y=1, increase_size_fac=1,
                    padding=[[0.08, 0.02],None])
figure.show_data(y="int_norm", x="time",
                  plot_type="line", 
                  row = "neurite", 
                  hue="neurite", y_axis_label="Microtubule\ndensity",
                    row_labels = [("0", "Axon"), ("1", "Neurite 1"), 
                                  ("2", "Neurite 2"), ("3", "Neurite 3"), 
                                  ("4", "Neurite 3"), ("5", "Neurite 5"), 
                                  ("6", "Neurite 6"), ("7", "Neurite 3")],
                  perform_stat_test=False,
                  borderaxespad_=0.5,
                  sub_padding_y_factor=0.30,
                  smoothing_rad = 2, show_row_label=True,
                  row_label_orientation="hor",
                  y_tick_interval=0.3,
                    y_range=[0.2,1.65],
                    x_tick_interval=2,
                  inclusion_criteria = inclusion_criteria,
                    x_axis_label = "Time [h]",
                    scale_columns={"time":1/60},
                  plot_colors=sb.xkcd_palette(["black","grey"])
                  )
figure.draw_line_on_images(765/60, color="gray", orientation="vert",
                            line_style=(0, (5,2)))
figure.get_basic_statistics()


figure.create_panel("E", increase_size_fac=4, padding=[0.6, None])# was 0.1 
inclusion_criteria = [{}]
inclusion_criteria[0]["cycle_threshold"] = [0.2]
inclusion_criteria[0]["stage"] = [2.0]
figure.show_data(x="MT-RFmed_neg", y="cycles/h", col=None,
                  plot_type="regression", y_axis_label="Microtubule density\ncycles [1/h]",
                  x_axis_label="Microtubule retrograde flow [\u03BCm/min]",
                  plot_colors=sb.xkcd_palette(["black","grey"]),
                    perform_stat_test=False, x_range = [0.05, 1.0],
                    y_range=[0,1.81],
                    y_tick_interval=0.3,
                    inclusion_criteria=inclusion_criteria, 

                   data_plot_kwds={"show_formula":True,
				   "position_regression_text":"top-left"},
                    scale_columns={"MT-RFmed_neg":-1})


figure.save("png")