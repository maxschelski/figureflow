# -*- coding: utf-8 -*-

from figureflow import figure
import seaborn as sb
from matplotlib import pyplot as plt
import importlib
import numpy as np
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

figure = Figure(input_folder, name="Movie", number=12, height=0.6, dpi=200, 
                width=3, video=True, font_size=6, dark_background=True)

figure.create_panel("G", height=0.34, increase_size_fac=1,
                    hor_alignment="right")
figure.add_cropping(top=0, bottom=0.05, left=0.15, right=0.05, column=0)
figure.add_cropping(top=0, bottom=0.05, left=0.05, right=0.15, column=1)
figure.add_cropping(top=0, bottom=0.05, left=0.1, right=0.1, column=2)
figure.show_images(frames=range(81),
                    cmaps="viridis",use_same_LUTs=False)
figure.add_colorbars(site="right", size=0.04, label_padding=0.2,
                     tick_distance_from_edge=0.1,
                     tick_labels=["Low", "High"],
                     font_size_factor = 1)
figure.label_images(texts=["Control", "Pa-Blebb", "Taxol"])
figure.annotate_channel_within_image(["Tubulin"], position="bottom-left", 
                                     only_show_in_columns=[0],
                                     channel_colors=["white"])
figure.add_scale_bar(um_per_px=0.22, lengths_um=20, position="bottom-right")
figure.add_timestamp(time_per_frame="3m",start_time=0, format="hh:mm", 
                      show_unit=True, position="top-left",
                      only_show_in_columns=[0])

figure.draw_on_image(targets=[[374, 240]], direction="top", size=50, images={"images":0})
figure.draw_on_image(targets=[[180, 136]], direction="right", size=50, images={"images":1})
figure.draw_on_image(targets=[[219, 126]], direction="right", size=50, images={"images":2})


inclusion_criteria = []
inclusion_criteria.append({
                            "neuron" : ["cell0046"],
                            "date" : ["190430"],
                            "channel": [0],
                            "origin":[3.0]
                            })
inclusion_criteria.append({
                            "neuron" : ["cell0084"],
                            "date" : ["190430"],
                            "channel": [0],
                            "origin":[1.0]
                            })
inclusion_criteria.append({
                            "neuron" : ["cell0007"],
                            "date" : ["190430"],
                            "channel": [0],
                            "origin":[1.0]
                            })

figure.create_panel("H", y=0.34, height=0.26, increase_size_fac=1,
                    padding=[[0.12,0.35], None])

figure.show_data(y="int_norm", x="frame", col="treatment",
                  plot_type="line",
                  hue="origin", y_axis_label="Tubulin intensity",
                    col_labels= [("dmso", "Control"),
                                ("pablebb", "Pa-Blebb"),
                                ("taxol", "Taxol")],
                  perform_stat_test=False,
                  row_label_orientation = "hor", 
                  show_col_labels_above = False,
                  show_legend=False, smoothing_rad = 2, 
                  auto_scale_group_padding=False,
                  group_padding=0.02,
                  sub_padding_y_factor = 1,
                  add_background_lines = False,
                   x_range = [0.01,3.99],
                  y_range= [0.55, 1.6], 
                   x_tick_interval=1, 
                  y_tick_interval=0.3,                 
                  show_x_label_in_all_columns=False,
                  inclusion_criteria = inclusion_criteria,
                    x_axis_label = "Time [h]", 
                    show_y_minor_ticks=False,
                  plot_colors=sb.xkcd_palette(["white","grey"]),
                    scale_columns={"frame":1/20}
                  )

title_page_txt = ("Influence of pa-Blebb and taxol treatment\n"
                  "on microtubule density cycles\n\n"
                  "(Tubulin-mNeonGreen expressed)")


figure.save_video(fps=10,  repeats=3, 
                  title_page_text = title_page_txt,
                  bitrate=300000,
                  duration_title_page=3,
                  frames_to_show_longer=[0],
                  seconds_to_show_frames=0.5
                  )