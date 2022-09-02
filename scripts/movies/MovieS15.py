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

figure = Figure(input_folder, name="Movie", number=15, height=1, dpi=200, 
                width=2.3, video=True, font_size=7, dark_background=True)

figure.create_panel("A", height=1, increase_size_fac=1, hor_alignment="center", vert_alignment="center")
figure.add_cropping(left=0.15, bottom=0, right=0.3, top=0)

figure.show_images(frames=range(1,65),channels=[0,1],
                   show_focus_in="columns",
                   focus="channels",
                    additional_padding = None,
                   cmaps=["viridis", "gray"])

figure.add_scale_bar(um_per_px=0.22, lengths_um=[20])
figure.draw_marker(frames=range(24,65), position="top-left", radius=0.06,
                   only_show_in_columns=[1], only_show_in_rows=[0])
figure.label_channels(texts=["Not photoconverted", "Photoconverted"])

figure.annotate_channel_within_image(channel_names=["Tubulin",""],
                                      only_show_in_columns=[0],
                                      channel_colors=["white", "white"])

figure.add_timestamp(time_per_frame="90s", format="mm:ss", 
                     show_unit=True, start_time=-26, 
                     first_time_difference=1, only_show_in_rows = [0],
                     only_show_in_columns=[1])
figure.draw_marker(frames=range(26,65), position="top-left", radius=0.06,
                   only_show_in_columns=[1], only_show_in_rows=[0])

figure.add_colorbars(site="bottom",
                     only_show_in_columns=[0],
                     size=0.02)

figure.draw_on_image(targets=[ (202, 209 ) ], direction="right", size=40)
figure.add_text_within_at_coords("Axon", 232, 209,
                                 line_spacing=0.9,
                                 vert_align="center",
                                 font_size=7, hor_align="left",
                                 images={"channels":[0]})#,
figure.draw_on_image(targets=[ (163, 402) ], direction="top-left", size=40)
figure.add_text_within_at_coords("Dendrite", 77,383,
                                 hor_align="left",
                                 line_spacing=0.9,
                                 font_size=7,
                                 images={"channels":[0]})
figure.draw_on_image(targets=[ (284, 432 ) ], direction="top-right", size=40)
figure.add_text_within_at_coords("Dendrite", 252, 414,
                                 hor_align="left",
                                 line_spacing=0.9,
                                 font_size=7,
                                 images={"channels":[0]})

title_page_txt = ("MT-RF and microtubule density\n"
                  "after expressing and recruiting\n"
                  "dynein motor domain to the membrane\n"
                  "in an old neuron\n\n"
                  "(FRB-C2-Cerulean3,\n"
                  "FKBP-Dync1h1motor, HaloTag-CAMSAP3 \n"
                  "and Tubulin-mEos3.2 expressed)")

figure.save_video(fps=10,  repeats=3, 
                  title_page_text = title_page_txt,
                  frames_to_show_longer=[0],
                  seconds_to_show_frames=1,
                  duration_title_page=5
                  )