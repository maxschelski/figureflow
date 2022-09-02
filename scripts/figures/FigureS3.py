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
script_path = os.path.abspath(__file__)
figureflow_folder = os.path.dirname(os.path.dirname(os.path.dirname(script_path)))
figure_folder_name = os.path.basename(script_path).replace(".py", "")
data_folder = os.path.join(figureflow_folder, "data")
input_folder = os.path.join(data_folder,figure_folder_name)

figure = Figure(input_folder,number="S3",dpi=600,width=3)


figure.create_panel("A", padding=[0.11,0.05], hor_alignment="left",
                    vert_alignment="center")
figure.add_cropping(left=0.3)
figure.show_images()
figure.add_border(left=True)
figure.rescale_font_size()

figure.create_panel("B", increase_size_fac=6, hor_alignment="center",
                    padding=[None, None])
figure.show_data(hue=None, y="speed", x="type",
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test="Wilcoxon",
                    x_labels=[("proximal","Proximal"),('distal','Distal')], 
                    x_order=["Proximal", "Distal"],
                    pair_unit_columns=["date", "cell"],
                  average_columns=["date", "cell"],
                    y_range = [-0.4, 1.8],
                  y_tick_interval=0.2,
                  verbose=True,
                  y_axis_label="Microtubule retrograde flow\n[\u03BCm/min]",
                    swarmplot_point_size=1.7,
                  )
figure.get_basic_statistics(show_from_ungrouped_data=True,
                            n_columns=["date", "cell"])
figure.draw_line_on_images(position = 0, line_width=0.5, 
                            orientation="hor", color="black")


figure.save("png")