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

figure = Figure(input_folder, name="Movie", number=11, height=0.7, dpi=200, 
                width=4, video=True, font_size=7, dark_background=True)

figure.create_panel("C", height=0.7, increase_size_fac=1, hor_alignment="center", vert_alignment="center")
figure.add_cropping(top=0.1, bottom=0.1, left=0.05, right=0.1)
figure.show_images(frames=range(21),images=[0,1,2], 
                   channels=[0,1],focus="images",
                   show_focus_in="columns",
                    order_of_categories=["images","channels"], 
                    additional_padding = None, 
                    show_non_zoom_channels=True, show_zoom_number_in_image=False,
                    use_same_LUTs = False)

figure.label_category(category="images", texts=["Control", "pa-Blebb", "Taxol"], 
                      label_orientation="hor", font_size="large", site="top")
figure.label_channels(texts=["Not\nphotoconverted", "Photoconverted"], site="left", 
                      label_orientation="vert", line_color="white")
figure.add_scale_bar(um_per_px=0.44, lengths_um=[20])
figure.draw_marker(frames=range(1,21), position="top-left", radius=0.12,
                   only_show_in_columns=[1], only_show_in_rows=[0])

figure.draw_on_image(targets=[(80,107)], direction="bottom-left", images={"images":0}, size=60)
figure.draw_on_image(targets=[(119,158)], direction="right", images={"images":0}, size=60)

figure.draw_on_image(targets=[(138,95)], direction="right", images={"images":1}, size=60)
figure.draw_on_image(targets=[(175,161)], direction="bottom-left", images={"images":1}, size=60)

figure.draw_on_image(targets=[(166,89)], direction="bottom-right", images={"images":2}, size=60)
figure.draw_on_image(targets=[(181,140)], direction="bottom", images={"images":2}, size=60)


figure.add_timestamp(time_per_frame="30s", format="mm:ss", 
                     show_unit=True, start_time=-4, 
                     first_time_difference=5, only_show_in_rows = [0],
                     only_show_in_columns=[1])

title_page_txt = ("Influence of pa-Blebb and taxol treatment\n"
                  "on MT-RF\n\n"
                  "(Tubulin-mEos3.2 expressed)")

figure.save_video(fps=5,  repeats=4, 
                  title_page_text = title_page_txt,
                  frames_to_show_longer=[0,20],
                  seconds_to_show_frames=1
                  )