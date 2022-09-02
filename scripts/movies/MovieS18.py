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

figure = Figure(input_folder, name="Movie", number=18, height=1, dpi=200, 
                width=2.3, video=True, font_size=7, dark_background=True)

figure.create_panel("G", height=0.5, increase_size_fac=1, hor_alignment="center", vert_alignment="center")
figure.add_cropping(top=0.15, bottom=0.15, left = 0.2, right=0.15)

figure.show_images(frames=range(35),channels=[0],
                    additional_padding = {"images":4},
                   use_same_LUTs=False)
figure.add_scale_bar(um_per_px=0.22, lengths_um=[20])
figure.draw_marker(frames=range(23,35), position="top-left", radius=0.06,
                   only_show_in_columns=[1], only_show_in_rows=[0])

figure.label_images(texts=["Control", "Speedup"], site="top")

figure.annotate_channel_within_image(["CAMSAP3", "Tubulin"], 
                                     only_show_in_columns=[0],
                                      position="top-right",
                                      channel_colors=["white",
                                                      "white"])

figure.add_timestamp(time_per_frame="90s", format="mm:ss", 
                     show_unit=True, start_time=-23,
                     first_time_difference=0, only_show_in_rows = [0],
                     only_show_in_columns=[1])


figure.create_panel("H", y = 0.5, height=0.5, increase_size_fac=1, 
                    hor_alignment="center", vert_alignment="center")
figure.add_cropping(top=0.15, bottom=0.15, left = 0.13, right=0.15)

figure.show_images(frames=range(35),channels=[1],
                    additional_padding = {"images":4},
                   use_same_LUTs=False, cmaps="viridis")
figure.add_colorbars(site="bottom",
                    size=0.03, only_show_in_columns=[0],
                    label_padding=0.3, tick_distance_from_edge=0.1)


figure.draw_on_image(targets=[(166,138)], direction="bottom-left", 
                     images={"frames":list(range(23,35)),
                             "images":1},size=30)

figure.add_text_within_at_coords("Neurite \nretracted", 74 , 215,
                                 line_spacing=0.9,
                                 font_size=6, hor_align="left",
                     images={"frames":list(range(23,35)),
                             "images":1})

figure.draw_on_image(targets=[(330,353)], direction="bottom-left", 
                     images={"frames":list(range(23,35)),
                             "images":1},size=30)

figure.add_text_within_at_coords("Neurite \nretracted", 240, 430,
                                 line_spacing=0.9,
                                 font_size=6, hor_align="left",
                     images={"frames":list(range(23,35)),
                             "images":1})

figure.annotate_channel_within_image(["CAMSAP3","Tubulin"], 
                                     only_show_in_columns=[0],
                                      position="top-right",
                                      channel_colors=["white",
                                                      "white"])

figure.label_images(texts=["", ""], site="bottom")
figure.add_scale_bar(um_per_px=0.22, lengths_um=[20])

title_page_txt = ("Microtubule density and neurite length\n"
                  "after expressing and recruiting\n"
                  "dynein motor domain to the membrane\n\n"
                  "(FRB-C2-Cerulean3 (Speedup) or \n"
                  "C2-Cerulean (Control),\n"
                  "FKBP-Halo-Dync1h1motor,\n"
                  " mNeonGreen-CAMSAP3 \n"
                  "and Tubulin-mScarlet expressed)")

figure.save_video(fps=10,  repeats=3, 
                  title_page_text = title_page_txt,
                  frames_to_show_longer=[0],
                  seconds_to_show_frames=0.01,
                  duration_title_page=5
                  )