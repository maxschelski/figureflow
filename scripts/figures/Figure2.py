# -*- coding: utf-8 -*-

from figureflow.figure import Figure
import seaborn as sb
import os

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

figure = Figure(input_folder,number=2, dpi=600, width=5)

figure.create_panel("A",increase_size_fac=1, hor_alignment="left",
                    padding=[0.11, 0.05])
figure.add_cropping(left=0.2, bottom=0, right=0, top=0)
figure.show_images()
figure.add_border(left=True)
figure.rescale_font_size()


inclusion_criteria=[{"exclude":[False]}]
figure.create_panel("B", increase_size_fac=4, hor_alignment="center",
                    padding=[0.04,None])
figure.show_data(x="neurite", y="speed", col="stage", hue=None,
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test="Wilcoxon",
                  x_labels=[("short","Minor\nneurite"),('long','Axon')], x_order=["Minor\nneurite","Axon"],
                  col_labels=[("3.0","Stage 3")],col_order=["Stage 3"],
                  pair_unit_columns=["date", "experiment", "cell"],
                  y_range = [-0.3, 2], y_tick_interval=0.3,
                  y_axis_label="Microtubule retrograde\nflow [\u03BCm/min]",
                  inclusion_criteria = inclusion_criteria)
figure.draw_line_on_images(position = 0, line_width=0.5, 
                            orientation="hor", color="black")
figure.get_basic_statistics(show_from_ungrouped_data=True,
                            n_columns=["date", "experiment", "cell"])


figure.create_panel("C", increase_size_fac=2, padding=[None, [None,0]], hor_alignment="right")
figure.add_zoom(xy=(110,135), width=26, height=30, channels=[1], label_position_overview="right")
figure.add_zoom(xy=(154,198), width=26, height=30, channels=[1], label_position_overview="right")

size_factor_dict= {("zoom",0):2}
figure.add_cropping(left=0.0,right=0.1)
figure.show_images(frames=[0,2,11,21], order_of_categories=["zooms","frames"], 
                    show_focus_in="columns",
                    focus="frames",
                    enlarged_image_site="left",
                    channels_to_show_first_nonzoomed_timeframe=[0], 
                    position_zoom_nb="top-left")
figure.label_channels(texts=["Not\nphotoconverted", "Photoconverted tubulin"], site="top")
figure.label_frames(texts=["- 2:00 min", "0:30", "5:00", "10:00"], site="bottom")
figure.draw_on_image(targets=[ (111,135) ], direction="right", images={"zooms":1}, size=50)
figure.draw_on_image(targets=[ (153,196) ], direction="bottom-left", images={"zooms":2}, size=50)
figure.add_scale_bar(um_per_px=0.44, lengths_um=[5,20])
figure.annotate_channel_within_image(["Tubulin", "Tubulin"], 
                                      only_show_in_columns=[0],
                                      position="top-left")


figure.create_panel("D", increase_size_fac=1.7, vert_alignment= "center", 
                    padding=[None,0.08])
figure.show_images()
figure.rescale_font_size()

figure.create_panel("E", increase_size_fac=5,padding=[0.04,None])
figure.show_data(x="type", y="speed", col=None, hue=None,
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=True, test="Wilcoxon",
                  x_labels=[("neurite","Minor\nneurite"),('axon','Axon')], x_order=["Minor\nneurite","Axon"],
                   pair_unit_columns=["date", "cell"],
                  y_tick_interval=0.3,
                  y_axis_label="Microtubule retrograde\nflow [\u03BCm/min]")
figure.get_representative_data(unit_columns=["date", "cell"])
figure.draw_line_on_images(position = 0, line_width=0.5, 
                            orientation="hor", color="black")
figure.get_basic_statistics(show_from_ungrouped_data=True,
                            n_columns=["date", "cell"])


figure.create_panel("F", increase_size_fac=2, vert_alignment="center")
figure.add_zoom(xy=(208,133), width=40, height=60, channels=[1], label_position_overview="right")
figure.add_zoom(xy=(93,252), width=40, height=60, channels=[1], label_position_overview="right")
figure.add_cropping(left=0.02, bottom=0, right=0, top=0)
figure.add_cropping(left=0,right=0.13, bottom=0.35, top=0.05)
figure.show_images(frames=[0,1,3,4,6], channels=[0,1],
                    order_of_categories=["zooms","channels","frames"], 
                    channels_to_show_first_nonzoomed_timeframe=[0], 
                    position_zoom_nb="top-left", 
                    focus="frames",
                    show_focus_in="columns")
figure.label_channels(texts=["Not\nphotoconverted", "Photoconverted tubulin"], 
                      site="top")
figure.annotate_channel_within_image(["Tubulin", "Tubulin"], 
                                      only_show_in_columns=[0],
                                      position="top-left")
figure.label_frames(texts=["- 2:00 min", "0:30", "6:30", "9:30", "15:30"], site="bottom")
figure.draw_on_image(targets=[ (206,130) ], direction="top-left", images={"zooms":1}, size=40)
figure.draw_on_image(targets=[ (89,260) ], direction="right", images={"zooms":2}, size=40)
figure.add_scale_bar(um_per_px=0.22, lengths_um=[5,20])


figure.save("png")
