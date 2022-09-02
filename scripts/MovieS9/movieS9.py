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

figure = Figure(input_folder, name="Movie", number=9, height=0.45, dpi=200, 
                width=2.2, video=True, font_size=6, dark_background=True)

figure.create_panel("B",x=0, height=0.45, y=0, width=0.33, increase_size_fac=1)
figure.add_cropping(left=0.05, right=0.15, top=0.1, bottom=0.2)

figure.show_images()
figure.label_channels(texts=["caKIF5C"], site="bottom")
figure.label_channels(texts=[" \n"], site="top")

figure.add_scale_bar(um_per_px=0.44, lengths_um=20)

figure.draw_on_image(targets=[(60,149 )], direction="top-left", size=30)

figure.create_panel("C",x=0.33, height=0.45, y=0, width=0.67, increase_size_fac=1)
figure.add_cropping(left=0.05, right=0.15, top=0.1, bottom=0.2)

figure.show_images(frames=range(0,21), channels=[0,1],
                    position_zoom_nb="bottom-right")
figure.label_channels(texts=["Not\nphotoconverted","Photoconverted"], site="top")
figure.add_timestamp(time_per_frame="30s", format="mm:ss", show_unit=True, start_time=1,
                     only_show_in_columns=[1])
figure.label_images(["Tubulin"], site="bottom", line_color="white")
figure.draw_on_image(targets=[(60,149 )], direction="top-left", size=30)
figure.draw_on_image(targets=[(167,84)], direction="top-left", size=30)


title_page_txt = ("MT-RF before axon formation\n"
                  "in neurites\n"
                  "with and without caKIF5C accumulation\n\n"
                  "(Tubulin-mEos3.2 and\n"
                  "caKIF5C-Cerulean3 expressed)")
figure.save_video(fps=5, repeats=3, 
                  title_page_text = title_page_txt,
                  frames_to_show_longer=[0, 20],
                  seconds_to_show_frames=1
                  )