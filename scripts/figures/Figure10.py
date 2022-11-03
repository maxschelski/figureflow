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

figure = Figure(input_folder,number=10, dpi=600, width=5)


figure.create_panel("A", increase_size_fac=1, hor_alignment="center",
                    padding=[None, 0.13])
figure.show_images()
figure.rescale_font_size()


figure.create_panel("B", increase_size_fac=6, hor_alignment = "center",
                    padding=[None, None])
figure.show_data(x="condition", y="MT-RFmed", col=None, hue=None,
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test=["stats.kruskal","posthocs.posthoc_dunn"],
                    always_show_col_label=True,
                    x_labels=[("FRB","Speedup"),("Cer", "Control")], x_order=["Control", "Speedup"],
                    y_axis_label="Microtubule\nretrograde flow\n[\u03BCm/min]",
                    average_columns=["date", "neuron"],
                   data_plot_kwds={"swarm_plot_size":1.5},
                    y_range=[-0.05,5.2],
                    y_tick_interval=1,
                    x_tick_label_rotation=False,
                    scale_columns = {"MT-RFmed":-1},
                  )
figure.draw_line_on_images(position = 0, line_width=0.5, 
                            orientation="hor", color="black")
figure.get_basic_statistics(n_columns=["date", "neuron"])



figure.create_panel("C", increase_size_fac=6, hor_alignment = "center")
figure.show_data(x="condition", y="intensity_norm", col=None, hue=None,
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test=["stats.kruskal","posthocs.posthoc_dunn"],
                    always_show_col_label=True,
                    x_labels=[("FRB","Speedup"),("Cer", "Control")], x_order=["Control", "Speedup"],
                    y_axis_label="Immediate microtubule\ndensity decrease [%]",
                    average_columns=["date", "neuron"],
                    swarmplot_point_size=1.5, y_range=[-60,80],
                    y_tick_interval = 20,
                    x_tick_label_rotation=False,
                    scale_columns = {"intensity_norm":-100},
                  )
figure.draw_line_on_images(position = 0, line_width=0.5, 
                            orientation="hor", color="black")
figure.get_basic_statistics(n_columns=["date", "neuron"])



figure.create_panel("D", increase_size_fac=6, hor_alignment = "center",
                    padding=[None,None])
figure.show_data(x="condition", y="length", col=None, hue=None,
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test=["stats.kruskal","posthocs.posthoc_dunn"],
                    always_show_col_label=True,
                    x_labels=[("FRB","Speedup"),("Cer", "Control")], x_order=["Control", "Speedup"],
                    y_axis_label="Immediate\nneurite retraction [\u03BCm]",
                    average_columns=["date", "neuron"],
                    swarmplot_point_size=1.5,
                    y_tick_interval=5,
                    x_tick_label_rotation=False,
                    scale_columns = {"length":-0.22},
                  )
figure.draw_line_on_images(position = 0, line_width=0.5, 
                            orientation="hor", color="black")
figure.get_basic_statistics(n_columns=["date", "neuron"])


figure.create_panel("E", increase_size_fac=1, 
                    hor_alignment="center",
                    vert_alignment="center",
                    padding=[None, 0.0])
figure.add_cropping(left=0.2, right=0.15, bottom=0.19, top=0.14, column=[0])
figure.add_cropping(left=0.2, right=0.15, bottom=0.19, top=0.14, column=[1])
figure.show_images(frames=[0,29], images=[0,1], channels=[0],
                                      use_same_LUTs=False,
                                      cmaps=["","viridis"])
figure.label_images(texts=["Control","Speedup"])
figure.add_scale_bar(um_per_px=0.22, lengths_um=[20], position="bottom-left")
figure.annotate_channel_within_image(["","Tubulin"], only_show_in_rows=[0],
                                      only_show_in_columns=[0],
                                      position="top-right",
                                      channel_colors=["white","white"])

figure.label_frames(texts=["Before", "After"])

figure.add_colorbars(site="bottom",
                      only_show_in_columns=[0],
                      size=.06,
                      font_size_factor=1)

figure.draw_on_image(targets=[ (195,227) ], 
                      direction="top", 
                      images={"images":0}, size=50)
figure.draw_on_image(targets=[ (215,170) ], 
                      direction="top-right", 
                      images={"images":1}, size=50)



inclusion_criteria = []
inclusion_criteria.append({
                            "neuron" : [12],
                            "date" : [211001],
                            "neurite": [123],
                            "manipulation":["before", "after"],
                            "out_of_focus":[False],
                            "dead":[False],
                            "time":"<51"
                            })
inclusion_criteria.append({
                            "neuron" : [32],
                            "date" : [211001],
                            "neurite": [50],
                            "manipulation":["before", "after"],
                            "out_of_focus":[False],
                            "dead":[False],
                            "time":"<51"
                            })


figure.create_panel("F", increase_size_fac=1,padding=[0, [0.04,0]])
figure.show_data(y=["int_norm","length"], x="time", 
                  plot_type="line", 
                  hue="condition", 
                  y_axis_label=["\nMicrotubule\ndensity",
                                "\nLength\n[\u03BCm]"],
                  hue_labels = [("FRB", "Speedup"),
                                ("Cer", "Control")],
                  perform_stat_test=False,sub_padding_y_factor=0.4,
                  smoothing_rad = 2, show_row_label=False,
                  show_y_label_in_all_rows=True,
                  legend_handle_length = 0.7,
                    y_tick_interval= [0.3, 10],
                    y_range=[[0,1.2],[0,46]],
                  inclusion_criteria = inclusion_criteria,
                    x_axis_label = "Time [min]",
                    scale_columns={"time":1,"length":0.22},
                  plot_colors=sb.xkcd_palette(["grey","black"])
                  )
figure.draw_line_on_images(34.5, color="gray", orientation="vert",
                            line_style=(0, (5,2)))


figure.create_panel("G", increase_size_fac=1, hor_alignment="center",
                    vert_alignment="bottom",
                    padding=[0.02, None])
figure.show_images()
figure.rescale_font_size(linespacing=1)


figure.save("png")