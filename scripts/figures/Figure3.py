# -*- coding: utf-8 -*-

from figureflow.figure import Figure
import seaborn as sb
import os

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

figure = Figure(input_folder,number=3, dpi=600, width=5)


figure.create_panel("A", increase_size_fac=1, hor_alignment="center",
                    padding=[None, 0.01])
figure.show_images()
figure.rescale_font_size(linespacing=1)


figure.create_panel("B", increase_size_fac=1, hor_alignment="right")
figure.show_data(x="group",y="fraction",hue="group_hue",
                  plot_colors=sb.xkcd_palette(["silver","white","grey"]),
                perform_stat_test=False, plot_type="bar", 
                y_axis_label="Neurons showing\nslower MT-RF over time [%]",
                x_labels=[("both","In all\nneurites"),
                          ("none","In no\nneurite"),
                          ("axon","In the\naxon")],
                hue_labels=[("both","In all\nneurites"),
                            ("none","In no\nneurite"),
                            ("axon","In the\naxon")],
                hue_order=["In the\naxon","In all\nneurites",
                            "In no\nneurite"],
                x_order=["In the\naxon","In all\nneurites",
                          "In no\nneurite"],
                show_data_points=False,
                show_x_axis=False)

                
figure.create_panel("C", increase_size_fac=6, hor_alignment="center")
inclusion_criteria = []
inclusion_criteria.append({})
inclusion_criteria[-1]["min_diff"] = [0.2]
inclusion_criteria[-1]["nb_neurites_slower"] = [0]
inclusion_criteria[-1]["MTRF_column"] = ["MT-RF_neg_smooth_200"]
# time_slowdown_diff is in hours - 9999 was used as value indicating
# that MT-RF did not slow down compared to all other other neurites
inclusion_criteria[-1]["time_slowdown_diff"] = "<1000"
figure.show_data(x="nb_neurites_slower", y="time_slowdown_diff", 
                  y_axis_label="Time of MT-RF slowdown\nafter initial axon growth [h]", 
                  inclusion_criteria=inclusion_criteria,
                   data_plot_kwds={"swarm_plot_size":3.5},)
figure.draw_line_on_images(position = 0, line_width=0.5, 
                            orientation="hor", color="black")
figure.get_basic_statistics()


figure.create_panel("D", increase_size_fac = 1, hor_alignment="center")
figure.add_cropping(top=0.085)
figure.show_images(frames=[0, 1, 2], channels=[0])
figure.add_text_within_at_coords("Axon",x=328, y=388, only_show_in_rows=[2])
figure.add_text_within_at_coords("1",x=142, y=402, only_show_in_rows=[2])
figure.add_text_within_at_coords("2",x=158, y=285, only_show_in_rows=[2])
figure.add_text_within_at_coords("3",x=108, y=153, only_show_in_rows=[2])
figure.add_text_within_at_coords("4",x=221, y=126, only_show_in_rows=[2])
figure.add_text_within_at_coords("5",x=385, y=172, only_show_in_rows=[2])
figure.annotate_channel_within_image(channel_names=["","Cytosol"], position="bottom-right", only_show_in_rows=[0])
figure.add_scale_bar(um_per_px=0.22, lengths_um=20)


figure.create_panel("E", increase_size_fac=1, hor_alignment="center", 
                    vert_alignment="top",
                    padding=[None, None])
figure.add_cropping(bottom=0.3, column=0)
figure.add_cropping(bottom=0.3, column=2)
figure.add_cropping(bottom=0.3, column=3)
figure.add_cropping(bottom=0.3, column=4)
figure.add_cropping(bottom=0.3, column=5)
figure.add_cropping(bottom=0.3,right=0.1, column=1)
figure.set_image_scaling(x_scale = 0.22, y_scale = 1/60)
additional_padding = {"images":2}
figure.show_images(additional_padding=additional_padding, 
                    use_same_LUTs=True)
figure.label_category(category="images", 
                      texts=["Axon\n", "Neurite\n1", "\n2", "\n3", "\n4", "\n5" ])
figure.annotate_channel_within_image(channel_names=["CAMSAP3"], 
                                     position="top-right", 
                                     only_show_in_columns=[0])
figure.add_y_axis(show_in_columns=[0],  axis_padding=2,
                    axis_title="Time [h]", show_tick_labels=True)
figure.add_x_axis(show_in_columns=[0], 
                    tick_values=[0,20,40], axis_padding=1,
                    axis_title="Soma\ndistance [\u03BCm]",
                    tick_length=2.5, tick_width=0.7,
                    tick_color="black",
                    direction="out")
figure.draw_line_on_images(position = 348, line_width=2,
                            line_style=(0, (5,2)))
figure.draw_line_on_images(position=482, line_width=1,
                            line_style=(0, (5,2)))


figure.save("png")
