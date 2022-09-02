# -*- coding: utf-8 -*-

from figureflow import figure
import seaborn as sb
from matplotlib import pyplot as plt
import importlib
import numpy as np
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

figure = Figure(input_folder,number=7,dpi=600,width=5)


figure.create_panel("A", increase_size_fac=1.5, hor_alignment="right",
                    vert_alignment="center")
figure.show_images()
figure.rescale_font_size()


figure.create_panel("B", increase_size_fac=5.5, hor_alignment="center",
                    padding=[None,None])
inclusion_criteria = [{}]
inclusion_criteria[0]["cycle_threshold"] = [0.2]
inclusion_criteria[0]["treatment"] = ["dmso","taxol","pablebb"]
inclusion_criteria[0]["stage"] = [2.0, 2.5]
figure.show_data(x="treatment", y="cycles/h", col=None, hue=None,
                  plot_colors=sb.xkcd_palette(["white","silver","grey"]),
                    perform_stat_test=True, test="Dunn",
                    x_labels=[("dmso","Control"),('pablebb','pa-\nBlebb'), 
                              ('taxol', 'Taxol')],
                    x_order=["Control","pa-\nBlebb", "Taxol"],
                    average_columns=["date", "neuron"],
                  y_axis_label="Microtubule density\ncycles [1/h]",
                  inclusion_criteria=inclusion_criteria, neg_y_vals = False,
                    y_tick_interval=0.2,
                  show_data_points=True, verbose=True,
                  )
figure.get_basic_statistics()


figure.create_panel("C", increase_size_fac=1, hor_alignment="center",
                    vert_alignment="center")
figure.add_cropping(bottom=0.05, top=0.1, left=0.05, column=1)
figure.add_cropping(bottom=0.05, top=0.1, left=0.05, column=2)
figure.add_cropping(bottom=0.15, top=0.0, left=0.05, column=0)
figure.show_images(frames=[1], channels=[0], cmaps="viridis")
figure.label_images(texts=["Control", "pa-Blebb", "Taxol"])
figure.add_colorbars(site="bottom", size=.06,font_size_factor=1)
figure.add_scale_bar(um_per_px=0.22, lengths_um=[20])
figure.annotate_channel_within_image(["Tubulin"], only_show_in_rows=[0],
                                      position="top-left",
                                      channel_colors=["white"])

inclusion_criteria = []
inclusion_criteria.append({
                            "neuron" : ["cell0046"],
                            "date" : [190430],
                            "channel": [0],
                            "origin":[3.0, 1.0]
                            })
inclusion_criteria.append({
                            "neuron" : ["cell0084"],
                            "date" : ["190430"],
                            "channel": [0],
                            "origin":[1.0, 5.0]
                            })
inclusion_criteria.append({
                            "neuron" : ["cell0007"],
                            "date" : ["190430"],
                            "channel": [0],
                            "origin":[6.0, 4.0]
                            })

figure.create_panel("D", increase_size_fac=1)
figure.show_data(y="int_norm", x="time", col="origin",
                  plot_type="line", 
                  row = "treatment",
                  hue="origin", y_axis_label="Microtubule\ndensity",
                    col_labels= [("1.0", "Neurite 1"),
                                ("2.0", "Neurite 2"),
                                ("3.0", "Neurite 2"),
                                ("4.0", "Neurite 3")],
                    row_labels= [("dmso", "Control"),
                                ("pablebb", "pa-\nBlebb"),
                                ("taxol", "Taxol")],
                  perform_stat_test=False, show_row_label = True,
                  x_tick_interval=1, y_tick_interval=0.3,
                  row_label_orientation = "hor", 
                  show_col_labels_above = True,
                  show_legend=False, smoothing_rad = 2, 
                  sub_padding_y_factor = 0.4,
                  x_range = [0.01,3.99],
                  y_range = [0.45,1.6],
                  show_y_label_in_all_rows=False,
                  show_x_label_in_all_columns=False,
                  inclusion_criteria = inclusion_criteria,
                    x_axis_label = "Time [h]", show_y_minor_ticks=False,
                  plot_colors=sb.xkcd_palette(["black","grey"]),
                   scale_columns={"time":1/60}
                  )

figure.save("png")
