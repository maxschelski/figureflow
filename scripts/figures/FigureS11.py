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

figure = Figure(input_folder,number="S11",dpi=600,width=4.75)

figure.create_panel("A", increase_size_fac=1, hor_alignment="center",
                    vert_alignment="center",
                    padding=[None,0.15])
figure.show_images()
figure.rescale_font_size()


figure.create_panel("B", increase_size_fac=7, hor_alignment="center",
                    padding=[None, None])
figure.show_data(col="time_speedup", y="tubb_frac", x="region",
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test=["stats.kruskal","posthocs.posthoc_dunn"],
                    col_order=["During initial speedup"],
                    x_labels=[("retrograde","Retro-\ngrade"),
                              ('anterograde','Antero-\ngrade'),
                              ('stationary','Stationary')], 
                    x_order=["Retro-\ngrade",'Antero-\ngrade','Stationary'],
                    average_columns=["date", "cell"],
                    col_labels=[("same", "During initial speedup")],
                    y_ticks=[0,20,40,60,80,100],
                    always_show_col_label=True,
                    y_range = [-2, 120],
                    y_axis_label="Fraction of\nmicrotubule mass [%]",
                   data_plot_kwds={"swarm_plot_point_size":1.6},
                    legend_handle_length=1,
                    scale_columns={"tubb_frac":100}
                  )
figure.get_basic_statistics(show_from_ungrouped_data=True,
                            n_columns=["date", "cell"])



figure.create_panel("C", increase_size_fac=7, hor_alignment="center",
                    padding=[None, None])
figure.show_data(col="time_speedup", y="tubb_frac", x="region",
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test=["stats.kruskal","posthocs.posthoc_dunn"],
                    col_order=["After initial speedup"],
                    x_labels=[("retrograde","Retro-\ngrade"),
                              ('anterograde','Antero-\ngrade'),
                              ('stationary','Stationary')], 
                    x_order=["Retro-\ngrade",'Antero-\ngrade','Stationary'],
                    col_labels=[("before", "After initial speedup")],
                    average_columns=["date", "cell"],
                    always_show_col_label=True,
                    y_range = [-2, 105],
                    y_ticks=[0,20,40,60,80,100],
                    y_axis_label="Fraction of\nmicrotubule mass [%]",
                   data_plot_kwds={"swarm_plot_point_size":1.6},
                    legend_handle_length=1,
                    scale_columns={"tubb_frac":100}
                  )
figure.get_basic_statistics(show_from_ungrouped_data=True,
                            n_columns=["date", "cell"])


figure.create_panel("D", increase_size_fac=1, hor_alignment="left", 
                    vert_alignment="center",
                    padding=[None, None])
figure.add_cropping(bottom=0.5, right=0.3, row=0)
figure.set_image_scaling(x_scale = 0.22, y_scale = 1.5)
additional_padding = {"images":1}
figure.show_images(additional_padding=additional_padding, 
                    use_same_LUTs=False, scale_images=False,
                    cmaps=["viridis"],
                    )

figure.add_y_axis(show_title_in_rows=[0],show_title_in_columns=[1],
                    axis_padding=1, site="right",
                    axis_title="Time [min]",
                    tick_values=[20,40, 60],
                    tick_length=3, tick_width=1,
                    tick_color="white")

figure.label_category(category="images", texts=["CAMSAP3", "Photoconverted tubulin"], 
                       site="top", label_orientation="hor")

figure.add_x_axis(show_title_in_rows=[0],show_title_in_columns=[0],
                    axis_padding=1,
                    axis_title="Soma distance [\u03BCm]",
                    tick_values=[0,10,20],
                    tick_length=3, tick_width=1,
                    tick_color="white")

figure.add_colorbars(site="left", only_show_in_rows = [0],
                     size=.04, font_size_factor=1)

figure.draw_line_on_images(position = 28, line_width=0.6,
                           only_show_in_rows=[0],
                            line_style=(0, (3,1)), color="white")

figure.save("png")