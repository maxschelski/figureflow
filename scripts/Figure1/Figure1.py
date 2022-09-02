# -*- coding: utf-8 -*-

from figureflow.figure import Figure
import seaborn as sb

# get the path to the data of the respective figure or movie
# the data is in the data folder in a folder with the same
# name as the folder that the script is in
# the input_folder can also just be the folder in which the script is
# in which case you would just need the following:
# input_folder = os.path.dirname(os.path.abspath(__file__))
script_figure_folder = os.path.dirname(os.path.abspath(__file__))
scripts_folder = os.path.dirname(script_figure_folder)
figure_folder_name = os.path.basename(script_figure_folder )
data_folder = os.path.join(os.path.dirname(scripts_folder), "data")
input_folder = os.path.join(data_folder,figure_folder_name)

figure = Figure(input_folder,number=1, dpi=600, width=5)

figure.create_panel("A", padding=[0.11,0.05], hor_alignment="left")
figure.add_cropping(left=0.3)
figure.show_images()
figure.add_border(left=True)
figure.rescale_font_size()

figure.create_panel("B", increase_size_fac=3.4, hor_alignment = "left")
inclusion_criteria = [{"exclude":[False], "speed": "< 3"}]
figure.show_data(x="neurite", y="speed", col="stage", hue=None,
                  plot_colors=sb.xkcd_palette(["white","white","white"]),
                    perform_stat_test=False, test="Dunn",
                  x_labels=[("short","Minor\nneurite")], x_order=["Minor\nneurite"],
                  col_labels=[("2.0","Stage 2")],col_order=["Stage 2"],
                  y_axis_label="Microtubule\nretrograde flow [\u03BCm/min]",
                  swarmplot_point_size=1.8, y_range=[-0.5,2],
                  y_tick_interval=0.3,
                  inclusion_criteria= inclusion_criteria)
figure.draw_line_on_images(position = 0, line_width=0.5, 
                            orientation="hor", color="black")
figure.get_basic_statistics(n_columns=["date", "experiment", "cell"])


figure.create_panel("C", increase_size_fac=1,vert_alignment="top", 
                    hor_alignment="right")
figure.add_cropping(left=0.17, bottom=0.25, right=0.08, top=0.2)
figure.add_zoom(xy=(144, 98), width=32, height=30, channels=[1], label_position_overview="top")
figure.add_zoom(xy=(181, 110), width=32, height=30, channels=[1], label_position_overview="top")
figure.show_images(frames=[0,2,11,21], 
                    channels=[0, 1],
                    channels_to_show_first_nonzoomed_timeframe=[0],
                    auto_enlarge=True,
                      position_zoom_nb="top-left",
                      overlay_cmaps=["Reds", "Blues"])
figure.label_channels(texts=["Not photoconverted","Photoconverted tubulin"], 
                      site="top", label_overlays=False)
figure.annotate_channel_within_image(["Tubulin", "P"], 
                                      only_show_in_columns=[0],
                                      position="top-left",
                                      color="black")#
figure.label_frames(texts=["- 2:00 min", "0:30", "5:00", "10:00"], site="bottom")
figure.draw_on_image(targets=[ (144, 98) ], direction="left", size=50, images={"zooms":1})
figure.draw_on_image(targets=[ (181, 110) ], direction="top-left", size=50, images={"zooms":2})
figure.add_scale_bar(um_per_px=0.44, lengths_um=[5,20])


figure.create_panel("D", padding=[0.11,0.05], hor_alignment="left")
figure.add_cropping(left=0.3)
figure.show_images()
figure.add_border(left=True)
figure.rescale_font_size()


figure.create_panel("E", increase_size_fac=3.4, hor_alignment = "left")
figure.show_data(x="analysis", y="rel distance [%]", 
                  y_axis_label="Difference in\ntraveled distance [%]",
                  y_tick_interval=40,
                neg_y_vals=False, scale_columns={"rel distance [%]": 100})
figure.get_basic_statistics()

figure.get_representative_data(unit_columns=["date", "cell"])

figure.create_panel("F", increase_size_fac=1.2, hor_alignment="right")
figure.add_cropping(left=0.2, right=0.2, top=0.17, bottom=0.23)
figure.add_zoom(xy=(287, 198), width=80, height=80, channels=[2], frames=[2,4,7])
repositioning_map = {}
repositioning_map[("channels",0,"zooms",0)] = ("zooms",1)
figure.show_images(frames=[0,2,4,7], channels=[1,2], 
                    channels_to_show_first_nonzoomed_timeframe=[1],
                    repositioning_map=repositioning_map, position_zoom_nb="top-left")
figure.label_frames(texts=["- 0:30 min", "0:30", "2:30", "5:30"], site="bottom")
figure.label_category(category="channels",
                      texts=["Before\nphotoactivation","Photoactivated tubulin"], 
                      site="top")
figure.add_scale_bar(um_per_px=0.22, lengths_um=[20,5])
figure.draw_on_image(targets=[ [280,207], [301,177]], 
                      direction="bottom-right", size=50, images={"zooms":1})
figure.annotate_channel_within_image(["Tubulin", "Tubulin"], 
                                      only_show_in_columns=[0],
                                      position="top-left")

figure.save("png")
