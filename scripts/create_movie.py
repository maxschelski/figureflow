
# impor package to work with
from fastfig import figure
Figure = figure.Figure
"""
For all strings (e.g. text which are labeled, title page etc), 
"\n" in the string/text will make line break.
"""


"""
You need one folder where the tiff file is that should be used to generate
the movie. The tiff file needs to be formated as a Hyperstack by ImageJ
and needs to contain "frames"
set the absoluste path to the folder in which the tiff file is
"""
input_folder = ""

"""
Create figure object on which all functions will be executed.
Per file there can be as many figure objects as you like. 
Thereby multiple movies can be processed one after another to allow
generation of movies overnight in case of movies with a lot of frames
which would take a long time to be processed.

Arguments:
    input_folder (string): Absolute path to folder with tiff file
                            name of tiff file needs to start with
                            "panelZ_" where "Z" is the letter of the panel
                            in capital
    name (string): Name of the file as which the movie will be saved
    number (int): Added to the name after a "_"
    width (float): Width of movie in inches
    relative_height (boolean): Whether height should be relative to width
    height (float): Height of movie 
                    in relative width (if relative_height == True)
                    in inches (if relative_height == False)
    dpi (int): resolution of movie (dots/pixels per inch)
    video (boolean): Whether the Figure object is a movie; 
                     must be True for movies
    font_size (float): font size of all text in movie
    dark_background (boolean): Whether background of movie should be 
                                dark (and text on it white) or 
                                white (and text on it black)
Returns:
    Figure: Figure object on which functions are executed
"""
figure = Figure(folder=input_folder,  name="Movie",  number=10, 
                width=3, relative_height=True, height=0.6,
                dpi=1000,  video=True, font_size=6, 
                dark_background=True
                )

"""
Create panel on Figure.

Arguments:
    letter (string): Letter of panel, determines what letter should be 
                     included in the tiff file name 
                     "panelZ_" where "Z" is the letter of the panel in capital
    height (float): Height of panel 
                    in relative width (if relative_height == True)
                    in inches (if relative_height == False)
    hor_alignment (string): horizontal alignment of images/objects in panel
                            possible values: "left", "right", "center"
    vert_alignment (string): vertical alignment of images/objects in panel
                             possible values: "bottom", "top", "center"
Returns:
    None
"""
figure.create_panel(letter="G", height=0.34, hor_alignment="right",
                    vert_alignment="center")

"""
Crop image or images in last added panel. 
Needs to be done before show_images.

Arguments:
    xy (tuple of ints): mid position of zoomed area in pixels
                        first int is x position, second int is y position
    width (int): total width of zoomed area in pixels
    height (int): total height of zoomed area in pixels
    channels (list of ints): channels to which zoom should be added
    images (list of ints): images to which zoom should be added
Returns:
    None
"""
figure.add_zoom(xy=(144, 98), width=32, height=30, 
                channels=[1], label_position_overview="top")


"""
Crop image or images in last added panel. 
Needs to be done before show_images.

Arguments:
    bottom(float): Relative cropping of image from bottom
    top (float): Relative cropping of image from top
    left (float): Relative cropping of image from left
    right (float): Relative cropping of image from top
    column (int or list): column/s in image grid to which the cropping will be applied
    row (int or list): row/s in image grid to which the cropping will be applied
Returns:
    None
"""
figure.add_cropping(bottom=0.05, top=0, left=0.15, right=0.05, 
                    column=0, row=0)

"""
Show images of last created panel.

Arguments:
    frames (list): Frames (int) which should be included, "range" allows to include
                    all frames until the supplied number (e.g. 81)
                    can also be not incrementing frames (e.g. [0,50,99,100])
    channels (list): Channels (int) which should be included.
                    can also include overlay of channels by supplied
                    a string in the list that separates the two channel
                    numbers with a "-" (e.g. "0-1" in [0, 1, "0-1"])
    cmaps (list or string): colormaps which should be used, if a list
                            will be mapped to different channels
    overlay_cmaps (list or string): colormaps which should be used for overlay
                                    images, will be mappes to overlayed channels
    channels_to_show_first_nonzoomed_timeframe (list of ints): number of channels
                                    for which the nonzoomed images should be shown
Returns:
    None
"""
figure.show_images(frames=range(81),
                    cmaps="viridis",
                    channels_to_show_first_nonzoomed_timeframe=[0])

"""
Add colorbar to outside of images. 
Colorbar will have one high and one low tick 
which indicates where "high" and where "low" values are.

Arguments:
    site (float): site of images, allowed: "left", "right", "bottom", "top"
    size (float): size of colorbar in relative figure size (?)
    label_padding (float): padding of colorbar tick labels to colorbar
    tick_distance_from_edge (float): relative distance of ticks from colorbar edge
    tick_labels (list): labels (string) of ticks on colorbar 
    font_size_factor (int): font size of tick labels relative to global font size
                            allows for smaller tick label size if desired
Returns:
    None
"""
figure.add_colorbars(site="right", size=0.04, label_padding=0.2,
                     tick_distance_from_edge=0.1,
                     tick_labels=["Low", "High"],
                     font_size_factor = 1)

"""
Add labels outside of image/s.
Label different images of image-grid.

Arguments:
    texts (list): list of strings mapped to different images 
                    (each tiff file is considered one image)
Returns:
    None
"""
figure.label_images(texts=["Control", "Pa-Blebb"])

