# -*- coding: utf-8 -*-

from figureflow import figure
import seaborn as sb
from matplotlib import pyplot as plt
import importlib
import numpy as np
importlib.reload(figure)
import os

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

figure = Figure(input_folder, name="Movie",number=7, height=0.5, dpi=400, 
                width=2.2, video=True, font_size=6, dark_background=True)

figure.create_panel("B",height=0.5,increase_size_fac=1)
figure.show_images(frames=range(0,22),
                   order_of_categories=["channels","frames"])

figure.label_channels(texts=["Not photoconverted","Photoconverted"], site="top")
figure.add_timestamp(time_per_frame="30s", format="mm:ss", show_unit=True, 
                     start_time=-4, first_time_difference=5,
                     only_show_in_columns=[1])
figure.draw_on_image(targets=[ (92,153) ], direction="left")
figure.draw_on_image(targets=[ (176,208) ], direction="top-right")
figure.draw_marker(frames=range(1,21), position="top-left", radius=0.07,
                   only_show_in_columns=[1])

figure.add_scale_bar(um_per_px=0.22, lengths_um=20, row=0, column=0)


title_page_txt = ("MT-RF\n"
                  "in dendrites and the axon\n"
                  "of old neurons\n\n"
                  "(Tubulin-mEos3.2 expressed)")
figure.save_video(fps=5,  repeats=3,
                  title_page_text = title_page_txt,
                  frames_to_show_longer=[0],
                  seconds_to_show_frames=1.8
                  )