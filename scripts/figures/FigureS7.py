# -*- coding: utf-8 -*-

from figureflow import figure
import seaborn as sb

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

figure = Figure(input_folder,number="S7", dpi=600, width=2.2)

figure.create_panel("A", increase_size_fac=4.5)
renaming_dicts = [{}]
renaming_dicts[-1]["__from__"] = "Minor\nneurite"
renaming_dicts[-1]["__to__"] = "Dendrite\n"
renaming_dicts[-1]["__target-column__"] = "neurite"
renaming_dicts[-1]["stage"] = ["With axon\nwith dendrites"]
figure.show_data_columns()
figure.show_data(x="neurite", y="speed", col="stage",hue=None,
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test="Dunn",
                    col_labels=[("3","With axon\nno dendrites"),("4", "With axon\nwith dendrites")],
                    col_order=["With axon\nno dendrites","With axon\nwith dendrites"],
                  x_labels=[("short","Minor\nneurite"),('long','Axon')], x_order=["Minor\nneurite","Dendrite\n","Axon"],
                  y_axis_label="Microtubule retrograde flow\n[\u03BCm/min]",
                  y_range=[-0.3, 2], y_tick_interval=0.3,line_height=0.13,
                  swarmplot_point_size=2,
                  renaming_dicts = renaming_dicts)
figure.draw_line_on_images(position = 0, line_width=0.5, 
                            orientation="hor", color="black")
figure.get_basic_statistics(show_from_ungrouped_data=True,
                            n_columns=["date", "experiment", "cell"])



figure.create_panel("B", increase_size_fac=2)
figure.add_zoom(xy=(93,154), width=26, height=34, channels=[1], label_position_overview="right")
figure.add_zoom(xy=(173,209), width=26, height=34, channels=[1], label_position_overview="right")
figure.show_images(frames=[0,1,10,20], order_of_categories=["zooms","channels","frames"], 
                    focus="frames",
                    show_focus_in="columns",
                    channels_to_show_first_nonzoomed_timeframe=[0],
                    position_zoom_nb="top-left", 
                    )
figure.label_channels(texts=["Not\nphotoconverted", "Photoconverted tubulin"], site="top")
figure.label_frames(texts=["- 2:00 min", "0:30", "5:00", "10:00"], site="bottom")
figure.draw_on_image(targets=[ (92,153) ], direction="left", images={"zooms":1})
figure.draw_on_image(targets=[ (176,208) ], direction="top-right", images={"zooms":2})
figure.add_scale_bar(um_per_px=0.44, lengths_um=[5,20])
figure.annotate_channel_within_image(["Tubulin", "Tubulin"], 
                                      only_show_in_columns=[0],
                                      position="top-right")

figure.save("png")