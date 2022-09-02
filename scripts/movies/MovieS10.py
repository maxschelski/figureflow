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

figure = Figure(input_folder, name="Movie", number=10, height=0.4, dpi=200, 
                width=4, video=True, font_size=6, dark_background=True)

figure.create_panel("G", increase_size_fac=1, animate_panel=True,
                vert_alignment="top")
figure.add_cropping(bottom=0.13, left=0.15, right=0.15)
figure.show_images(frames=range(90),
                   order_of_categories=["channels","frames"],
                    channels=[0],
                    cmaps="viridis")
figure.add_colorbars(site="bottom", size=0.08, label_padding=0.3,
                     tick_distance_from_edge=0.1,
                     tick_labels=["Low", "High"])
figure.label_channels(texts=["Tubulin"], site="top")
figure.add_timestamp(time_per_frame="60s", format="hh:mm", show_unit=True, 
                     position="bottom-right")

figure.add_scale_bar(um_per_px=0.22, lengths_um=20, line_width=2)


figure.add_text_within_at_coords("Axon has\nformed", 270, 80,
                                 line_spacing=0.9,
                                 font_size=6, hor_align="right",
                     images={"frames":list(range(765,1329))})

figure.draw_on_image(targets=[ (320,130) ], direction="bottom-right", 
                     size=30)
figure.write_on_image("Axon",[325, 191])

figure.draw_on_image(targets=[ (292,229) ], direction="bottom-right", 
                     size=30)
figure.write_on_image("Neurite\n1",[321, 294])


inclusion_criteria = []
inclusion_criteria.append({
                            "neuron" : [9],
                            "date" : [200529],
                            "neurite": [0, 1]
                            })
figure.create_panel("H",increase_size_fac=1,
                    animate_panel = True, padding=[None, None])

figure.show_data(y="int_norm", x="time", 
                  plot_type="line",
                  row="neurite", 
                  hue="neurite", y_axis_label="Tubulin\nintensity",
                    row_labels = [("0", "Axon"), ("1", "Neurite 1")],
                  perform_stat_test=False,
                    show_legend=False,
                    borderaxespad_ =0.1,
                  smoothing_rad = 2, show_row_label=True,
                  row_label_orientation="vert",
                  y_tick_interval=0.3,
                  x_tick_interval=2,
                    x_range = [0.0001,3],
                    y_range=[0.00001,1.5],
                  inclusion_criteria = inclusion_criteria,
                    x_axis_label = "Time [h]",
                    scale_columns={"time":1/60},
                    plot_colors=sb.xkcd_palette(["white","grey"])
                  )
figure.draw_line_on_images(765/60, color="gray", orientation="vert",
                            line_style=(0, (5,2)), line_width=1)

title_page_txt = ("Microtubule\n"
                  "density cycles\n"
                  "from before to\n"
                  "after axon formation\n\n"
                  "(Tubulin-mScarlet\nexpressed)")

figure.save_video(fps=60,  repeats=3, bitrate=300000,#fps=60
                  title_page_text = title_page_txt,
                  frames_to_show_longer=[0],
                  seconds_to_show_frames=0
                  )