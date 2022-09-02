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
script_figure_folder = os.path.dirname(os.path.abspath(__file__))
scripts_folder = os.path.dirname(script_figure_folder)
figure_folder_name = os.path.basename(script_figure_folder )
data_folder = os.path.join(os.path.dirname(scripts_folder), "data")
input_folder = os.path.join(data_folder,figure_folder_name)

figure = Figure(input_folder, name="Movie", number=1, height=0.5, dpi=200, 
                width=2.2, video=True, font_size=6, dark_background=True)

figure.create_panel("C", height=0.5, increase_size_fac=1,
                    hor_alignment="center", vert_alignment="center")

figure.add_cropping(left=0.28, bottom=0.3, right=0.15, top=0.25)

figure.show_images(frames=range(0,21), order_of_categories=["channels",
                                                            "frames"],
                    )

figure.label_channels(texts=["Not photoconverted","Photoconverted"], site="top")

figure.add_timestamp(time_per_frame="30s", format="mm:ss", show_unit=True, start_time=-4, 
                     first_time_difference=5, only_show_in_columns=[1])

figure.draw_on_image(targets=[ (144, 98) ], direction="left", size=40)
figure.draw_on_image(targets=[ (181, 110) ], direction="top-left", size=40)

figure.add_scale_bar(um_per_px=0.44, lengths_um=20, line_width=2, padding=0.04)

figure.draw_marker(frames=range(1,21), position="top-left", radius=0.07,
                   only_show_in_columns=[1])

title_page_txt = ("Behavior of photoconverted microtubule patches\n"
                  "before axon formation\n\n"
                  "(Tubulin-mEos3.2 expressed)")

figure.save_video(fps=5, title_page_text = title_page_txt,
                  repeats=3, frames_to_show_longer=[0,20],
                  seconds_to_show_frames=1)