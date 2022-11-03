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

figure = Figure(input_folder,number="S13",dpi=600,width=4.75)


figure.create_panel("A", increase_size_fac=1, hor_alignment="center",
                    vert_alignment="center",
                    padding=[0.1,0.05])
figure.show_images()
figure.rescale_font_size()


figure.create_panel("B", increase_size_fac=6, hor_alignment="center",
                    padding=[None, None])
figure.show_data(x="condition", y="MT-RFmed", col="manipulation",
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test=["stats.kruskal","posthocs.posthoc_dunn"],
                  col_labels=[("before","Before"),('early','After')],
                  col_order=["Before","After"],
                  x_labels =[("wt", "Wildtype"), ("mut", "Motor-\ndeficient")],
                  average_columns=["date", "neuron"],
                    y_range = [-0.05, 5.1],
                  y_tick_interval=0.5,
                  y_axis_label="Microtubule retrograde flow\n[\u03BCm/min]",
                   data_plot_kwds={"swarm_plot_point_size":1.3},
                    legend_handle_length=1,
                    scale_columns={"MT-RFmed":-1}
                  )
figure.get_basic_statistics(show_from_ungrouped_data=True,
                            n_columns=["date", "neuron"])


figure.create_panel("C", increase_size_fac=1, hor_alignment="left", 
                    vert_alignment="top",
                    padding=[None, 0.07])
figure.add_cropping(bottom=0, right=0.4)#, row=0)
figure.add_rows_to_delete([39],images=[1])
figure.set_image_scaling(x_scale = 0.22, y_scale = 1/40)
additional_padding = {"images":4}
figure.show_images(
                    focus="images",
                    show_focus_in="columns",
                    additional_padding=additional_padding, 
                    use_same_LUTs=False, scale_images=False,
                    make_image_size_equal=["height", "bottom",65513]
                    )

figure.add_y_axis(show_title_in_rows=[0],show_title_in_columns=[1],
                  show_in_columns=[1],
                    axis_padding=1, site="right",
                    axis_title="Time [h]",
                    tick_values=[0.5, 1, 1.5, 2, 2.5],
                    tick_length=3, tick_width=1,
                    tick_color="white")

figure.add_y_axis(show_title_in_rows=[0],show_title_in_columns=[1],
                  show_in_columns=[0],
                    axis_padding=1, site="right",
                    tick_values=[0.5, 1, 1.5, 2, 2.5],
                    show_tick_labels = False,
                    tick_length=3, tick_width=1,
                    tick_color="white")

figure.label_category(category="images", texts=["Motor deficient", "Wildtype"], 
                       site="top", label_orientation="hor")

figure.add_x_axis(show_title_in_rows=[0],show_title_in_columns=[0],
                  show_in_columns=[1],
                    axis_padding=1,
                    axis_title="Soma distance [\u03BCm]",
                    tick_values=[0,10,20],
                    tick_length=3, tick_width=1,
                    tick_color="white")


figure.add_x_axis(show_title_in_rows=[0],show_title_in_columns=[0],
                  show_in_columns=[0],
                    axis_padding=1,
                    axis_title="Soma distance [\u03BCm]",
                    tick_values=[0,10,20],
                    tick_length=3, tick_width=1,
                    tick_color="black")

figure.draw_line_on_images(position = 65, line_width=1.2,
                           only_show_in_columns=[0],
                            line_style=(0, (3,1)), color="white")
figure.draw_line_on_images(position = 62, line_width=1.2,
                           only_show_in_columns=[1],
                            line_style=(0, (3,1)), color="white")


figure.save("png")