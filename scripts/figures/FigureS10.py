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

figure = Figure(input_folder,number="S10",dpi=600,width=4.75)

cycle_thresholds = [0.05,0.1,0.2,0.3,0.4]
letters = "ABCDE"

for nb, cycle_threshold in enumerate(cycle_thresholds):
    letter = letters[nb]
    figure.create_panel(letter, increase_size_fac=1, show_letter=True)
    figure.show_data_columns()
    inclusion_criteria = [{}]
    inclusion_criteria[0]["cycle_threshold"] = [cycle_threshold]
    inclusion_criteria[0]["stage"] = [2.0]
    figure.show_data(x="MT-RFmed_neg", y="cycles/h",
                      plot_type="regression", y_axis_label="Microtubule density\ncycles [1/h]",
                      x_axis_label="Microtubule retrograde flow\n[\u03BCm/min]",
                      always_show_col_label=True,
                      show_col_labels_above=True,
                      plot_title="Minimum microtubule densitiy change of:\n"+str(cycle_threshold),
                      show_x_label_in_all_columns=False,
                      plot_colors=sb.xkcd_palette(["black","grey"]),
                        perform_stat_test=False,
                        use_same_y_ranges=False,
                        inclusion_criteria=inclusion_criteria, 
                        neg_y_vals=False, x_range = [0.05, 1.0],
                        show_formula=True, position_formula ="top-left",
                        scale_columns={"MT-RFmed_neg":-1,
                                       "MT-RFmed":-1,
                                       "speed_decrease":-100, 
                                        "speed_increase":100})
figure.save("png")