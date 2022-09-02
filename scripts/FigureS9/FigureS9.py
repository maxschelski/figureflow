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

figure = Figure(input_folder,number="S9",dpi=600,width=4.75)

inclusion_criteria = []
inclusion_criteria.append({
                            "neuron" : [6],
                            "date" : [200529]
                            })
inclusion_criteria.append({
                            "neuron" : [1],
                            "date" : [200605]
                            })
inclusion_criteria.append({
                            "neuron" : [4],
                            "date" : [200529]
                            })
figure.create_panel("A", increase_size_fac=1)
figure.show_data(y="intensity_norm", x="time", col="neuron",
                  plot_type="line", 
                  show_col_labels_above=True,
                  group_padding=0.15,
                  col_labels=[("1","Neuron 1"),
                              ("4","Neuron 2"),
                              ("6","Neuron 3"),
                              ],
                  hue_order=["Intensities",
                              "Fitted\nexpression"],
                    hue="type", 
                    show_legend=True,
                    hue_labels=[("raw", "Intensities"),
                                ("fitted", "Fitted\nexpression")],
                  y_axis_label="Tubulin intensity",
                  perform_stat_test=False,
                  show_x_label_in_all_columns=False,
                  legend_handle_length=0.7,
                  borderaxespad_=0.5,
                  sub_padding_y_factor=0.30,
                  add_background_lines=False,
                  smoothing_rad = 2, 
                    y_range=[0.0001,2.4],
                    inclusion_criteria = inclusion_criteria,
                    x_axis_label = "Time [h]",
                    scale_columns={"time":1/60},
                  plot_colors=sb.xkcd_palette(["grey","black","white"])
                  )


inclusion_criteria = []
inclusion_criteria.append({
                            "neuron" : [6],
                            "date" : [200529],
                            "type":["raw"]
                            })
inclusion_criteria.append({
                            "neuron" : [1],
                            "date" : [200605],
                            "type":["raw"]
                            })
inclusion_criteria.append({
                            "neuron" : [4],
                            "date" : [200529],
                            "type":["raw"]
                            })
figure.create_panel("B", increase_size_fac=1)
figure.show_data(y="intensity_corrected", x="time", col="neuron",
                  plot_type="line",hue="type", 
                  show_col_labels_above=True,
                  group_padding=0.15,
                  add_background_lines=False,
                  col_labels=[("1","Neuron 1"),
                              ("4","Neuron 2"),
                              ("6","Neuron 3"),
                              ],
                  y_axis_label="Tubulin intensity/\nfitted expression",
                  perform_stat_test=False,
                  borderaxespad_=0.5,
                  sub_padding_y_factor=0.30,
                  smoothing_rad = 2, 
                  y_range=[0,2.4],
                  inclusion_criteria = inclusion_criteria,
                    x_axis_label = "Time [h]",
                    scale_columns={"time":1/60},
                  plot_colors=sb.xkcd_palette(["black","grey"])
                  )

inclusion_criteria = []
inclusion_criteria.append({
                            "neuron" : [6],
                            "date" : [200529],
                            "neurite":[0]
                            })
inclusion_criteria.append({
                            "neuron" : [1],
                            "date" : [200605],
                            "neurite":[0]
                            })
inclusion_criteria.append({
                            "neuron" : [4],
                            "date" : [200529],
                            "neurite":[0]
                            })
figure.create_panel("C", increase_size_fac=1)
figure.show_data(y=["intensity", "int_norm"], 
                 x="time", col="neuron",
                  plot_type="line", hue="neurite",
                  show_col_labels_above=True,
                  normalize=True,
                  norm_cats=["date", "neuron"],
                  normalize_by="first",
                  col_labels=[("1","Neuron 1\nNeurite 1"),
                              ("4","Neuron 2\nNeurite 1"),
                              ("6","Neuron 3\nNeurite 1")],
                  y_axis_label=["\nTubulin intensity",
                                "Tubulin intensity/\nfitted expression"],
                  perform_stat_test=False,
                   borderaxespad_=0.5,
                   # x_range=[0,42],
                  sub_padding_y_factor=0.60,
                  smoothing_rad = 2, 
                    y_range=[0,3.9],
                  inclusion_criteria = inclusion_criteria,
                    x_axis_label = "Time [h]",
                    scale_columns={"time":1/60},
                  plot_colors=sb.xkcd_palette(["black","grey"])
                  )

figure.save("png")