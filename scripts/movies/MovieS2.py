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

figure = Figure(input_folder, name="Movie", number=2, height=0.5,dpi=200, 
                width=2.2, video=True, font_size=6, dark_background=True)

figure.create_panel("E",width=0.5, height=0.5, increase_size_fac=1)
figure.add_cropping(left=0.3, right=0.20, top=0.3, bottom=0.2)

figure.show_images()
figure.add_timestamp(time_per_frame="30s", format="mm:ss", show_unit=True, start_time=-4, first_time_difference=4)
figure.label_channels(texts=["Before photoactivation"], site="top")
figure.add_scale_bar(um_per_px=0.44, lengths_um=20)
figure.draw_on_image(targets=[ [232,305], [211,335]], direction="top-left", size=40)


figure.create_panel("F",x=0.5, width=0.5, height=0.5, increase_size_fac=1)
figure.add_cropping(left=0.3, right=0.20, top=0.3, bottom=0.2)

figure.show_images(frames=range(2,10), order_of_categories=["channels","frames"], channels=[2],
                    position_zoom_nb="bottom-right")
figure.draw_on_image(targets=[ [232,305], [211,335]], direction="top-left", size=40)
figure.label_channels(texts=["After photoactivation"], site="top")
figure.add_timestamp(time_per_frame="30s", format="mm:ss", show_unit=True, start_time=-4, first_time_difference=4)


title_page_txt = ("Behavior of\n"
                  "two photoactivated microtubule patches\n"
                  "in one neurite\n\n"
                  "(Tubulin-Dronpa expressed)")
figure.save_video(fps=5,  repeats=3, 
                  title_page_text = title_page_txt,
                  frames_to_show_longer=[0],
                  seconds_to_show_frames=1)