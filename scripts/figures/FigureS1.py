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

figure = Figure(input_folder,number="S1",dpi=600,width=2.2)

figure.create_panel("A", increase_size_fac=4)
inclusion_criteria = [{"channel": ["eos","halo"]}]
figure.show_data(x="channel", y="Mean_norm", col=None, hue=None,
                  plot_colors=sb.xkcd_palette(["white","white","grey"]),
                    perform_stat_test=True,
                    test="Dunn",
                    x_order=["Patch", "Array"],
                    x_labels=[("eos", "Patch"),("halo","Array")],
                  y_axis_label="Normalized tubulin intensity",
                  average_columns=["date", "cell", "ROI"],
                  neg_y_vals = False, inclusion_criteria = inclusion_criteria)

figure.get_basic_statistics()

figure.create_panel("B", increase_size_fac=3)
inclusion_criteria = [{"channel": ["difference"]}]
figure.show_data(x="channel", y="Mean_norm", col=None, hue=None,
                  plot_colors=sb.xkcd_palette(["white","silver","grey"]),
                    perform_stat_test=True,
                  average_columns=["date", "cell", "ROI"],
                  y_axis_label="Normalized tubulin intensity\ndifference",
                  inclusion_criteria = inclusion_criteria)

figure.save("png")
