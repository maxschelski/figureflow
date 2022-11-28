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

figure = Figure(input_folder,number="S15",dpi=600,width=4.75)

figure.create_panel("A", increase_size_fac=6, hor_alignment="center",
                    padding=[None, None])
figure.show_data_columns()
figure.show_data(col="orientation", y="fraction", x="treatment",hue="timepoint",
                  plot_colors=sb.xkcd_palette(["white","grey","white"]),
                    perform_stat_test=True, test="stats.wilcoxon",
                    x_labels=[("DMSO-EB","Control"),
                              ('Tax-EB','Taxol'),
                              ("paBlebb-EB", "pa-\nBlebb"),
                              ("LatB-EB", "LatB")], 
                    x_order=["Control","pa-\nBlebb","Taxol", "LatB"],
                   col_order=["plus-end-out"],
                   hue_labels=[("0", "Before"),("1", "After")],
                   box_pairs=[["Before", "After"]],
                  average_columns = ["date", "treatment","cell"],
                   y_range = [-2, 100],
                  y_axis_label="Fraction plus-end-out\nmicrotubules [%]",
                   data_plot_kwds={"swarm_plot_point_size":1.3},
                    legend_handle_length=1,
                    scale_columns={"fraction":100}
                  )
figure.get_basic_statistics(show_from_ungrouped_data=True,
                            n_columns=["date", "cell"])
figure.get_representative_data(unit_columns=["date", "treatment", "cell" ])


figure.create_panel("B", increase_size_fac=6, hor_alignment="center",
                    padding=[None, None])
figure.show_data(col="orientation", y="fraction", x="treatment",hue="timepoint",
                  plot_colors=sb.xkcd_palette(["white","grey","white"]),
                    perform_stat_test=True, test="stats.wilcoxon",
                    x_labels=[("DMSO-EB","Control"),
                              ('Tax-EB','Taxol'),
                              ("paBlebb-EB", "pa-\nBlebb"),
                              ("LatB-EB", "LatB")], 
                    x_order=["Control","pa-\nBlebb","Taxol", "LatB"],
                   col_order=["minus-end-out"],
                   hue_labels=[("0", "Before"),("1", "After")],
                   box_pairs=[["Before", "After"]],
                  average_columns = ["date", "cell"],
                   y_range = [-2, 100],
                  y_axis_label="Fraction plus-end-in\nmicrotubules [%]",
                   data_plot_kwds={"swarm_plot_point_size":1.3},
                    legend_handle_length=1,
                    scale_columns={"fraction":100}
                  )

figure.save("png")