"""
Add labels outside of image/s.
Label different channels of image-grid.
See label_images.
"""
# figure.label_channels(texts=["Control", "Pa-Blebb", "Taxol"])


"""
Add labels outside of image/s.
Label different zooms of image-grid.
See label_images.
"""
# figure.label_zooms(texts=["Control", "Pa-Blebb", "Taxol"])

"""
Annotate different channels within images.
Needs to be done after all labels outside of image!

Arguments:
    channel_names (list): list of strings that will be mapped to channels 
    position (string): position of channel label on image, 
                        string before "-" indicates position in bottom-top axis
                        (possible values: "bottom" or "top")
                        string after "-" indicates position in left-right axis
                        (possible values: "left" or "right")
    only_show_in_columns (list of ints): columns in image grid where the 
                                        label will be added
    only_show_in_rows (list of ints): rows in image grid where the 
                                        label will be added
    padding (list or float): distance of label from image edge
                            if list, first float value is padding in x
                            second float value is padding in y
    channel_colors (list of strings): colors to be used to label different 
                                    channels; if None, highest value in cmap
                                    of channel will be used.
    only_show_in_columns (list of ints): columns in image grid where the 
                                        label will be added
    only_show_in_rows (list of ints): rows in image grid where the 
                                        label will be added
Returns:
    None
"""
figure.annotate_channel_within_image(channel_names = ["Tubulin"], 
                                     position="bottom-left", 
                                     only_show_in_columns=[0],
                                     channel_colors=["white"])

"""
Add scale bar to images.
Needs to be done after all labels outside of image!

Arguments:
    um_per_px (float): micrometer per pixel in image
    lengths_um (list or float): length of scale bar in image
                        if list, first value is for non-zoomed image and
                        second value is for zoomed image
    position (string): position of channel label on image, 
                        string before "-" indicates position in bottom-top axis
                        (possible values: "bottom" or "top")
                        string after "-" indicates position in left-right axis
                        (possible values: "left" or "right")
    only_show_in_columns (list of ints): columns in image grid where the 
                                        label will be added
    only_show_in_rows (list of ints): rows in image grid where the 
                                        label will be added
Returns:
    None
"""
figure.add_scale_bar(um_per_px=0.22, lengths_um=20, position="bottom-right")

"""
Add timestamp in images.
Needs to be done after all labels outside of image!

Arguments:
    time_per_frame (string): time between frames, first number than unit 
                            ("s", "m" or "h")
    start_time (float): start time as multiples of time_per_frame
    format (string): format of timestamp plotted on image with
                        "s" for seconds, "m" for minutes and "h" for hours
                        number of each letter represent how many digits will
                        be used for each part, separation of different units
                        by ":"
    show_unit (float): whether unit should be shown in timestamp 
    long_unit_names (Boolean): Whether long ("sec", "min", "hour") or 
                                short ("s", "m", "h") unit names should be shown
    all_units_shown (Boolean): Whether all units should be shown in timestamp
                                if True for format "ss:mm" "s:m" / "sec:min"
                                will be shown
    position (string):  position of channel label on image, 
                        string before "-" indicates position in bottom-top axis
                        (possible values: "bottom" or "top")
                        string after "-" indicates position in left-right axis
                        (possible values: "left" or "right")
    only_show_in_columns (list of ints): columns in image grid where the 
                                        label will be added
    only_show_in_rows (list of ints): rows in image grid where the 
                                        label will be added
Returns:
    None
"""
figure.add_timestamp(time_per_frame="3m",start_time=0, format="hh:mm", 
                      show_unit=True, position="top-left",
                      only_show_in_columns=[0],
                      only_show_in_rows=[0])

"""
Add arrow to image/s at defined positions.
Needs to be done after all labels outside of image!
Arguments:
    targets (list of list of ints): positions at which arrows should be added
                                    first int is position in x, second in y
    direction (string or int): Direction of the shaft starting at the tip
                                if string:
                                consists of two parts separated by "-",
                                first part is for bottom-top axis
                                (possible values: "bottom", "top")
                                second part is for left-right axis
                                (possible values: "left", "right")
                                can also just be one part with one of these
                                if int is degrees of direction
    size (float): Size in points (?)
    images (dictionary): images in which arrow should be drawn
                    each key corresponds to one category of the image
                    ("images", "frames", "channels")
                    and each value is an int of the value in that category or
                    a list of values in that category
Returns:
    None
"""
figure.draw_on_image(targets=[[305,120]], direction="right", size=50, 
                     images={"frames":range(10,81),"images":0})


title_page_txt = ("")

"""
Save Figure as movie.

Arguments:
    fps (int): frames per second of movie
    repeats (int): number of times the movie will be repeated
    title_page_text (string): text shown as title page, "\n" will make line break
    bitrate (int): bitrate in bits per second (e.g. 200 kbit is 200,000)
    duration_title_page (int): duration in seconds that title page should be 
                                shown
    frames_to_show_longer (int): list of frames which should be displayed 
                                longer, e.g. to highlight features or to
                                emphasize the start of the movie
    seconds_to_show_frames (float): seconds to show frames which should be shown
                                    longer
Returns:
    None
"""
figure.save_video(fps=10,  repeats=3, 
                  title_page_text = title_page_txt,
                  bitrate=300000,
                  duration_title_page=3,
                  frames_to_show_longer=[0],
                  seconds_to_show_frames=0.5
                  )