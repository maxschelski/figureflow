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

figure = Figure(input_folder, name="Movie", number=20, height=0.5, dpi=200, 
                width=2.3, video=True, font_size=7, dark_background=True)
o
figure.create_panel("A", height=0.5, increase_size_fac=1, 
                    hor_alignment="center", vert_alignment="center")
figure.add_cropping(left=0.10, top=0.20)

figure.show_images(frames=range(100),channels=[0,1],
                    cmaps="viridis",
                    additional_padding={"channels":4})

figure.add_scale_bar(um_per_px=0.22, lengths_um=[20])
figure.draw_marker(frames=range(16,100), position="top-right", radius=0.06,
                   only_show_in_columns=[0], only_show_in_rows=[0])

figure.label_channels(texts=["Not photoconverted", "Photoconverted"])

figure.add_colorbars(site="bottom",
                     only_show_in_columns=[0],
                     size=.04)

figure.annotate_channel_within_image(channel_names=["Tubulin"],
                                      position="bottom-right",
                                      only_show_in_columns=[0],
                                      channel_colors=["white"])

figure.add_timestamp(time_per_frame="90s", format="mm:ss", 
                     show_unit=True, start_time=-16, 
                     first_time_difference=1, only_show_in_rows = [0],
                     only_show_in_columns=[1])

figure.draw_on_image(targets=[(178,153)], direction="right", size=40)
figure.draw_on_image(targets=[(338,312)], direction="right", size=40)


title_page_txt = ("MT-RF and microtubule density\n"
                  "after actin depolymerization with LatB\n"
                  "and expressing and recruiting\n"
                  "dynein motor domain to the membrane\n\n"
                  "(FRB-C2-Cerulean3, \n"
                  "FKBP-Dync1h1motor, HaloTag-CAMSAP3\n"
                  "and Tubulin-mEos3.2 expressed)")

figure.save_video(fps=4,  repeats=3, 
                  title_page_text = title_page_txt,
                  frames_to_show_longer=[0],
                  seconds_to_show_frames=1,
                  duration_title_page=5
                  )