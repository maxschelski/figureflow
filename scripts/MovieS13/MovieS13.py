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

figure = Figure(input_folder, name="Movie", number=13, height=1.5, dpi=200, 
                width=2.3, video=True, font_size=7, dark_background=True)

figure.create_panel("C", height=1.5, increase_size_fac=1, hor_alignment="center", vert_alignment="center")
figure.add_cropping(top=0.1, bottom=0.1, left=0.05, right=0.1)
figure.show_images(frames=range(21),images=[[0,1],[2,3]],
                   channels=[0,1],focus="channels",
                   show_focus_in="columns",
                    order_of_categories=["channels","images_sub", "images"], 
                    show_non_zoom_channels=True, show_zoom_number_in_image=False,
                    use_same_LUTs = False)

figure.label_category(category="images", texts=["Control", "Ciliobrevin", "Control", "IC2N"], 
                      label_orientation="hor", site="left")
figure.label_category(category="images_sub", texts=["Acute inhibition", "Chronic inhibition"], 
                      label_orientation="vert", site="right", line_color="white")
figure.label_channels(texts=["Not\nphotoconverted", "Photoconverted"], site="top", 
                      label_orientation="hor", line_color="white")
figure.add_scale_bar(um_per_px=0.44, lengths_um=[20])
figure.draw_marker(frames=range(1,21), position="top-left", radius=0.1,
                    only_show_in_columns=[1], only_show_in_rows=[2])

figure.draw_on_image(targets=[(182,90)], direction="bottom-right", images={"images":0}, size=35)
figure.draw_on_image(targets=[(104,151)], direction="bottom-right", images={"images":0}, size=35)

figure.draw_on_image(targets=[(135,73 )], direction="right", images={"images":1}, size=35)
figure.draw_on_image(targets=[(140,175)], direction="right", images={"images":1}, size=35)

figure.draw_on_image(targets=[(159,106 )], direction="left", images={"images":2}, size=35)
figure.draw_on_image(targets=[(136,180)], direction="bottom-right", images={"images":2}, size=35)

figure.draw_on_image(targets=[(115,106)], direction="bottom-left", images={"images":3}, size=35)
figure.draw_on_image(targets=[(135,165)], direction="bottom-right", images={"images":3}, size=35)

figure.add_timestamp(time_per_frame="30s", format="mm:ss", 
                     show_unit=True, start_time=-4, 
                     first_time_difference=5, only_show_in_rows = [2],
                     only_show_in_columns=[1])

title_page_txt = ("Influence of Dynein inhibition\n"
                  "on MT-RF\n\n"
                  "(Tubulin-mEos3.2 and \n"
                  " for 'IC2N' also\n"
                  "IC2N-dCer (IC2N) expressed)")

figure.save_video(fps=5,  repeats=4, 
                  title_page_text = title_page_txt,
                   frames_to_show_longer=[0],
                   seconds_to_show_frames=1
                  )