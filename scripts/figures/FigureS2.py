# -*- coding: utf-8 -*-

from fastfig import figure
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

figure = Figure(input_folder,number="S2",dpi=600,width=4.75)


figure.create_panel("A", hor_alignment="center", vert_alignment="center")
figure.add_cropping(left=0.3)
figure.show_images()
figure.add_border(left=True)

figure.create_panel("B", increase_size_fac=6, hor_alignment="left")
figure.set_data_params(x="neurite", y="speed", col="stage")
inclusion_criteria = [{"stage":["2.0"]}]
fraction_criteria = {}
fraction_criteria["Retrograde"] = {"speed":" > 0"}
fraction_criteria["Anterograde"] = {"speed":" < 0"}
fraction_criteria["Stationary"] = {"speed":" == 0"}
figure.calculate_fractions(fraction_criteria)
figure.show_data_columns()
figure.show_data(x="neurite",hue = "fraction_group", 
                  plot_colors=sb.xkcd_palette(["white","silver","grey"]),
                  y_axis_label="Neurites with\nmicrotubule patches\nmoving in direction [%]",
                  perform_stat_test = False,
                  plot_type="bar", show_x_axis=False,
                  show_data_points=False,
                   data_plot_kwds={"swarm_plot_size":2},
                  inclusion_criteria=inclusion_criteria,
                  scale_columns={"speed":100})
figure.get_basic_statistics(["fraction_group"])

figure.create_panel("C", increase_size_fac=5)

figure.show_data(x="MTRF", y="length_difference", col=None, hue=None,
                  plot_colors=sb.xkcd_palette(["black","silver","grey"]),
                    perform_stat_test=False, plot_type="scatter",
                  y_axis_label="Neurite growth [\u03BCm]", 
                  x_axis_label="Microtubule retrograde flow [\u03BCm/min]",
                  scale_columns={"length_difference":0.44,
                                  "MTRF":-1})
figure.draw_line_on_images(position = 0, line_width=1, 
                            orientation="hor", color="black")
figure.draw_line_on_images(position = 0, line_width=1, 
                            orientation="vert", color="black")
figure.save("png")
