#  -*- coding: utf-8 -*-
"""
Created on Fri Feb  7 18:14:28 2020
still working on it...
@author: Maxsc
"""
import time
import numpy as np
import pandas as pd
from . import statannot
from matplotlib import pyplot as plt
import matplotlib
from matplotlib.colors import LinearSegmentedColormap
import inspect
import os
import itertools
# for extracting information from tif files
from skimage import io
from PIL import Image
from collections import OrderedDict
#  from skimage.external.tifffile import TiffFile
from tifffile import TiffFile
from matplotlib import patches
from scipy import ndimage

import cv2

import functools
import seaborn as sb
from PIL.TiffTags import TAGS as tiff_tags_dict
import copy
import re
import matplotlib.textpath as textpath
from matplotlib import lines
from matplotlib.font_manager import FontProperties

from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.path as mpath
import matplotlib.patches as mpatches
import matplotlib.text
from math import sqrt, pow, sin, cos
import tkinter as tk
from tkinter import font
import textwrap
# reloading is necessary to load changes made in the other script since the editor was started
import importlib
importlib.reload(statannot)
from pprint import pprint


"""
Features to add:
-allow adding title to categories labeled!
    title should be added at some distance to the labels
-automated showing of annotations in image only in first occurence ()
    -solve problem of back and forth switching 
    by creating array with 1 for value
     and zero for other values. then use computer vision labeling 
     to get all islands
     then process each island separately like scale bars are processed

Features to correct:
-scale is positioned on top left most position of group with same 
 scale bars lengths
    - would be a problem if there is a back and forth switch between scale bars lengths
"""

class FigurePanel():

    def __init__(self, figure, fig,
                 fig_width_available, fig_height_available,
                 fig_padding,
                 panel_file_paths, all_panel_imgs,
                 panel_pptxs, data, letter, y_pos,
                 height, x_pos, width, letter_fontsize,
                 hor_alignment="left", vert_alignment="top",
                 show_letter=True, padding="DEFAULT",
                 size_factor=1, increase_size_fac=1,
                 font_size=7, video=False,
                 animate_panel=None):
        """
            Initiate new Panel of Figure, returns panel.
            Automatically detect files for panel letter.
            Put images in grid according to image names or automatically
            in one row or column.
            :param padding: list or float, if list, first value is xpadding,
                            second is ypadding if float,
                            is padding for both xpadding and ypadding
                            xpadding and ypadding can each also be a float
                            or list. if list, the first value is for padding
                            left / top and the second value is for padding
                            right / bottom.
        """
        # figure is the parent figure object
        # not a matplotlib figure!

        self.itertypes = set([tuple, list])

        self.figure = figure
        self.fig = fig
        self.fig_padding = fig_padding
        self.fig_width_available = fig_width_available
        self.fig_height_available = fig_height_available
        #  self.fig_rows = fig_rows
        self.letter = letter
        self.panel_y = y_pos
        self.panel_x = x_pos
        self.width = width
        self.height = height
        #  self.grid = grid
        self.font_size = font_size
        self.letter_fontsize = letter_fontsize
        self.increase_size_fac = increase_size_fac
        self.size_factor = size_factor
        self.tick_scales = [1,1]
        self.video = video


        self.dark_background = figure.dark_background
        # if animate_panel is not set, make it true if figure panel is
        # part of video, otherwise false
        if (type(animate_panel) == type(None)):
            if video:
                animate_panel = True
            else:
                animate_panel = False
        self.animate_panel = animate_panel
        self.panel_file_paths = panel_file_paths
        self.all_panel_imgs = all_panel_imgs
        self.panel_pptxs = panel_pptxs
        self.show_letter = show_letter
        self.data = data
        # create copy of data
        self.data_orig = pd.DataFrame(data)

        self.hor_alignment = hor_alignment
        self.vert_alignment = vert_alignment

        self.x = None
        self.y = None
        self.hue = None
        self.col = None
        self.row = None
        
        self.image_padding_y = None
        self.image_padding_x = None

        # save functions to be executed in list
        self.functions_for_video = []
        self.video_frames = [0]
        self.show_function_called = False

        # set padding same as letter_fontsize,
        #  let letters stay in the padding between figures
        letter_fontsize_inch = self.letter_fontsize / 72
        if padding == "DEFAULT":
            # divide by two to have half of the padding on each side of the plot
            self.padding = [[letter_fontsize_inch / 2,
                            letter_fontsize_inch / 2],
                            [letter_fontsize_inch / 2,
                             letter_fontsize_inch / 2]]

        else:
            # expand padding into nested list where the first dimension
            # is x / y and the second is left/right or top/bottom
            if type(padding) in self.itertypes:
                self.padding = []
                for dim_nb, padding_one_dim in enumerate(padding):
                    self.padding.append([])
                    if (type(padding_one_dim) in self.itertypes):
                        self.padding[dim_nb] = padding_one_dim
                    else:
                        self.padding[dim_nb] = [padding_one_dim, padding_one_dim]

            else:
                self.padding = [[padding, padding],
                                [padding, padding]]
        self.xpadding = self.padding[0]
        self.ypadding = self.padding[1]


        # if the set context is None, the font_scale will immideately be applied
        #  to all figures (even those plotted already)
        #  sb.set_context(context="notebook",
        #  font_scale = font_scale * increase_size_fac)
        rc_dict= {}
        rc_dict["font.size"] = font_size
        rc_dict["axes.titlesize"] = font_size
        rc_dict["axes.labelsize"] = font_size
        rc_dict["legend.fontsize"] = font_size
        rc_dict["xtick.labelsize"] = font_size
        rc_dict["ytick.labelsize"] = font_size
        sb.set_context(context="paper",rc=rc_dict)

        self.all_axs = {}
        self.crop_params = []
        self.all_rows_to_delete = []
        self.zoom_params = {}
        # dictionary to save how each position was cropped
        self.cropped_positions = {}

        # initialized here to be available for images
        # and also for data (empty there)
        self.orig_size_enlarged_images = {}
        self.x_space = 0
        self.y_space = 0

        self.grouped_data = []
        self.included_data = []
        self.data_transformations = []
        self.y = None

        # define regexp for panel
        self.dim_val_finder = {}
        self.dim_val_finder["frames"] = re.compile("__t([\d]+)")
        self.dim_val_finder["channels"] = re.compile("__c([\d-]+)")
        self.dim_val_finder["slices"] = re.compile("__z([\d-]+)")

        # get outer border as relative coordinates in whole figure (min=0,max=1)
        self._calculate_outer_border_ax_grid()

        if (not self.video) & show_letter:
            # if letter ever is hidden, its probably because it is added
            #  before all the other things are added in the panel
            # probably also an addition error of the padding could be the cause
            self._add_letter_subplot(letter)

        self._initiate_label_dicts()


    def set_image_scaling(self, x_scale = 1, y_scale = 1):
        """
        Set scaling for how values on image axes should be scaled for displaying
        the values on the axes ticks
        (does not change the size of images but only the axes tick values)

        :param x_scale: Relative scale of x values
        :param y_scale: Relative scale of y values
        """
        self.tick_scales = [x_scale, y_scale]


    def show_images(self, images=None, channels=None, slices=None, frames=None,
                    order_of_categories=None, focus=None, show_focus_in=None,
                    interpolate_images="None",
                    dimension_equal="heights", scale_images=True,
                    auto_image_sub_param=None, make_image_size_equal=None,
                    auto_enlarge=True,enlarged_image_site="left",
                    simple_remapping=False,
                    channels_to_show_first_nonzoomed_timeframe=None,
                    show_only_zoom=True, force_show_non_zoom_channels=False,
                    show_non_zoom_channels=False,
                    position_zoom_nb = "top-left", zoom_nb_frames=0,
                    show_single_zoom_numbers = False,
                    show_zoom_number_in_image=True,
                    zoom_nb_rows=None, zoom_nb_columns=None,
                    line_width_zoom_rectangle = 0.3,
                    zoom_nb_font_size_overview = None, zoom_nb_color = "white",
                    zoom_nb_font_size = None, zoom_nb_padding = 0.015,
                    repositioning_map = None, additional_padding = None,
                    show_axis_grid = False, use_same_LUTs=True,
                    cmaps="gray", composite_cmaps=None,
                    black_composite_background=True,
                    replace_nan_with=0, sub_padding_factor= 0.25
                    ):
        """
        Display images of current panel.
        Always use function that annotate within the image
        after functions that annotate outside of the image.
        Ranges seemingly can only be extracted from ImageJ images
        if the LUT is set to gray.

        :param images: List of images (integers) which should be displayed
                        each image corresponds to one image file for the 
                        panel
        :param channel: List of channels (integers) which should be displayed
                        composite/composite images can be by adding
                        a string with all channel numbers separated by "-",
                        e.g. channels=[0,1,2,"0-1-2"].
                        dimension is extracted from ImageJ Hyperstack
                        information
        :param slices: List of slices (integers) which should be displayed
                        dimension is extracted from ImageJ Hyperstack
                        information
        :param frames: List of frames (integers) which should be displayed
                        dimension is extracted from ImageJ Hyperstack
                        information
        :param order_of_categories: List of strings with order of the image
                                    dimensions ("images", "channels", "slices",
                                    "frames"), determines how images will be 
                                    put into a grid. Images of different 
                                    dimensions values for a dimension
                                    earlier in the list will be closer together
                                    (e.g. for ["frames", "channels"] first
                                    all frames from one channel will be shown
                                    then all frames from the other channel)
        :param focus: String of dimensions ("images", "channels", "slices",
                                    "frames") that will be alone on one axis 
                                    of the image grid (e.g. for "frames" all 
                                    different frames will be along one axis 
                                    (e.g. columns) while the different images
                                    and channels will be along the other axis 
                                    (e.g. rows).
        :param show_focus_in: "row" or "column" - allows to fix
                                in which dimension the focus will be shown
        :param interpolate_images: Type of interpolation for the matplotlib
                                    function ax.imshow
        :param dimension_equal: Determines in which dimension
                                ("height" or "width") images should be similar
                                e.g. for "height", images in same row
                                will be adjusted to have the same height
                                for "width images in same column
                                will be adjusted to have the same width
        :param scale_images: Boolean. Whether images should be scaled
                            to fit into an even grid.
                            dimension_equal will only be considered
                            if scale_images == True
                            scaling is necessary
                            to show zoomed regions actually enlarged
                            however, it might be a problem
                            if it is important for the data
                            to be equally scaled in the entire panel
        :param auto_image_sub_param: String. Substring in panel file names that
                                    defines how images should be grouped
                                    into image_sub automatically
                                    (without defining images manually
                                    as a nested list)
                                    image file names must have this substring
                                    together with an identifier for the
                                    specific image sub group separated by "_"
                                    on each site from the rest of the file name
                                    auto_image_sub_param must only be ONCE
                                    in each file name!
                                    e.g. if you want to group various images
                                    for a panel by the cell from which
                                    they originate
                                    and each image file name somewhere contains
                                    "_cellXXXX_" where each X is some digit
                                    then auto_image_sub_param should be "cell"
                                    to catch the right group

        :param make_image_size_equal: List. Allows for adding px to images
                                    in one dimension ("height" or "width")
                                    to make the size of images
                                    in that dimension equal.
                                    list must have at least two values.
                                    The first value must be "height" or "width"
                                    the second value defines
                                    at which site pxs are added
                                    "right" or "left" for "width" OR "bottom"
                                    or "top" for "height"
                                    The third value in the list is optional
                                    and defines which values will be added
                                    The default value to be added is 0
        :param auto_enlarge: Boolean; Whether images should
                            be enlarged automatically
                            to fill up grid into rectangle
                            "focus", "show_focus_in",
                            the first element in "order_of_categories"
                            and "enlarged_image_site" can determine how the
                            enlarged images will be shown
                            (where they will be displayed
                            and how much they will consequently be enlarged
                            to fill up the image grid)
        :param enlarged_image_site: Site at which the enlarged image should be
                                    shown ("left", "right", "top" or "bottom"
                                    possible)
        :param simple_remapping: Whether only the image with the identity
                                should be increased in size
        :param channels_to_show_first_nonzoomed_timeframe: If a zoom is defined,
                                                should the first frame
                                                of each channel be always shown
                                                (as overview)
        :param show_only_zoom: Potentially apart from overview image,
                                dont show any non zoom pictures
        :param force_show_non_zoom_channels: Force to show channels that were
                                            not zoomed independent
                                            of other settings
        :param show_non_zoom_channels: show channels that were
                                        not zoomed independent of other settings
        :param show_zoom_mark_on_all_channels: Whether rectangle with number of
                                                zoom should be shown on top
                                                of all channels
                                                otherwise they will only be
                                                shown on overview
        :param position_zoom_nb: position at which the zoom number shouldbe
                                shown in the zoomed image
        :param show_single_zoom_numbers: Show zoom number in image
                                        and at zoom rectangle in overview
                                        image, even if there is just one
                                        zoomed area
        :param show_zoom_number_in_image: Add zoom number to edge of zoomed
                                        image
        :param zoom_nb_rows: List of rows in image grid in which zoom numbers will be
                            added
        :param zoom_nb_columns: List of columns in image grid in which zoom
                                numbers will be added
        :param line_width_zoom_rectangle: Line width in pt of zoom rectangle
                                            added to overview iamge
        :param zoom_nb_font_size_overview: font size of zoom number in overview image
        :param zoom_nb_color: Color of zoom number text on images
        :param zoom_nb_padding: Padding of zoom number text to edges of image
        :param zoom_nb_font_size: font size of zoom number in zoom image
        :param zoom_nb_frames: List with ints or int, Index of frames where
                                zoom nb should be shown in zoom
                                For each int will use the Xth frame
                                (e.g. if frame 5,10,20 will be shown
                                and zoom_nb_frames is [0,1] then the zoom_nb
                                will be shown in the first and second frame (5, 10)
        :param repositioning_map: join specific images together with another
                                dimension (by remapping the identity)
                                e.g. join one image from a channel
                                with the images of another channel
                                supply a dict where the key is a tuple
                                corresponding to the images
                                that should be remapped
                                (e.g. ("channel",1,"zoom",0))
                                the value should be a tuple
                                that identifies the group
                                that the images should be joined to uniquely
                                the value tuple should correspond to images
                                that only differ in one category (e.g. frame)
                                the images will be joined in this category
                                differing (like being added as additional
                                frame points in this example)
                                if "image" is not part of the value tuple
                                then the images will be remapped on the same image
        :param additional_padding: Multiply padding by factor to separate
                                    elements within one category dict
                                    where key is the category and value is the factor
        :param show_axis_grid: Show axis grid on top of image (major ticks
                                for x and y axis)
        :param use_same_LUTs: Should the ranges from the first image
                                in each chanel be applied to all images
        :param replace_nan_with: float, Replace nan in images with value
        :param cmaps: string or list of strings corresponding to matplotlib
                        colormaps; each entry in list corresponds to one channel
                        in same order
        :param composite_cmaps: list of strings corresponding to matplotlib
                                colors for composite channel (only if composite
                                is defined in 'channels'). Order of cmaps
                                corresponds to order of channels in ImageJ,
                                changes in order in the 'channels' parameter
                                do not change the order of composite_cmaps.
                                 Will create cmap for each channel from
                                 black/white (depending on 
                                 'black_composite_background' parameter to 
                                 color.)
        :param black_composite_background: Whether the background (image below
                                            image range) of the composite should
                                            be black, if False, background is
                                            white
        :param replace_nan_with: With what values to replace nan values with
        :param sub_padding_factor: Multiple of figure_panel padding that is
                                    used for padding in image grid


        """
        # differentiate between the case when there is data and when images
        # (combination of both or multiple data files in same panel not possible
        if self.panel_file_paths[0].find(".csv") != -1:
            raise ValueError("Showing images is not supported for csv files"
                             "but csv file {} is part of the "
                             "panel".format(self.panel_file_paths[0]))

        print("DISPLAYING IMAGES FOR PANEL {}.............".format(self.letter))

        self._initiate_show_images_variables()

        self.interpolate_images = interpolate_images

        self.sub_padding_factor = sub_padding_factor

        if type(channels_to_show_first_nonzoomed_timeframe) == type(None):
            channels_to_show_first_nonzoomed_timeframe = []

        # since this could also be an composite
        # convert into composite format from strings
        for channel_nb, channel_val in enumerate(channels_to_show_first_nonzoomed_timeframe):
            if type(channel_val) == str:
                channel_vals = channel_val.split("-")
                channel_vals = tuple([int(channel_val) for channel_val in channel_vals])
                channels_to_show_first_nonzoomed_timeframe[channel_nb] = channel_vals

        place_holder_identities = {}

        if type(additional_padding) == type(None):
            additional_padding = {}


        if type(make_image_size_equal) == type(None):
            make_image_size_equal = []

        # auto_sorting panels into sub_images by a defined name criteria
        if type(auto_image_sub_param) != type(None):
            images = self._group_images_by_sub_param(auto_image_sub_param)

        self.display_mode = self._set_max_row_and_col()

        (category_vals,
         allowed_categories,
         additional_categories) = self._get_categories(images, channels,
                                                       frames, slices)

        # save category vals to make available for label_frames
        self.category_vals = category_vals

        allowed_categories = allowed_categories + list(additional_categories.keys())

        (self.map, 
         order_of_categories) = self._get_map_of_categories(allowed_categories, 
                                                            order_of_categories)

        self.inv_map = { v : k for k, v in self.map.items() }

        # define datatype of all dimensions where data type is not string
        self.data_types = {}
        self.data_types["frames"] = int

        identity_to_add_zoom_mark_to = {}

        if self.display_mode == "auto":

            (self.sub_category_map,
             self.reassign_new_categories,
             self.reassign_new_categories_inv) = self._add_new_categories(additional_categories)

            # define how values for different image dimensions
            #  (frame, channels, etc) should be sorted
            # only add something if it differs from standard ascending value sorting
            sorters = {}
            sorters["channels"] = self._sort_category_vals_key

            extract_info = self._check_if_images_should_be_extracted_from_tif()

            if extract_info:
                #  first pre_identity is constructed without zoom and image_sub
                #  these properties will be added later
                #  (they cannot be inferred from the image directly)
                #  give basic_map object to function to exclude zoom and image_sub
                (all_images_by_pre_identity,
                 img_ranges,
                 pre_identity_val_map) = self._extract_images_from_tiff(self._get_basic_map(),
                                                               category_vals["channels"],
                                                               category_vals["slices"],
                                                               category_vals["frames"])
            else:
                (all_images_by_pre_identity,
                 img_ranges) = self._get_img_dict_by_pre_identity(self.inv_map)
                pre_identity_val_map = {}

            # add categories to pre_identity before
            #  pre_identity is needed the first frame
            # specifically zoom and _sub categories are added to pre_identities
            # categories will be added here,
            #  therefore the initial mapping (inv_sorting_identity_map)
            #  will not be correct anymore!
            #  (won't even work since identities have too few values)
            all_images_by_pre_identity = self._add_categories_to_pre_identities(all_images_by_pre_identity,
                                                                             self.sub_category_map)

            self.dim_val_maps = self._get_category_maps(all_images_by_pre_identity,
                                                        self.inv_map, sorters,
                                                        self.reassign_new_categories,
                                                        pre_identity_val_map)
            
            all_images_by_identity = self._finalize_pre_identity_dicts(all_images_by_pre_identity,
                                                                      self.inv_map, self.dim_val_maps)


            (all_images_by_identity,
             identity_to_add_zoom_mark_to) = self._add_zoom_images(all_images_by_identity,
                                                                show_only_zoom,
                                                                channels_to_show_first_nonzoomed_timeframe,
                                                                force_show_non_zoom_channels,
                                                                show_non_zoom_channels)

            (reposition_dict,
             remapped_categories) = self._get_reposition_dict_for_mapping(all_images_by_identity,
                                                                        repositioning_map,
                                                                        simple_remapping)

            all_images_by_identity = self._apply_mapping(all_images_by_identity,
                                                        reposition_dict)

            self.inv_reposition_dict = {v:k for k,v in reposition_dict.items()}

            identity_remap_correction = self._get_identity_remapping_correction_map(
                remapped_categories, all_images_by_identity)

            #  apply remapping
            all_images_by_identity = self._apply_mapping(all_images_by_identity,
                                                        identity_remap_correction)

            self.inv_identity_remap_correction = {v: k for k, v in
                                                  identity_remap_correction.items()}


            # think about how to organize order_of_categories if none were supplied
            # if some were supplied use those supplied in that order first
            # then add remaining categories afterwards in specific order

            cats_similar_for_all_images = self._get_similar_categories_of_identities(all_images_by_identity.keys())

            flexible_order_first = []
            flexible_order_second = []
            cats_similar_for_all_images = set([self.inv_map[cat]
                                                for cat in
                                                cats_similar_for_all_images])
            for category in order_of_categories["flexible"]:
                if category in cats_similar_for_all_images:
                    flexible_order_second.append(category)
                else:
                    flexible_order_first.append(category)

            order_of_categories["flexible"] = [*flexible_order_first,
                                               *flexible_order_second]

            # --------------------AUTO ENLARGE IMAGES----------------------
            # if only one dimension is not similar for all images
            # then no auto enlarge is possible
            # since everything can be displayed in a single row
            nb_categories = len(list(all_images_by_identity.keys())[0])
            nb_of_categories_different = nb_categories - len(cats_similar_for_all_images)

            if nb_of_categories_different <= 1:
                auto_enlarge = False

            images_enlarge = []

            if auto_enlarge:

                # implement increased size (size_factor_dict)
                # increasing size only works nicely if there is enough space
                # in between images to accomodate increased size

                #  If focus is defined, then images in one dimension are clear
                #  should be a function to auto enlarge images
                #  how to find images that should be enlarged?
                #  plot images as "1" in N-dimensional array
                #  filled otherwise with zeros
                #  with dimensions being image, frame, zoom etc.
                #  for each position (image) in array get number
                #  of dimension with neighbors
                neighbors, identity_array = self._get_nb_neighbors_from_identities(all_images_by_identity)

                #  get images to be enlarged from neigbors
                images_enlarge = self._get_images_to_be_enlarged(neighbors, 
                                                                identity_array)

            if len(images_enlarge) > 0:
                # get different combinations of dimensions
                # to enlarge the image
                dimension_combinations = self._get_dimension_combinations(focus,
                                                                          order_of_categories,
                                                                          cats_similar_for_all_images)

                if self._is_none(show_focus_in):
                    all_show_focus_in = ["rows", "cols"]
                elif type(show_focus_in) not in self.itertypes:
                    all_show_focus_in = [show_focus_in]
                else:
                    all_show_focus_in = show_focus_in

                if self._is_none(enlarged_image_site):
                    enlarged_image_sites = ["top", "left"]
                elif type(enlarged_image_site) not in self.itertypes:
                    enlarged_image_sites = [enlarged_image_site]
                else:
                    enlarged_image_sites = enlarged_image_site

                # go through all
                all_scores = {}
                for first_dimension, second_dimension in dimension_combinations:
                    enlarge_combinations = itertools.product(all_show_focus_in,
                                                             enlarged_image_sites)
                    # calculate size increase factor as number
                    # of different values in first or second dimension
                    # try out both dimensions
                    # will be done through different show_focus_in
                    # and through different enlarged_image_site
                    
                    for (show_focus_in,
                         enlarged_image_site) in enlarge_combinations:

                        all_images_by_identity_tmp = copy.copy(all_images_by_identity)

                        (size_increase_dim_nb,
                         size_increase_cat_is_focus) = self._get_size_increase_cat_for_enlarged_image_site(
                                                                                                show_focus_in,
                                                                                                enlarged_image_site)

                        order_of_categories_tmp = self._resort_order_of_categories_from_primer([first_dimension, second_dimension],
                                                                                              order_of_categories)

                        # size increase dim is the category that determines
                        #  how much the image will be enlarged

                        (all_images_by_identity_tmp,
                        _, _, _) = self._auto_enlarge_images(images_enlarge,
                                                            first_dimension,
                                                           second_dimension,
                                                            size_increase_dim_nb,
                                                            size_increase_cat_is_focus,
                                                           order_of_categories_tmp,
                                                            all_images_by_identity_tmp,
                                                            show_focus_in)

                        # if all images where returned as None,
                        # then the current combination cannot be used to
                        # enlarge images but the images themselves indicate
                        # that some images should be enlarged
                        # since enlarging is not possible, don't use combination

                        if self._is_none(all_images_by_identity_tmp):
                            continue

                        width_imgs, height_imgs = self._get_width_height_matrices_of_categories(
                                                        self.inv_map,
                                                        all_images_by_identity_tmp)

                        (column_categories,
                         row_categories) = self._get_dimension_categories(first_dimension,
                                                                         second_dimension,
                                                                         size_increase_cat_is_focus,
                                                                         size_increase_dim_nb,
                                                                         order_of_categories_tmp,
                                                                         show_focus_in)

                        grid_fit_score = self._get_image_category_grid_fit_score(column_categories,
                                                                           row_categories,
                                                                           all_images_by_identity_tmp,
                                                                           width_imgs, height_imgs,
                                                                           additional_padding
                                                                           )
                        best_permutation = (column_categories, row_categories)
                        # save best score for current combination
                        score_key = [first_dimension, second_dimension,
                                      show_focus_in, enlarged_image_site,
                                     best_permutation]

                        all_scores[tuple(score_key)] = grid_fit_score

                # after the best permutation for the best combination of
                # show_focus_in and enlarged_image_site is found,
                # use the combination to:
                # 1) _auto_enlarge_images
                # 2) get_width_and_height_matrices_of_categories
                best_score = np.inf
                for combination, score in all_scores.items():
                    if score < best_score:
                        best_score = score
                        best_combination = combination
                
                (first_dimension,
                 second_dimension,
                 show_focus_in,
                 enlarged_image_site,
                 best_permutation) = best_combination

                (size_increase_dim_nb,
                 size_increase_cat_is_focus) = self._get_size_increase_cat_for_enlarged_image_site(
                                                            show_focus_in,
                                                            enlarged_image_site)

                order_of_categories = self._resort_order_of_categories_from_primer([first_dimension,
                                                                                    second_dimension],
                                                                                      order_of_categories)

                (all_images_by_identity,
                 self.inv_increase_size_map,
                 self.size_factors_for_identities,
                 self.place_holder_identity_map) = self._auto_enlarge_images(
                                                                images_enlarge,
                                                                first_dimension,
                                                                second_dimension,
                                                                size_increase_dim_nb,
                                                                size_increase_cat_is_focus,
                                                                order_of_categories,
                                                                all_images_by_identity,
                                                                show_focus_in)

                (width_imgs,
                 height_imgs) = self._get_width_height_matrices_of_categories(
                                                                            self.inv_map,
                                                                            all_images_by_identity)

            else:

                # move ALL other images in that direction as well
                # move the correction for empty positions here for that

                # all identities that were used from before repositioning need to be mapped with the repositioning dict as well
                # they can be mapped to the pre_identity val then in create_image_dict_by_position_auto_mode


                # do NOT use absolute pixel values
                # images will not be scaled according to their pix values
                # instead the ratio of width to height matters
                (width_imgs,
                 height_imgs) = self._get_width_height_matrices_of_categories(self.inv_map,
                                                                            all_images_by_identity)

                # write function to find how many different values there are for the dimension
                # extract number of different values for additional_padding and use this to calculate width/height to find best permutation

                permutation_differences = self._get_differences_of_permutations(
                                                                order_of_categories,
                                                                self.map, width_imgs,
                                                                height_imgs, focus,
                                                                additional_padding,
                                                                all_images_by_identity,
                                                                show_focus_in)

                best_permutation, _ = self._get_best_permutation_of_cats_for_axes(
                                                            permutation_differences)

            self._set_max_row_and_col_in_auto_mode(best_permutation, width_imgs)

            self._create_image_dict_by_position_auto_mode(all_images_by_identity,
                                                         best_permutation,
                                                         width_imgs,
                                                         self.inv_map)


        else:
            img_ranges = self._create_image_dict_by_position()


        self._initiate_label_matrices()
        self._initiate_label_dicts()

        (self.image_widths,
         self.image_heights) = self._plot_images_without_setting_position(img_ranges,
                                                                          use_same_LUTs,
                                                                          cmaps,
                                                                         composite_cmaps,
                                                                          make_image_size_equal,
                                                                          replace_nan_with,
                                                                          scale_images,
                                                                         black_composite_background)


        width_columns, height_rows = self._get_width_columns_and_height_rows(self.image_widths,
                                                                            self.image_heights,
                                                                            dimension_equal,
                                                                            scale_images)

        self._set_additional_padding_matrices(additional_padding)

        # get inner border and width and height
        #  to use as coordinates relative to figure size
        inner_border, width_to_use, height_to_use = self._get_centered_inner_border(width_columns,
                                                                                   height_rows)

        # position plots in inner border
        self._set_position_of_plots(width_to_use, height_to_use, width_columns,
                                   height_rows, inner_border)

        # make size of images equal in one dimension (row or column)
        #  by adding nan px to respective site
        # get maximum width and maximum height
        #  for position, ax in self.all_images_by_position.items():


        self._remove_xy_axes(show_axis_grid)

        self._create_img_position_matrix()

        if "zooms" in self.map:

            self._add_zoom_marks_to_overview_images(identity_to_add_zoom_mark_to,
                                                   line_width_zoom_rectangle,
                                                   zoom_nb_font_size_overview,
                                                   zoom_nb_padding,
                                                   zoom_nb_color,
                                                   show_single_zoom_numbers)

            if show_zoom_number_in_image:
                self._add_zoom_number_to_zoomed_images(position_zoom_nb,
                                                     zoom_nb_frames,
                                                     zoom_nb_rows,
                                                      zoom_nb_columns,
                                                      zoom_nb_font_size,
                                                      zoom_nb_color,
                                                      zoom_nb_padding,
                                                      show_single_zoom_numbers)

    def _initiate_show_images_variables(self):
        self.y_space = 0
        self.x_space = 0
        self.all_images_by_position = {}
        # map of position to original identity (including actual frames etc.)
        self.pos_to_pre_identity_map = {}
        # map of position to identity used for positioning
        # needed to map a specific place holder image to the real image
        self.pos_to_identity_map = {}
        self.pre_identity_to_pos_map = {}

        # map of place holder identity
        # to pre identities of corresponding images
        self.place_holder_identity_map = {}

        # map of colormaps for positions
        self.cmaps_for_position = {}

        self.default_label_positions = {}
        self.dim_val_maps = {}
        self.reassign_new_categories_inv = {}
        self.inv_reposition_dict = {}
        self.inv_identity_remap_correction = {}
        self.inv_increase_size_map = {}
        self.inv_remap_for_orientation = {}
        self.size_factors_for_identities = {}
        self.site_of_colorbars = {}
        self.all_colorbars = {}
        # set one global value for padding of colorbars
        self.padding_of_colorbars = np.nan
        # initialize a dict that will keep track of
        # all positions for a specific channel (for different colormaps)
        # is important for plotting colorbars
        # so that for each different colormap a colorbar is plotted
        self.positions_for_cmaps = {}
        # initialize map of cmap names to channel ints
        self.cmap_to_channels = {}

        #  dict that saves how much space there is
        #  on each site already for labels
        #  this space is created by adding labels on that site
        # e.g. adding a label in the first of three rows on the left site
        # creates space on the left site for further labels to be added
        # on the left site in different positions (second or third row)
        self.space_for_labels = {}
        self.space_for_labels["left"] = 0
        self.space_for_labels["right"] = 0
        self.space_for_labels["top"] = 0
        self.space_for_labels["bottom"] = 0

    def add_colorbars(self, site ="right", channels = None,
                      tick_labels = None,
                      size = 0.1, tick_distance_from_edge = 0.2,
                      font_size_factor = 0.6,
                      padding = 0.2, tick_length = 1,
                      label_padding = 0,
                        only_show_in_rows = None, only_show_in_columns = None
                      ):
        """
        Add colorbars to imagegrid, based on their colormaps.
        For each colormap in the image grid only one colorbar will be shown.

        :param site: None or str, one of ["bottom", "top", "left", "right"]
                    colorbar will be shown at the respective site of the panel
                    If it is bottom or top, it will be shown in every column
                    If it is left or right it will be shown in every row
                    For now, it assumes that in the respective dimension
                    (row or column)
                    the image ranges are different and therefore should be
                    displayed in every row/column
                    site of image grid ad which colorbar/s will be shown
                    it will never be shown within the image grid
        :param channels: list of ints; channels for which colorbars
                        will be shown
                        if multiple channels have the same colormap
                        only one of the channels has to be in the list
                        for it to be displayed.
                        default is that colorbars are shown for all channels
        :param tick_labels: list of two strings, labels to put on left (first value)
                            and right end (second value) of colorbar, instead
                            of floats
        :param size: float, size of colorbar in fraction of axes it is added to
        :param tick_distance_from_edge: int, 0 to 0.4; relative distance
                                        from edge to indicate value on colorbar
                                        (relative value is indicated)
                                        Move two ticks of colorbar from outer
                                        edges away thereby preventing the
                                        numbers to overlap
                                        with neighboring images
        :param font_size_factor: factor by which the font size is incrased,
                                factor of 1 means that self.font_size is used
        :param padding: padding, float; in relative units of size of colorbar
        :param tick_length: float; length of ticks for tick values at colorbar
                            in points
        :param label_padding: float; padding of tick values from ticks in points
        :param only_show_in_rows: list of ints;
                                    in which rows of the image grid should
                                    the colorbar be shown
        :param only_show_in_columns: list of ints; in which columns
                                    of the iamge grid should
                                    the colorbar be shown
        """

        self._add_colorbars_to_axs(site,
                                  channels,
                                  self.image_heights,
                                  tick_labels,
                                  size,
                                  tick_distance_from_edge,
                                  font_size_factor,
                                  padding,
                                  tick_length,
                                  label_padding,
                                  only_show_in_rows,
                                  only_show_in_columns)


    def _group_images_by_sub_param(self, auto_image_sub_param):
        image_sub_param_name = str(auto_image_sub_param)
        # create a dict where each sub_group is one key
        # and the value is a list
        # with each image in that subgroup as one element
        sub_image_dict = {}
        for file_number, file_path in enumerate(self.panel_file_paths):
            file_name = os.path.basename(file_path)
            if file_name.find(image_sub_param_name) == -1:
                raise ValueError("The file '{}' did not have the "
                                 "auto_image_sub_param included "
                                 "in the name.".format(file_name))
            else:
                # find part in the file_name (separated by "_")
                # that includes the image_sub_param_name
                for sub_image_prop in file_name.split("_"):
                    if sub_image_prop.find(image_sub_param_name) != -1:
                        break
                if sub_image_prop not in sub_image_dict:
                    sub_image_dict[sub_image_prop] = []
                sub_image_dict[sub_image_prop].append(file_number)
        # create new images attribute by adding together all lists into one list
        images = list(sub_image_dict.values())
        return images

    def _get_categories(self, images, channels, frames, slices):
        # create list of allowed categories
        category_vals = {}
        category_vals["images"] = images
        category_vals["channels"] = channels
        category_vals["frames"] = frames
        category_vals["slices"] = slices
        allowed_categories = list(category_vals.keys())
        # if zoom was defined, add an additional category
        if len(self.zoom_params) > 0:
            allowed_categories.append("zooms")
        # extract additional categories by going through each of the
        #  allowed category parameters if not None
        # if at least one element is a list in that variable
        # treat each element in the variable as having
        #  a different value in a new category
        additional_categories = {}
        for category, values in category_vals.items():
            if self._is_none(values):
                continue

            for value in values:
                if (type(value) not in self.itertypes):
                    continue
                additional_categories[category+"_sub"] = values
                break

        # flatten all categories
        for category, values in category_vals.items():
            if values != None:
                new_values = []
                for value in values:
                    if (type(value) in self.itertypes):
                        new_values += value
                    else:
                        new_values.append(value)
                category_vals[category] = new_values

        return category_vals, allowed_categories, additional_categories


    def _get_map_of_categories(self, allowed_categories, order_of_categories):

        if self._is_none(order_of_categories):
            order_of_categories = []

        for category in order_of_categories:
            if category not in allowed_categories:
                raise ValueError("The supplied category '{}' for "
                                 "order_of_category is not allowed. Only the "
                                 "following categories are allowed: "
                                 "{}.".format(category,
                                              ", ".join(allowed_categories) ))

        order_of_categories_dict = {}

        # set fixed order of categories as pre-defined order of categories
        order_of_categories_dict["fixed"] = order_of_categories
        order_of_categories_dict["flexible"] = []

        # order in which the categories are sorted
        #  when on the same axes (column or rows)
        # can be determined by changing mapping

        for category in allowed_categories:
            if category not in order_of_categories_dict["fixed"]:
                order_of_categories_dict["flexible"].append(category)

        map = {}
        for cat_nb, category in enumerate([*order_of_categories_dict["fixed"],
                                           *order_of_categories_dict["flexible"]]):
            map[category] = cat_nb

        return map, order_of_categories_dict

    def _add_new_categories(self, additional_categories):
        sub_category_map = {}
        reassign_new_categories = {}
        # inv map maps sub category value and category value from identity
        # uniquely to original value (from pre identity)
        reassign_new_categories_inv = {}
        # create map of additional categories
        # and remap values of categories that have new sub category
        # so that all sub categories have the same values in the category
        for add_category, values_list in additional_categories.items():
            sub_category_map[add_category] = {}
            orig_category = add_category.replace("_sub","")
            reassign_new_categories[orig_category] = {}
            reassign_new_categories_inv[orig_category] = {}

            for nb, values in enumerate(values_list):
                for value_nb, value in enumerate(values):
                    sub_category_map[add_category][value] = nb
                    reassign_new_categories[orig_category][value] = value_nb
                    reassign_new_categories_inv[orig_category][(value_nb, nb)] = value

        return (sub_category_map, reassign_new_categories,
                reassign_new_categories_inv)


    def _check_if_images_should_be_extracted_from_tif(self):
        # if tif files were provided, extract channels desired from them
        extract_info = False
        for file_path in self.panel_file_paths:
            file_name = os.path.basename(file_path)
            if (file_name.find(".tiff") != -1) | (file_name.find(".tif") != -1):
                extract_info = True
            elif extract_info:
                raise ValueError("All files provided for one panel need to be "
                                 ".tiff / .tif or .png / .jpeg. Some files "
                                 "were .tiff / .tif but '{}' was of a different "
                                 "format.'".format(file_name))
        return extract_info


    def _extract_img_ranges_from_file(self, file_path):
        ranges = []
        if file_path.find(".tif") == -1:
            return ranges

        # scale images according to ranges found in tiff file from ImageJ
        # get ranges from tiff file
        #  with TiffFile(file_path) as tif:
        tif = TiffFile(file_path)
        #  vals = tif.imagej_metadata(
        #      tif.pages[0].tags[50839].value,
        #      tif.pages[0].tags[50838].value,  #  IJMetadataByteCounts
        #      tif.byteorder,
        #      )
        # if image was not yet opened in imageJ
        # it will not have ranges or any imagej metadata
        if type(tif.imagej_metadata) == type(None):
            return ranges

        imagej_tags = tif.imagej_metadata
        if "Ranges" in imagej_tags:
            ranges = np.array(imagej_tags["Ranges"])
            # reshape ranges to have two columns (one for min, one for max)
            # and as many rows as channels
            ranges = np.reshape(ranges, ( int(len(ranges)/2 ) , 2) )
        elif "min" in imagej_tags:
            ranges = np.array( [ [ imagej_tags["min"], imagej_tags["max"] ] ] )

        return ranges

    def _get_image_properties(self, file_path):
        """
        Extracts order of dimensions of imageJ image and image width and height
        """
        # with Image.open(file_path) as img:
        with TiffFile(file_path) as img:
            file_name = os.path.basename(file_path)
            # get key that is used for imagedescription in ".tag" dict
            tiff_tags_inv_dict = {v:k for k,v in tiff_tags_dict.items()}
            tiff_tag = tiff_tags_inv_dict["ImageDescription"]
            # use create ordered dict of imagedescription
            # order in dict determines which dimension in the array is used
            # counting starts from rightf

            data_dict = OrderedDict()
            if tiff_tag not in img.pages[0].tags:
                print("WARNING: The file '{}' has not been opened and saved "
                      "by ImageJ yet.".format(file_name))
            else:
                data = img.pages[0].tags[tiff_tag].value
                data_values = data.split("\n")
                for value in data_values:
                    value_split = value.split("=")
                    if len(value_split) == 2:
                        data_dict[value_split[0]] = value_split[1]
            img_width = np.array(img.asarray()).shape[-1]
            img_height = np.array(img.asarray()).shape[-2]
        return data_dict, img_width, img_height


    def _move_xy_axes_in_img_to_last_dimensions(self, img, img_width,
                                               img_height):
        """
        Move x and y axes of all images in stack (img)
        to last position in dimension list
        :param img: multi-dimensional numpy array
        :param img_width: width (length of x axis) of one image in img (stack)
        :param img_height: height (length of y axis) of one image in img (stack)
        """
        img_axes = img.shape
        # if there are more than 2 (x,y) axes
        if len(img_axes) > 2:
            # check which axes are x and y and put these axes last
            xy_axes = []
            for ax_nb, axis in enumerate(img_axes):
                if (axis == img_width) | (axis == img_height):
                    xy_axes.append(ax_nb)
            for xy_nb, xy_axis in enumerate( reversed(xy_axes) ):
                img = np.moveaxis(img, xy_axis, - xy_nb - 1 )
        return img


    def _extract_images_from_tiff(self, basic_map, channels, slices, frames):
        """
        Extract images according to channels, slices and frames from hyperstack
        tiff file from ImageJ
        :param basic_map: dictionary, mapping category name to number of category
                            of basic categories
                            (images, channels, slices, frames)
        :param channels: list of ints; channels which should be extracted
        :param slices: list of ints; slices which should be extracted
        :param frames: list of ints; frames which should be extracted
        """
        if len(self.panel_file_paths) == 1:
            warning_string = "the file"
        else:
            warning_string = "files"
        if channels == None:
            print("WARNING: Since no channels were provided,"
                  " all channels from {} "
                  "will be displayed.".format(warning_string))
        if slices == None:
            print("WARNING: Since no slices were provided, "
                  "all z-slices from {} "
                  "will be displayed.".format(warning_string))
        if frames == None:
            print("WARNING: Since no timepoints were provided, "
                  "all timepoints from {} "
                  "will be displayed.".format(warning_string))

        all_images_by_pre_identity = {}

        img_ranges = {}

        identity_val_map = {}

        for img_nb, file_path in enumerate(self.panel_file_paths):

            file_name = os.path.basename(file_path)

            if (len(self.all_panel_imgs) > 1) & (file_name.find(".csv") != -1):
                raise Exception("The data file '{}' can only be used "
                                "if a single file is provided "
                                "for the panel.".format(file_name))

            data_dict, img_width, img_height = self._get_image_properties(file_path)

            raw_img = self.all_panel_imgs[img_nb]

            raw_img = self._move_xy_axes_in_img_to_last_dimensions(raw_img,
                                                              img_width,
                                                              img_height)

            # names of dimensions in ImageJ image description
            dimensions = ["image", "frames", "slices", "channels"]
            map_for_dim = {}
            map_for_dim["image"] = "images"
            map_for_dim["frames"] = "frames"
            map_for_dim["slices"] = "slices"
            map_for_dim["channels"] = "channels"
            # sort dimensions according to order in map
            dimensions.sort(key=lambda dimension: self.map[map_for_dim[dimension]])

            # get the number of frames (timepoints), (z) slices and channels
            # of current image, as well as order of the dimensions
            dimension_dict = {}
            dimension_order_in_props = []

            # for non hyperstack images, the dimension present might
            # not be annotated correctly from imageJ
            #  (the standard for one dimension is slices)
            # therefore prevent frames being mistaken for slices
            # check if only "slices" and NOT "frames" are in data_dict
            # but frames are defined and slices
            #  are not defined when showing images
            if ("frames" not in data_dict) & ("slices" in data_dict):
                if (type(slices) == type(None)) & (type(frames) != type(None)):
                    # rewrite data_dict with keys slices rewritten as frames
                    data_dict = {("frames" if (k == "slices")
                                  else k):v for k,v in data_dict.items()}

            for dimension, value in data_dict.items():
                if dimension in dimensions:
                    dimension_order_in_props.append(dimension)
                    dimension_dict[dimension] = value

            dimension_order_in_props.reverse()

            # dict to keep track of position of image in hyperstack
            current_dimension = {}
            for dimension in dimension_order_in_props:
                current_dimension[dimension] = 0

            # dict to keep track of identity of image after extraction
            # might be different from position in hyperstack
            # since order of category values can be defined as not incremently
            # will be implemented as mapping
            # since actual category values need to be kept
            #  (e.g. to know from which frame point a frame comes)
            current_identity = {}
            for dimension in dimension_order_in_props:
                current_identity[dimension] = 0

            dimension_vals_to_include = {}
            for dimension in dimensions:
                # check if dimension is in current image
                # dimension_dict has all dimensions of current image
                # from imageJ description
                if dimension in dimension_dict:
                    vals_to_include = locals()[dimension]
                    if vals_to_include == None:
                        vals_to_include = range(0,int(dimension_dict[dimension]))
                    dimension_vals_to_include[dimension] = vals_to_include

            # check if the current image actually is
            #  only one image and not a multi-tiff

            if len(dimension_order_in_props) == 0:
                # first pre_identity is constructed without zoom and image_sub
                # these properties will be added later
                #  (they cannot be inferred from the image directly)
                # map object that is given to the function is a basic map object
                simple_inv_map = {v:k for k,v in basic_map.items()}
                pre_identity = [0 for _ in simple_inv_map]
                for dim, cat_str in simple_inv_map.items():
                    if cat_str == "images":
                        identity_val = img_nb
                    else:
                        identity_val = 0
                    pre_identity[dim] = identity_val
                raw_img = self._expand_img_dimensions(raw_img)
                raw_img = np.expand_dims(raw_img, 0)
                all_images_by_pre_identity[tuple(pre_identity)] = raw_img
            else:

                # recursively get all images from all dimensions
                # in one dict with the identity as key

                # add to exclude images not in channels, slices, timepoints
                dimension_nb = 0

                (all_images_by_pre_identity,
                 identity_val_map) = self._get_images_from_dimension(raw_img,
                                                                all_images_by_pre_identity,
                                                                dimension_nb,
                                                                current_dimension,
                                                                current_identity,
                                                                identity_val_map,
                                                                dimensions,
                                                                dimension_dict,
                                                                dimension_order_in_props,
                                                                dimension_vals_to_include,
                                                                basic_map,
                                                                img_nb)

            ranges = self._extract_img_ranges_from_file(file_path)
            img_ranges[img_nb] = ranges

        return all_images_by_pre_identity, img_ranges, identity_val_map


    def _get_images_from_dimension(self, raw_multi_dimension_img,
                                  images_by_pre_identity,
                                  dimension_nb, current_dimension,
                                    current_identity,
                                    identity_val_map,
                                  dimensions, dimension_dict,
                                  dimension_order_in_props,
                                  dimensions_vals_to_include,
                                  basic_map, img_nb):
        """
        Recursively go through all dimensions and get image at respective
        position in image stack (raw_multi_dimension_img).
        """
        dimension = dimension_order_in_props[dimension_nb]
        # iterate through each dimension
        nb_of_imgs_in_dim = int(dimension_dict[dimension])
        all_imgs_in_dim = list(range(0,nb_of_imgs_in_dim))

        # get all values that should be included for current dimension
        vals_to_include = dimensions_vals_to_include[dimension]

        # go through each value that should be included
        for pre_identity_val, dim_val in enumerate(vals_to_include):
            # check if current value exists in dimension
            dim_val_in_image = False
            #  if the dim val is a string,
            #  then  a composite might be defined
            #  check for composite image (ints in string separated by "-")
            if (type(dim_val) == str):
                # split dim_val by separator
                dim_val = tuple([int(val) for val in dim_val.split("-")])

                # prevent lists with just one element
                if len(dim_val) == 1:
                    dim_val = dim_val[0]

            # if dim_val is indeed a list now
            # check whether each channel from the list is in image
            if type(dim_val) in self.itertypes:
                dim_val_in_image = True
                for one_channel in dim_val:

                    if one_channel not in all_imgs_in_dim:
                        dim_val_in_image = False
                        break
            else:
                if dim_val in all_imgs_in_dim:
                    dim_val_in_image = True

            if not dim_val_in_image:
                continue

            # update the current dimension with value
            #  for position in hyperstack
            current_dimension[dimension] = dim_val
            # update the current pre identity value
            current_identity[dimension] = pre_identity_val
            # if there is still one more dimension to go down into,
            # recursively move into that dimension
            if dimension_nb < ( len(dimension_order_in_props) - 1):
                new_dimension_nb = dimension_nb +  1
                (images_by_pre_identity,
                 identity_val_map) = self._get_images_from_dimension(raw_multi_dimension_img,
                                                                 images_by_pre_identity,
                                                                 new_dimension_nb,
                                                                 current_dimension,
                                                                 current_identity,
                                                                 identity_val_map,
                                                                 dimensions,
                                                                 dimension_dict,
                                                                 dimension_order_in_props,
                                                                 dimensions_vals_to_include,
                                                                    basic_map,
                                                                 img_nb)
            else:
                # if there is no further dimension to go down into,
                # save image with current dimension with the order
                # defined by the map dict for the identity as key
                pre_identity = []
                for dim_identity in dimensions:
                    if dim_identity in current_dimension:
                        dim_val = current_dimension[dim_identity]
                        pre_identity.append(dim_val)
                        # mapped identity contains the newly ordered
                        # category values, defined by the order
                        # category values are in list supplied to
                        # show_images (e.g. in "channels")
                        mapped_identity_val = current_identity[dim_identity]
                    else:
                        if dim_identity == "image":
                            pre_identity.append(img_nb)
                            mapped_identity_val = img_nb
                        else:
                            # add a starting value for other dimensions
                            # (e.g. zoom or _sub categories)
                            pre_identity.append(0)
                            mapped_identity_val = 0
                    if dim_identity not in identity_val_map:
                        identity_val_map[dim_identity] = {}
                    # map current pre_identity val to mapped_identity_val
                    # for current dimension
                    identity_val_map[dim_identity][pre_identity[-1]] = mapped_identity_val

                # if there are multiple dim vals
                # then this is an composite, for which multiple images
                # have to be concatanated
                all_pre_identities = [pre_identity]

                # since only one dimension can be used for composite
                # keep track that this is the case
                composite_dimension = np.nan

                # create list of pre_identities corresponding to all
                # images which are compositeed
                for dimension_nb, dim_identity in enumerate(dimensions):

                    dim_val = current_dimension.get(dim_identity, np.nan)

                    # only create list of all pre identities
                    # if dimension actually contains multiple values
                    if (type(dim_val) not in self.itertypes):
                        continue

                    # if another dimension already is composite
                    # then prompt error
                    if not np.isnan(composite_dimension):
                        error_msg = ("composites can be defined "
                                     "in only one category. "
                                     "However, composites are defined"
                                     " for categories '{}' and '{}'"
                                     "".format(self.inv_map[dimension_nb],
                                        self.inv_map[composite_dimension]))
                        raise ValueError(error_msg)

                    composite_dimension = dimension_nb

                    # create list with as many pre_identities as there
                    # are images compositeed, where each pre_identity
                    # differs only in the dimension with composite
                    all_pre_identities *= len(dim_val)
                    # make independent objects of each pre_identity
                    # otherwise they point to the same object
                    # and thus cannot be changed independently
                    all_pre_identities = [list(pre_identity)
                                          for pre_identity in all_pre_identities]

                    # change category value from tuple
                    # to one of the tuple values for each pre_identity
                    for dim_val_nb, one_dim_val in enumerate(dim_val):
                        all_pre_identities[dim_val_nb][dimension_nb] = one_dim_val

                # create concatanated image for composites
                # with one image for each composite value
                # save this multi image then
                # under the pre_identity with the list
                # and under mapped identity with the position of the composite
                # compared to other values in that category

                # get all images for composite
                all_imgs = []

                for sub_pre_identity in all_pre_identities:
                    img = None
                    #  get image of current dimension

                    for dim_in_order in dimension_order_in_props:
                        idx_in_pre_identity = basic_map[dim_in_order]
                        if type(img) == type(None):
                            img = raw_multi_dimension_img[sub_pre_identity[idx_in_pre_identity]]
                        else:
                            img = img[sub_pre_identity[idx_in_pre_identity]]
                    # fill dimension up to 3 to have unified dimensions
                    # also with RGB images
                    # this makes referencing the correct dimension easier
                    img = self._expand_img_dimensions(img, target_dim=3)
                    # add first dimension as dimension on which to concatanate
                    img = np.expand_dims(img,0)
                    all_imgs.append(img)

                pre_identity = tuple(pre_identity)
                # create numpy array
                # from list of images
                all_imgs = np.concatenate(all_imgs, axis=0)

                images_by_pre_identity[pre_identity] = all_imgs
                
        return images_by_pre_identity, identity_val_map




    def _get_img_dict_by_pre_identity(self, inv_map):

        # think about defining factory function for each category
        # and then cycle through factory functions to get all details of image
        # would make it more easily adaptable for multiple dimensions

        # get max widths and heights for channels and frames,
        #  each for the respective image number only
        # get all images and the corresponding channel and frame
        # give each separate base image file a unique number
        # save all in the dict all_images
        base_files = {}
        all_images_by_pre_identity = {}
        img_ranges = {}

        for img_nb, file_path in enumerate(self.panel_file_paths):

            file_name = os.path.basename(file_path)
            if ((len(self.panel_file_paths) > 1) & 
                    (file_name.find(".csv") != -1)):
                raise Exception("The data file '{}' can only be used if a "
                                "single file is provided "
                                "for the panel.".format(file_name))

            details = {}
            frame_result = self.dim_val_finder["frames"].search(file_name)
            channel_result = self.dim_val_finder["channels"].search(file_name)
            slice_result = self.dim_val_finder["slices"].search(file_name)
            if frame_result:
                frame_string = frame_result[0]
                frame = int(frame_result[1])
            else:
                frame_string = ""
                frame = 0
            if channel_result:
                channel_string = channel_result[0]
                # FUSE CHANNELS of multi channel image
                # into one expression of channel without the "-" inbetween channels
                channel = channel_result[1]
            else:
                channel_string = ""
                channel = "0"
            if slice_result:
                slice_string = slice_result[0]
                slice = slice_result[1]
            else:
                slice_string = ""
                slice = "0"
            # get the basic file name without channel and frame information
            base_file_name = file_name.replace(frame_string,"").replace(channel_string,"")
            if base_file_name not in base_files:
                if len(base_files) == 0:
                    img_nb = 0
                else:
                    img_nb = max(base_files.values())
                base_files[base_file_name] = img_nb
            else:
                img_nb = base_files[base_file_name]
            details["images"] = img_nb
            details["frames"] = frame
            details["channels"] = channel
            details["slices"] = slice

            # construct identity in order defined in map dict
            pre_identity = []
            for dimension_nb in range(0,len(inv_map)):
                # check if name from inv_map is in details
                # would not be for additional criteria
                #  that were supplied by the user
                # to the upstream function show_images
                if inv_map[dimension_nb] in details:
                    pre_identity.append(details[inv_map[dimension_nb]])
            pre_identity = tuple(pre_identity)

            image = self.all_panel_imgs[img_nb]

            # increase dimensionality of non-RGB or 2D image
            # to 2D RGB image by adding dimensions
            image = self._expand_img_dimensions(image)

            # add dimension for composite as first dimension
            image = np.expand_dims(image, axis=0)

            all_images_by_pre_identity[pre_identity] = image

            ranges = self._extract_img_ranges_from_file(file_path)
            img_ranges[img_nb] = ranges

        return all_images_by_pre_identity, img_ranges

    def _get_basic_map(self):
        """
        Get basic map without sub categories and zoom.
        """
        map_no_sub = {}
        for cat in self.map.keys():
            if (cat.find("_sub") == -1) & (cat.find("zooms") == -1):
                map_no_sub[cat] = len(map_no_sub)
        return map_no_sub

    def _add_categories_to_pre_identities(self, all_images_by_pre_identity,
                                       sub_category_map):
        # remap pre_identity of images by adding values of respective
        #  category to the identity
        # do everything in the order that is defined in the ordered map

        # create map without the sub categories, this inv_map
        #  will have the real order of categories in pre_identity
        # _sub categories were left out before since they are not
        #  infered from the image itself
        map_no_sub = self._get_basic_map()

        new_all_images_by_pre_identity = {}
        for pre_identity, image in all_images_by_pre_identity.items():
            new_pre_identity, _ = self._add_categories_to_identity(pre_identity,
                                                               map_no_sub,
                                                               sub_category_map)


            new_all_images_by_pre_identity[tuple(new_pre_identity)] = image

        return new_all_images_by_pre_identity


    def _add_categories_to_identity(self, identity,
                                   map_no_sub,
                                   sub_category_map):
        """
        Returns identity with added categories and a dict with
        lisst of positions of the unchanged category values
        in the identity before and after categories are added
        (those are different because the identity from before
        does not take into account the user-defined order)
        """
        # map to identity since initial sorting mapping was already done
        new_identity = []

        # track the position
        pos_unchanged_categories_before = []
        pos_unchanged_categories_after = []
        # go through each category in sorted map
        for category_nb, category in enumerate(self.map.keys()):
            # check if category is a sub category
            if category in sub_category_map:
                # for a sub category first get the identity val
                #  of the original category
                no_sub_category = category.replace("_sub","")
                no_sub_identity_val = identity[map_no_sub[no_sub_category]]
                # and then get identity val by using the identity val
                #  of the original category
                identity_val = sub_category_map[category][no_sub_identity_val]
            elif category in map_no_sub:
                identity_val = identity[map_no_sub[category]]
                pos_unchanged_categories_before.append(category_nb)
                pos_unchanged_categories_after.append(category_nb)
            else:
                # if it is not a sub category and
                # if it was not part of the categories extracted from the image
                # set it to 0. It will be changed later then
                identity_val = 0

            pos_unchanged_categories = {}
            pos_unchanged_categories["before"] = pos_unchanged_categories_before
            pos_unchanged_categories["after"] = pos_unchanged_categories_after

            new_identity.append(identity_val)
        return new_identity, pos_unchanged_categories


    def _get_category_maps(self, all_images_by_pre_identity,
                           inv_map, sorters, reassign_new_categories,
                           pre_identity_val_map):
        """
        create maps for frame and channel
        map lowest to 0 and highest to number of values minus 1
        otherwise the absolute number in the filename (especially of the frame!)
        would mess up the max_row and max_column attributes
        which will be derived from identity
        and therefore the frame and channel in nb in the file name
        """
        all_identities = all_images_by_pre_identity.keys()
        pre_identity_value_lists = self._get_all_category_vals(all_identities,
                                                              inv_map)

        # sort lists of each category
        # to determine which values get the lower numbers
        #  (starting from 0) and which the higher numbers
        for category in pre_identity_value_lists:
            if category in sorters:
                sorter = sorters[category]
            else:
                sorter = lambda x: x
            pre_identity_value_lists[category].sort(key=sorter)

        maps = {}
        # identity val is incrementing number
        # and its connection to the real identity is saved in maps

        for category in pre_identity_value_lists:
            for identity_val, pre_identity_val in enumerate(set(pre_identity_value_lists[category])):
                if not category in maps:
                    maps[category] = {}
                # check if the current category is in reassignment dict
                # then remap values not to identity_val but to value in reassignment dict
                if category in reassign_new_categories:
                    maps[category][pre_identity_val] = reassign_new_categories[category][pre_identity_val]
                else:
                    # remap pre identity val according to the order that
                    # the values were supplied by the user
                    # if mapping was not used (since no order was defined
                    # by user or cant be defined for category)
                    # then go back to default of incrementally sorted values
                    used_mapped_for_identity_val = False
                    if category in pre_identity_val_map:
                        if pre_identity_val in pre_identity_val_map[category]:
                            maps[category][pre_identity_val] = pre_identity_val_map[category][pre_identity_val]
                            used_mapped_for_identity_val = True

                    if not used_mapped_for_identity_val:
                        maps[category][pre_identity_val] = identity_val

        return maps

    def _sort_category_vals_key(self, value):
        if type(value) in self.itertypes:
            return max(value) + 0.5
        elif type(value) == str:
            values = value.split("-")
            values = [int(value) for value in values]
            return max(values) + 0.5
        else:
            return value

    def _get_all_category_vals(self, all_identities, inv_map):
        """
        get list of all values in each category
        :param all_identities: list of all identities (tuples)
        :param inv_map: dict mapping int of category in identity to
                        category name (e.g. "channel")
        """
        identity_value_lists = {}

        for pre_identity in all_identities:

            for identity_nb, pre_identity_val in enumerate(pre_identity):
                category = inv_map[identity_nb]
                if not category in identity_value_lists:
                    identity_value_lists[category] = []
                identity_value_lists[category].append(pre_identity_val)

        for category in identity_value_lists.keys():
            cat_vals = identity_value_lists[category]
            identity_value_lists[category] = list(set(cat_vals))
            # with key make sure that composites are also sorted
            # they are sorted based on their highest number
            identity_value_lists[category].sort(key=self._sort_category_vals_key)

        return identity_value_lists

    def _iterable_to_dict(self, iterable):
        """
        zip iterable so that every value at an odd position will be a key and
        every value at an even position will be a value
        """
        keys = []
        values = []
        id = 0
        while id < len(iterable):
            keys.append(iterable[id])
            values.append(iterable[id+1])
            id += 2
        return dict(zip(keys, values))

    def _get_identities_matching_dict_criteria(self, identity_array, dict,
                                              group_identity = None,
                                              pre_identity_transform=True):
        matching = []
        for identity in identity_array:
            if pre_identity_transform:
                pre_identity = self._get_pre_identity(identity)
            else:
                pre_identity = identity
            matches = self._check_if_identity_matches_dict_criteria(pre_identity,
                                                                   dict,
                                                                   group_identity)
            if matches:
                matching.append(identity)
        return matching

    def _get_similar_categories_of_identities(self, identity_list):
        # get all values of each identity
        grouped_cat_values = self._get_grouped_cat_values_from_identity_list(identity_list)
        # get categories which only have one value (categories similar between all images)
        similar_cats = set([cat_nb
                            for cat_nb, cat_values in enumerate(grouped_cat_values)
                            if (len(cat_values) == 1)])
        return similar_cats

    def _get_group_identity(self, identity):
        image_nb = identity[self.map["images"]]
        if "images_sub" in self.map:
            image_sub_nb = identity[self.map["images_sub"]]
        else:
            image_sub_nb = 0

        if "frames_sub" in self.map:
            frame_sub_nb = identity[self.map["frames_sub"]]
        else:
            frame_sub_nb = 0
        return (image_nb, image_sub_nb, frame_sub_nb)


    def _check_if_identity_matches_dict_criteria(self, identity, criteria,
                                                group_identity = None):
        matches = True
        if group_identity != None:

            new_group_identity = self._get_group_identity(identity)
            if new_group_identity != group_identity:
                return False
        if criteria is None:
            return True
        for criterion_cat, criterion_val in criteria.items():
            # if a range was supplied, change to list
            if type(criterion_val) == type(range(1)):
                criterion_val = list(criterion_val)

            if type(criterion_val) in self.itertypes:
                if identity[self.map[criterion_cat]] not in criterion_val:
                    return False
            else:
                if criterion_val != identity[self.map[criterion_cat]]:
                    return False
        return matches


    def _identity_sorter(self, identity):
        """
        create value to incrementally sort a list of identities.
        Sort by incrementing the numbers at the different positions,
        giving higher priority to earlier positions.
        """
        evaluated = 0
        length = len(identity)
        for val_nb, val in enumerate(identity):
            evaluated += val_nb * 10 ** (length - val_nb)
        return evaluated


    def _get_categories_different_in_list_of_identities(self, identities):
        """
        Return cat that is different or empty list if none is different
        """
        different_categories = []
        prev_identity = None
        prev_differed_cat = None
        for identity in identities:
            if prev_identity == None:
                prev_identity = identity
            else:
                diff_cats = self._check_for_diff_in_identities(identity,
                                                              prev_identity)
                for diff_cat in diff_cats:
                    if diff_cat not in different_categories:
                        different_categories.append(diff_cat)
        return different_categories


    def _check_for_diff_in_identities(self, identity1, identity2):
        diffs = []
        for nb in range(len(identity1)):
            if identity1[nb] != identity2[nb]:
                diffs.append(nb)
        return diffs

    def _get_reposition_dict_for_mapping(self, all_images_by_identity,
                                        repositioning_map, simple_remapping):
        # How to remap images into rectangle
        #  if multidimensional identity matrices
        # have spots without images:
        # let user supply dict to say which criterions should be mapped
        # e.g. {("channel",1,"zoom",0): ("zoom",2)}
        #  means that channel 1 will be mapped to the same category as "zoom":2
        # both the key and the value can specify multiple categories and
        #  values to narrow the criteria
        # the categories it will me mapped to need to be
        # different keys in the dict must not point to
        #  the same element / identity!
        # values need to match identities that only differ in ONE category,
        # the different category will determine
        #  in which category the per key defined identities will be added before
        # otherwise positioning will not
        reposition_dict = {}
        remapped_categories = set()

        if repositioning_map == None:
            return reposition_dict, remapped_categories

        # check which identities match criteria defined by repositioning_map
        for target, goal in repositioning_map.items():
            # create dictionary from tuples looking like:
            # ("channel",1,"zoom",0), use string as key, nb as value
            target_dict = self._iterable_to_dict(target)
            goal_dict = self._iterable_to_dict(goal)

            targets = self._get_identities_matching_dict_criteria(all_images_by_identity.keys(),
                                                                 target_dict,
                                                                 pre_identity_transform=False)

            # group targets based on image and image_sub identity
            grouped_targets = {}
            if simple_remapping:
                grouped_targets = {(0,0,0):targets}
            else:

                for target in targets:

                    group_identity = self._get_group_identity(target)

                    if group_identity not in grouped_targets:
                        grouped_targets[group_identity] = []
                    grouped_targets[group_identity].append(target)

            for group_identity, targets in grouped_targets.items():

                goals = self._get_identities_matching_dict_criteria(all_images_by_identity.keys(),
                                                                   goal_dict,
                                                                   group_identity,
                                                                   pre_identity_transform=False)
                if len(goals) == 0:
                    print("WARNING: The defined categories {} for the target "
                          "to map images to did not match any "
                          "elements.".format(", ".join(str(one_goal)
                                                       for one_goal in goal)))
                    print("Goals will be found without using the group_identity "
                          "now. This might lead to wrong goals found.")
                    # if it didnt work while using the group_identity,
                    #  try again without group identitiy
                    # this will lead to more matches
                    goals = self._get_identities_matching_dict_criteria(all_images_by_identity.keys(),
                                                                       goal_dict,
                                                                       None,
                                                                       pre_identity_transform=False)

                # check which is the category for all goals that is different
                # this category will be used to position the targets with them
                categories_different_in_goals = self._get_categories_different_in_list_of_identities(goals)

                if len(categories_different_in_goals) > 1:
                    raise ValueError("The defined categories {} for the target "
                                     "to map images to lead to identities "
                                     "differeing in more than one category"
                                     ".".format(", ".join(str(one_goal)
                                                          for one_goal in goal)))

                category_differing = categories_different_in_goals[0]

                # add the differing category as the category in which remapping will be done
                remapped_categories.add(category_differing)

                # create map of targets to new_targets
                # in which the category different will be changed into incrementing values starting at 0
                targets.sort(key=self._identity_sorter)

                for target_nb, target in enumerate(targets):
                    # baseline new target is like any identity in goals
                    new_target = list(goals[0])
                    # but changed in the category different in goals
                    new_target[category_differing] = target_nb
                    reposition_dict[target] = tuple(new_target)

                # remap goals by adding the length of targets
                # to the differing category
                nb_of_targets = len(targets)
                for goal in goals:
                    new_goal = list(goal)
                    new_goal[category_differing] += nb_of_targets
                    reposition_dict[goal] = tuple(new_goal)
        return reposition_dict, remapped_categories

    def _get_dimension_combinations(self, focus, order_of_categories,
                                   cats_similar_for_all_images):
        """
        Get list of combination of categories two put in columns and rows.
        To enlarge an image, two dimensions each defined by one category
        are needed. The first dimension will be the focus of the image grid
        (which is the dimension that is plotted alone on one axis)
        the second dimension will be the first dimension by which images are
        split along the other dimension if focus is already defined by user,
        use this as first dimension otherwise try each focus dimension.
        :param focus: string, name of category that should be put in one
                        dimension (row or columns) by itself
        :param order_of_categoriers: list of strings, names of categories that
                                    should be put in the other dimension
        :param cats_similar_for_all_images: list of ints; numbers of categories
                                            which are the same for all images
        """

        flexible_order_not_similar_for_imgs = (set(order_of_categories["flexible"]) -
                                               cats_similar_for_all_images)

        # should only be focus IF focus is defined
        # if focus is not defined, use first value of "fixed" map of categories
        # if there is no fixed part, try ALL category not similar for all images
        # if ALL categories are the same for all images, use ANY category
        if not self._is_none(focus):
            first_dimensions = [focus]
        elif len(order_of_categories["fixed"]) > 0:
            first_dimensions = [order_of_categories["fixed"][0]]
        elif len(flexible_order_not_similar_for_imgs) > 0:
            first_dimensions = flexible_order_not_similar_for_imgs
        else:
            first_dimensions = [order_of_categories["flexible"][0]]
        second_dimensions = []
        # second dimensions should be earliest fixed dimension
        # which is not in first_dimensions
        if len(order_of_categories["fixed"]) > 0:
            for category in order_of_categories["fixed"]:
                if category not in first_dimensions:
                    second_dimensions = [category]
                    break

        if len(second_dimensions) == 0:
            if len(flexible_order_not_similar_for_imgs) > 0:
                second_dimensions = flexible_order_not_similar_for_imgs
            else:
                for category in order_of_categories:
                    if category not in first_dimensions:
                        second_dimensions = [category]
                        break

        #  combine all first and second dimensions that should be tried
        dimension_combinations = []
        for first_dimension in first_dimensions:
            for second_dimension in second_dimensions:
                #  combinations should include two different dimensions
                if first_dimension != second_dimension:
                    dimension_combinations.append((first_dimension, second_dimension))

        return dimension_combinations

    def _get_size_increase_cat_for_enlarged_image_site(self, show_focus_in,
                                                   enlarged_image_site):
        """
        Get variation number to display enlarged image on specific site
        or try out both sites. This will define which category determines
        the size_factor and which category images will be shifted in to
        make space for enlarged image.
        :param show_focus_in: string, "rows" or "columns
        :param enlarged_image_site: string, "left", "top" or None
                                    if it is None, then both variations
                                    will be tried
        """
        # set variation number so that the enlarged image is left or top
        if show_focus_in == "rows":
            if enlarged_image_site == "left":
                size_increase_dim_nb = 0
                size_increase_cat_is_focus = True
            elif enlarged_image_site == "top":
                size_increase_dim_nb = 1
                size_increase_cat_is_focus = False

        elif (show_focus_in.find("col") != -1):
            if enlarged_image_site == "left":
                size_increase_dim_nb = 1
                size_increase_cat_is_focus = False
            elif enlarged_image_site == "top":
                size_increase_dim_nb = 0
                size_increase_cat_is_focus = True

        else:
            if not self._is_none(enlarged_image_site):
                raise ValueError("Parameter 'show_focus_in' can only"
                                 "be 'rows' or contain 'col'.")

        return size_increase_dim_nb, size_increase_cat_is_focus

    def _resort_order_of_categories_from_primer(self, order_primer,
                                               order_of_categories):
        new_order_of_categories = order_primer
        for category in [*order_of_categories["fixed"],
                         *order_of_categories["flexible"]]:
            if category not in new_order_of_categories:
                new_order_of_categories.append(category)
        return new_order_of_categories


    def _auto_enlarge_images(self, images_enlarge,
                            first_dimension, second_dimension,
                            size_increase_dim_nb,
                            size_increase_cat_is_focus, order_of_categories,
                            all_images_by_identity,
                            show_focus_in):
        """
        size_facot_dict will be checked for matches on pre_identities
        However, the algorithm will try to infer the similarity
        of the images based on the mapped identity
        """

        size_increase_cat = [first_dimension, second_dimension][size_increase_dim_nb]
        size_increase_cat = self.map[size_increase_cat]

        # other_dim is the other category needed
        #  for enlarging images
        # which determines in the direction
        #  of which category images will be pushed
        other_dim = [first_dimension, second_dimension][size_increase_dim_nb - 1]
        other_dim = self.map[other_dim]

        new_order_of_categories = [second_dimension]
        #  if more than one order of categories was supplied
        #  append the remaining order to the new order to try out
        if not self._is_none(order_of_categories):
            if len(order_of_categories) > 1:
                new_order_of_categories.extend(order_of_categories[1:])

        order_of_categories = new_order_of_categories

        (nb_of_cat_vals,
         min_cat_vals) = self._get_nb_and_min_cat_vals(all_images_by_identity,
                                                       images_enlarge)

        size_factor = nb_of_cat_vals[size_increase_cat]

        # if focus is already defined, never change it
        # the same is true for order_of_categories
        # for creating combinations either the first or the second must include focus

        # dimension which defines size increase is dimension
        # which is NOT pushed for other images
        # to accompany new size of image
        # with the current implementation increased size only works
        # in non focus dimension (since there are otherwise multiple in


        # HOWEVER, some frames the image that should be enlarged
        # contributes to the number of values in that dimension
        # therefore count the number of different values in focus
        # while ignoring all images that should be enlarged

        # for trying dimensions for enlarging image
        # also use these dimensions for making image grids
        # then compare for ALL possible solutions which one uses space
        # most efficiently

        # plotting focus in rows or columns should not make a difference here
        (category_change,
         new_cat_val) = self._get_changed_category_and_value(all_images_by_identity,
                                                            images_enlarge,
                                                            size_increase_cat,
                                                            other_dim,
                                                            order_of_categories,
                                                            size_factor)
        # if a category that was changed was found
        # but no category value in which should be changed
        # that indicates that it would not be cleanly possible to enlarge image
        # therefore, don't use this combination

        if (not np.isnan(category_change)) & (np.isnan(new_cat_val)):
            return (None, None, None, None)

        #  move each size_factor and all identities matching it except in other_dim
        (increase_size_map,
         place_holder_identities,
         other_dim_dict_of_enlarged_images,
         size_factors_for_identities,
         place_holder_identity_map) = self._make_space_for_enlarged_images(images_enlarge,
                                                                           size_factor,
                                                                           size_increase_cat,
                                                                           other_dim,
                                                                           min_cat_vals,
                                                                           category_change,
                                                                            new_cat_val,
                                                                            show_focus_in,
                                                                            size_increase_cat_is_focus,
                                                                            all_images_by_identity)

        #  apply mapping right away to allow the next mapping to be based on that
        all_images_by_identity = self._apply_mapping(all_images_by_identity,
                                                    increase_size_map)

        inv_increase_size_map = {v: k for k, v in increase_size_map.items()}

        images_cat_nb = self.map["images"]
        place_holder_pre_identity = tuple([-1
                                           if cat_nb != images_cat_nb
                                           else images_enlarge[0][images_cat_nb]
                                           for cat_nb, _ in
                                           enumerate(range(len(images_enlarge[0])))])

        for place_holder_identity, image in place_holder_identities.items():
            #  add place_holder_identities to inv_map
            #  to map them to a clearly identifieable identitiy
            #  when converting the identity to pre_identity
            inv_increase_size_map[place_holder_identity] = place_holder_pre_identity
            all_images_by_identity[place_holder_identity] = np.expand_dims(image[0], axis=0)

        return (all_images_by_identity, inv_increase_size_map,
               size_factors_for_identities,
               place_holder_identity_map)


    def _get_nb_and_min_cat_vals(self, all_images_by_identity, images_enlarge):
        """
        Get the number of category values and the minimum category value
        for all identities except the
        """
        identity_without_enlarged_image = set(list(all_images_by_identity.keys()))
        images_enlarge_unique = set([tuple(image_enlarge)
                                     for image_enlarge in images_enlarge])
        identity_without_enlarged_image -= images_enlarge_unique

        nb_of_cat_vals = self._get_nb_of_category_vals(identity_without_enlarged_image)

        # get minimum cat vals for images without enlarged image
        # as start point for positioning after enlarging image
        min_cat_vals = np.array(list(identity_without_enlarged_image)).min(axis=0)

        return nb_of_cat_vals, min_cat_vals


    def _get_nb_of_category_vals(self, all_image_identities):
        """
        Get number of values in each category (e.g. "channel")
        :param all_image_identities: list of tuples; tuples are identities
                                    which each value corresponding to the value
                                    in the respective category
        """
        all_identities = []
        for new_identity in all_image_identities:
            all_identities.append(new_identity)
        all_identities = np.array(all_identities)

        # transpose all identities to have all values of one category
        # in one row
        all_identities = all_identities.T
        nb_of_category_vals = []
        for category_values in all_identities:
            nb_of_category_vals.append(len(np.unique(category_values)))
        nb_of_category_vals = np.array(nb_of_category_vals)

        return nb_of_category_vals

    def _get_changed_category_and_value(self, all_images_by_identity,
                                        images_enlarge,
                                        size_increase_cat, other_dim,
                                        order_of_categories, size_factor
                                        ):
        """
        Get the number of the category which needs to be changed in enlarged
        image in order to put it next to not enlarged images.
        Example:
        This can become necessary e.g. if two zooms are shown
        for channel 0 for the first three timeframes
        and the first timeframe of channel 1 (without zooms) is shown.
        Focus could be "zooms" or "frames" and then channels would be a category
        by which images are separated additionally.
        The image of the first timeframe of channel 1 would be enlarged
        to form a rectangle together with the zoomed images. However, since
        it is also from a different channel, it would not be shown next to it.
        """
        order_of_categories = [self.map[cat] for cat in order_of_categories]

        image_to_be_enlarged = images_enlarge[0]
        category_change = np.nan
        new_cat_val = np.nan

        size_increase_vals = {}
        new_cat_vals = {}
        #  if not, then the values for a category have to be changed
        #  for the to be enlarged image to be shown next to not enlarged images

        # since tested identity and the identity of the to be enlarged image
        # are different in more categories
        # than size_increase_cat and other_dim
        # find the category which needs to be changed to put the
        # enlarged image along the same axis as the other images
        # based on which the size was increase
        for identity in all_images_by_identity.keys():

            same = self._check_if_identities_are_the_same_except_categories(
                identity,
                image_to_be_enlarged,
                [])

            if same:
                continue

            #  check whether any identity that should not be enlarged
            #  has similar category values except in
            #  size_increase_cat and other_dim
            cats_can_be_different = [size_increase_cat, other_dim]
            similar = self._check_if_identities_are_the_same_except_categories(
                identity,
                image_to_be_enlarged,
                cats_can_be_different)
            if similar:
                continue

            # The category_change is the category different
            # from the images based on which the image was enlarged,
            # for each category save all size_increase_cat values
            # to find the category which has the same number of different
            # values in the size_increase as size_factor

            # create a set of all categories
            all_categories = set(order_of_categories)
            # remove categories which already can be different
            other_categories = all_categories - set(cats_can_be_different)

            # order categories based on order_of_categories
            included_order_of_categories = []
            for cat in order_of_categories:
                if cat in other_categories:
                    included_order_of_categories.append(cat)

            for category in included_order_of_categories:
                test_cats_different = copy.copy(cats_can_be_different)
                test_cats_different.append(category)
                similar = self._check_if_identities_are_the_same_except_categories(
                    identity,
                    image_to_be_enlarged,
                    test_cats_different)
                if not similar:
                    continue

                if category not in size_increase_vals:
                    size_increase_vals[category] = []

                size_increase_vals[category].append(identity[size_increase_cat])

                if category not in new_cat_vals:
                    new_cat_vals[category] = []

                new_cat_vals[category].append(identity[category])

        # check for which categories there are as many different values
        # as the image is increased in size
        # find the category for this that is earliest
        # in order_of_categories and save the corresponding
        # value of the tested identity in that category
        for category in included_order_of_categories:
            if category not in size_increase_vals:
                continue
            cat_vals = size_increase_vals[category]
            if len(np.unique(cat_vals)) != size_factor:
                continue
            category_change = category
            new_cat_vals_one_cat = np.unique(new_cat_vals[category])
            # there should only be one new cat val for the correct
            # category
            if len(new_cat_vals_one_cat) != 1:
                continue
            new_cat_val = new_cat_vals_one_cat[0]
            break

        return category_change, new_cat_val

    def _make_space_for_enlarged_images(self, images_enlarge, size_factor,
                                        size_increase_cat, other_dim,
                                        min_cat_vals, category_change,
                                        new_cat_val, show_focus_in,
                                        size_increase_cat_is_focus,
                                        all_images_by_identity):
        """
        Shift category values for images to make space for enlarged images.
        Also add place holder images on top of enlarged image
        (will be removed later) to mark the space occupied by the enlarged
        image.
        :param other_dim: int, number of category used for making space for
                            enlarged image. Different from category used to
                            determine how much the image should be enlarged
                            (size factor).
        :param category_change: int, of category which has to be changed in
                                enlarged image in order to put it next to not
                                enlarged image
        :param new_cat_val: int, value that the category be changed
                            (category_change) has to be changed into
        """
        increase_size_map = {}
        size_factors_for_identities = {}
        place_holder_identities = {}
        other_dim_dict_of_enlarged_images = {}
        place_holder_identity_map = {}

        nb_elements_to_add = size_factor - 1
        for image_to_enlarge in images_enlarge:

            image_to_enlarge = tuple(image_to_enlarge)
            #  new_increase_size_map = {}

            image_to_enlarge_pre_identity = self._get_pre_identity(image_to_enlarge)
            # save information on how much an image with a specific identity was enlarged
            size_factors_for_identities[image_to_enlarge_pre_identity] = size_factor

            other_dim_dict_of_enlarged_images[image_to_enlarge_pre_identity] = other_dim

            all_images_to_remap = set()
            all_images_to_remap.add(image_to_enlarge)

            for identity in all_images_by_identity.keys():
                dims_allowed_different = [size_increase_cat,
                                          other_dim,
                                          category_change]
                add_identity = self._check_if_identities_are_the_same_except_categories(identity,
                                                                        image_to_enlarge,
                                                                        dims_allowed_different)

                if add_identity:
                    all_images_to_remap.add(identity)

            increase_size_map = self._shift_cat_values_for_enlarged_image(all_images_to_remap,
                                                                          other_dim,
                                                                          nb_elements_to_add,
                                                                          min_cat_vals,
                                                                          increase_size_map)
            #  create set to identify added identities / images
            #  save place holder identities to add after applying remapping
            #  at the end remove the images from the set again

            place_holder_image = all_images_by_identity[image_to_enlarge]

            # position of image in grid of two dimensions
            # should always be lower left
            # since size of image will be increased towards top-right
            # lower left position is where image to enlarge should be moved to
            # first value in position is size_increase_cat, second is other_dim
            lower_left_pos = self._get_lower_left_position_in_grid(show_focus_in,
                                         size_increase_cat_is_focus,
                                         nb_elements_to_add,
                                         min_cat_vals, size_increase_cat)

            all_place_holder_identities = []
            for cat1_value in range(min_cat_vals[size_increase_cat],
                                    nb_elements_to_add +
                                    min_cat_vals[size_increase_cat] + 1):

                for cat2_value in range(0, nb_elements_to_add + 1):
                    #  if cat2_value == 0:
                    place_holder_identity = list(image_to_enlarge)
                    place_holder_identity[size_increase_cat] = cat1_value
                    place_holder_identity[other_dim] = cat2_value
                    # change category value that needs to be changed
                    # to put images next to one another
                    # to new value
                    if not np.isnan(category_change):
                        place_holder_identity[category_change] = new_cat_val

                    if (cat1_value, cat2_value) != lower_left_pos:
                        place_holder_identities[tuple(place_holder_identity)] = place_holder_image
                        all_place_holder_identities.append(tuple(place_holder_identity))
                    else:
                        #  if (cat1_value, cat2_value) == lower_left_pos:
                        # remap original image to lower left position
                        increase_size_map[image_to_enlarge] = tuple(place_holder_identity)

            # go through all place_holder identities
            # and map them to the pre_identity
            # of the corresponding enlarged image
            enlarged_image_pre_identity = self._get_pre_identity(image_to_enlarge)
            for place_holder_identity in all_place_holder_identities:
                place_holder_identity_map[place_holder_identity] = enlarged_image_pre_identity

        return (increase_size_map,
                place_holder_identities,
                other_dim_dict_of_enlarged_images,
                size_factors_for_identities,
                place_holder_identity_map)


    def _shift_cat_values_for_enlarged_image(self, all_images_to_remap,
                                             other_dim, nb_elements_to_add,
                                             min_cat_vals, increase_size_map):
        """
        Shift values of category to make space for enlarged image.
        """
        #  add images along the axes of the similar category
        for image_to_remap in all_images_to_remap:
            remapped_image = list(image_to_remap)
            remapped_image[other_dim] += nb_elements_to_add
            # add 1 to value since if it starts at 0 but size increase is 2
            # it should move two spaces
            remapped_image[other_dim] += 1 - (min_cat_vals[other_dim])

            increase_size_map[image_to_remap] = tuple(remapped_image)
        return increase_size_map


    def _get_lower_left_position_in_grid(self, show_focus_in,
                                         size_increase_cat_is_focus,
                                         nb_elements_to_add,
                                         min_cat_vals,
                                         size_increase_cat):
        # there are 4 variants of how the enlarged image is positioned
        # for each position the lower left corner is defined differently
        if show_focus_in == "rows":
            if size_increase_cat_is_focus:

                lower_left_pos = (nb_elements_to_add +
                                  min_cat_vals[size_increase_cat] ,
                                  0)
                #  lower_left_pos = (nb_elements_to_add +1 , min_cat_vals[size_increase_cat] - 1)
            else:
                lower_left_pos = (min_cat_vals[size_increase_cat],
                                  nb_elements_to_add)
        else:
            if size_increase_cat_is_focus:
                lower_left_pos = (min_cat_vals[size_increase_cat],
                                  nb_elements_to_add)
            else:
                lower_left_pos = (nb_elements_to_add +
                                  min_cat_vals[size_increase_cat] ,
                                  0)
        return lower_left_pos


    def _get_nb_neighbors_from_identities(self, all_images_by_identity):
        # plot images in N-dimensional array
        #  with dimensions being image, frame, zoom etc.
        # get maximum nb of values for each dimension first to create array

        max_vals_of_dimension = self._get_max_values_of_dimensions(all_images_by_identity)
        # output of function is dictionary
        #  with names of cats as keys and max values as values
        max_vals_of_dimension = np.array([max_val + 1
                                          for max_val in
                                          max_vals_of_dimension.values()])

        identity_array = np.zeros(tuple(max_vals_of_dimension))

        # for each image put a 1 in the array at coordinates of it's identity
        for new_identity in all_images_by_identity.keys():
            identity_array[new_identity] = 1

        # now find images which have fewer other images directly adjacent
        #  (not diagonal)
        filter_shape = copy.copy(max_vals_of_dimension)
        filter_shape[:] = 3

        # get neighbors above and below midpoint
        nb_categories = len(filter_shape)
        # in each dimension the filter has three values
        # which means that the coordinates [1] * nb_categories
        # is the middle point
        # changing one dimension to 0 is one direct neighbor
        # convolve for each single category to get neighbors
        # for each single category, which will then be summed up.
        # Thereby it can be controlled that each category just leads to
        # an increase in neighbors of max. 1
        # making it possible to get the number of categories with neighbors
        # which is undirected
        neighbors_all_dim = []
        for category in range(nb_categories):
            filter_first_site = np.zeros((filter_shape))
            filter_slice = [1] * nb_categories
            filter_slice[category] = 0
            filter_first_site[tuple(filter_slice)] = 1
             # convolve array once with all adjacent images in each direction
            neighbors_first_site = ndimage.convolve(identity_array,
                                                    filter_first_site,
                                                    mode="constant")
            filter_second_site = np.zeros((filter_shape))
            filter_slice[category] = 2
            filter_second_site[tuple(filter_slice)] = 1
            neighbors_second_site = ndimage.convolve(identity_array,
                                                     filter_second_site,
                                                    mode="constant")
            neighbors_dim = np.maximum(neighbors_first_site,
                                       neighbors_second_site)
            # set number of neighbors in sub_category to 0
            # since they can be highly asymetrically defined, e.g. with gaps
            # making finding neighbors very difficult
            #

            # number of neighbors needs to be corrected for _sub categories
            # which have only one value in one of the _sub categories
            # but more than one in at least one other _sub category
            # since only one non_sub value for a _sub value means
            # that there were no neighbors in the non_sub category before
            # while there actually should have been some

            # check if category is sub_category
            category_name = self.inv_map[category]
            if category_name.find("_sub") != -1:
                neighbors_dim[:] = 0
                # get all _sub values and their corresponding non_sub values
                sub_values_dict = {}
                non_sub_category_name = category_name.replace("_sub", "")
                non_sub_category = self.map[non_sub_category_name]
                for identity in all_images_by_identity.keys():
                    sub_val = identity[category]
                    if sub_val not in sub_values_dict:
                        sub_values_dict[sub_val] = []
                    sub_values_dict[sub_val].append(identity[non_sub_category])
                # for each _sub value get how many non_sub values there are
                nb_for_sub_values = {key:len(np.unique(values))
                                     for key, values in sub_values_dict.items()}
                # if there is only one for at least one _sub value but
                # more than one for at least one other _sub value
                min_nb_for_sub_values = min(nb_for_sub_values.values())
                max_nb_for_sub_values = max(nb_for_sub_values.values())
                if (min_nb_for_sub_values == 1) & (max_nb_for_sub_values > 1):
                    #get all sub values with only one value
                    sub_values_with_one_val = [sub_value
                                               for sub_value, length in
                                               nb_for_sub_values.items()
                                               if length == 1]
                    # increase number of neighbors for all identities with
                    # _sub value that only has one non_sub value
                    # get index referring to all images in sub_values
                    # with one val
                    idx = [slice(None)] * nb_categories
                    idx[category] = sub_values_with_one_val
                    neighbors_dim[idx] += 1

            neighbors_all_dim.append(neighbors_dim)

        neighbors_all_dim = np.array(neighbors_all_dim)
        neighbors = np.sum(neighbors_all_dim, axis=0)
        return neighbors, identity_array



    def _get_images_to_be_enlarged(self, neighbors, identity_array):
        #  take maximum and minimum of array
        max_neighbors = np.max(neighbors)
        # set neighbor values at positions without image to max
        # so that they are not included for min calculation
        neighbors[(identity_array == 0)] = max_neighbors
        min_neighbors = np.min(neighbors)
        # if different, some images have fewer dimensions adjacent
        # and therefore should be enlarged to fill up the grid
        images_enlarge = []
        if max_neighbors != min_neighbors:
            # take all images with minimum number of adjacent dimensions
            # as images that should be enlarged
            # get all imags
            images_idx_enlarge = np.where((neighbors == min_neighbors))
            images_enlarge = np.array([tuple(idx)
                                       for idx in images_idx_enlarge]).T
        return images_enlarge



    def _get_identity_remapping_correction_map(self, remapped_categories,
                                              all_images_by_identity):
        # correct for alignment errors of matrices
        # that were caused by remapping only some parts of the identities
        # this correction ONLY works if the repositioning
        #  was done in dimensions which did not
        # target the same identity more than once!

        # create 0 matrix of all identities by using max value of each category
        # of each identity as size of each dimension
        
        keys = all_images_by_identity.keys()
        cat_values = self._get_grouped_cat_values_from_identity_list(keys)

        cat_max_values = np.array([max(x) for x in cat_values])
        identity_matrix = np.zeros(tuple(cat_max_values +1))

        # fill in points in matrix that are used with 1
        for identity in all_images_by_identity.keys():
            identity_matrix[identity] = 1

        identity_remap_correction = {}
        # get all 0 positions, if there is at least 1, continue
        empty_identities = np.transpose(np.where(identity_matrix == 0))

        if len(empty_identities) == 0:
            return identity_remap_correction

        # go through each remapped category
        for cat_nb in remapped_categories:
            for empty_identity in empty_identities:
                # check whether each of the identity values
                #  is in the cat_values for the identities
                # if not, dont consider this identity since it is outside
                # of the rectangle
                identity_in_rectangle = self._check_if_identity_vals_are_in_array(empty_identity,
                                                                                 cat_values)
                if not identity_in_rectangle:
                    continue
                # and check whether any of the 0 positions
                #  is at max of this remapped category
                if empty_identity[cat_nb] != cat_max_values[cat_nb]:
                    continue
                # if so, get all zero identities there are differing
                #  only in the remapped category
                # go through each zero identity and excluded those
                # differing in categories other than the remapped category
                add_empty_identities = []
                for add_empty_identity in empty_identities:
                    empty_identity_is_in_same_dim = self._check_if_identities_are_the_same_except_categories(empty_identity,
                                                                                                          add_empty_identity,
                                                                                                          cat_nb)
                    if empty_identity_is_in_same_dim:
                        add_empty_identities.append(add_empty_identity)
                nb_empty_pos_in_same_dim = len(add_empty_identities)

                for identity in all_images_by_identity.keys():
                    is_target = self._check_if_identities_are_the_same_except_categories(empty_identity,
                                                                                      identity,
                                                                                      cat_nb)
                    if not is_target:
                        continue
                    remapped_identity = list(identity)
                    remapped_identity[cat_nb] += nb_empty_pos_in_same_dim
                    identity_remap_correction[identity] = tuple(remapped_identity)
        return identity_remap_correction


    def _get_grouped_cat_values_from_identity_list(self, identity_list):
        cat_values = [set() for x in range(len(self.map))]
        for identity in identity_list:
            for cat_nb, cat_value in enumerate(identity):
                cat_values[cat_nb].add(cat_value)
        return cat_values


    def _check_if_identity_vals_are_in_array(self, identity, array):
        identity_in_rectangle = True
        for cat_nb_empty, cat_val_empty in enumerate(identity):
            if cat_val_empty not in array[cat_nb_empty]:
                identity_in_rectangle = False
                break
        return identity_in_rectangle


    def _check_if_identities_are_the_same_except_categories(self, identity1,
                                                         identity2, categories):
        identites_similar = True
        if (type(categories) not in self.itertypes):
            categories = [categories]

        for cat_nb, cat_val in enumerate(identity1):
            if (cat_val != identity2[cat_nb]) & (cat_nb not in categories):
                identites_similar = False
                break
        return identites_similar


    def _apply_mapping(self, all_images_by_identity, mapping_dict):
        # remap identities in all_images_by_identity according to reposition_dict
        all_images_by_identity_new = {}
        for identity, image in all_images_by_identity.items():
            if identity in mapping_dict:
                new_identity = mapping_dict[identity]
                all_images_by_identity_new[new_identity] = image
            else:
                all_images_by_identity_new[identity] = image

        return all_images_by_identity_new

    def _get_image_min_max_dict(self, all_images_by_position):
        # create nested dict with image_nb as key and
        # dict as value, where channel is the key and
        # image_min and max values as value
        image_min_max = {}
        for position, image in all_images_by_position.items():
            pre_identity = self.pos_to_pre_identity_map[position]
            pre_identities, _ = self._get_all_pre_identities_from_composite(pre_identity)
            for composite_img_nb, pre_identity in enumerate(pre_identities):
                image_nb = pre_identity[self.map["images"]]
                # for composite, channel is a list of channels
                channel = pre_identity[self.map["channels"]]
                # remove nan and inf values from image
                # image can only contain nan or inf values if the dtype
                # is float
                if image.dtype == float:
                    # convert all inf to nan to allow min and max across axis
                    image[np.isinf(image)] = np.nan

                if image_nb not in image_min_max:
                    image_min_max[image_nb] = {}
                # get minima and maxima of each image at the current position
                # there would only be multiple images if the image is an composite
                min_val = np.nanmin(image, axis=(-3,-2,-1))[composite_img_nb]
                max_val = np.nanmax(image, axis=(-3,-2,-1))[composite_img_nb]
                image_min_max[image_nb][channel] = [min_val, max_val]
        return image_min_max

    def _get_range_of_image(self, img_ranges, pre_identity,
                           images_min_max, use_same_LUTs,
                           image_nb_composite = 0):
        """
        Get pixel value range of current image, based on ranges extracted
        from tiff and alternatively minimum and maximum values in image.
        For composites with similar ranges (same image and channel but
        e.g. different slices) and if no range was set in imageJ, the lowest
        min of all mins and the highest max of all max values of the composite
        will be used for the range.
        :param img_ranges: List of ranges for each channel in each image,
                            extracted from values set in ImageJ for tiff file
        :param pre_identity: list of dimension values of current image
        :param images_min_max: list of min and max values for each
                                image - channel combination; for composite
                                of channels/images, channel/image would be a
                                list of channels/images
                                for composites will include list of
                                min and max values for each image in composite:
                                [all_min_values, all_max_values]
        :param use_same_LUTs: string or Boolean; if string, then it is
                             dimension within which the same LUTs should be used
                             if Boolean, then whether to use same LUTs for
                             all images or have separate LUTs for each image
        :param image_nb_composite: Number of the image in the composite
        :return: range of current image to use
        """

        image_nb = pre_identity[self.map["images"]]
        channel = pre_identity[self.map["channels"]]

        # check for each condition of use_same_LUTs
        # whether there is one image in the right category
        #  (all images or within same image_sub)
        #  with ranges defined from imagej
        # or if no image is in the category with defined imagej range
        #  take min max from image from same category
        image_min_max = images_min_max[image_nb][channel]

        if type(use_same_LUTs) == str:
            image_sub_map = self.sub_category_map["images_sub"]
            if use_same_LUTs == "images_sub":
                # if use_same_LUTs is a string, it can be only "image_sub"
                # it then defines that within each image_sub
                #  the same LUTs should be used
                # check which is the first image in the same image_sub
                image_sub = image_sub_map[image_nb]
                # first go through all img_ranges (imagej defined ranges)
                # if one fits, return that, otherwise
                # go through image min max to set range that way
                a = 0
                for img_ranges_to_use in [img_ranges, image_min_max]:
                    a += 1
                    for image_nb, ranges in img_ranges_to_use.items():
                        other_image_sub = image_sub_map[image_nb]
                        same_image_sub = (image_sub == other_image_sub)
                        range_defined = (len(ranges) > channel)
                        if same_image_sub & range_defined:
                            # if range is tuple, only use position in tuple
                            # corresponding to the current composite
                            if type(ranges) in self.itertypes:
                                ranges = self._get_range_from_min_max(ranges,
                                                                    image_nb_composite)
                            else:
                                ranges = ranges[channel]
                            return ranges

        #  if same LUTs should be used for each image,
        #  use only the first image that has a range defined
        elif use_same_LUTs:
            for image_nb, range in img_ranges.items():
                if len(range) > channel:
                    return range[channel]
        else:
            # if not same LUTs, use preferably
            # imagej range of current image
            # or alternatively min max values of image
            if len(img_ranges) > image_nb:
                if len(img_ranges[image_nb]) > channel:
                    return img_ranges[image_nb][channel]
            return self._get_range_from_min_max(image_min_max, image_nb_composite)

    def _get_range_from_min_max(self, image_min_max, image_nb_composite):
        # if there is no composite with different ranges,
        # the minimum min value and the maximum max value
        # will be used (indicated by image_nb_composite
        # being None
        if type(image_nb_composite) == type(None):
            range = [np.min(image_min_max[0]),
                     np.max(image_min_max[1])]
        else:
            range = image_min_max[image_nb_composite]
        return range

    def _get_max_values_of_dimensions(self, all_images_by_identity):
        max_values = {}
        for dimension, dimension_nb in self.map.items():
            max_values[dimension] = 0
            for identity in all_images_by_identity.keys():
                dimension_value = identity[dimension_nb]
                max_values[dimension] = max(max_values[dimension], 
                                            dimension_value)

        return max_values


    def _finalize_pre_identity_dicts(self, all_images_by_pre_identity, 
                                    inv_map, maps):
        """
        Convert pre_identities in panel_file dict
        and images dict into real identity
        by using mapping from maps
        """

        base_files = {}
        all_images_by_identity = {}

        for pre_identity, image in all_images_by_pre_identity.items():
            identity = []
            for dimension_nb, pre_identity_val in enumerate(pre_identity):
                dimension = inv_map[dimension_nb]
                identity_val = maps[dimension][pre_identity_val]
                identity.append(identity_val)
            identity = tuple(identity)
            all_images_by_identity[identity] = image

        return all_images_by_identity

    def _get_zoom_params_for_identity(self, identity, is_pre_identity = True):
        if not is_pre_identity:
            identity = self._get_pre_identity(identity)
        identifier = identity[self.map["images"]]
        #  if "image_sub" in self.map:
        #      identifier = tuple([identifier, identity[self.map["image_sub"]]])
        zoom_params_this_image = []
        if None in self.zoom_params:
            zoom_params_this_image += self.zoom_params[None]
        if identifier in self.zoom_params:
            zoom_params_this_image += self.zoom_params[identifier]
        return zoom_params_this_image


    def _add_zoom_images(self, all_images_by_identity, show_only_zoom,
                        channels_to_show_first_nonzoomed_timeframe,
                        force_show_non_zoom_channels,
                        show_non_zoom_channels):
        identity_to_add_zoom_mark_to = {}
        # add zoom images
        # remove some images if only_show_zoom is True
        # keep all imges of first timeframe for each channel
        #  all_images_by_identity_new = copy.copy(all_images_by_identity)
        #  all_images_by_identity_new = all_images_by_identity
        images_to_add = {}
        images_to_delete = set([])
        if len(self.zoom_params) == 0:
            return all_images_by_identity, identity_to_add_zoom_mark_to

        for identity, image in all_images_by_identity.items():
            pre_identity = self._get_pre_identity(identity)

            image_nb = pre_identity[self.map["images"]]
            channel = pre_identity[self.map["channels"]]
            frame = pre_identity[self.map["frames"]]
            # get list of zooms in dict zoom_params with key of image_nb
            # for this remap image_nb to pre_identity image_nb
            zoom_params_this_image = self._get_zoom_params_for_identity(pre_identity)

            for zoom_nb, zoom_param in enumerate(zoom_params_this_image):
                channel_correct = True
                image_correct = True
                if zoom_param["channels"] != None:
                    if channel not in zoom_param["channels"]:
                        channel_correct = False
                if zoom_param["images"] != None:
                    if image_nb not in zoom_param["images"]:
                        image_correct = False

                # if non zoom channels should be shown
                # then dont remove images if the channel is not correct
                # also if the image is correct but not the channel
                # AND show_non_zoom_channels is true
                # then the zoom markers should be added to that image
                if (show_non_zoom_channels &
                     image_correct &
                     (not channel_correct)):
                        if pre_identity not in identity_to_add_zoom_mark_to:
                            identity_to_add_zoom_mark_to[pre_identity] = []
                        identity_to_add_zoom_mark_to[pre_identity].append(zoom_nb)
                elif (image_correct & show_only_zoom):
                    # if the image is correct (and therefore there will
                    # be a channel on which zoom will be
                    #  applied for that image)
                    # and if only zoom images should be shown,
                    #  delete non zoom image
                    delete_image = True
                    # if check if first timeframe of current channel
                    #  should be shown
                    if channels_to_show_first_nonzoomed_timeframe != None:
                        # print(channel, channels_to_show_first_nonzoomed_timeframe)
                        if (channel in channels_to_show_first_nonzoomed_timeframe) & (identity[self.map["frames"]] == 0):
                            delete_image = False
                    if (not channel_correct) & force_show_non_zoom_channels:
                        # if non zoom channels should always be shown,
                        #  dont delete those
                        delete_image = False
                    # for first timeframe add zoom number
                    #  to pre_identity key of zoom mark dict
                    if identity[self.map["frames"]] == 0:

                        if pre_identity not in identity_to_add_zoom_mark_to:
                            identity_to_add_zoom_mark_to[pre_identity] = []
                        identity_to_add_zoom_mark_to[pre_identity].append(zoom_nb)
                    if delete_image:
                        if identity in all_images_by_identity:
                            images_to_delete.add(identity)
                            #  del all_images_by_identity_new[identity]

                # only check if frame is correct for adding zoomed images
                # do not check frame for deleting images
                frame_correct = True
                if zoom_param["frames"] != None:
                    if frame not in zoom_param["frames"]:
                        frame_correct = False
                # if channel ad image are correct add zoom
                #  to identity image dict
                if not (channel_correct & image_correct & frame_correct):
                    continue
                # create identity tuple of zoom identity
                zoom_identity = list(copy.copy(identity))
                zoom_identity[self.map["zooms"]] = zoom_nb + 1
                (x1,
                 x2,
                 y1,
                 y2) = self._get_rectangle_position_from_zoom_param(zoom_param)
                zoom_image = image[:, y1:y2,x1:x2]
                images_to_add[tuple(zoom_identity)] = zoom_image
                if not show_only_zoom:
                    if pre_identity not in identity_to_add_zoom_mark_to:
                        identity_to_add_zoom_mark_to[pre_identity] = []
                    identity_to_add_zoom_mark_to[pre_identity].append(zoom_nb)

                # all_images_by_identity_new[tuple(zoom_identity)] = zoom_image

        #  delete images
        for identity in images_to_delete:
            del all_images_by_identity[identity]

        # add images
        for identity, image in images_to_add.items():
            all_images_by_identity[tuple(identity)] = image


        return all_images_by_identity, identity_to_add_zoom_mark_to


    def _get_rectangle_position_from_zoom_param(self, zoom_param):
        height = zoom_param["height"]
        width = zoom_param["width"]
        x1 = zoom_param["xy"][0] - int(np.round(height/2,0))
        y1 = zoom_param["xy"][1] - int(np.round(width/2,0))
        x2 = x1 + height
        y2 = y1 + width

        return x1, x2, y1, y2


    def _get_width_height_matrices_of_categories(self, inv_map,
                                                all_images_by_identity):
        """
        create matrix with all widths and heights of all images
        """
        # create dimensions dynamically from maximum values in each category

        max_values = self._get_max_values_of_dimensions(all_images_by_identity)

        dimensions = []
        for one_category in inv_map.values():
            dimensions.append(max_values[one_category] + 1)
        dimensions = tuple(dimensions)
        width_imgs = np.zeros(dimensions)
        height_imgs = np.zeros(dimensions)

        for identity, image in all_images_by_identity.items():
            width = image.shape[-2]/image.shape[-3]
            height = 1
            width_imgs[ identity ] = width
            height_imgs[ identity ] = height

        return width_imgs, height_imgs


    def _get_differences_of_permutations(self, order_of_categories,
                                        map, width_imgs,
                                       height_imgs, focus,
                                       additional_padding,
                                        all_images_by_identity,
                                       show_focus_in,
                                       enforce_rectangle = False):
        """
        :param order_of_categories: list with number of category
                                    in identity values
                                    determines the order of categories!
        :param map: dict with names of categories as key and number of category
                    in identity as value
        """


        allowed_focus_vals = map.keys()
        possible_focus_vals = []

        if not self._is_none(focus):
            if focus not in allowed_focus_vals:
                raise ValueError("The supplied focus '{}' is not valid. "
                                 "Only the following focus values are allowed:"
                                 " {}.".format(focus,
                                               ", ".join(allowed_focus_vals)))
            possible_focus_vals.append(focus)
        else:
            if len(order_of_categories["fixed"]) > 0:
                possible_focus_vals = [order_of_categories["fixed"][0]]
            else:
                possible_focus_vals = allowed_focus_vals

        order_of_categories = [*order_of_categories["fixed"],
                               *order_of_categories["flexible"]]

        permutations = []
        # get all permutations for focus and non-focus combination
        # permutations consist of one value alone on one axis (row or column)
        # and ALL the other values on the other axis
        # this could be non-ideal for more than 3 categories
        for focus in possible_focus_vals:
            # get all vals which are not focus
            # use order_of_categories to have list of not_focus_vals
            # sorted similarly
            not_focus_vals = tuple([self.map[cat] for cat in order_of_categories
                                    if cat != focus])

            # try both direction for focus if show_focus_in is not defined
            if type(show_focus_in) == type(None):
                permutations.append(((map[focus]),not_focus_vals))
                permutations.append((not_focus_vals,(map[focus])))
            # allow for tolerance for show_focus_in value
            # (row and rows is both fine, also with arbitrary capitalization)
            elif show_focus_in.lower().find("row") != -1:
                permutations.append((not_focus_vals, (map[focus])))
            elif show_focus_in.lower().find("col") != -1:
                permutations.append(((map[focus]),not_focus_vals))
            else:
                raise ValueError("Show_focus_in has invalid value '{}' "
                                 "only words including 'col' or 'row' "
                                 "are allowed".format({show_focus_in}))


        # get dict with ratio of width to height for each permutation
        permutation_differences = {}
        for column_categories, row_categories in permutations:

            if type(column_categories) not in self.itertypes:
                column_categories = [column_categories]
            if type(row_categories) not in self.itertypes:
                row_categories = [row_categories]

            grid_fit_score = self._get_image_category_grid_fit_score(column_categories,
                                                                    row_categories,
                                                                    all_images_by_identity,
                                                                    width_imgs, height_imgs,
                                                                    additional_padding
                                                                    )

            permutation_differences[tuple(column_categories),
                                    tuple(row_categories)] = grid_fit_score

        return permutation_differences


    def _get_image_category_grid_fit_score(self, column_categories,
                                          row_categories,
                                          all_images_by_identity,
                                          width_imgs, height_imgs,
                                          additional_padding
                                          ):
        """
        Get fit of image grid determined by categories shown in
        columns and categories shown in rows.
        """
        # calculate sub padding which is the padding
        #  that will be introduced between the images
        fig = plt.gcf()
        fig_size = fig.get_size_inches()
        sub_xpadding = self.xpadding[0] / 4
        sub_ypadding = self.ypadding[0] / 4
        if type(column_categories) not in self.itertypes:
            column_categories = [column_categories]
        if type(row_categories) not in self.itertypes:
            row_categories = [row_categories]

        # one width-height pair for permutation
        permutation_widths = np.amax(width_imgs,tuple(row_categories))
        permutation_heights = np.amax(height_imgs,tuple(column_categories))
        permutation_width = np.sum(permutation_widths)
        permutation_height = np.sum(permutation_heights)
        permutation_ratio = permutation_width / permutation_height

        # calculate additional padding in each dimension
        add_x_padding = 0
        add_y_padding = 0
        for column_cat in column_categories:
            cat_str = self.inv_map[column_cat]
            if cat_str not in additional_padding:
                continue
            nb_cat_vals = self._get_number_of_vals_for_cat(column_cat,
                                                          all_images_by_identity.keys())
            # subtract 1 from nb cat vals since padding
            #  is added BETWEEN the vals
            # subtract one from value from additional_padding
            #  since it is a factor
            # and 2 means twice the padding, therefore one frame
            #  the padding more than usually
            add_x_padding += (nb_cat_vals - 1) * (additional_padding[cat_str] - 1)

        for row_cat in row_categories:
            cat_str = self.inv_map[row_cat]
            if cat_str not in additional_padding:
                continue
            nb_cat_vals = self._get_number_of_vals_for_cat(row_cat,
                                                          all_images_by_identity.keys())
            add_y_padding += ((nb_cat_vals - 1) *
                              (additional_padding[cat_str] - 1))


        # factor in spaces between images as well for available ratio
        # get dict with differences of permutation ratio to available ratio
        # calculate available ratio with inches
        available_width = ((self.inner_border[1] - self.inner_border[0]) *
                           fig_size[0] -
                           (permutation_widths.size + add_x_padding) *
                           sub_xpadding)
        available_height = ((self.inner_border[3] - self.inner_border[2]) *
                            fig_size[1] -
                            (permutation_height.size + add_y_padding) *
                            sub_ypadding)

        available_ratio = available_width / available_height

        fit_score = max(available_ratio/permutation_ratio,
                   permutation_ratio/available_ratio)
        return fit_score

    def _get_dimension_categories(self, first_dimension, second_dimension,
                                 size_increase_cat_is_focus,
                                 size_increase_dim_nb,
                                 order_of_categories, show_focus_in):
        # get row and column categories
        if size_increase_cat_is_focus:
            focus_dim_nb = size_increase_dim_nb
        else:
            focus_dim_nb = 1 - size_increase_dim_nb
        focus = [first_dimension,
                 second_dimension][focus_dim_nb]

        non_focus_categories = [[first_dimension,
                                second_dimension]
                                [1 - focus_dim_nb]]

        for cat in order_of_categories:
            if cat not in [focus, *non_focus_categories]:
                non_focus_categories.append(cat)

        if show_focus_in == "rows":
            row_categories = tuple([focus])
            column_categories = non_focus_categories
        else:
            column_categories = tuple([focus])
            row_categories = non_focus_categories

        column_categories = tuple([self.map[cat] for cat in column_categories])
        row_categories = tuple([self.map[cat] for cat in row_categories])

        return column_categories, row_categories

    def _get_best_permutation_of_cats_for_axes(self, permutation_differences, 
                                              enforce_rectangle = False):
        """
        focus value refers to dimension which will be spread on one axis alone
        e.g. for focus="frame" on one axis (e.g. x) only images
        with different frame points will be placed
        differentiation for the image and channel
        will be done on the other axis (e.g. y)
        :param enforce_rectangle: Enforce that only permutations
                                will be considered
                                that have more than one category
                                in each direction
                                !!!NOT IMPLEMENTED YET!!!
        """


        min_difference = None
        best_permutation = None
        # get lowest permutation difference
        for permutation, difference in permutation_differences.items():
            if min_difference == None:
                min_difference = difference
                best_permutation = permutation
            elif difference < min_difference:
                min_difference = difference
                best_permutation = permutation

        return best_permutation, min_difference


    def _get_number_of_vals_for_cat(self, category, all_identities):
        if type(category) == str:
            category = self.map[category]
        all_cat_vals = set()
        for identity in all_identities:
            all_cat_vals.add(identity[category])
        return len(all_cat_vals)


    def _set_max_row_and_col_in_auto_mode(self, best_permutation, width_imgs):
            # get max row and max column
            max_values = []
            for cat_nb, categories in enumerate(best_permutation):
                dim_matrix = np.amax(width_imgs,
                                     axis=best_permutation[1-cat_nb])
                nb_values = np.count_nonzero(dim_matrix)
                max_values.append(nb_values)

            self.max_row = max_values[1] - 1
            self.max_col = max_values[0] - 1

    def _create_image_dict_by_position_auto_mode(self, all_images_by_identity,
                                                best_permutation, width_imgs,
                                                inv_map):
        """
        get positions of images based on identity for best_permutation
        which defines which categories go in columns and rows and in
        which order, put in dict
        also define default label positions for each category and value
        which will be used when adding labels outside of the image
        after they have been shown
        """

        all_identities = all_images_by_identity.keys()
        #get number of category vals
        #do not use maximum values since some values might not be used
        #due to automatic remapping after enlarging images
        nb_cat_vals = [self._get_number_of_vals_for_cat(cat ,all_identities)
                        for cat in self.map.values()]
        nb_cat_vals = np.array(nb_cat_vals)

        all_cat_vals = self._get_all_category_vals(all_identities,
                                                              inv_map)

        new_identity_to_add_zoom_mark_to = {}
        for identity, image in all_images_by_identity.items():
            # get row and column
            # for this count number of cells in width matrix
            #  for categories with non zero values
            position = []

            # go through both dimensions (rows and columns)
            # and save position in that dimension of the current identity
            for dimension_nb, categories in enumerate(best_permutation):
                # categories are usually not incrementing

                #  dim_matrix = np.amax(width_imgs,
                #                       axis=best_permutation[1 - dimension_nb])

                if type(categories) not in self.itertypes:
                    categories = [categories]

                # sort images by order of categories, which means
                # that they are separted by their categories in a defined order
                # categories earlier in the list will be the first categories
                # for which images are sorted (meaning that images with same
                # values in all categories except the defined category will be
                # after one another first, before other categories can vary)
                #  (the order is defined in 'best_permutation' and 'categories'
                #  and determined by order_of_categories if defined by user)

                # To calculate the total number of images
                # in the current dimension
                # before the image with the current identity:
                # use array with widths of all imgs
                # in which the identity of each image is the index at which
                # the width of the image is saved
                # a zero-image means that there is no image with that identity

                # change category numbers since the categories
                # of the other dimension will be removed from width array
                # and the identity. But the categories should still be the
                # number that corresponds to the position in the array of the
                # respective category.
                if len(categories) == 1:
                    # If there is only one category then
                    # the position is always 0.
                    new_categories = [0]
                else:
                    # Otherwise the categoriy is reduced by one
                    # if the category comes after (ist larger)
                    # the removed category (from the other dimension)
                    # the reason is that the the dimension of width
                    # corresponding to the other dimension will be removed
                    # and therefore all dimensions after this dimension
                    # will be technically one dimension lower
                    new_categories = [cat - len(best_permutation[1 - dimension_nb])
                                  if cat > best_permutation[1 - dimension_nb][0]
                                  else cat for cat in categories]

                nb_imgs_before = 0
                # convert identity to numpy array to allow a list of
                # multiple, non-ascending/-descending indices

                identity_array = np.array(identity)
                # get maximum width across category/ies of other dimension
                # thereby get nonzero width at positions in current dimension
                # where there is at least one image across
                # the entire other dimension
                new_width_imgs = np.amax(width_imgs,
                                         axis=best_permutation[1 - dimension_nb])

                # get all images before the current image
                # by checking how many images are
                # in the first category before it and adding
                # from categories afterwards images, which are lower
                # in the current category and have any value in a category
                # before that
                for nb_category, category in enumerate(categories):

                    # categories need to be sorted in order to keep
                    # the order in the identity correct
                    # otherwise the positions in the identity refer to
                    # the wrong category and thereby to the wrong dimension
                    # in the widths
                    categories_for_identity = list(categories)
                    categories_for_identity.sort()

                    # get the identity values of categories of current dimension
                    idx = list(identity_array[categories_for_identity])# WAS list(identity_array[[categories_for_identity]])

                    # go through each category  (new_category numbers are needed
                    # since non-category positions in identity array were
                    # already removed)
                    # and change idx to refer to all images with identities
                    # which are any value in categories before nb_cat
                    # and category values lower than the current identity
                    # in nb_category, while identity values in categories
                    # afterwards are the same as in current identity
                    for new_nb_category, new_category in enumerate(new_categories):
                        if new_nb_category < nb_category:
                            idx[new_category] = slice(None)
                        elif new_nb_category == nb_category:
                            idx[new_category] = slice(idx[new_category])
                    sub_widths = new_width_imgs[tuple(idx)]

                    nb_imgs_before += np.count_nonzero(sub_widths)

                position.append(nb_imgs_before)

            self.all_images_by_position[position[1], position[0]] = image

            pre_identity = self._get_pre_identity(identity)

            # map of position original identitiy (including actual frames etc.)
            self.pos_to_pre_identity_map[position[1],
                                         position[0]] = tuple(pre_identity)

            self.pos_to_identity_map[position[1],
                                     position[0]] = tuple(identity)

            if self._identity_is_placeholder(pre_identity):
                continue

            # for non place holder images save connection
            # of pre_identity to position
            self.pre_identity_to_pos_map[pre_identity] = (position[1],
                                                          position[0])

            # ???
            # default label positions dont work anymore!
            # various steps of remapping images leads to identities differing
            # massively from real properties (category values) of images
            # column and row categories are based on these "wrong" identities
            # therefore these categories do not represent the real identities

            # create list for each category value
            #  with all [row, column] positions
            # for each category create two lists of positions
            #  for left and right / top and bottom
            # option 0 is for positon left and top,
            #  option 1 is for position right and bottom
            for nb, one_val in enumerate(pre_identity):
                for sites in [["top", "bottom"], ["left", "right"]]:
                    row = [ position[1], position[1] ]
                    column = [ position[0], position[0] ]
                    if sites[0] == "top":
                        row[0] = 0
                        row[1] = self.max_row
                    elif sites[0] == "left":
                        column[0] = 0
                        column[1] = self.max_col

                    identity_string = inv_map[nb]
                    if identity_string not in self.default_label_positions:
                        self.default_label_positions[identity_string] = {}
                    if one_val not in self.default_label_positions[identity_string]:
                        self.default_label_positions[identity_string][one_val] = {}
                    for site in sites:
                        if site not in self.default_label_positions[identity_string][one_val]:
                            self.default_label_positions[identity_string][one_val][site] = []
                    for option_nb, site in enumerate(sites):
                        self.default_label_positions[identity_string][one_val][site].append([row[option_nb],
                                                                                             column[option_nb]])

        # define minimum and maximum row and column position for each list
        for identity_string, identity_dicts in self.default_label_positions.items():
            for identity_val, position_list in identity_dicts.items():
                # get start- and end- row and -column
                sites = list(position_list.keys())
                for site in sites:
                    row_positions = [position[0] 
                                     for position in position_list[site]]
                    col_positions = [position[1] 
                                     for position in position_list[site]]
                    min_row = min(row_positions)
                    min_col = min(col_positions)
                    max_row = max(row_positions)
                    max_col = max(col_positions)
                    self.default_label_positions[identity_string][identity_val][site] = [ [min_row, min_col],
                                                                                          [max_row, max_col] ]



    def _get_pre_identity(self, identity):
        # convert identity to pre_identity
        pre_identity = []
        remapped_identity = copy.copy(identity)

        if remapped_identity in self.inv_remap_for_orientation:
            remapped_identity = self.inv_remap_for_orientation[remapped_identity]
        if remapped_identity in self.inv_increase_size_map:
            remapped_identity = self.inv_increase_size_map[remapped_identity]

        if remapped_identity in self.inv_identity_remap_correction:
            remapped_identity = self.inv_identity_remap_correction[remapped_identity]

        if remapped_identity in self.inv_reposition_dict:
            remapped_identity = self.inv_reposition_dict[remapped_identity]

        # if remapped identity is -1 at first position
        #  (actually it is -1 at all positions)
        # then it is a place holder identity and image
        #  that does not need to be further remapped
        # only if dim_val_maps was filled already
        if (self._identity_is_placeholder(remapped_identity) |
                (len(self.dim_val_maps) == 0)):
            pre_identity = remapped_identity
        else:
            for dimension_nb, identity_val in enumerate(remapped_identity):
                dimension = self.inv_map[dimension_nb]
                # check if dimension has a sub category
                # if that is the case, it needs to be remapped
                #  using reassign_new_categories_inv dict
                if dimension in self.reassign_new_categories_inv:
                    # get dimension number of sub category
                    dimension_nb_sub = self.map[dimension+"_sub"]
                    # get identity_val of sub dimension
                    identity_val_sub = remapped_identity[dimension_nb_sub]
                    # remap identity_val_sub & identity_val to pre_identity_val

                    pre_identity_val = self.reassign_new_categories_inv[dimension][(identity_val,
                                                                                    identity_val_sub)]
                else:
                    dim_map = self.dim_val_maps[dimension]
                    dim_inv_map = {v:k for k,v in dim_map.items()}
                    # some values were only added after converting
                    #  pre_identity to identity
                    # therefore the identity values are also
                    #  the pre_identity_values (correct values)
                    # these values are not in dim_val_maps since
                    #  this dictionary was created to map
                    # new identity vals to old (correct) pre identity vals
                    if identity_val in dim_inv_map:
                        pre_identity_val = dim_inv_map[identity_val]
                    else:
                        pre_identity_val = identity_val

                pre_identity.append(pre_identity_val)
        pre_identity = tuple([val if type(val) in self.itertypes else int(val)
                              for val in pre_identity])

        return pre_identity

    def add_rows_to_delete(self, rows,
                            images = None,
                           only_in_grid_rows=None,
                           only_in_grid_cols=None):
        """
        Create dictionary with one dictionary entry per rows that should
        be deleted.

        :param rows: list of rows (integers) that should be deleted
        :param images: list of images (integeres) in which rows should be
                        deleted
        :param only_in_grid_rows: List of rows in image grid
                                    in which rows should be deleted
                                    in the image array
        :param only_in_grid_cols: List of columns in image grid
                                    in which rows should be deleted
                                    in the image array
        """
        new_rows_to_delete = {}
        new_rows_to_delete["rows"] = rows
        new_rows_to_delete["images"] = images
        new_rows_to_delete["only_in_grid_rows"] = only_in_grid_rows
        new_rows_to_delete["only_in_grid_cols"] = only_in_grid_cols
        self.all_rows_to_delete.append(new_rows_to_delete)

    def add_cropping(self,left=0, right=0, top=0, bottom=0, coords="rel",
                     row=None, column=None,
                     images=None):
        """
        Add cropping to an image or a set of images.

        :param left: crop from left site, either rel width of image
                    or actual number of pixels
        :param right: crop from right site, either rel width of image
                    or actual number of pixels
        :param top: crop from top, either rel width of image
                    or actual number of pixels
        :param bottom: crop rom bottom, either rel width of image
                        or actual number of pixels
        :param coords: either "rel" for relative image coords,
                        or px for px counts
        :param row: images in which row should be cropped, if not defined
                    or None, in all rows
        :param column: images in which column should be cropped, if not defined
                        or None, in all rows
        :param images: Apply cropping to only a subset of images,
                        specific number of images
                        (numbers will be given incrementally to images
                        in alphanumerical order),
        """
        """
        Create dictionary with one dictionary entry per crop
        at a set of positions to be performed
        Cropping can also be done differently on different rows
        while still keeping the size similar
        for that the cropping values in the same dimension.
        """
        new_crop_param = {}
        new_crop_param["left"] = left
        new_crop_param["right"] = right
        new_crop_param["top"] = top
        new_crop_param["bottom"] = bottom
        if (left > 1) | (right > 1) | (top > 1) | (bottom > 1):
            coords = "abs"
        new_crop_param["coords"] = coords
        new_crop_param["row"] = row
        new_crop_param["col"] = column
        # new added settings to restrict cropping to a specific image
        new_crop_param["images"] = images
        self.crop_params.append(new_crop_param)

    def add_zoom(self, xy, width, height, images = None, channels = None,
                 frames=None, label_position_overview = "left"):
        """
        Append  zoom parameters to dictionary.
        For each image/channel/frame the same number of zooms have to be added.
        Otherwise auto_enlarging won't work.

        :param xy: x,y point as list for bottom-left origin of zoom rectangle
        :param width: width of zoom rectangle
        :param height: height of zoom rectangle
        :param images: dict with each key corresponding to one category
                        ("images", "channels" and "frames" allowed) and
                        the value being a list with all allowed values
                    Alternative use, will be deprecated:
                    list, which images the zoom should be applied on.
                    If None, it will be applied to all images
        :param channels: Will be deprecated
                    list, which channels the zoom should be applied to.
                    If None, it will be applied to all channels
        :param frames: Will be deprecated
                    list, which frames the zoom should be applied to.
                    If None, it will be applied to all channels
        :param label_position_overview: at which position should the number
                                        label be added to the overview image
        """

        new_zoom_param = {}
        new_zoom_param["xy"] = xy
        # flip width and height
        new_zoom_param["width"] = height
        new_zoom_param["height"] = width

        if type(images) == dict:
            image_numbers = images.get("images",None)
            channel_numbers = images.get("channels", None)
            frame_numbers = images.get("frames", None)
        else:
            image_numbers = images
            channel_numbers = channels
            frame_numbers = frames
        new_zoom_param["images"] = image_numbers
        new_zoom_param["channels"] = channel_numbers
        new_zoom_param["frames"] = frame_numbers
        new_zoom_param["label_position_overview"] = label_position_overview
        # add zoom param to sub dicts in zoom_params, one sub dict for each image
        # since all parameters are list or tuples, this check asks whether images
        if (image_numbers is None):
            if None not in self.zoom_params:
                self.zoom_params[None] = []
            self.zoom_params[None].append(new_zoom_param)
        else:
            for image in image_numbers:
                if image not in self.zoom_params:
                    self.zoom_params[image] = []
                self.zoom_params[image].append(new_zoom_param)

    def _check_if_positions_match(self, row_pos, column_pos,
                                 row_ref, column_ref):
        """
        check if two positions (with row and col) are the same.
        If the reference position is None,
        the corresponding position is always correct
        """
        row_correct = False
        if row_ref != None:
            if row_ref == row_pos:
                row_correct = True
        else:
            row_correct = True

        column_correct = False
        if column_ref != None:
            if column_ref == column_pos:
                column_correct = True
        else:
            column_correct = True

        if row_correct & column_correct:
            return True
        return False


    def add_border(self, left=False, right=False, top=False,
                   bottom=False, row = None, column = None,
                   color="black", line_width = 2):
        """
        Add border to images.

        :param left: Whether to add left border
        :param right: Whether to add right border
        :param top: Whether to add top border
        :param bottom: Whether to add bottom border
        :param row: row (integer) in which borders should be added
        :param column: column (integer) in which borders should be added
        :param color: Color of added border
        :param line_width: Line width in pt of added border
        """

        line_width *= self.size_factor
        for position, ax in self.all_axs.items():
            row_pos = position[0]
            column_pos = position[1]

            position_correct = self._check_if_positions_match(row_pos,
                                                             column_pos,
                                                             row, column)

            if not position_correct:
                continue

            if left:
                line_x, line_y = [0,0],[0,1]
                line = lines.Line2D(line_x,line_y,lw=line_width,
                                    transform=ax.transAxes,c=color,
                                    solid_capstyle="butt")
                ax.add_line(line)
            if right:
                line_x, line_y = [1,1],[0,1]
                line = lines.Line2D(line_x,line_y,lw=line_width,
                                    transform=ax.transAxes,c=color,
                                    solid_capstyle="butt")
                ax.add_line(line)
            if top:
                line_x, line_y = [0,1],[1,1]
                line = lines.Line2D(line_x,line_y,lw=line_width,
                                    transform=ax.transAxes,c=color,
                                    solid_capstyle="butt")
                ax.add_line(line)
            if bottom:
                line_x, line_y = [0,1],[0,0]
                line = lines.Line2D(line_x,line_y,lw=line_width,
                                    transform=ax.transAxes,c=color,
                                    solid_capstyle="butt")
                ax.add_line(line)


    def _set_max_row_and_col(self):
        # get maximum number of rows and columns from all panel_file_paths
        self.max_col = 0
        self.max_row = 0
        display_mode = "default"
        for file_path in self.panel_file_paths:
            file_name = os.path.basename(file_path)
            col_pos, row_pos = self._get_col_and_row_from_name(file_name)
            if col_pos != None:
                self.max_col = max(col_pos,self.max_col)
                self.max_row = max(row_pos,self.max_row)
            else:
                if len(self.panel_file_paths) > 1:
                    print("Warning: At least one of the files ( {} ) does not "
                          "contain the keyword for positioning "
                          "'__position-col-row' or "
                          "'__position-col'.".format(file_name))
                    print("Images will be shown in one row or column, "
                          "ascendingly sorted alphanumerically according "
                          "by the filenames.")
                    print("Images will be shown in one row or one column "
                          "if the panel contains more columns "
                          "or rows respectively.")
                display_mode = "auto"
                break

        return display_mode

    def _initiate_label_matrices(self):
            # initiate matrices to keep track of labels already present
            self.label_matrices = {}
            self.label_matrices['left'] = np.full((self.max_row+1,
                                                   self.max_col+1), - np.inf)
            self.label_matrices['right'] = np.full((self.max_row+1,
                                                    self.max_col+1), - np.inf)
            self.label_matrices['bottom'] = np.full((self.max_row+1,
                                                     self.max_col+1), - np.inf)
            self.label_matrices['top'] = np.full((self.max_row+1,
                                                  self.max_col+1), - np.inf)

    def _initiate_label_dicts(self):

            # initiate dict for label_axs
            self.label_axs = {}
            self.label_axs['left'] = []
            self.label_axs['right'] = []
            self.label_axs['top'] = []
            self.label_axs['bottom'] = []

            self.labels = {}
            self.labels['left'] = []
            self.labels['right'] = []
            self.labels['top'] = []
            self.labels['bottom'] = []

            self.label_padding_px= {}
            self.label_padding_px['left'] = []
            self.label_padding_px['right'] = []
            self.label_padding_px['top'] = []
            self.label_padding_px['bottom'] = []

            self.label_lines_ploted = {}
            self.label_lines_ploted["left"] = []
            self.label_lines_ploted["right"] = []
            self.label_lines_ploted["top"] = []
            self.label_lines_ploted["bottom"] = []

    def _expand_img_dimensions(self, img, target_dim = 3):
        while len(img.shape) < target_dim:
            img = np.expand_dims(img, axis=-1)
        return img

    def _create_image_dict_by_position(self):

        img_ranges = {}

        for nb, file_path in enumerate(self.panel_file_paths):

            file_name = os.path.basename(file_path)

            if ((len(self.panel_file_paths) > 1) &
                    (file_name.find(".csv") != -1)):
                raise Exception("Data file can only be used "
                                "if a single file is provided for the panel.")

            column, row = self._get_col_and_row_from_name(file_name)

            image = self.all_panel_imgs[nb]

            # increase dimensionality of non-RGB or 2D image
            # to 2D RGB image by adding dimensions
            image = self._expand_img_dimensions(image)

            # create 4th dimension for composite images, to standarize dimensions
            image = np.expand_dims(image, axis=0)

            ranges = self._extract_img_ranges_from_file(file_path)

            self.all_images_by_position[(row, column)] = image

            identity = []
            # get identity of each image
            for dimension_nb in range(0, len(self.inv_map)):
                dimension = self.inv_map[dimension_nb]
                finder = self.dim_val_finder[dimension]
                result = finder.search(file_name)
                if result:
                    if dimension in self.data_types:
                        value = self.data_types[dimension](result[1])
                    else:
                        value = result[1]
                elif dimension == "image":
                    value = nb
                else:
                    value = 0
                identity.append(value)

            identity = tuple(identity)
            self.pos_to_pre_identity_map[(row, column)] = identity

            channel = identity[self.map["channel"]]
            image_nb = identity[self.map["image"]]
            img_ranges[image_nb][channel] = ranges

        return img_ranges


    def _add_px_to_image_dimension(self, image, row, column,
                                  parameters, max_widths_px, max_heights_px):
        if len(parameters) == 3:
            value_to_add = parameters[2]
        else:
            value_to_add = 0
        if parameters[0].lower() == "width":
            max_width = max_widths_px[column]
            # create shape of added array that only differs in dimension
            # where values should be added
            added_array_shape = np.array(image.shape)
            added_array_shape[-2] = int(max_width) - added_array_shape[-2]
            added_array = np.full(tuple(added_array_shape),
                                  value_to_add)
            if parameters[1].lower() == "right":
                image = np.concatenate((image, added_array), axis=-2)
            elif parameters[1].lower() == "left":
                image = np.concatenate((added_array, image), axis=-2)
            else:
                raise ValueError("The supplied site '{}' in "
                                 "'make_image_size_equal'"
                                 "for adding px is not allowed. "
                                 "Only 'right' and 'left' are "
                                 "allowed.".format(make_image_size_equal[1]))

        elif parameters[0].lower() == "height":
            max_height = max_heights_px[row]
            added_array_shape = np.array(image.shape)
            added_array_shape[-3] = int(max_height) - added_array_shape[-3]
            added_array = np.full(tuple(added_array_shape),
                                  value_to_add)
            if parameters[1].lower() == "bottom":
                image = np.concatenate((image, added_array), axis=-3)
            elif parameters[1].lower() == "top":
                image = np.concatenate((added_array, image), axis=-3)
            else:
                raise ValueError("The supplied site '{}' in "
                                 "'make_image_size_equal'"
                                 "for adding px is not allowed. "
                                 "Only 'bottom' and 'top' are "
                                 "allowed.".format(make_image_size_equal[1]))
        return image

    def _get_all_pre_identities_from_composite(self, pre_identity):

        all_pre_identities = [pre_identity]
        is_composite = False
        for cat_nb, cat_val in enumerate(pre_identity):
            if (type(cat_val) not in self.itertypes):
                continue
            is_composite = True
            #  create nested list with one entry for each
            #  pre_identity, differing only
            #  in the dimension with composite
            all_pre_identities *= len(cat_val)

            for cat_val_nb, one_cat_val in enumerate(cat_val):
                all_pre_identities[cat_val_nb] = list(all_pre_identities[cat_val_nb])
                all_pre_identities[cat_val_nb][cat_nb] = one_cat_val
                all_pre_identities[cat_val_nb] = tuple(all_pre_identities[cat_val_nb])


        return all_pre_identities, is_composite


    def _plot_images_without_setting_position(self, img_ranges, use_same_LUTs,
                                             cmaps, composite_cmaps,
                                             make_image_size_equal,
                                             replace_nan_with, scale_images,
                                             black_composite_background):
        fig = plt.gcf()
        heights = np.zeros((self.max_row+1,self.max_col+1))
        widths = np.zeros((self.max_row+1,self.max_col+1))

        # crop all images
        # needs to be done before px are added to image dimension
        # otherwise the max sizes are not correct
        for position, image in self.all_images_by_position.items():
            row = position[0]
            column = position[1]
            # crop images according to crop_params
            image = self._delete_rows(image, row, column)
            image = self._crop_image(image, row, column)
            self.all_images_by_position[position] = image

        images_min_max = self._get_image_min_max_dict(self.all_images_by_position)

        heights_px = np.zeros((self.max_row + 1, self.max_col + 1))
        widths_px = np.zeros((self.max_row + 1, self.max_col + 1))

        for position, image in self.all_images_by_position.items():
            row = position[0]
            column = position[1]
            widths_px[row,column] = image.shape[-2]
            heights_px[row,column] = image.shape[-3]

        max_widths_px = np.max(widths_px, axis=0)
        max_heights_px = np.max(heights_px, axis=1)

        for position, image in self.all_images_by_position.items():
            row = position[0]
            column = position[1]
            if len(make_image_size_equal) >= 2:
                # allow for adding px with multiple settings
                if type(make_image_size_equal[0]) in self.itertypes:
                    for one_make_image_size_equal in make_image_size_equal:
                        image = self._add_px_to_image_dimension(image, row,
                                                               column,
                                                               one_make_image_size_equal,
                                                               max_widths_px,
                                                               max_heights_px)
                else:
                    image = self._add_px_to_image_dimension(image, row, column,
                                                   make_image_size_equal,
                                                   max_widths_px, 
                                                           max_heights_px)


            label = str(self.letter) + "-" + str(row) + "-" + str(column)
            ax = fig.add_subplot(label = label)
            # if images should not be scaled, use original px size
            # instead of relative size

            if not scale_images:
                widths[row,column] = image.shape[-2]
                heights[row,column] = image.shape[-3]
            else:
                widths[row,column] = image.shape[-2]/image.shape[-3]
                heights[row,column] = 1

            pre_identity = self.pos_to_pre_identity_map[position]
            pre_identities, is_composite = self._get_all_pre_identities_from_composite(pre_identity)
            # pre_identity is now a LIST of pre_identities

            # for composites use composite_cmaps if they are defined
            if is_composite & (not (self._is_none(composite_cmaps))):
                cmaps_to_use = composite_cmaps
            else:
                cmaps_to_use = cmaps

            cmaps_for_img = []
            all_img_ranges = []
            for composite_img_nb, pre_identity in enumerate(pre_identities):
                # dont search for img_range for placeholder images
                if pre_identity[0] != -1:

                    img_range = self._get_range_of_image(img_ranges,
                                                        pre_identity,
                                                         images_min_max, 
                                                        use_same_LUTs,
                                                        composite_img_nb)

                    # replace nan in images by value
                    image[np.isnan(image)] = replace_nan_with
                    # if cmaps was supplied as list, separate by channels
                    if type(cmaps_to_use) in self.itertypes:
                        channel = pre_identity[self.map["channels"]]
                        if channel >= len(cmaps_to_use):
                            raise ValueError("More than one cmap was supplied but "
                                             "not enough for all channels."
                                             "No corresponding cmap for channel "
                                             "'{}'".format(channel)
                                             )
                        # for composite images (more than one image range)
                        # set cmap for each image separately
                        cmap_for_img = cmaps_to_use[channel]

                    else:
                        channel = 0
                        cmap_for_img = cmaps_to_use

                    # dont add information for colorbars for composite images
                    # since otherwise two colorbars would need to be at the same
                    # position!
                    if not is_composite:
                        # put each position in a list for each channel
                        if cmap_for_img not in self.positions_for_cmaps:
                            self.positions_for_cmaps[cmap_for_img] = []
                        self.positions_for_cmaps[cmap_for_img].append(position)
                        # map cmap name to channel
                        if cmap_for_img not in self.cmap_to_channels:
                            self.cmap_to_channels[cmap_for_img] = []
                        self.cmap_to_channels[cmap_for_img].append(channel)
                else:
                    # else only added due to problems when trying to change
                    # algorithm to find position for image
                    # maybe can be removed again.
                    if type(cmaps_to_use) == str:
                        cmap_for_img = cmaps_to_use
                    else:
                        cmap_for_img = cmaps_to_use[0   ]
                    img_range = [0,0]
                all_img_ranges.append(img_range)
                cmaps_for_img.append(cmap_for_img)

            if len(image) > 1:
                if black_composite_background:
                    start_color = "black"
                else:
                    start_color = "white"
                self.cmaps_for_position[position] = [LinearSegmentedColormap.from_list("dark",
                                                                                       [start_color,
                                                                                        cmap])
                                                     for cmap in cmaps_for_img]
                
            else:
                self.cmaps_for_position[position] = [plt.get_cmap(cmap)
                                                     for cmap in cmaps_for_img]
            #go through each image (first dimension) of potential composite image
        
            all_rgb_images = []
            for composite_img_nb, single_image in enumerate(image):

                img_range = all_img_ranges[composite_img_nb]

                cmap_for_img = self.cmaps_for_position[position][composite_img_nb]
                
                
                im = ax.imshow(single_image, cmap=cmap_for_img, clim=img_range,
                               alpha=1,
                               interpolation=self.interpolate_images)#,
                               # interpolation=self.interpolate_images)

                # get rgb image for additive blending
                rgb_image = im.make_image(fig.canvas.get_renderer(),
                                          unsampled=True)[0]

                all_rgb_images.append(rgb_image)

                ax.clear()

            # perform additive blending for composite images
            if len(all_rgb_images) > 1:
                rgb_image_to_show = all_rgb_images[0]
                for rgb_image in all_rgb_images[1:]:
                    if black_composite_background:
                        rgb_image_to_show = np.maximum(rgb_image_to_show,
                                                       rgb_image)
                    else:
                        rgb_image_to_show = np.minimum(rgb_image_to_show,
                                                       rgb_image)
            else:
                rgb_image_to_show = all_rgb_images[0]

            ax.imshow(rgb_image_to_show,
                      interpolation=self.interpolate_images,)
        
            
            # cmap was overwritten by creating rgb image, set cmap again
            # to create correct colorbars
            # Thus colorbars for composite images do not work!
            # would need implementing showing several colorbars next to
            # each other, for each channel
            ax.images[0].set_cmap(cmap_for_img)

            #  ax.set_axis_off()
            # add plot to all_axs[row]
            if row == None:
                row = 0
            if column == None:
                column = 0
            self.all_axs[(row,column)] = ax

        return widths, heights


    def pad_illustration_for_vector_graphic(self, y_padding_fraction = 40, 
                          x_padding_fraction=20):
        """
        Apply white padding to illustration to prevent cutoff of elements when 
        saving figure as pdf or svg. Only needed for vector-graphic file format 
        and illustrations that have elements exactly at or very close 
        to the border.
        If rescale_font_size is used, the pad_illustration_for_vector_graphic
        must be executed after rescale_font_size.
        :param y_padding_fraction: float of fraction of dpi that the padding 
            should be in y direction. Default optimized to keep black line at
            the image border.
        :param x_padding_fraction: float of fraction of dpi that the padding 
            should be in the x direction. Default optimized to keep black line
            at image border.

        """
        if self.figure.file_format not in ["pdf", "svg"]:
            print("WARNING: pad_illustration_for_vector_graphic was used,"
                   "but the file format of the figure object is not pdf or "
                  "svg. Are you sure you want to add white padding around the "
                  "image?")
        image = self.all_axs[0,0].images[0]._A
        y_pad = int(self.figure.dpi/y_padding_fraction)
        self.image_padding_y = y_pad
        y_pad_array = np.full((y_pad,image.shape[1], image.shape[2]),0)
        image = np.concatenate([y_pad_array , image, y_pad_array ], axis=0)

        x_pad = int(self.figure.dpi/x_padding_fraction)
        self.image_padding_x = x_pad
        x_pad_array = np.full((image.shape[0], x_pad, image.shape[2]),0)
        image = np.concatenate([x_pad_array, image, x_pad_array], axis=1)
        
        image = np.uint8(image)
        self.all_axs[0,0].images[0]._A = image

    def _check_if_pos_is_in_row_col_list(self, row, column,
                                        show_axes_in_rows,
                                        show_axes_in_columns):
        row_correct = True
        col_correct = True

        if ((type(show_axes_in_rows) not in self.itertypes) &
            (type(show_axes_in_rows) != type(None))
            ):
            show_axes_in_rows = [show_axes_in_rows]

        if ((type(show_axes_in_columns) not in self.itertypes) &
            (type(show_axes_in_columns) != type(None))
            ):
            show_axes_in_columns = [show_axes_in_columns]

        if type(show_axes_in_rows) != type(None):
            if row not in show_axes_in_rows:
                row_correct = False
        if type(show_axes_in_columns) != type(None):
            if column not in show_axes_in_columns:
                col_correct = False
        if row_correct & col_correct:
            return True
        else:
            return False


    def _delete_rows(self, image, row, col):

        image_without_rows = image

        for rows_to_delete in self.all_rows_to_delete:
            # update width and height after each cropping step
            width = image_without_rows.shape[-2]
            height = image_without_rows.shape[-3]
            # get identity
            pre_identity = self.pos_to_pre_identity_map[(row, col)]

            is_zoom = False
            # do not apply cropping to zoomed image
            if "zooms" in self.map:
                zoom_nb = pre_identity[self.map["zooms"]]
                if zoom_nb > 0:
                    is_zoom = True

            image_correct = True
            # check if image is correct if images were specified in the crop param
            if rows_to_delete["images"] != None:
                if pre_identity[self.map["images"]] not in rows_to_delete["images"]:
                    image_correct = False

            position_correct = self._check_if_pos_is_in_row_col_list(row, col,
                                                             rows_to_delete["only_in_grid_rows"],
                                                             rows_to_delete["only_in_grid_cols"])

            if (not is_zoom) & image_correct & position_correct:
                image_without_rows = np.delete(image, rows_to_delete["rows"], 
                                               axis=1)

        return image_without_rows


    def _crop_image(self, image, row, col):

        image_cropped = image

        for crop_param in self.crop_params:
            # update width and height after each cropping step
            width = image_cropped.shape[-2]
            height = image_cropped.shape[-3]
            # get identity
            pre_identity = self.pos_to_pre_identity_map[(row, col)]

            is_zoom = False
            # do not apply cropping to zoomed image
            if "zooms" in self.map:
                zoom_nb = pre_identity[self.map["zooms"]]
                if zoom_nb > 0:
                    is_zoom = True
            image_correct = True
            # check if image is correct if images were specified in the crop param
            if crop_param["images"] != None:
                if pre_identity[self.map["images"]] not in crop_param["images"]:
                    image_correct = False

            position_correct = self._check_if_pos_is_in_row_col_list(row, col,
                                                                    crop_param["row"],
                                                                    crop_param["col"])

            if (is_zoom) | ( not (image_correct & position_correct)):
                continue

            # get width_fac and height_fac to get from relative values
            #  to actual px values for cropping images
            if crop_param['coords'] == "rel":
                width_fac = width
                height_fac = height
            else:
                width_fac = 1
                height_fac = 1

            x0 = int(crop_param['left'] * width_fac)
            x1 = int(width - crop_param['right'] * width_fac)
            # switch top and bottom for 0 and 1 since y counting starts at the top
            y0 = int(crop_param['top'] * height_fac)
            y1 = int(height - crop_param['bottom'] * height_fac)

            position = (row, col)
            # check if this image was cropped already, print out a warning
            if position in self.cropped_positions.keys():
                print("WARNING: The image at row {} - col {} was cropped more "
                      "than once. Only the higher croping "
                      "at the same site will be "
                      "applied.".format(str(row), str(col)))
                # take higher croping values from croppings done already
                #  and current cropping
                x0 = max(self.cropped_positions[position][0], x0)
                x1 = min(self.cropped_positions[position][1], x1)
                y0 = max(self.cropped_positions[position][2], y0)
                y1 = min(self.cropped_positions[position][1], y1)

            # do not apply cropping if the current panel is edited
            # cropping rectangle will instead be added on top of image
            # if cropping should not be changed in the editor, do the cropping
            if ((self.figure.panel_to_edit != self.letter) |
                    (not self.figure.change_cropping)):
                image_cropped = image_cropped[:, y0:y1, x0:x1, :]

            self.cropped_positions[position] = [x0, x1, y0, y1]

        return image_cropped


    def _correct_xy_for_cropping_and_zoom(self, x, y, row, col):
        position = (row, col)
        # check if image is zoomed
        identity = self.pos_to_pre_identity_map[(row, col)]
        if "zooms" in self.map:
            zoom_nb = identity[self.map["zooms"]]
        else:
            zoom_nb = 0
        if zoom_nb > 0:
            zoom_params_this_image = self._get_zoom_params_for_identity(identity,
                                                                       is_pre_identity = True)
            zoom_param = zoom_params_this_image[zoom_nb - 1]
            zoom_origin_x = zoom_param["xy"][0] - zoom_param["height"] / 2
            zoom_origin_y = zoom_param["xy"][1] - zoom_param["width"] / 2
            x -= zoom_origin_x
            y -= zoom_origin_y

        else:
            # if it is cropped and and not edited, correct for cropping
            # if it is edited, cropping is not executed
            # except if cropping is not changed, then cropping is still executed
            # (cropping is always applied is cropping is not changed in
            #  the editor)
            if ((self.figure.panel_to_edit != self.letter) |
                    (not self.figure.change_cropping)):
                if position in self.cropped_positions.keys():
                    px_cropped = self.cropped_positions[position]
                    x -= px_cropped[0]
                    y -= px_cropped[2]

        return x, y


    def _calculate_outer_border_ax_grid(self):
        """
        Calculate border coordinates for whole ax_grid
        Includes border at outside of figure
        and also border around panel to separate it from other panels

        """

        fig = plt.gcf()
        fig_size = fig.get_size_inches()

        # first element in padding is for left, second for right padding
        padding_rel_x = self.xpadding / fig_size[0]
        # first element in padding is for top, second for bottom padding
        padding_rel_y = self.ypadding / fig_size[1]

        fig_padding_rel_x = self.fig_padding[0] / fig_size[0]
        fig_padding_rel_y = self.fig_padding[1] / fig_size[1]

        # add padding for figure to have shift from left site from figure border
        # add padding for panel to have shift from panel border as well
        #  (to have distance from other panels)
        x0_border = (self.panel_x * self.fig_width_available +
                     padding_rel_x[0] + fig_padding_rel_x)

        # remove padding_size x to have padding to next plot
        x1_border = (x0_border +
                     self.width * self.fig_width_available -
                     (padding_rel_x[0] + padding_rel_x[1]))

        height = self.height * self.fig_height_available
        # subtract from 1 to have lowest panel_y at top and highest at bottom
        # one padding size added for outer figure padding
        # one padding size subtracted for lower padding of panel
        y0_border = 1 - ( self.panel_y * self.fig_height_available +
                          height + fig_padding_rel_y - padding_rel_y[1])
        # subtract 2x padding_size from height since height
        #  is reduced by padding above and below
        y1_border = y0_border + height - (padding_rel_y[0] + padding_rel_y[1])

        self.inner_border = [x0_border, x1_border, y0_border, y1_border]

        x0_outer = (self.panel_x * self.fig_width_available + fig_padding_rel_x)
        x1_outer = x0_outer + self.width * self.fig_width_available
        y0_outer = 1 - ( self.panel_y * self.fig_height_available +
                          height + fig_padding_rel_y)
        y1_outer = y0_outer+ height
        self.outer_border = [x0_outer, x1_outer, y0_outer, y1_outer]

        #  # uncomment to see the borders of the panel
        #  # helpful to judge if boxes are properly aligned
        # bg_ax = plt.gcf().add_axes([x0_border,
        #                         y0_border,
        #                         x1_border-x0_border,
        #                         y1_border-y0_border
        #                         ])


    def _even_out_heights(self, heights, widths, height_rows):
        height_diff_to_max = height_rows / np.transpose(heights)
        heights *= np.transpose(height_diff_to_max)
        widths *= np.transpose(height_diff_to_max)

        np.nan_to_num(widths,copy=False)
        np.nan_to_num(heights,copy=False)

        # update width of columns and height of rows
        width_columns = np.max(widths, axis=0)
        height_rows = np.max(heights, axis=1)

        return heights, widths, height_rows, width_columns


    def _even_out_widths(self, heights, widths, width_columns):
        width_diff_to_max = width_columns / widths
        widths *= width_diff_to_max
        heights *= width_diff_to_max
        # remove nan values from arrays caused by division by zero
        np.nan_to_num(widths,copy=False)
        np.nan_to_num(heights,copy=False)

        # update widths and heights before evening out heights
        width_columns = np.max(widths,axis=0)
        height_rows = np.max(heights,axis=1)

        return heights, widths, height_rows, width_columns


    def _get_width_columns_and_height_rows(self, widths, heights,
                                          dimension_equal, scale_images):

        # fix for multiplications that are not allowed does not work!!!
        # the minimum nonzero width will determine the size of images
        #  widths[np.where(widths == 0)] = 0.00001
        #  heights[np.where(heights == 0)] = 0.0000001

        # get_width of all columns, use maximum value in each column
        width_columns = np.max(widths,axis=0)
        # get height of all rows, use max value in each row
        height_rows = np.max(heights,axis=1)

        # only even out dimensions if images should be scaled
        if scale_images:
            if dimension_equal == "heights":
                # first even out width then even out height afterwards
                new_values = self._even_out_widths(heights, widths, width_columns)
                heights, widths, height_rows, width_columns = new_values
                new_values = self._even_out_heights(heights, widths, height_rows)
                heights, widths, height_rows, width_columns = new_values

            elif dimension_equal == "widths":
                # first even out heights then even out widths afterwards
                new_values = self._even_out_heights(heights, widths, height_rows)
                heights, widths, height_rows, width_columns = new_values
                new_values = self._even_out_widths(heights, widths, width_columns)
                heights, widths, height_rows, width_columns = new_values


        return width_columns, height_rows

    def _get_vals_without_nan_and_values(self, matrix, values_to_exclude=None):
        matrix = matrix[~np.isnan(matrix)]
        if type(values_to_exclude) != type(None):
            if (type(values_to_exclude) not in self.itertypes):
                values_to_exclude = [values_to_exclude]
            for value_to_exclude in values_to_exclude:
                matrix = matrix[matrix != value_to_exclude]
        return matrix


    def _set_additional_padding_matrices(self, additional_padding):
        # check for additional_padding which positions should have added padding
        additional_padding_pos = {}
        for category, factor in additional_padding.items():
            # get matrix with all cat values
            cat_val_matrix = np.full((self.max_row+1, self.max_col+1),np.nan)
            for position, identity in self.pos_to_pre_identity_map.items():
                cat_val_matrix[position] = identity[self.map[category]]

            # calculate how many unique values are in each dimension
            # the dimension with higher number of unique values is the dimension
            # in which the category is distributed
            unique_in_rows = []
            unique_in_cols = []
            for row in range(cat_val_matrix.shape[0]):
                row_vals = cat_val_matrix[row,:]
                row_vals = self._get_vals_without_nan_and_values(row_vals, -1)
                nb_unique_vals = len(np.unique(row_vals))
                if nb_unique_vals == 0:
                    nb_unique_vals = -1
                unique_in_rows.append(nb_unique_vals)
            for col in range(cat_val_matrix.shape[1]):
                col_vals = cat_val_matrix[:,col]
                col_vals = self._get_vals_without_nan_and_values(col_vals, -1)
                nb_unique_vals = len(np.unique(col_vals))
                if nb_unique_vals == 0:
                    nb_unique_vals = -1
                unique_in_cols.append(nb_unique_vals)
            unique_in_rows = np.array(unique_in_rows)
            unique_in_cols = np.array(unique_in_cols)
            max_unique_in_rows = max(unique_in_rows)
            max_unique_in_cols = max(unique_in_cols)

            additional_padding_pos[category] = {}
            # check if category is in rows or in columns
            if max_unique_in_rows > max_unique_in_cols:
                cat_dimension = "rows"
                # get row with max number of unique values
                # get first row without nana values
                rows_with_max_unique_vals = np.where(unique_in_rows == max_unique_in_rows)[0]
                for row in rows_with_max_unique_vals:
                    all_values_for_separating = cat_val_matrix[row,:]
                    if not np.isnan(all_values_for_separating).any():
                        break
            else:
                cat_dimension = "columns"
                # get column with max number of unique values
                # get first column without nan values
                cols_with_max_unique_vals = np.where(unique_in_cols == max_unique_in_cols)[0]
                for col in cols_with_max_unique_vals:
                    all_values_for_separating = cat_val_matrix[:,col]
                    if not np.isnan(all_values_for_separating).any():
                        break
            additional_padding_pos[category][cat_dimension] = []
            # go through dimension and add point at which there is a change in the cat value

            for value_nb in range(1,len(all_values_for_separating)):
                if (all_values_for_separating[value_nb] != 
                        all_values_for_separating[value_nb-1]):
                    additional_padding_pos[category][cat_dimension].append(value_nb)

        self._initialize_padding_factor_matrices()

        for category, cat_dict in additional_padding_pos.items():
            for cat_dimension, dim_values in cat_dict.items():
                for dim_value in dim_values:
                    if cat_dimension == "rows":
                        self.x_padding_factors[:,dim_value:] += additional_padding[category] - 1
                    elif cat_dimension == "columns":
                        self.y_padding_factors[:dim_value,:] += additional_padding[category] - 1

    def _initialize_padding_factor_matrices(self):
        # create array for each position with total factor
        #  of increased padding up to that point
        self.x_padding_factors = np.full((self.max_row+1, self.max_col+1),0)
        self.y_padding_factors = np.full((self.max_row+1, self.max_col+1),0)

    def _get_centered_inner_border(self, width_columns, height_rows):
        # calculate total additional padding in x and in y
        total_additional_x_padding = np.max(self.x_padding_factors)
        total_additional_y_padding = np.max(self.y_padding_factors)

        fig = plt.gcf()
        fig_size = fig.get_size_inches()
        # center inner border vertically and horizonzally
        width_available = (self.inner_border[1] - self.inner_border[0])
        height_available = (self.inner_border[3] - self.inner_border[2])

        # get padding as percentage of available width and height
        # use sub padding here
        padding_size_x = (self.fig_padding[0] * 
                          self.sub_padding_factor) / fig_size[0]
        padding_size_y = (self.fig_padding[1] * 
                          self.sub_padding_factor) / fig_size[1]
        # add padding percentage to total width/height
        # divide width by width_available and height by height_available
        #  to indicate available space in each dimension
        width_row = np.sum(width_columns)
        height_col = np.sum(height_rows)
        width_row_useable_ratio = width_row / (width_available * fig_size[0])
        height_col_useable_ratio = height_col / (height_available * fig_size[1])


        if width_row_useable_ratio > height_col_useable_ratio:
            width_to_use = width_available
            # get the height to use by first getting the real width
            #  without the padding
            width_no_padd = width_to_use -  ( (self.max_col + 
                                               total_additional_x_padding) * 
                                              padding_size_x)
            # then calculate the height without padding which
            #  should be proportional
            # to the width without padding as the the height
            #  of the raw images in px (height_col)
            # to the width of the raw images in px (width_row)
            #  (these width and height are not the plotted values!)
            height_no_padd = (height_col / width_row *
                              (width_no_padd * fig_size[0]) / fig_size[1])
            # then add the padding
            height_to_use = height_no_padd +  ( (self.max_row +
                                                 total_additional_y_padding) *
                                                padding_size_y )

        elif height_col_useable_ratio >= width_row_useable_ratio:

            height_to_use = height_available
            height_no_padd = height_to_use - ( (self.max_row +
                                                total_additional_y_padding) *
                                               padding_size_y )
            width_no_padd = width_row / height_col * (height_no_padd *
                                                      fig_size[1]) / fig_size[0]
            width_to_use = width_no_padd +  ( (self.max_col+
                                               total_additional_x_padding) *
                                              padding_size_x )

        # calculate space left/right and top/bottom
        self.x_space = (width_available - width_to_use) * fig_size[0] * fig.dpi
        x_space_each_site = self.x_space  / 2 / (fig_size[0] * fig.dpi)
        if self.hor_alignment.lower() == "center":
            x0_inner_border = self.inner_border[0] + x_space_each_site
            x1_inner_border = self.inner_border[1] - x_space_each_site
        elif self.hor_alignment.lower() == "left":
            x0_inner_border = self.inner_border[0]
            x1_inner_border = self.inner_border[1] - 2 * x_space_each_site
        elif self.hor_alignment.lower() == "right":
            x0_inner_border = self.inner_border[0] + 2 * x_space_each_site
            x1_inner_border = self.inner_border[1]
        else:
            raise ValueError("The value for 'hor_alignment' ('{}') "
                             "is not allowed. "
                             "Only 'center', 'left' or 'right' "
                             "are allowed.".format(self.hor_alignment))


        self.y_space = (height_available - height_to_use) * fig_size[1] * fig.dpi
        y_space_each_site = self.y_space / 2 / (fig_size[1] * fig.dpi)

        if self.vert_alignment.lower() == "center":
            y0_inner_border = self.inner_border[2] + y_space_each_site
            y1_inner_border = self.inner_border[3] - y_space_each_site
        elif self.vert_alignment.lower() == "top":
            y0_inner_border = self.inner_border[2] + 2* y_space_each_site
            y1_inner_border = self.inner_border[3]
        elif self.vert_alignment.lower() == "bottom":
            y0_inner_border = self.inner_border[2]
            y1_inner_border = self.inner_border[3] - 2 * y_space_each_site
        else:
            raise ValueError("The value for 'vert_alignment' '{}' "
                             "is not allowed. "
                             "Only 'center', 'top' or 'bottom' "
                             "are allowed.".format(self.vert_alignment))

        inner_border = [x0_inner_border, x1_inner_border,
                        y0_inner_border, y1_inner_border]

        return inner_border, width_to_use, height_to_use


    def _set_position_of_plots(self, width_to_use, height_to_use,
                              width_cols, height_rows, inner_border):
            total_add_x_padding = np.max(self.x_padding_factors)
            total_add_y_padding = np.max(self.y_padding_factors)

            fig = plt.gcf()
            fig_size = fig.get_size_inches()
            # place each image in the grid,
            # keeping 1/4 of the padding space between them
            self.sub_padding_x = (( self.fig_padding[0] *
                                    self.sub_padding_factor ) / fig_size[0])
            self.sub_padding_y = (( self.fig_padding[1] *
                                    self.sub_padding_factor ) / fig_size[1])

            width_for_plots = (width_to_use -
                               (self.max_col + total_add_x_padding) *
                               self.sub_padding_x)
            height_for_plots = (height_to_use -
                                (self.max_row + total_add_y_padding) *
                                self.sub_padding_y)
            width_for_plots_px = width_for_plots * fig_size[0] * fig.dpi
            height_for_plots_px = height_for_plots * fig_size[1] * fig.dpi
            width_row_ref = np.sum(width_cols)
            height_col_ref = np.sum(height_rows)

            # get list of positions in which the positions
            # are sorted by row and column position:
            all_positions = list(self.all_axs.keys())
            all_positions.sort(key=lambda x: x[0] * 100 + x[1])
            get_shift = self._get_shift_by_padding_for_position


            for position in all_positions:
                ax = self.all_axs[position]

                pre_identity = self.pos_to_pre_identity_map[position]

                row = position[0]
                col = position[1]

                base_width = width_cols[col] / width_row_ref * width_for_plots
                base_height = (height_rows[row] /
                               height_col_ref * height_for_plots)

                (x_shift_by_padding, 
                 y_shift_by_padding) = get_shift(position)

                if pre_identity in self.size_factors_for_identities:
                    size_factor = self.size_factors_for_identities[pre_identity]
                    fig = plt.gcf()
                    fig_width_px = fig.get_size_inches()[0] * fig.dpi
                    fig_height_px = fig.get_size_inches()[1] * fig.dpi
                    self.orig_size_enlarged_images[position] = [base_width *
                                                                fig_width_px,
                                                                base_height *
                                                                fig_height_px]

                    # put image on top of place_holder image
                    # this leads to problems since you cannot create a full copy
                    # of the axes - when removing the original axes
                    # the "copied axes is removed from the figure as well.
                    # instead the placeholder axes will be removed at the end
                    #  ax_copy = copy.copy(ax)
                    #  ax.remove()
                    #  plt.axes(ax_copy)
                    #  self.all_axs[position] = ax_copy

                    # get additional width and height by padding
                    # between borders that were crossed due to larger image
                    last_pos_x = list(position)
                    #  to account for a difference in the position
                    # caused by shift through enlarged images
                    # add the shift size (size_factor)
                    last_pos_x[1] -= size_factor - 1
                    last_pos_y = list(position)
                    last_pos_y[0] -= size_factor - 1

                    _, add_y_shift_by_padding = get_shift(tuple(last_pos_y))
                    add_height_by_padding = abs(add_y_shift_by_padding -
                                                y_shift_by_padding)
                    add_x_shift_by_padding, _ = get_shift(tuple(last_pos_x))
                    add_width_by_padding = abs(add_x_shift_by_padding -
                                               x_shift_by_padding)
                else:
                    add_height_by_padding = 0
                    add_width_by_padding = 0
                    size_factor = 1

                # add necessary padding to width and height
                # for positions with increased size factor

                # x0 is x start of inner border + actual widths of plots left of
                #  this plot + paddings in between plots
                x0 = inner_border[0] + ( np.sum(width_cols[:col]) /
                                         width_row_ref *
                                         width_for_plots ) + x_shift_by_padding

                width =  base_width * size_factor + add_width_by_padding
                # y0 is similar to x0 but for heights,
                #  but remove from 1 to start with panels from top

                y0 = inner_border[2] + ( np.sum(height_rows[row+1:]) /
                                         height_col_ref *
                                         height_for_plots ) + y_shift_by_padding
                height = base_height * size_factor + add_height_by_padding
                ax.set_position([x0,y0,width,height])

    def _set_default_xy_ticks(self, dimension, ax):
        """
        Set xy ticks.
        :param dimension: string, "x" or "y" for xaxis or yaxis respectively
        """
        # set tick values scaled
        #  if self.ytick_scale / self.xtick_scale are defined
        get_lim = {0: ax.get_xlim, 1: ax.get_ylim}
        get_axis = {0: ax.xaxis, 1:ax.yaxis}
        set_ticks = {0: ax.set_xticks, 1:ax.set_yticks}
        set_labels = {0: ax.set_xticklabels, 1: ax.set_yticklabels}
        if dimension == "x":
            dim = 0
        elif dimension == "y":
            dim = 1

        #  if self.tick_scales[dim] != 1:
        # then get max and min values after scaling
        limits = get_lim[dim]()
        limits = np.array(limits)
        limits *= self.tick_scales[dim]
        if dim == 0:
            limits = [limits[1], limits[0]]

        # get recommended tick values
        #  for scaled with ax.yaxis.major.locator.tick_values(y_lim[0],y_lim[1])
        tick_values_scaled = get_axis[1].major.locator.tick_values(limits[0], 
                                                                   limits[1])
        tick_values_scaled = [int(tick_value)
                              if (tick_value % 1) == 0
                              else tick_value
                              for tick_value in tick_values_scaled]
        tick_values_scaled = np.array([tick_value
                                       for tick_value in tick_values_scaled
                                       if ( (tick_value > limits[1]) &
                                            (tick_value < limits[0]) ) ])
        # rescale values and use as ticks, use scaled tick values as labels
        #  (converted to string)
        tick_values = tick_values_scaled / self.tick_scales[dim]
        tick_labels = [str(tick) for tick in tick_values_scaled]
        # afterwards set ticks matplotlib.pyplot.yticks(ticks=None, labels=None)
        set_ticks[dim](ticks=tick_values)
        set_labels[dim](labels=tick_labels)


    def add_x_axis(self, axis_title="", site="bottom",
                   show_in_rows=None, show_in_columns=None,
                   show_title_in_rows=None, show_title_in_columns=None,
                   axis_padding=0, show_tick_labels=True,
                   always_show_all_tick_values=False,
                   tick_values=None, tick_color="black", tick_width = 0.4,
                   tick_length=5, shift=True, direction="in"):
        """
        Add x axis to images in image grid.

        :param axis_title: String of axis title
        :param site: Site of axis
        :param show_in_rows: List of rows in image grid in which to add x axis
        :param show_in_columns: List of columns in image grid in which to add
                                x axis
        :param show_title_in_rows: List of rows in image grid in which to
                                    show title
        :param show_title_in_columns: List of columns in image grid in which to
                                    show title
        :param axis_padding: padding of axis ticks
        :param show_tick_labels: Whether to show tick labels
        :param always_show_all_tick_values: Show all tick values, even those
                                            outside of the range of the image
        :param tick_values: list, manually define x tick values to be shown on
                            the inside of the image
                            values provided must be after
                            scaling with set_image_scaling
        :param tick_color: string, color of x ticks
        :param tick_width: tick width in pt
        :param tick_length: tick length in pt
        :param shift: whether to shift images after adding axis
        :param direction: direction of ticks ("in" or "out" of image)
        """
        for position, ax in self.all_axs.items():
            row = position[0]
            column = position[1]

            show_axes_here = self._check_if_pos_is_in_row_col_list(row, column,
                                                                  show_in_rows,
                                                                  show_in_columns)

            if not show_axes_here:
                continue

            show_title_here = self._check_if_pos_is_in_row_col_list(row,
                                                                  column,
                                                                  show_title_in_rows,
                                                                  show_title_in_columns)

            #  ax.set_axis_on()
            ax.axes.get_xaxis().set_visible(True)
            # add axis title if set
            if show_title_here:
                ax.set_xlabel(axis_title, labelpad=0)
            #  ax.tick_params(axis="x",which="both",pad=0)

            self._set_default_xy_ticks("x", ax)

            if type(tick_values) != type(None):
                x_tick_values = [x_tick_value/self.tick_scales[0]
                                 for x_tick_value in tick_values]

                if always_show_all_tick_values:
                    x_tick_values_in_range = x_tick_values
                    tick_values_in_range = tick_values
                else:
                    (x_tick_values_in_range,
                     tick_values_in_range) = self._get_ticks_in_range(ax.get_xlim(),
                                                                     x_tick_values,
                                                                     tick_values)
                ax.set_xticks(ticks=x_tick_values_in_range)
                ax.set_xticklabels(tick_values_in_range)

            ax.tick_params(axis="x", which="both", pad=axis_padding,
                               length =tick_length, width=tick_width,
                               direction=direction, color=tick_color,
                                bottom=True)

            if not show_tick_labels:
                ax.set_xticklabels([])
            x_axis_height_px = statannot.get_axis_dimension(ax, ax.xaxis,
                                                            "height",
                                                            ax.get_position().y0)

            if shift:
                self._shift_and_transform_axs(site, None, x_axis_height_px)


    def _get_ticks_in_range(self, range, tick_values, tick_labels):
        range = [min(range), max(range)]
        tick_values_in_range = []
        tick_labels_in_range = []
        for tick_nb, tick_value in enumerate(tick_values):
            if ((tick_value >= range[0]) &
                             (tick_value <= range[1])):
                tick_values_in_range.append(tick_value)
                tick_labels_in_range.append(tick_labels[tick_nb])
        return tick_values_in_range, tick_labels_in_range

    def add_y_axis(self, axis_title="", site="left",
                   show_in_rows=None, show_in_columns=None,
                   show_title_in_rows=None, show_title_in_columns=None,
                   axis_padding=0, show_tick_labels=True,
                   always_show_all_tick_values=False,
                   tick_values=None, tick_color="black", tick_width = 0.4,
                   tick_length=5, shift=True, direction="in"):
        """
        Add y axis to images in image grid.

        :param axis_title: String of axis title
        :param site: Site of axis
        :param show_in_rows: List of rows in image grid in which to add y axis
        :param show_in_columns: List of columns in image grid in which to add
                                y axis
        :param show_title_in_rows: List of rows in image grid in which to
                                    show title
        :param show_title_in_columns: List of columns in image grid in which to
                                    show title
        :param axis_padding: padding of axis ticks
        :param show_tick_labels: Whether to show tick labels
        :param always_show_all_tick_values: Show all tick values, even those
                                            outside of the range of the image
        :param tick_values: list, manually define y tick values to be shown
                                on the inside of the image
                                values provided must be after scaling
                                with set_image_scaling
        :param tick_color: string, color of y ticks
        :param tick_width: tick width in pt
        :param tick_length: tick length in pt
        :param shift: whether to shift images after adding axis
        :param direction: direction of ticks ("in" or "out" of image)
        """

        for position, ax in self.all_axs.items():
            row = position[0]
            column = position[1]

            show_axes_here = self._check_if_pos_is_in_row_col_list(row, column,
                                                                  show_in_rows,
                                                                  show_in_columns)

            if not show_axes_here:
                continue

            show_title_here = self._check_if_pos_is_in_row_col_list(row,
                                                                  column,
                                                                  show_title_in_rows,
                                                                  show_title_in_columns)

            ax.set_axis_on()
            ax.axes.get_yaxis().set_visible(True)
            # add axis title if set
            if show_title_here:
                ax.set_ylabel(axis_title, labelpad=axis_padding)
            #  ax.tick_params(axis="x",which="both",pad=0)

            self._set_default_xy_ticks("y", ax)
            if type(tick_values) != type(None):
                y_tick_values = [int(y_tick_value/self.tick_scales[1])
                                 for y_tick_value in tick_values]
                if always_show_all_tick_values:
                    y_tick_values_in_range = y_tick_values
                    tick_values_in_range = tick_values
                else:
                    (y_tick_values_in_range,
                     tick_values_in_range) = self._get_ticks_in_range(ax.get_ylim(),
                                                                     y_tick_values,
                                                                     tick_values)

                ax.set_yticks(ticks=y_tick_values_in_range)
                ax.set_yticklabels(tick_values_in_range)

            ax.tick_params(axis="y", which="both",
                           pad=axis_padding,
                               length =tick_length, width=tick_width,
                               direction=direction, color=tick_color)

            if not show_tick_labels:
                ax.set_yticklabels([])

            y_axis_width_px = statannot.get_axis_dimension(ax, ax.yaxis,
                                                           "width",
                                                           ax.get_position().x0)

            if site == "right":
                ax.yaxis.tick_right()
                ax.yaxis.set_label_position("right")

            if shift:
                self._shift_and_transform_axs(site, y_axis_width_px, None )


    def _remove_xy_axes(self, show_axis_grid):
        for position, ax in self.all_axs.items():

            if not show_axis_grid:
                ax.grid(False)

            ax.spines['bottom'].set_color('None')
            ax.spines['top'].set_color('None')
            ax.spines['right'].set_color('None')
            ax.spines['left'].set_color('None')

            ax.axes.get_xaxis().set_visible(False)
            ax.axes.get_yaxis().set_visible(False)

            hide_x_axis = False
            hide_y_axis = False

    def _create_img_position_matrix(self):
            # create position_matrix in shape of grid in which images
            #  are plotted
            # with zeros at positions where no image is and
            #  1 at positions with an image
            grid_dimension = [0,0]
            for position in self.all_axs:
                for dim in range(len(position)):
                    grid_dimension[dim] = max(grid_dimension[dim],
                                              position[dim])
            grid_dimension = np.array(grid_dimension) + 1

            self.position_matrix = np.zeros(tuple(grid_dimension))

            for position in self.all_axs:
                self.position_matrix[position] = 1

    def _get_shift_by_padding_for_position(self, position):
        add_x_padding = self.x_padding_factors[position]
        add_y_padding = self.y_padding_factors[position]

        x_shift_by_padding = self.sub_padding_x * (position[1] + add_x_padding)
        y_shift_by_padding = self.sub_padding_y * (self.max_row - position[0] +
                                                   add_y_padding)

        return x_shift_by_padding, y_shift_by_padding

    def _add_colorbars_to_axs(self, show_colorbar_at,
                             show_colorbar_for_channels,
                             heights, tick_labels,
                                 size, colorbar_tick_distance_from_edge,
                                font_size_factor, colorbar_padding,
                                tick_length,
                                label_padding,
                             only_show_in_rows, only_show_in_columns):

        position_matrix = copy.copy(heights)
        position_matrix[heights > 0] = 1
        position_matrix[heights <= 0] = 0

        # get number of rows with plots for each column
        # get number of columns for each row
        nb_rows = np.sum(position_matrix, axis=0)
        nb_cols = np.sum(position_matrix, axis=1)
        # check if there is only one set of min max values for all images
        all_min_max = set()
        for ax in self.all_axs.values():
            #  get min and max of image colormap
            all_min_max.add(tuple(ax.images[0].get_clim()))

        colorbar_height = 0
        colorbar_width = 0
        # iterate through list of positions for each channel separately
        # so that each channel with a different colormap get a different
        # colorbar
        for cmap, cmap_positions in self.positions_for_cmaps.items():
            channels = self.cmap_to_channels[cmap]
            plot_colorbar = False
            # check if cannel of current cmap should be used to show colorbar
            # if one channel for colormap should be used to show colorbar
            # use all channels for colormap
            if not self._is_none(show_colorbar_for_channels):
                for channel in channels:
                    if channel in show_colorbar_for_channels:
                        plot_colorbar = True
                        break
            else:
                plot_colorbar = True

            if not plot_colorbar:
                continue

            for pos in cmap_positions:
                row = pos[0]
                col = pos[1]
                ax = self.all_axs[pos]
                # colorbar should only be shown in each dimension (row or column)
                # for plot which is furthest in the direction
                #  where the colorbar should be shown
                # e.g. for a colorbar at the bottom in an image grid that has
                # three columns, first with 3 images, 2nd with 5 images
                #  and third with 7 images
                # the colorbar should be shown at:
                #  1st col: 3rd image from top, 2nd: 5th, 3rd: 7th
                show_colorbar = False
                if show_colorbar_at == "bottom":
                    if row == (nb_rows[col] - 1):
                        show_colorbar = True
                elif show_colorbar_at == "top":
                    if row == 0:
                        show_colorbar = True
                elif show_colorbar_at == "right":
                    if col == (nb_cols[row] - 1):
                        show_colorbar = True
                elif show_colorbar_at == "left":
                    if col == 0:
                        show_colorbar = True

                grid_position_correct = self._check_if_pos_is_in_row_col_list(row, col,
                                                                             only_show_in_rows,
                                                                             only_show_in_columns)

                if (not show_colorbar) | (not grid_position_correct):
                    continue

                ax_coords = ax.get_position()
                # will show color bar in rows if the location
                # is left or right
                # and will show in columns if the location is top or bottom
                if (show_colorbar_at == "bottom") | (show_colorbar_at == "top"):
                    # colorbar size will only be defined once for panel
                    # that way the colorbarsize is consistent for the entire panel
                    if colorbar_height == 0:
                        colorbar_height = ax_coords.height * size
                    orientation="horizontal"
                    # set one global parameter for padding of colorbars
                    if np.isnan(self.padding_of_colorbars):
                        self.padding_of_colorbars = (colorbar_padding * 
                                                     colorbar_height)
                    # move colobar down by height of colorbar
                    #  so that it does not overlap with image
                    if show_colorbar_at == "bottom":
                        y_start = (ax_coords.y0 - colorbar_height -
                                   self.padding_of_colorbars)
                    elif show_colorbar_at == "top":
                        y_start = (ax_coords.y0 + ax_coords.height +
                                   self.padding_of_colorbars)
                    cax = plt.gcf().add_axes([ax_coords.x0,
                                              y_start,
                                              ax_coords.width,
                                              colorbar_height
                                              ])
                else:
                    # colorbar size will only be defined once for panel
                    # that way the colorbarsize is consistent for the entire panel
                    if colorbar_width == 0:
                        colorbar_width = ax_coords.width * size
                    orientation = "vertical"
                    if np.isnan(self.padding_of_colorbars):
                        self.padding_of_colorbars = (colorbar_padding *
                                                     colorbar_width)
                    # move colobar left by width of colorbar
                    #  so that it does not overlap with image
                    if show_colorbar_at == "left":
                        x_start = (ax_coords.x0 - colorbar_width -
                                   self.padding_of_colorbars)
                    elif show_colorbar_at == "right":
                        x_start = (ax_coords.x0 + ax_coords.width +
                                   self.padding_of_colorbars)
                    cax = plt.gcf().add_axes([x_start,
                                              ax_coords.y0,
                                              colorbar_width,
                                              ax_coords.height])

                colorbar = plt.gcf().colorbar(ax.images[0], cax= cax,
                                              orientation=orientation)

                # get min and max of image colormap
                min, max = ax.images[0].get_clim()

                # calculate range of colormap
                range = max - min
                # move ticks from outer edges more to the middle
                # to prevent overlapping with neighboring images
                tick_distance_edge = colorbar_tick_distance_from_edge * range
                tick_min = np.round(min + tick_distance_edge, 0)
                tick_max = np.round(max - tick_distance_edge, 0)
                colorbar.set_ticks([tick_min, tick_max])

                # if tick_labels are defined, set first and second tick labels
                # as string tick labels defined in that list
                if not self._is_none(tick_labels):
                    first_tick_label, second_tick_label = tuple(tick_labels)
                else:
                    # otherwise set tick labels as normalized float
                    # between 0.0 and 1.0, 
                    # with user-defined distance from edge
                    # (or default distance of 0.2)
                    first_tick_label = np.round((tick_min - min)/(max - min),1)
                    second_tick_label = np.round((tick_max - min)/(max - min),1)

                colorbar.set_ticklabels([first_tick_label, second_tick_label])
                # use a defined fraction of normal font size
                colorbar_font_size = self.font_size * font_size_factor

                colorbar.ax.tick_params(labelsize=colorbar_font_size,
                                        pad=label_padding, length=tick_length,
                                        width=1)
                if (show_colorbar_at == "left") | (show_colorbar_at == "right"):
                    colorbar.ax.yaxis.set_ticks_position(show_colorbar_at)
                elif ((show_colorbar_at == "top") |
                      (show_colorbar_at == "bottom")):
                    colorbar.ax.xaxis.set_ticks_position(show_colorbar_at)
                colorbar.outline.set_visible(False)
                self.all_colorbars[pos] = colorbar
                self.site_of_colorbars[pos] = show_colorbar_at
                # only show first colorbar
                # if there is only one set of min_max values in all images
                if len(all_min_max) == 1:
                    break


        if len(self.all_colorbars) == 0:
            return

        fig = plt.gcf()

        colorbar = list(self.all_colorbars.values())[0]
        # dont need anymore
        #  colorbar_size = colorbar.outline.get_tightbbox(fig.canvas.renderer)

        # get maximum number in ALL colorbars
        # important for shift values for colorbars placed left or right
        max_label_value = 0
        for colorbar in self.all_colorbars.values():
            label_values = colorbar.get_ticks()[-1]
            max_label_value = np.max([max_label_value, np.max(label_values)])

        # to know width of label, get lab text
        # get text of last label since that will have the highest number
        # which will also be the number that needs the most space

        # then measure width
        txt_width, txt_height = FigurePanel._get_dimension_of_text(max_label_value,
                                                                  colorbar_font_size,
                                                                  cax)
        fig_size = fig.get_size_inches() * fig.dpi
        colorbar_width_px = cax.get_position().width * fig_size[0]
        colorbar_height_px = cax.get_position().height * fig_size[1]

        # total size of colorbar ax is a combination of the colorbar itself
        # the txt of the label and the length of the tick
        # factor 0.9 is
        label_padding_px = label_padding * 72 * 0.3

        if orientation == "vertical":
            padding = colorbar_width_px * colorbar_padding
            padding_of_colorbar = self.padding_of_colorbars * fig_size[0]
            x_shift = (colorbar_width_px + txt_width + tick_length +
                       label_padding_px + padding_of_colorbar)
            y_shift = None

        elif (orientation == "horizontal"):
            padding = colorbar_height_px * colorbar_padding
            padding_of_colorbar = self.padding_of_colorbars * fig_size[1]
            x_shift = None
            y_shift = (colorbar_height_px + txt_height + tick_length +
                       label_padding_px + padding_of_colorbar)

        self._shift_and_transform_axs(show_colorbar_at,
                                     x_shift, y_shift)

    def _get_img_from_axis(self, ax, img_nb = 0):
        image = ax.images[img_nb]._A
        image = self._expand_img_dimensions(image)
        return image

    def _add_zoom_marks_to_overview_images(self, identity_to_add_zoom_mark_to,
                                          line_width_zoom_rectangle,
                                          zoom_nb_font_size_overview,
                                          zoom_nb_padding, zoom_nb_color,
                                          show_single_zoom_numbers):
        fig = plt.gcf()
        fig_size_px = fig.get_size_inches() * fig.dpi

        # add zoom marks on non zoom images that were saved beforehand in auto_mode script
        for identity_for_zoom_mark, zoom_nbs in identity_to_add_zoom_mark_to.items():

            unique_zoom_nbs = set(np.unique(zoom_nbs))
            unique_zoom_nbs = unique_zoom_nbs - set([-1])
            nb_zooms = len(unique_zoom_nbs)

            for position, identity in self.pos_to_pre_identity_map.items():

                if identity != identity_for_zoom_mark:
                    continue

                #  image = self.all_images_by_position[position]
                ax = self.all_axs[position]
                image = self._get_img_from_axis(ax)

                ax_coords = ax.get_position()
                # get which zooms were applied to the current image
                for zoom_nb in zoom_nbs:

                    zoom_params_this_image = self._get_zoom_params_for_identity(identity)
                    zoom_param = zoom_params_this_image[zoom_nb]
                    x0, x1, y0, y1 = self._get_rectangle_position_from_zoom_param(zoom_param)
                    x0, y0 = self._correct_xy_for_cropping_and_zoom(x0, y0,
                                                                   position[0],
                                                                   position[1])
                    x1, y1 = self._correct_xy_for_cropping_and_zoom(x1, y1,
                                                                   position[0],
                                                                   position[1])

                    label_position = zoom_param["label_position_overview"]
                    rect_label = "___label_position"
                    # draw rectangle on image
                    x0_ax, y0_ax = self._transform_coords_from_data_to_axes(x0,
                                                                           y0,
                                                                           ax)
                    x1_ax, y1_ax = self._transform_coords_from_data_to_axes(x1,
                                                                           y1,
                                                                           ax)

                    width = x1_ax - x0_ax
                    height = y1_ax - y0_ax

                    rect = patches.Rectangle((x0_ax, y0_ax), width,
                                                                      height,
                                                                      linewidth=line_width_zoom_rectangle,
                                                                      edgecolor="white",
                                                                      label = rect_label,
                                                                      transform=ax.transAxes,
                                                                      facecolor="none")
                    ax.add_patch(rect)

                    # Option: dont show zoom numbers if there is only one
                    if (not show_single_zoom_numbers) & (nb_zooms <= 1):
                        continue

                    # draw number on image outside of rectangle
                    # check size of number drawn
                    if zoom_nb_font_size_overview == None:
                        zoom_nb_font_size_overview = self.font_size
                    nb_str = str(zoom_nb + 1)
                    str_width, str_height = FigurePanel._get_dimension_of_text(nb_str,
                                                                              zoom_nb_font_size_overview,
                                                                              ax)

                    # get relative coordinates
                    # have list of possible positions
                    # go through list of positions
                    x0_rel = x0 / image.shape[-2]
                    x1_rel = x1 / image.shape[-2]
                    y0_rel = y0 / image.shape[-3]
                    y1_rel = y1 / image.shape[-3]

                    ax_width_px = ax_coords.width * fig_size_px[0]
                    ax_height_px = ax_coords.height * fig_size_px[1]

                    str_width_rel = str_width / (ax_width_px)
                    str_height_rel = str_height / (ax_height_px)


                    # convert zoom nb padding from inch to rel ax coords
                    padding_x_rel = zoom_nb_padding / (ax_coords.width *
                                                       fig.get_size_inches()[0])
                    padding_y_rel = zoom_nb_padding / (ax_coords.height *
                                                       fig.get_size_inches()[1])

                    label_positions =  []
                    if zoom_param["label_position_overview"] != None:
                        label_positions.append(zoom_param["label_position_overview"])
                    # add other positions as backup even if a position was defined
                    for backup_position in ["left", "right", "bottom", "top"]:
                        if backup_position not in label_positions:
                            label_positions.append(backup_position)

                    #  line_width_zoom_rectangle_x_rel = (line_width_zoom_rectangle / 72 * fig.dpi ) / ax_width_px
                    line_width_zoom_rectangle_y_rel = (line_width_zoom_rectangle /
                                                       72 * fig.dpi ) / ax_height_px

                    # 0.21 is the trial-and-error-determiend factor
                    # which corrects for overhang below font for low letters like "g"
                    # and check for the first one where the number is not outside of the image
                    for label_position in label_positions:
                        if label_position == "left":
                            x0_label = x0_rel - str_width_rel - padding_x_rel
                            y0_label = (y1_rel + str_height_rel * 0.21 +
                                        line_width_zoom_rectangle_y_rel)
                        elif label_position == "right":
                            x0_label = x1_rel + padding_x_rel
                            y0_label = (y1_rel + str_height_rel * 0.21 +
                                        line_width_zoom_rectangle_y_rel)
                        elif label_position == "bottom":
                            x0_label = x1_rel - str_width_rel
                            y0_label = (y1_rel + str_height_rel +
                                        line_width_zoom_rectangle_y_rel +
                                        padding_y_rel)
                        elif label_position == "top":
                            x0_label = x1_rel - str_width_rel
                            y0_label = y0_rel # - padding_y_rel / 2


                        x1_label = x0_label + str_width_rel
                        y1_label = y0_label - str_height_rel
                        position_in_image = True
                        for coord in [x0_label, x1_label, y0_label, y1_label]:
                            if (coord < 0) | (coord > 1):
                                position_in_image = False

                        if position_in_image:
                            break

                    # PROBLEM:
                    # y position of label not accurate yet. Looks still good.
                    # use that position to draw the number
                    # fixed by now?! (accounted for descending letters)
                    ax.annotate(xy=(x0_label,1-y0_label),text=nb_str,
                                fontsize=zoom_nb_font_size_overview,
                                label ="label_zoom_overview",
                                color=zoom_nb_color,  xycoords="axes fraction",
                                va="bottom", ha="left")


    def _add_zoom_number_to_zoomed_images(self, position_zoom_nb,
                                         show_in_frames,
                                         zoom_nb_rows, zoom_nb_columns,
                                         zoom_nb_font_size,
                                         zoom_nb_color, zoom_nb_padding,
                                         show_single_zoom_numbers):
        # add number of zoom on zoomed images
        iterable_types = [list, tuple]
        if ((type(show_in_frames) not in iterable_types) &
                (not self._is_none(show_in_frames))):
            show_in_frames = [show_in_frames]
        # for each zoom number get a sorted list of frames
        # then use "show in frames" as indices for that list
        zoom_nb_frame_dict = {}
        for pre_identity in self.pos_to_pre_identity_map.values():
            zoom_nb = pre_identity[self.map["zooms"]]
            if zoom_nb not in zoom_nb_frame_dict:
                zoom_nb_frame_dict[zoom_nb] = []
            frame = pre_identity[self.map["frames"]]
            zoom_nb_frame_dict[zoom_nb].append(frame)

        add_zoom_numbers = True

        # option: dont add zoom numbers
        # if there is only one zoom region
        if not show_single_zoom_numbers:

            zoom_nbs = set(zoom_nb_frame_dict.keys())
            zoom_nbs -= set([0]) - set([-1])
            nb_zooms = len(zoom_nbs)
            if nb_zooms == 1:
                add_zoom_numbers = False

        if not add_zoom_numbers:
            return

        # sort frames ascendingly in each list
        for zoom_nb_frame_list in zoom_nb_frame_dict.values():
            zoom_nb_frame_list.sort()

        for position, pre_identity in self.pos_to_pre_identity_map.items():
            zoom_nb = pre_identity[self.map["zooms"]]
            # check if current identity is a zoomed image
            if zoom_nb > 0:
                position_allowed = self._check_if_positions_match(position[0],
                                                                 position[1],
                                                                 zoom_nb_rows,
                                                                 zoom_nb_columns)
                if not self._is_none(show_in_frames):
                    identity = self.pos_to_pre_identity_map[position]
                    frame = identity[self.map["frames"]]
                    frames_to_match = [zoom_nb_frame_dict[zoom_nb][frame]
                                       for frame in show_in_frames]
                    if frame not in frames_to_match:
                        position_allowed = False

                if position_allowed:
                    ax = self.all_axs[position]
                    if type(zoom_nb_font_size) == type(None):
                        zoom_nb_font_size = self.font_size

                    self._add_text_within_image(ax, str(zoom_nb),
                                                position_zoom_nb,
                                                zoom_nb_font_size,
                                                zoom_nb_color,
                                                "left", "top", zoom_nb_padding,
                                                ax_position=position,
                                                label="label_zoom")


    def _add_letter_subplot(self,letter):
            fig = plt.gcf()
            fig_size = fig.get_size_inches()
            padding_size_x = self.xpadding / fig_size[0]
            padding_size_y = self.ypadding / fig_size[1]
            # add the panel letter
            label = "letter subplot "+str(letter)
            self.ax_letter = fig.add_subplot(label = "letter subplot - " + str(letter))
            # remove outer padding again since letter should be within this padding
            letter_x0 = self.outer_border[0]#  - padding_size_x
            # just add one padding, since the other was added with x0 / y0
            letter_width = self.outer_border[1] - letter_x0#  + padding_size_x
            letter_y0 = self.outer_border[2] # - padding_size_y
            letter_height = self.outer_border[3] - letter_y0#  + padding_size_y
            # increase outer_border by padding size target_padding for first row
            # since there 2x padding was added in y to accomodate enough space for letter
            #  if self.panel_y == 0:
            #      letter_height += padding_size_y
            self.ax_letter.set_position([letter_x0,letter_y0,letter_width,letter_height])
            # adjust y position so that letter is within plot
            ax_letter_coords = self.ax_letter.get_position()
            ax_letter_height_px = ax_letter_coords.height * fig.get_size_inches()[1] * fig.dpi
            # move about half into ax
            fraction_of_fontsize_lowered = 2

            y_position_letter = 1 - ( ( self.letter_fontsize /
                                        fraction_of_fontsize_lowered *
                                        (fig.dpi / 72)) / ax_letter_height_px )

            self.ax_letter.annotate(letter,xy=(0,y_position_letter),
                                    fontsize=self.letter_fontsize,va="center",
                                    ha="left",
                                    fontweight="bold")
            self.ax_letter.set_axis_off()

    def label_category(self, category, texts, site=None, font_size=None,
                       padding=2, font_size_factor = None,
                       label_orientation = None, **kwargs):
        """
        Label a category (images, channels, frames or slices; also _subs).

        :param category: String of category that should be labeled
                            ("images", "channels", "frames" or "slices")
        :param texts: Text that should be used as labels; should match the
                            number of different values in the defined category
                            Same labels that are adjacent are only labeled
                            once across all affected images
        :param site: String of site at image grid at which labels should be
                    adde ("top", "bottom", "left" or "right"). Depending on the
                    dimension (columns or rows) in which the category is,
                    top/bottom (for columns) might is better for left/right
                    (for rows).
        :param font_size: font_size of labels; if None default for figure_panel
                            will be used
        :param padding: Padding in pt of labels from images
        :param font_size_factor: Factor by which the default font_size should be
                                 scaled to obtain font size for labels
        :param label_orientation:  "hor" or "vert"
                                    default is horizontal for "top" and "bottom"
                                    site and vertical for "left" and "right"
                                    site
        """
        label_cat = category
        self._label_category(label_cat, texts, site = site, font_size=font_size,
                             padding=padding,
                             font_size_factor = font_size_factor,
                             label_orientation=label_orientation, **kwargs)

    def label_images(self, texts=None, text_prefix=None, site=None,
                     label_sub_remapped=False, font_size = None, padding=2,
                     font_size_factor = None, label_orientation = None,
                     **kwargs):
        """
        Label images in panel. If no texts are supplied, images will be labeled
        with incrementing numbers.

        :param texts: Text that should be used as labels; should match the
                            number of different values in the defined category
                            Same labels that are adjacent are only labeled
                            once across all affected images
        :param text_prefix: If texts is None, what text should be added in front
                            of incrementing numbers
        :param site: String of site at image grid at which labels should be
                    adde ("top", "bottom", "left" or "right"). Depending on the
                    dimension (columns or rows) in which the category is,
                    top/bottom (for columns) might is better for left/right
                    (for rows).
        :param label_sub_remapped: Whether the new image numbers after remapped
                                    accoding to defined _sub categories should
                                    be used (if True) or whether original image
                                    numbers should be used (if False)
        :param font_size: font_size of labels; if None default for figure_panel
                            will be used
        :param padding: Padding in pt of labels from images
        :param font_size_factor: Factor by which the default font_size should be
                                 scaled to obtain font size for labels
        :param label_orientation:  "hor" or "vert"
                                    default is horizontal for "top" and "bottom"
                                    site and vertical for "left" and "right"
                                    site
        """

        label_cat = "images"
        if texts is None:
            max_image_nb = np.max(list(self.reassign_new_categories["images"].values()))
            texts = []
            for image_nb in range(1,max_image_nb + 2):
                if type(text_prefix) != type(None):
                    new_text = text_prefix + str(image_nb)
                else:
                    new_text = str(image_nb)
                texts.append(new_text)

        self._label_category(label_cat, texts, site = site, 
                             label_sub_remapped = label_sub_remapped,
                             font_size=font_size,
                             padding=padding, font_size_factor = font_size_factor,
                             label_orientation=label_orientation, **kwargs)


    def label_channels(self, texts, site=None, label_composites=False,
                       default_composite_label=None, font_size=None,
                       padding=2, font_size_factor = None,
                       label_orientation = None, **kwargs):
        """
        Label a category (images, channels, frames or slices; also _subs).

        :param texts: Text that should be used as labels; should match the
                            number of different values in the defined category
                            Same labels that are adjacent are only labeled
                            once across all affected images
        :param site: String of site at image grid at which labels should be
                    adde ("top", "bottom", "left" or "right"). Depending on the
                    dimension (columns or rows) in which the category is,
                    top/bottom (for columns) might is better for left/right
                    (for rows).
        :param label_composites: Whether to label composite channels
        :param font_size: font_size of labels; if None default for figure_panel
                            will be used
        :param default_composite_label: Default composite label to use,
                                        otherwise composites will be labeled
                                        as a combination of the channel names
                                        which are composited together
        :param padding: Padding in pt of labels from images
        :param font_size_factor: Factor by which the default font_size should be
                                 scaled to obtain font size for labels
        :param label_orientation:  "hor" or "vert"
                                    default is horizontal for "top" and "bottom"
                                    site and vertical for "left" and "right"
                                    site
        """
        label_cat = "channels"

        self._label_category(label_cat, texts, site = site,
                             label_composites=label_composites,
                             default_composite_label=default_composite_label,
                             font_size=font_size,
                             padding=padding, font_size_factor=font_size_factor,
                             label_orientation=label_orientation, **kwargs)


    def label_frames(self, texts=None, site=None, label_sub_remapped=False,
                     font_size = None, padding=2,
                    font_size_factor = None, label_orientation = None,
                    start_time = 0, time_per_frame="1m", format="hh:mm",
                     show_unit=True, first_time_difference=1, frame_jumps=None,
                     long_unit_names = True, all_units_shown = False, **kwargs):
        """
        Label a category (images, channels, frames or slices; also _subs).

        :param texts: Text that should be used as labels; should match the
                            number of different values in the defined category
                            Same labels that are adjacent are only labeled
                            once across all affected images
        :param site: String of site at image grid at which labels should be
                    adde ("top", "bottom", "left" or "right"). Depending on the
                    dimension (columns or rows) in which the category is,
                    top/bottom (for columns) might is better for left/right
                    (for rows).
        :param label_sub_remapped: Whether the new image numbers after remapped
                                    accoding to defined _sub categories should
                                    be used (if True) or whether original image
                                    numbers should be used (if False)
        :param font_size: font_size of labels; if None default for figure_panel
                            will be used
        :param padding: Padding in pt of labels from images
        :param font_size_factor: Factor by which the default font_size should be
                                 scaled to obtain font size for labels
        :param label_orientation: "hor" or "vert"
                                    default is horizontal for "top" and "bottom"
                                    site and vertical for "left" and "right"
                                    site
        :param start_time: number of first timeframe
        :param time_per_frame: string of number and unit ("m" for min,
                                "h" for hour, or "s" for second) for
                                time difference between frames
        :param format: format of how time should be displayed.
                        The number of letter indicates the number of digits
                        in that category. Possible categories are "s" for
                        seconds, "m" for minutes or "h" for hours.
        :param show_unit: Whether to show unit name in the label of the time
        :param first_time_difference: Difference of timesteps
                                        from first to second frame
                                        (helpful if after a first frame there
                                        was an imaging break, longer than the
                                        normal time between frames)
        :param frame_jumps: Dictionary with keys being timepoint before which
                            timejumps happened and values being number of frames
                            that the jump was long (e.g. {4: 2, 10:20} for a
                            timejump of 2 timeframes before timeframe 5 and a
                            timejump of 20 timeframes before timeframe 11)
        :param long_unit_names: Whether to use long unit names ("min" instead of
                                "m", "hour" instead of "h" and "sec" instead of
                                "s").
        :param all_units_shown: Whether to show the unit name of the
                                first unit in the format (e.g. "h" for "hh:mm)
                                (if False) or both unit names separated by ":"
                                (if True)
        """

        label_cat = "frames"
        # get frame to annotate automatically
        if texts == None:
            texts = []
            frame_points = self.category_vals["frames"]
            for frame_point in frame_points:
                text = self._get_frame_string(frame_point, start_time,
                                             time_per_frame, format, show_unit,
                                            first_time_difference, frame_jumps,
                                            long_unit_names, all_units_shown)
                texts.append(text)

        self._label_category(label_cat, texts, site = site,
                             label_sub_remapped = label_sub_remapped,
                             font_size = font_size,
                             padding = padding,
                             font_size_factor = font_size_factor,
                             label_orientation = label_orientation, **kwargs)


    def _label_category(self, label_cat, label_vals, site=None,
                        label_sub_remapped=False, label_composites=False,
                        default_composite_label=None, font_size=None, padding=2,
                        font_size_factor=None, label_orientation = None,
                        plot_line=None, string_separating_channels=" + ",
                        **kwargs):
        """
        :param label_cat: category that should be labeled, can be "images", "channels", or "frames"
        :param label_vals: labels that will be assigned to the category values of the label_cat
            order needs to correspond to ascending order of category values
            (e.g. channel1, channel2, etc.)
        """

        positions_for_cat_vals = self.default_label_positions[label_cat]

        positions_for_cat_vals = self._remap_image_for_sub_cat(positions_for_cat_vals,
                                                              label_cat,
                                                              label_sub_remapped)

        all_cat_vals = list(positions_for_cat_vals.keys())
        all_cat_vals.sort(key=self._sort_category_vals_key)

        # find first site that actually works without overlapping labels
        if site == None:
            site = self._find_site_without_overlapping_labels(all_cat_vals,
                                                             positions_for_cat_vals)

        # check if plot_line should be switched to False
        # since no label has more than one row
        if self._is_none(plot_line):
            plot_line = False
            plot_line = self._check_if_label_has_multiple_rows(all_cat_vals,
                                                              positions_for_cat_vals,
                                                              site)

        (positions_for_cat_vals,
         all_cat_vals,
         label_vals) = self._pool_adjacent_similar_labels(label_vals, all_cat_vals,
                                                         positions_for_cat_vals,
                                                         label_cat)

        # initiate counter for multiple categories (composite channels)
        for cat_nb, cat_val in enumerate(all_cat_vals):
            site_positions = positions_for_cat_vals[cat_val]

            # for composites either label wth default_composite_label or with
            # combination of labels of respective channels
            # labeling with channel names in respective colors is not possible
            # this has to be done within the image
            if type(cat_val) in self.itertypes:
                label_text = ""
                if (label_composites) | (default_composite_label != None):
                    if not label_composites:
                        print("WARNING: Since '{}' was supplied as "
                              "default_composite_label, "
                              "composite channels will be printed "
                              "even though label_composite "
                              "is False.".format(default_composite_label))
                    if default_composite_label != None:
                        label_text = str(default_composite_label)
                    else:
                        # if default composite label is None,
                        #  then use a combination of label_texts
                        #  from all the labels included
                        # build label_text from texts of all channels
                        for cat_val_nb, composite_cat_val in enumerate(cat_val):
                            if (cat_val_nb) > 0:
                                label_text += string_separating_channels
                            label_text += str(label_vals[composite_cat_val])
            else:
                if cat_nb >= len(label_vals):
                    print("WARNING: Not enough labels were supplied for labeling "
                          "category in panel {}".format(self.letter))
                    break
                label_text = label_vals[cat_nb]

            label_positions = site_positions[site]
            row_start = label_positions[0][0]
            col_start = label_positions[0][1]
            row_end = label_positions[1][0]
            col_end = label_positions[1][1]

            self._add_label(label_text, row_start, row_end, col_start,
                            col_end, site, font_size, padding,
                            font_size_factor, label_orientation,
                            plot_line=plot_line, **kwargs)


    def _remap_image_for_sub_cat(self,positions_for_cat_vals, label_cat,
                                label_sub_remapped):
        # allow to label sub_remapped images
        # if the _sub category is defined for the current label_cat
        # for that remap the positions_for_cat_vals dict
        if not ((label_cat+"_sub" in self.sub_category_map) & 
                label_sub_remapped):
            return positions_for_cat_vals
        new_positions_for_cat_vals = {}
        for image_nb, value in  positions_for_cat_vals.items():
            image_nb_remapped = self.reassign_new_categories["images"][image_nb]
            if image_nb_remapped not in new_positions_for_cat_vals:
                new_positions_for_cat_vals[image_nb_remapped] = value
        positions_for_cat_vals = new_positions_for_cat_vals
        return positions_for_cat_vals

    def _find_site_without_overlapping_labels(self, all_cat_vals,
                                             positions_for_cat_vals):
        all_sites = positions_for_cat_vals[list(positions_for_cat_vals)[0]].keys()
        for site in all_sites:
            last_label_positions = None
            site_works = True
            for cat_val in all_cat_vals:
                site_positions =  positions_for_cat_vals[cat_val]
                label_positions = site_positions[site]
                if last_label_positions != label_positions:
                    last_label_positions = label_positions
                else:
                    site_works = False
                    break
            if site_works:
                return site

    def _check_if_label_has_multiple_rows(self, all_cat_vals,
                                         positions_for_cat_vals, site):
        for cat_val in all_cat_vals:
            site_positions =  positions_for_cat_vals[cat_val]
            label_positions = site_positions[site]
            if label_positions[0] != label_positions[1]:
                return True
        return False

    def _pool_adjacent_similar_labels(self, label_vals, all_cat_vals,
                                     positions_for_cat_vals, label_cat):
        # pool positions for same labels together
        # if labels appear directly after one another
        new_positions_for_cat_vals = {}
        new_all_cat_vals = []
        new_label_vals = []
        printed_warning = False

        for label_nb, label in enumerate(label_vals):
            # if more labels were defined than cat vals
            # are present, ignore too many cat vals
            # & output warning
            if len(all_cat_vals) <= label_nb:
                if not printed_warning:
                    warning_msg = (f"WARNING: For labelling {label_cat} in "
                                   f"panel {self.letter} more "
                                   f"labels were defined than values exist in "
                                   f"the category. From label '{repr(label)}' "
                                   f"on no label was used.")
                    print(warning_msg)
                    printed_warning = True
                continue
            cat_val = all_cat_vals[label_nb]
            # initialize if first
            if label_nb == 0:
                pool_positions = False
            else:
                # if label is the same as label before
                # pool positions of label
                if label == last_label:
                    pool_positions = True
                else:
                    pool_positions = False

            if pool_positions:
                for dict_site, range_at_site in new_positions_for_cat_vals[
                    last_cat_val].items():
                    additional_ranges = positions_for_cat_vals[cat_val][
                        dict_site]
                    # for left and right get min and max of first coordinate
                    #  (row position in image grid)
                    if (dict_site == "left") | (dict_site == "right"):
                        index_for_site = 0
                    # for top and bottom get min and max of second coordinate
                    # (column position in image grid)
                    if (dict_site == "top") | (dict_site == "bottom"):
                        index_for_site = 1
                    # get minimum in first position / start of range
                    range_min = min(range_at_site[0][index_for_site],
                                    additional_ranges[0][index_for_site])
                    # get maximum in second position / end of range
                    range_max = max(range_at_site[1][index_for_site],
                                    additional_ranges[1][index_for_site])
                    # get new start and end positions for range
                    range_start = [0, 0]
                    range_start[index_for_site] = range_min
                    range_start[index_for_site - 1] = range_at_site[0][
                        index_for_site - 1]
                    range_end = [0, 0]
                    range_end[index_for_site] = range_max
                    range_end[index_for_site - 1] = range_at_site[1][
                        index_for_site - 1]
                    new_positions_for_cat_vals[last_cat_val][dict_site] = [
                        range_start, range_end]

            else:
                new_positions_for_cat_vals[cat_val] = positions_for_cat_vals[
                    cat_val]
                new_all_cat_vals.append(cat_val)
                new_label_vals.append(label)
                last_label = label
                last_cat_val = cat_val

        return (new_positions_for_cat_vals, new_all_cat_vals, new_label_vals)

    def label(self, text, position=None, span=None, site = "left",
              font_size=None, padding=2, label_orientation=None, **kwargs):
        """
        Label specific positions in image grid directly.

        :param text: Text to use as label
        :param position: Position (integer) in image grid to label
        :param span: Number of images that should be spanned by label
        :param site: site at which the label should be added
                        ("top","bottom", "left" or "right")
        :param font_size: font size of label added
        :param padding: Padding from images in pt of label
        :param label_orientation: Orientation of labels ("hor" or "vert")
                                    default is horizontal for "top" and "bottom"
                                    site and vertical for "left" and "right"
                                    site

        """
        # this is when labelling by position and not by category
        # DO NOT ALLOW in between rows or column labels
        (row_start, row_end,
         col_start,  col_end) = self._validate_and_set_site_defaults(site,
                                                                     position,
                                                                     span)
        self._add_label(text, row_start, row_end, col_start, col_end, site,
                        font_size, padding, label_orientation, **kwargs)



    def _add_label(self, text, row_start, row_end, col_start, col_end,
                   site="left",  font_size=None, padding = 3,
                   font_size_factor=None,  label_orientation = None,
                   plot_line = True,  line_end_padding = 0.02, line_width = 1,
                   line_color="black", align_all_labels = False,
                   plot_line_for_all=False):
        """
        :param text: text that should be displayed in label
        :param site: "top", "bottom", "left" or "right"
        :param start: row or column at which the label should start
        :param end: row or column at which the label should end,
                    if None, label will only be shown in start
        :param plot_line: whether a line should be used for labels
                        stretching over multiple images
        :param plot_line_for_all: Whether a line should be used for all labels
        :param line_end_padding: Padding at the end of plotted lines in inches
        :param align_all_labels: align all labels, including those with
                                and those without a line
                                this increases the distance of labels
                                without line to the image
        """

        # do not plot line f there is no text:
        if text == "":
            plot_line_for_all = False
            plot_line = False

        if plot_line_for_all:
            plot_line =True

        # check whther label stretches over more than one image
        # only plot lines for labels that stretch over more than one image
        multi_image = False
        if (row_start != row_end) | (col_start != col_end):
            multi_image = True

        fig = plt.gcf()

        if font_size == None:
            font_size = self.font_size

        if font_size_factor != None:
            font_size = self.font_size * font_size_factor

        font_size_pt = FontProperties(size=font_size).get_size_in_points()

        rotation_degrees = self._get_rotation_degrees(label_orientation, site)

        # reduce padding if lower part of text is in direction of images
        # if its not multi_image (no line will be drawn) and
        #  not all labels should be aligned
        # then decrease padding of labels without line
        if ((not plot_line) |
                ((not multi_image) & (not align_all_labels)) |
                (plot_line_for_all)):
            padding *= 0.4
            
        padding_px = padding * fig.dpi / 72


        # check if labels are already present at of the postions of new label
        # checking for anything else in the matrix allows later to also account
        #  for different font sizes for different labels
        labels_at_site = self.label_matrices[site][row_start:row_end+1,
                                                    col_start:col_end+1]

        if 1 in np.unique(labels_at_site):
            raise ValueError("There is already a label on the {} at one "
                             "position where the new label '{}' "
                             "should go.".format(site, text))

        # create ax for label, set coordinates according to positions defined (row_start etc)
        # set values for outer site of label to outer border
        label_for_plot = (self.letter +"_"+ site + "_" + str(row_start) +
                          "-" + str(row_end) + "_" + str(col_start) +
                          "-" + str(col_end))
        ax_label = fig.add_subplot(label=label_for_plot)
        ax_label.set_axis_off()

        # increase padding by 50% to calculate shift to account
        #  for additional space next to line
        # but only if the line is plotted
        # if line is plotted in general and will be
        #  for the current label (multi_image)
        # or if line is plotted in general and all labels
        #  (with and without lines) should be aligned
        if (plot_line & (multi_image | align_all_labels)) | (plot_line_for_all):
            # since additional padding for top labels is 1/4 and
            #  not 1/2 increase padding acordingly
            if site == "top":
                padding_px_for_shift = padding_px *  1.5
            else:
                padding_px_for_shift = padding_px *  2
        else:
            padding_px_for_shift = padding_px

        # TODO:
        # for composites: fuse text objects together
        # check if text objects fused together are wider than image
        # if so, add \n after each time that the text is wider than the image

        total_x_shift, total_y_shift, label_size = self._set_shift_values(site,
                                                                         font_size_pt,
                                                                         padding_px_for_shift,
                                                                         ax_label,
                                                                         text,
                                                                         rotation_degrees)

        # first shift all axes to get correct positions for labels based on new axes position
        if (total_x_shift != None) | (total_y_shift != None):

            # track all new x spaces made by adjusting ax size in both dimensions simultaneously
            # while only needing it in the dimension where label is added
            # allows also for figures with images in one panel which
            # are not aligned in rows with similar heights and columns with similar widths
            # COMMENT: probably those asymmetrical figures will not be generated
            # but in case this will be implemented, the current code should support labels for those as well
            self._shift_and_transform_axs(site, total_x_shift,
                                         total_y_shift, padding_px)


        # check if any label ax is already at the same site
        # if there is one, no shifting was done by shift_values,
        # retrieve start position of last label to annotate label
        # DOES NOT SUPPORT LABELS IN BETWEEN ROWS AND COLUMNS!
        x0, x1, y0, y1 = self._get_label_position_from_present_label(site)
        # annotate text at correct position

        (x0, y0,
         label_width, 
         label_height) = self._get_final_label_position_and_dimension(row_start,
                                                                    row_end,
                                                                    col_start,
                                                                    col_end,
                                                                    site,
                                                                    padding_px,
                                                                    x0=x0,
                                                                    x1=x1,
                                                                    y0=y0,
                                                                    y1 =y1)

        ax_label.set_position((x0,y0,label_width,label_height))

        if (plot_line & multi_image) | plot_line_for_all:
            self._plot_line_for_image_label(ax_label, site, line_end_padding,
                                           line_width, line_color)

        x_text, y_text = self._get_position_of_text(ax_label, text, site,
                                                   font_size_pt,
                                                   rotation_degrees, padding_px,
                                                   plot_line)

        ha, va = self._get_label_alignment(rotation_degrees, site)

        label = ax_label.annotate(
            text, xy=(x_text, y_text),
            xycoords='axes fraction', ha=ha, va=va,
            rotation = rotation_degrees,
            fontsize=font_size_pt,fontweight='normal',
            linespacing=1,
            clip_on=False, annotation_clip=False)

        label.set_position([x_text, y_text])

        self.label_padding_px[site].append(padding_px)
        self.label_lines_ploted[site].append(plot_line)
        self.labels[site].append(label)
        self.label_axs[site].append(ax_label)
        # set positions 1 where labels were added
        self.label_matrices[site][row_start:row_end+1,
                                  col_start:col_end+1] = max(np.max(self.label_matrices[site]) + 1, 0)

    def _get_rotation_degrees(self, label_orientation, site):

        if label_orientation == "hor":
            rotation_degrees = 0
        elif label_orientation == "vert":
            rotation_degrees = 90
        else:
            if (site == "top") | (site == "bottom"):
                rotation_degrees = 0
            elif (site == "left") | (site == "right"):
                # if label is left or right, rotate text by 90 degree
                rotation_degrees = 90
        return rotation_degrees

    def _plot_line_for_image_label(self, ax_label, site, line_end_padding,
                                  line_width, line_color):
        """
        Plot line with padding for one image label.
        :param site: Site of label ("bottom", "top", "left" or "right")
        :param line_end_padding: Padding of line to end of image
                                (in direction of line) in points
        :param ax_label: axes where label is added
        :return: None
        """
        fig = plt.gcf()
        # add padding to end of lines to separate lines better
        line_end_padding_rel_x = (line_end_padding /
                                  (ax_label.get_position().width *
                                   fig.get_size_inches()[0]))
        line_end_padding_rel_y = (line_end_padding /
                                  (ax_label.get_position().height *
                                   fig.get_size_inches()[1]))
        if site == "left":
            line_x = [1, 1]
            line_y = [line_end_padding_rel_y, 1-line_end_padding_rel_y]
        elif site == "right":
            line_x = [0, 0]
            line_y = [line_end_padding_rel_y, 1-line_end_padding_rel_y]
        elif site == "top":
            line_x = [line_end_padding_rel_x, 1-line_end_padding_rel_x]
            line_y = [0, 0]
        elif site == "bottom":
            line_x = [line_end_padding_rel_x, 1-line_end_padding_rel_x]
            line_y = [1, 1]

        line = lines.Line2D(line_x, line_y, lw = line_width,
                            color = line_color,
                            transform=ax_label.transAxes,
                            solid_capstyle="butt")
        ax_label.add_line(line)
        return None


    def _get_label_alignment(self, rotation_degrees, site):
        """
        Get alignment of a label depending on rotation degrees
        :param rotation_degrees: rotation of label in degrees
        :return: horizontal alignment (ha) and vertical alignment (va) 
                as tuple of strings
        """
        ha = "center"
        if (rotation_degrees == 0):
            if ( site == "left"):
                ha = "right"
            elif (site == "right"):
                ha = "left"
        va = "center"
        if (rotation_degrees == 90):
            if (site == "top"):
                va = "top"
            elif (site == "bottom"):
                va = "bottom"
        return ha, va

    @staticmethod
    def _is_none(object):
        return object is None


    def _validate_and_set_site_defaults(self, site, position, span):

        valid_sites = ["left","right","bottom","top"]
        if site not in valid_sites:
            raise ValueError("The entered site {} is not valid. Only the "
                             "following sites are valid: "
                             "{}.".format(site,", ".join(valid_sites)))

        start = position

        if (not FigurePanel._is_none(start)) & (not FigurePanel._is_none(span)):
            end = start + span
        else:
            end = span

        # DO NOT ALLOW in between rows or column labels
        # still, code for tracking labels allows to also track labels in between,
        #  in case this will be implemented later...
        # if label is left or right, dont allow to choose the column
        if (site == "left") | (site == "right"):
            if FigurePanel._is_none(start):
                # if none, start at first row
                row_start = 0
            else:
                row_start = start
            if FigurePanel._is_none(end):
                # if both are None, label should go from first to last row
                if FigurePanel._is_none(start):
                    row_end = self.max_row
                else:
                    # if only end is none, stop label where it started
                    row_end = row_start
            else:
                row_end = end
            if site == "left":
                col_start = 0
                col_end = 0
            elif site == "right":
                col_start = self.max_col
                col_end = self.max_col
        elif (site == "top") | (site == "bottom"):
            # set standard values (very left for start and very right for end)
            if FigurePanel._is_none(start):
                col_start = 0
            else:
                col_start = start
            if FigurePanel._is_none(end):
                if FigurePanel._is_none(start):
                    # if both are None, label should go from first to last column
                    col_end = self.max_col
                else:
                    # if only end is none, stop label where it started
                    col_end = col_start
            else:
                col_end = end
            # set values to put top labels top and bottom labels bottom
            if site == "bottom":
                row_start = self.max_row
                row_end = self.max_row
            elif site == "top":
                row_start = 0
                row_end = 0
        return row_start, row_end, col_start, col_end


    def _set_shift_values(self, site, font_size_pt, padding_px, ax, text,
                         rotation_degrees):
        get_label_size = self._get_label_size_depending_on_rotation_and_site
        label_size = get_label_size(ax, text, font_size_pt, site,
                                    rotation_degrees)
        if site == "left":
            total_x_shift = label_size + padding_px
            total_y_shift = None
        elif site == "right":
            total_x_shift = - (label_size + padding_px)
            total_y_shift = None
        elif site == "bottom":
            total_x_shift = None
            total_y_shift = label_size + padding_px
        elif site == "top":
            total_x_shift = None
            total_y_shift = - (label_size + padding_px)
        return total_x_shift, total_y_shift, label_size


    def _create_attribute_matrices_for_axs(self):
        # create one matrix with heights, one with widths,
        #  one with x0 and one with y0 of all axs
        fig = plt.gcf()
        fig_size_px = fig.get_size_inches() * fig.dpi
        # set each element in array as very small negative number
        # thereby its clear that negative numbers indicate an empty spot
        # and the small negative numbers dont change any calculation meaningfully
        heights = np.full((self.max_row+1,self.max_col+1),-0.00000001)
        widths = np.full((self.max_row+1,self.max_col+1),-0.00000001)
        x0s = np.full((self.max_row+1,self.max_col+1),-0.00000001)
        y0s = np.full((self.max_row+1,self.max_col+1),-0.00000001)
        for ax_pos, ax in self.all_axs.items():
            row = ax_pos[0]
            col = ax_pos[1]
            ax_size_px = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
            ax_coords = ax.get_position()
            widths[row,col] = ax_size_px.width * fig.dpi
            heights[row,col] = ax_size_px.height * fig.dpi
            x0s[row,col] = ax_coords.x0 * fig_size_px[0]
            y0s[row,col] = ax_coords.y0 * fig_size_px[1]
        return widths, heights, x0s, y0s


    def _get_label_position_from_present_label(self,site):
        x0 = None
        x1 = None
        y0 = None
        y1 = None
        # check if any label ax is already at the same site
        # if there is one, dont do any shifting, just add label
        # retrieve start position of last label
        # DOES NOT YET SUPPORT LABELS IN BETWEEN ROWS AND COLUMNS!
        if len(self.label_axs[site]) > 0:
            ax_label_ref = self.label_axs[site][0]
            ax_label_ref_coords = ax_label_ref.get_position()
            # choose first value, as this is the np.inf value,
            #  equalling the x position
            if (site == "left"):
                x0 = ax_label_ref_coords.x0
            elif (site == "right"):
                x1 = ax_label_ref_coords.x1
            elif (site == "top"):
                y1 = ax_label_ref_coords.y1
            elif (site == "bottom"):
                y0 = ax_label_ref_coords.y0
        return x0, x1, y0, y1


    def _get_final_label_position_and_dimension(self, row_start, row_end,
                                                col_start, col_end, site, 
                                               padding_px,
                                                x0 = None, x1 = None, 
                                               y0 = None, y1 = None):
        fig = plt.gcf()
        fig_size_px = fig.get_size_inches() * fig.dpi
        first_x_coords, last_y_coords = self._get_axs_to_define_x_and_y_coords_for_position((row_start,
                                                                                            col_start))
        last_x_coords, first_y_coords = self._get_axs_to_define_x_and_y_coords_for_position((row_end,
                                                                                            col_end))

        # test whether first is really first, otherwise switch first and last

        if x0 == None:
            if site == "left":
                x0 = self.inner_border[0]
            elif site == "right":
                x0 = first_x_coords.x1 + padding_px / fig_size_px[0]
            else:
                x0 = first_x_coords.x0
                #  x0 = x0s[row_start,col_start] / fig_size_px[0]
        if x1 == None:
            if site == "right":
                x1 = self.inner_border[1]
            elif site == "left":
                x1 = first_x_coords.x0 - padding_px / fig_size_px[0]
            else:
                x1 = last_x_coords.x1
                #  x1 = (x0s[row_start,col_end] +
                #  widths[row_start,col_end])  / fig_size_px[0]
        if y0 == None:
            if site == "bottom":
                y0 = self.inner_border[2]
            elif site == "top":
                y0 = first_y_coords.y1 + padding_px / fig_size_px[1]
            else:
                y0 = first_y_coords.y0
                #  y0 = y0s[row_end,col_start] / fig_size_px[1]
        if y1 == None:
            if site == "top":
                y1 = self.inner_border[3]
            elif site == "bottom":
                y1 = first_y_coords.y0 - padding_px / fig_size_px[1]
            else:
                y1 = last_y_coords.y1
                #  y1 = (y0s[row_start,col_start] +
                #  heights[row_start,col_start]) / fig_size_px[1]

        # set positions where current label is put as 1 in respective matrix
        label_width = x1 - x0
        label_height = y1 - y0

        return x0, y0, label_width, label_height



    def _get_position_of_text(self, ax_label, text, site, font_size_pt,
                             rotation_degrees, padding_px = None,
                             plot_line=False):
        ax_label_coords = ax_label.get_position()
        label_height = ax_label_coords.height
        label_width = ax_label_coords.width

        fig = plt.gcf()
        fig_size_px = fig.get_size_inches() * fig.dpi

        label_size = self._get_label_size_depending_on_rotation_and_site(ax_label,
                                                                        text,
                                                                        font_size_pt,
                                                                        site,
                                                                        rotation_degrees)

        # divide label size by two since horizontal alignment (ha) for horizontal labels
        # and vertical alignment (va) for vertical labels will be centered
        # label site should than only considered as half to center it in the same position
        vert_rotation_hor_edge = ((rotation_degrees == 90) &
                                  ((site =="left") | (site == "right")))
        hor_rotation_vert_edge = ((rotation_degrees == 0) &
                                  ((site == "top") | (site == "bottom")))
        if vert_rotation_hor_edge | hor_rotation_vert_edge:
            label_size /= 2

        if (padding_px != None) & (plot_line == True):
            padding_px_rel_width = padding_px / (ax_label.get_position().width *
                                                 fig_size_px[0])
            padding_px_rel_height = padding_px / (ax_label.get_position().height *
                                                  fig_size_px[1])
        else:
            padding_px_rel_width = 0
            padding_px_rel_height = 0

        # move label completely into plot since position ha=center
        # puts it directly on the line (half in, half out)
        if site == "top":
            x_text = 0.5
            y_text = (label_size / (label_height * fig_size_px[1]))
            if not hor_rotation_vert_edge:
                y_text = 0
            y_text += padding_px_rel_height/2

        elif site == "bottom":
            x_text = 0.5
            y_text = 1 - (label_size / (label_height * fig_size_px[1]))
            if not hor_rotation_vert_edge:
                y_text = 1
            y_text -= padding_px_rel_height

        elif site == "left":
            y_text = 0.5
            x_text = 1 - (label_size / (label_width * fig_size_px[0]))
            if not vert_rotation_hor_edge:
                x_text = 1
            x_text -= padding_px_rel_width

        elif site == "right":
            y_text = 0.5
            x_text = (label_size / (label_width * fig_size_px[0]))
            if not vert_rotation_hor_edge:
                x_text = 0
            x_text += padding_px_rel_width

        return x_text,y_text


    def _get_label_size_depending_on_rotation_and_site(self, ax, text,
                                                      font_size_pt, site,
                                                      rotation_degrees):
        get_text_dimension = FigurePanel._get_dimension_of_text
        label_width, label_height = get_text_dimension(text, font_size_pt,
                                                       ax, rotation_degrees)
        if (site == "left") | (site == "right"):
            label_size = label_width
        elif (site == "top") | (site == "bottom"):
            label_size = label_height

        return label_size

    @staticmethod
    def _get_direct_shift_and_remaining_space(site,total_shift,space):
        # compare space to shift that would need to be done
        # reduce total shift by available space that already happened

        # get absolute to calculate difference correctly
        total_shift = abs(total_shift)
        if total_shift <= space:
            # divide total_shift by 2 to distribute shift among
            #  both spaces on each site equally
            # this is necessary since the image grid is centered
            #  before the shifting
            # and should be centered after the shifting
            # accounting for other alignments than center will be done
            #  further downstream
            # processing other alignments could also be done here
            #  (and would be nicer here)
            #  but require some careful testing
            direct_shift = total_shift / 2

            space = space - total_shift
            total_shift = None
        else:
            total_shift = total_shift - space
            direct_shift = space / 2
            space = 0

        # shift in opposite direction for right and top label
        if (site == "right") | (site == "top"):
            direct_shift = - direct_shift
            if total_shift != None:
                total_shift = - total_shift

        return total_shift, direct_shift, space


    def _process_and_use_available_space(self, site,
                                        total_x_shift, total_y_shift):
        fig = plt.gcf()
        fig_size_px = fig.get_size_inches() * fig.dpi
        direct_x_shift = 0
        direct_y_shift = 0
        # check for current space and compare to shift necessary
        # get direct shift from space and possibly have remainder
        #  of total shift to do (that will include changing size of ax)
        if not self._is_none(total_y_shift):
            # if there is more y space than y shift
            # set y shift as 0
            if abs(total_y_shift) < self.space_for_labels[site]:
                total_y_shift = 0
            else:
                # deduct available space from y shift
                if total_y_shift < 0:
                    total_y_shift += self.space_for_labels[site]
                elif total_y_shift > 0:
                    total_y_shift -= self.space_for_labels[site]

            # increase space for labels on the site
            # if the new y shift is larger
            self.space_for_labels[site] = max(abs(total_y_shift),
                                              self.space_for_labels[site])

            (total_y_shift,
             direct_y_shift_px,
             self.y_space) = self._get_direct_shift_and_remaining_space(site,
                                                                       total_y_shift,
                                                                       self.y_space)

            direct_y_shift = direct_y_shift_px / fig_size_px[1]

        elif not self._is_none(total_x_shift) > 0:
            # if there is more space than x shift
            # set y shift as 0
            if abs(total_x_shift) < self.space_for_labels[site]:
                total_x_shift = 0
            else:
                # deduct available space from y shift
                if total_x_shift < 0:
                    total_x_shift += self.space_for_labels[site]
                elif total_x_shift > 0:
                    total_x_shift -= self.space_for_labels[site]
            # increase space for labels on the site
            # if the new y shift is larger
            self.space_for_labels[site] = max(abs(total_x_shift),
                                              self.space_for_labels[site])

            (total_x_shift,
             direct_x_shift_px,
             self.x_space) = self._get_direct_shift_and_remaining_space(site,
                                                                       total_x_shift,
                                                                       self.x_space)

            direct_x_shift = direct_x_shift_px / fig_size_px[0]

        # direct shift is the shift that is done based on the available space right now
        # all remaining shift will be done afterwards
        # and space will be made through making panel axes objects smaller
        if self.hor_alignment == "left":
            # shift to the right (positive) is OK
            # however, shift to the left cannot happen
            # since the images are already on the very left
            # therefore, prevent negative values
            direct_x_shift = max(direct_x_shift, 0)
            # multiply frames two since it shouldnt be moved
            # to the middle
            direct_x_shift *= 2
        elif self.hor_alignment == "right":
            # same as for left but opposite:
            # dont allow positive shifts
            direct_x_shift = min(direct_x_shift, 0)
            direct_x_shift *= 2

        if self.vert_alignment == "top":
            # dont allow positive shifts
            #  (in direction of top)
            direct_y_shift = min(direct_y_shift, 0)
            direct_y_shift *= 2
        elif self.vert_alignment == "bottom":
            # dont allow negative shifts
            # (direction of bottom)
            direct_y_shift = max(direct_y_shift, 0)
            direct_y_shift *= 2

        if (direct_x_shift != 0) | (direct_y_shift != 0):

            # unchanged direct shifts are for center alignment
            # for left and right  / top and bottom must be changed

            self._shift_labels_parallel_to_shift(direct_x_shift,direct_y_shift)

            # shift all ax directly by the necessary of current 0 point
            #  to 0 point it should be (space for label)
            for ax in self.all_axs.values():
                ax_coords = ax.get_position()
                x0 = ax_coords.x0 + direct_x_shift
                y0 = ax_coords.y0 + direct_y_shift

                ax.set_position([x0,y0,ax_coords.width,ax_coords.height])

        return total_x_shift, total_y_shift


    def _shift_labels_parallel_to_shift(self,direct_x_shift,direct_y_shift):
        # shift labels parallel to shift direction
        if direct_x_shift != 0:
            sites_to_shift = ["top","bottom"]
        elif direct_y_shift != 0:
            sites_to_shift = ["left","right"]

        for site_to_shift in sites_to_shift:
            for ax in self.label_axs[site_to_shift]:
                ax_coords = ax.get_position()
                y0 = ax_coords.y0 + direct_y_shift
                x0 = ax_coords.x0 + direct_x_shift
                ax.set_position([x0,y0,ax_coords.width,ax_coords.height])



    def _create_dimension_reduction_matrices(self, total_y_shift,
                                            total_x_shift, heights, widths):
        fig = plt.gcf()
        # create matrix with width_reductions and
        #  one with height_reductions for all axs
        width_reductions = np.zeros((self.max_row+1,self.max_col+1))
        height_reductions = np.zeros((self.max_row+1,self.max_col+1))
        # IMPORTANT ERROR TO CORRECT AT ONE POINT:
        # for enlarged images, padding that is included
        #  in the new image size is not considered
        # for the image size since it is not included in heights and widths
        # therefore, larger images might get an unproportionally higher share
        #  of the height reduction
        # (really?)
        col_height, _ = self._get_col_height(heights)
        row_width, _ = self._get_row_width(widths)
        # get missing shift (x or y)
        for ax_pos, ax in self.all_axs.items():
            row = ax_pos[0]
            col = ax_pos[1]
            ax_size_inch = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
            ax_size_inch = [ax_size_inch.width, ax_size_inch.height]
            # for enlarged images, replace ax_size_inch with size before enlarging
            if ax_pos in self.orig_size_enlarged_images:
                ax_size_inch = np.array(self.orig_size_enlarged_images[ax_pos]) / fig.dpi
            if total_y_shift != None:
                # calculate change in height
                #  as part of the whole change in height necessary for label
                # extent of height is ratio of ax height compared to col_height
                height_reduction = ax_size_inch[1] * fig.dpi / col_height * total_y_shift
                height_reductions[row,col] = abs(height_reduction)
                # width reduction is proportional
                #  to height reduction as width is to height of ax
                width_reduction = height_reduction * ax_size_inch[0] / ax_size_inch[1]
                width_reductions[row,col] =  abs(width_reduction)
            elif total_x_shift != None:
                # calculate change in width similar as change of eight
                width_reduction = ax_size_inch[0] * fig.dpi / row_width * total_x_shift
                width_reductions[row,col] = abs(width_reduction)
                height_reduction = width_reduction * ax_size_inch[1] / ax_size_inch[0]
                height_reductions[row,col] =  abs(height_reduction)
        return width_reductions, height_reductions


    def _shift_and_transform_axs(self, site, total_x_shift,
                                total_y_shift, padding_px = 0):
        """
        Shift all images away from "site" by px
        :param total_x_shift: shift in x direction in px
        :param total_y_shift: shift in y direction in px
        :param padding_px: padding in each(?)  dimension in px
        """
        #  create one matrix with heights, one with widths,
        #  one with x0 and one with y0 of all axs
        widths, heights, x0s, y0s = self._create_attribute_matrices_for_axs()

        #  set widths and heights for positions
        #  with increased widths or heights to max
        #  in respective dimension
        #  first set it to zero to not consider it
        #  for getting the max values in the dimension
        for position, size in self.orig_size_enlarged_images.items():
            widths[position] = size[0]
            heights[position] = size[1]

        total_x_shift, total_y_shift = self._process_and_use_available_space(site,
                                                                            total_x_shift,
                                                                            total_y_shift)
        #  process remaining difference with normal code
        #  create matrix with width_reductions and
        #  one with height_reductions for all axs
        width_reductions, height_reductions = self._create_dimension_reduction_matrices(total_y_shift,
                                                                                       total_x_shift,
                                                                                       heights, widths)

        #  create matrices for new dimensions after reduction
        new_heights = heights - height_reductions
        new_widths = widths - width_reductions


        fig = plt.gcf()
        fig_size_px = fig.get_size_inches() * fig.dpi
        # shift all axs and change their size
        all_new_y_spaces = []
        all_new_x_spaces = []


        _, width_reductions_columns = self._get_row_width(width_reductions)
        _, height_reductions_rows = self._get_col_height(height_reductions)

        for ax_pos, ax in self.all_axs.items():

            new_y_space_ax = 0
            new_x_space_ax = 0
            row = ax_pos[0]
            col = ax_pos[1]

            ax_coords = ax.get_position()

            width_reduction = width_reductions[row, col]
            height_reduction = height_reductions[row, col]

            # adjust width and height reductions for enlarged images
            # scale it by the actual increase in size that these images have
            if ax_pos in self.orig_size_enlarged_images:
                pre_identity = self.pos_to_pre_identity_map[ax_pos]
                width_reduction *= self.size_factors_for_identities[pre_identity]
                # round(ax_coords.width / (self.orig_size_enlarged_images[ax_pos][0]
                #  / fig_size_px[0]))
                height_reduction *= self.size_factors_for_identities[pre_identity]
                # round(ax_coords.height /
                #  (self.orig_size_enlarged_images[ax_pos][1] / fig_size_px[1]))

            new_width = ax_coords.width - width_reduction / fig_size_px[0]
            new_height = ax_coords.height - height_reduction / fig_size_px[1]

            if site == "left":
                x_shift = np.sum(width_reductions_columns[col:])
                x_position = ax_coords.x0 + x_shift / fig_size_px[0]
                (y_position, 
                 new_y_space_ax) = self._get_vert_aligned_y_position_after_height_reduction(new_height,
                                                                                           row, col,
                                                                                           heights,
                                                                                           new_heights,
                                                                                           y0s,
                                                                                           fig_size_px)

            elif site == "right":
                x_shift = - np.sum(width_reductions_columns[:col])
                x_position = ax_coords.x0 + x_shift / fig_size_px[0]
                (y_position,
                 new_y_space_ax) = self._get_vert_aligned_y_position_after_height_reduction(new_height,
                                                                                           row, col,
                                                                                           heights,
                                                                                           new_heights,
                                                                                           y0s,
                                                                                           fig_size_px)

            elif site == "bottom":
                y_shift = np.sum(height_reductions_rows[:row+1])
                y_position = ax_coords.y0 + y_shift / fig_size_px[1]
                (x_position,
                 new_x_space_ax) = self._get_hor_aligned_x_position_after_width_reduction(new_width,
                                                                                         row, col,
                                                                                         widths,
                                                                                         new_widths,
                                                                                         x0s,
                                                                                         fig_size_px)

            elif site == "top":
                y_shift = - np.sum(height_reductions_rows[row+1:])
                y_position = ax_coords.y0 + y_shift / fig_size_px[1]
                (x_position,
                 new_x_space_ax) = self._get_hor_aligned_x_position_after_width_reduction(new_width,
                                                                                       row,
                                                                                       col,
                                                                                       widths,
                                                                                       new_widths,
                                                                                       x0s,
                                                                                       fig_size_px)

            all_new_y_spaces.append(new_y_space_ax)
            all_new_x_spaces.append(new_x_space_ax)

            # adjust position of annotations
            for child in ax.get_children():
                if not isinstance(child, matplotlib.text.Annotation):
                    continue
                if child.get_label().find("inside_image") != -1:
                    continue

                child_bbox = child.get_tightbbox(fig.canvas.get_renderer())
                child_coords = self._bbox_to_list(child_bbox)

                ax_coords_px = self._bbox_to_list(ax_coords)
                # get ax coords

                ax_coords_px[0] *= fig_size_px[0]
                ax_coords_px[1] *= fig_size_px[1]
                ax_coords_px[2] *= fig_size_px[0]
                ax_coords_px[3] *= fig_size_px[1]
                # get child_coords in relative figure coords
                # get px coords in ax
                
                child_coords[0] -= ax_coords_px[0]
                child_coords[1] -= ax_coords_px[1]
                child_coords[2] -= ax_coords_px[0]
                child_coords[3] -= ax_coords_px[1]
                
                ax_width_px = ax_coords.width * fig_size_px[0]
                ax_height_px = ax_coords.height * fig_size_px[1]
                
                child_coords[0] /= ax_width_px
                child_coords[1] /= ax_height_px
                child_coords[2] /= ax_width_px
                child_coords[3] /= ax_height_px

                # check if annotation is closer to top or bottom
                top_diff = 1 - child_coords[3]
                if height_reduction > 0:
                    height_reduction_factor = 1 - (height_reduction /
                                                   ax_height_px)
                    # calculate factor to keep top_diff (in inches) the same
                    distance_increase_factor = 1 / height_reduction_factor
                    # child_coords[1] is the distance from bottom
                    if top_diff < child_coords[1]:
                        # is closer to top
                        # therefore, move more down
                        # to calculate how much, take the difference
                        #  to the top at the start
                        # calculate how much larger it would need to be
                        # subtract 1 since we already have 1x top_diff
                        child_coords[1] -= ((1 - child_coords[1])  *
                                            (distance_increase_factor - 1))
                    else:
                        # is closer to bottom
                        # therefore, move more up
                        child_coords[1] += (child_coords[1] *
                                            (distance_increase_factor - 1))

                if width_reduction > 0:
                    right_diff = 1 - child_coords[2]
                    width_reduction_factor = 1 - (width_reduction / ax_width_px)

                    # calculate factor to keep top_diff (in inches) the same
                    distance_increase_factor = 1 / width_reduction_factor
                    # child_coords[0] is the distance from left
                    if right_diff < child_coords[0]:
                        # is closer to right
                        # therefore, move more left
                        child_coords[0] -= ((1 - child_coords[0]) *
                                            (distance_increase_factor - 1))
                    else:
                        # is closer to left
                        # therefore, move more right
                        child_coords[0] += (child_coords[0] *
                                            (distance_increase_factor - 1))

                child.set_position([child_coords[0],
                                    child_coords[1]])

            ax.set_position([x_position, y_position, new_width, new_height])

            self._shift_colorbars(ax_pos, x_position, y_position,
                                  new_width, new_height)

        self._shift_labels(padding_px)

        new_x_space = np.min(all_new_x_spaces)
        new_y_space = np.min(all_new_y_spaces)

        #  update orig size of enlarged images
        for position, size in self.orig_size_enlarged_images.items():
            ax = self.all_axs[position]
            self.orig_size_enlarged_images[position][0] -= width_reductions[position]
            self.orig_size_enlarged_images[position][1] -= height_reductions[position]

        self.y_space += new_y_space
        self.x_space += new_x_space


    def _shift_colorbars(self, ax_pos,
                         x_position, y_position, new_width, new_height):

        if ax_pos not in self.all_colorbars:
            return

        # also shift and transform colorbars
        colorbar = self.all_colorbars[ax_pos]
        colorbar_site = self.site_of_colorbars[ax_pos]
        colorbar_ax = colorbar.ax
        colorbar_ax_coords = colorbar_ax.get_position()
        colorbar_height = colorbar_ax_coords.height
        colorbar_width = colorbar_ax_coords.width
        if colorbar_site == "bottom":
            colorbar_x0 = x_position
            colorbar_y0 = (y_position - colorbar_height -
                           self.padding_of_colorbars)
            colorbar_width = new_width
        elif colorbar_site == "top":
            colorbar_x0 = x_position
            colorbar_y0 = y_position + new_height + self.padding_of_colorbars
            colorbar_width = new_width
        elif colorbar_site == "left":
            colorbar_x0 = (x_position - colorbar_width -
                           self.padding_of_colorbars)
            colorbar_y0 = y_position
            colorbar_height = new_height
        elif colorbar_site == "right":
            colorbar_x0 = x_position + new_width + self.padding_of_colorbars
            colorbar_y0 = y_position
            colorbar_height = new_height

        # use old colorbar height but otherwise
        #  same properties as for the normal ax
        colorbar_ax.set_position([colorbar_x0, colorbar_y0,
                                  colorbar_width, colorbar_height])


    def _bbox_to_list(self, bbox):
        return [bbox.x0, bbox.y0, bbox.x1, bbox.y1]


    def _get_hor_aligned_x_position_after_width_reduction(self, new_width, row,
                                                         col, widths,
                                                         new_widths, x0s,
                                                         fig_size):
        fig = plt.gcf()
        row_width,_ = self._get_row_width(widths)
        new_row_width, new_column_widths = self._get_row_width(new_widths)
        x_shift_by_padding, _ = self._get_shift_by_padding_for_position((row, col))
        width_left_of_plot = (np.sum(new_column_widths[:col]) +
                              x_shift_by_padding *
                              fig.get_size_inches()[0] * fig.dpi)

        # 0 position indicate no image at that position
        # get first x position that is not 0
        origin_x = 0
        new_row = row
        while (origin_x <= 0) & (x0s.shape[0] > new_row):
            origin_x = x0s[new_row,0]
            if new_row == row:
                new_row = 0
                # set row None to prevent the reset being
                #  triggered more than once
                row = None
            else:
                new_row += 1
                # stop if new col is out of boundaries of y0s
                if new_row >= x0s.shape[1]:
                    break


        #  Not necessary to fix for now, but should be later
        # align plot vertically centered in space given to plot
        # total space available for ax is the height of the row
        space_available = new_column_widths[col]
        # height_px of axes from supplied height of axes in figure fraction
        new_width_px = new_width * fig.get_size_inches()[0] * fig.dpi

        # not working for enlarged images at the moment
        #  their size is not only increased by a factor
        # but also increased by padding between images,
        #  which makes it harder to calculate the available space
        if new_width_px < space_available:
            # y shift is half of space that is not used
            x_shift_for_hor_center = (space_available - new_width_px) / 2
            # apply y shift
            width_left_of_plot += x_shift_for_hor_center


        fig_width = fig_size[0]
        # unchanged new_x_space is for center alignment
        new_x_space = row_width - new_row_width
        new_x_space_tmp = new_x_space
        if self.hor_alignment.lower() == "left":
            # no shift necessary since width reduction
            # is done from right
            # and plots already are aligned at the left
            new_x_space_tmp = 0
        elif self.hor_alignment.lower() == "right":
            new_x_space_tmp *= 2

        # get new x_position as start of plot from the left
        # for that the size_before_plot will be used as the size LEFT of the plot
        x_position = self._get_aligned_position_after_size_reduction(new_space = new_x_space_tmp,
                                                                     size_before_plot = width_left_of_plot,
                                                                     origin = origin_x,
                                                                     fig_size = fig_width)
        return x_position, new_x_space

    def _get_col_height(self, heights):
        row_heights = np.max(heights,axis=1)
        col_height = np.sum(row_heights)
        return col_height, row_heights

    def _get_row_width(self, widths):
        column_widths = np.max(widths, axis=0)
        row_width = np.sum(column_widths)
        return row_width, column_widths

    def _get_height_below_plot(self, row, new_row_heights,
                              y_shift_by_padding, fig):

        fig_height_px = fig.get_size_inches()[1] * fig.dpi

        return (np.sum(new_row_heights[row + 1:]) +
                y_shift_by_padding * fig_height_px)


    def _get_vert_aligned_y_position_after_height_reduction(self, new_height,
                                                           row, col,
                                                            heights,
                                                           new_heights, y0s,
                                                           fig_size):
        fig = plt.gcf()
        col_height,_ = self._get_col_height(heights)
        new_col_height, new_row_heights = self._get_col_height(new_heights)
        _ , y_shift_by_padding = self._get_shift_by_padding_for_position((row, col))
        height_below_plot = self._get_height_below_plot(row, new_row_heights,
                                                       y_shift_by_padding, fig)

        # 0 position indicate no image at that position
        # get first y position that is not 0 or -0.00000001
        #  (small negative was defined for empty plots)
        origin_y = 0
        new_col = col
        while (origin_y == -0.00000001) | (origin_y == 0):
            origin_y = y0s[-1,new_col]
            if new_col == col:
                new_col = 0
                # set col None to prevent the reset being triggered more than once
                col = None
            else:
                new_col += 1
                # stop if new col is out of boundaries of y0s
                if new_col >= y0s.shape[1]:
                    break


        # align plot vertically centered in space given to plot
        # total space available for ax is the height of the row
        space_available = new_row_heights[row]
        # height_px of axes from supplied height of axes in figure fraction
        new_height_px = new_height * fig.get_size_inches()[1] * fig.dpi

        # not working for enlarged images at the moment
        #  their size is not only increased by a factor
        # but also increased by padding between images,
        #  which makes it harder to calculate the available space
        if new_height_px < space_available:
            # y shift is half of space that is not used
            y_shift_for_vertical_center = (space_available - new_height_px) / 2

            # add to height_below plot - to keep padding similar (?)
            height_below_plot += y_shift_for_vertical_center

        fig_height = fig_size[1]
        new_y_space = (col_height - new_col_height)
        if self.vert_alignment.lower() == "top":
            # move the complete distance to the top
            # since height reduction is done from the top
            new_y_space *= 2
        elif self.vert_alignment.lower() == "bottom":
            # dont move further since plots already are at the bottom
            # since height reduction is done from the top
            new_y_space = 0
        y_position = self._get_aligned_position_after_size_reduction(new_space = new_y_space,
                                                                     size_before_plot = height_below_plot,
                                                                     origin = origin_y,
                                                                     fig_size = fig_height)
        return y_position, new_y_space

    def _get_aligned_position_after_size_reduction(self, new_space,
                                                  size_before_plot, origin,
                                                  fig_size):
        # size before plot
        # is the size below or left of that plot

        # calculate additional distance (start_shift) on both sites of panel
        #  after changing height and putting images close together again
        start_shift = new_space / 2
        # add all new sizes of plot before current plot to start of y_shift
        shift_from_origin = start_shift + size_before_plot
        position = (origin + shift_from_origin) / fig_size
        return position

    def _shift_labels(self, padding_px):
        fig = plt.gcf()
        fig_size_px = fig.get_size_inches() * fig.dpi
        # shift labels
        for site, label_arr in self.label_matrices.items():
            # check if there are labels at the site
            if len(self.label_axs[site]) == 0:
                continue

            label_nbs = np.unique(label_arr)
            for label_nb in label_nbs:
                if label_nb == - np.inf:
                    continue

                label_positions = list(np.array(np.where(label_arr ==
                                                         label_nb)).transpose())
                # positions are already sorted according to column,
                #  change to row for top and bottom site
                # sort positions according to column or row,
                #  depending on site of label
                if (site == "top") | (site == "bottom"):
                    label_positions = sorted(label_positions,key=lambda x:x[1])
                # first element in each position is the row, second is the column
                first_position = (label_positions[0][0],label_positions[0][1])
                last_position = (label_positions[-1][0],label_positions[-1][1])

                ax_label = self.label_axs[site][int(label_nb)]
                padding_px = self.label_padding_px[site][int(label_nb)]
                (x0, y0,
                 label_width,
                 label_height) = self._get_final_label_position_and_dimension(first_position[0],
                                                                             last_position[0],
                                                                             first_position[1],
                                                                            last_position[1],
                                                                             site, padding_px)

                ax_label.set_position([x0, y0, label_width, label_height])

                for child in ax_label.get_children():
                    if isinstance(child, matplotlib.text.Annotation):
                        rotation_degrees = child.get_rotation()
                        text = child.get_text()
                        font_size_pt = child.get_fontsize()
                        break

                # get info whether line was plotted at position
                plot_line = self.label_lines_ploted[site][int(label_nb)]

                (x_text,
                 y_text) = self._get_position_of_text(ax_label,
                                                   text, site,
                                                   font_size_pt,
                                                   rotation_degrees=rotation_degrees,
                                                   padding_px = padding_px,
                                                   plot_line = plot_line )

                label = self.labels[site][int(label_nb)]
                label.set_position((x_text,y_text))



    def _get_axs_to_define_x_and_y_coords_for_position(self, position):

        if position in self.all_axs:
            identity = self.pos_to_identity_map[position]
            #check if identity (not pre_identity) is a place holder image
            if identity in self.place_holder_identity_map:
                #get identity of enlarged image corresponding to place holder
                enlarged_image_pre_identity = self.place_holder_identity_map[identity]
                enlarged_image_pos = self.pre_identity_to_pos_map[enlarged_image_pre_identity]
                ax = self.all_axs[enlarged_image_pos]
            else:
                ax = self.all_axs[position]
            ax_coords = ax.get_position()
            x_coords = ax_coords
            y_coords = ax_coords
        else:
            position_matrix_shape = self.position_matrix.shape
            pos_slice = [ slice(position_matrix_shape[0]),
                          slice(position_matrix_shape[1])]
            x_pos = copy.copy(pos_slice)
            y_pos = copy.copy(pos_slice)
            x_pos[1] = position[1]
            y_pos[0] = position[0]
            # get which position in that slice is correct by
            # checking which value in the position matrix is 1
            x_pos[0] = np.where(self.position_matrix[tuple(x_pos)] == 1)[0][0]
            y_pos[1] = np.where(self.position_matrix[tuple(y_pos)] == 1)[0][0]
            x_coords = self.all_axs[tuple(x_pos)].get_position()
            y_coords = self.all_axs[tuple(y_pos)].get_position()

        return x_coords, y_coords


    @staticmethod
    def _get_col_and_row_from_name(file_name):
        # extract position from file __position-row-column__
        position_finder = re.compile("__pos-([\d]+)-*([\d]*)")
        position = position_finder.search(file_name)
        if position == None:
            row = None
            col = None
        else:
            # if only one number is after position (only one group),
            #  assume images are in one row
            if position[2] == "":
                row = 0
                col = int(position[1]) - 1
            else:
                row = int(position[1]) - 1
                col = int(position[2]) - 1
        return (col,row)

    def _validate_data_file(self):
        if len(self.panel_file_paths) != 1:
            raise Exception("Only showing data from a single data file "
                            "is supported.")
        if ((self.panel_file_paths[0].find(".csv") == -1) &
                ((self.panel_file_paths[0].find(".feather") == -1))):
            raise Exception("Only showing data from a csv or feather file "
                            "is supported.")

    def _remove_unpaired_data(self, data, pair_unit_columns,
                             col, x, hue):
        
        def get_paired_data(data, pair_level_column, pair_unit_columns):
            pair_values = data[pair_level_column].drop_duplicates().values

            # first get all paired units which are present in all pair values
            paired_data_units = data.loc[data[pair_level_column] == pair_values[0]]
            for pair_value in pair_values[1:]:
                new_data = data.loc[data[pair_level_column] == pair_value]
                paired_data_units = paired_data_units.merge(new_data,
                                                            on=pair_unit_columns,
                                                            how="inner")
            all_paired_units = paired_data_units[pair_unit_columns].drop_duplicates().values
            all_paired_units = [tuple(unit) for unit in all_paired_units]

            data_pair_indexed = data.set_index(pair_unit_columns)
            paired_data = data_pair_indexed.loc[all_paired_units].reset_index()
            # for pair_value in pair_values:
            #     new_data = paired_data.loc[paired_data[pair_level_column] == pair_value]

            return paired_data

        # if pair columns are defined, only paired data is allowed
        # remove data for which no paired samples are available
        # go through each group of pairs
        # NOTE: one group can also contain more than two connected
        # groups for which datapoints will be connected
        if type(hue) != type(None):
            group_level_columns = [col, x]
            pair_level_column = hue
        elif type(col) != type(None):
            group_level_columns = [col]
            pair_level_column = x
        else:
            group_level_columns = []
            pair_level_column = x

        if len(group_level_columns) > 0:
            paired_data = data.groupby(group_level_columns,
                                       as_index=False).apply(get_paired_data,
                                                                pair_level_column,
                                                                pair_unit_columns)
        else:
            paired_data = get_paired_data(data, pair_level_column, 
                                          pair_unit_columns)

        return paired_data

    def show_data_columns(self, nb_vals = 10, show_min_max=True):
        """
        Show type and some values for all columns of the data file.

        :param nb_vals: number of values for column to show
        """
        self._validate_data_file()

        data = self.data

        data_columns = data.columns
        for column in data_columns:
            unique_values = data[column].drop_duplicates().dropna()[:nb_vals]
            if len(unique_values) == 0:
                print("Column : NO NON-NAN VALUES!")
            else:
                min = data[column].min()
                max = data[column].max()
                type_str = "(" + str(type(unique_values.values[0])) +")"
                unique_values = [str(unique_value)
                                 for unique_value in unique_values]
                prefix =column+" : "
                wrapper = textwrap.TextWrapper(initial_indent=prefix, width=90,
                                    subsequent_indent=" " * len(prefix))
                unique_values_str = str(min) + " to " + str(max) + "; "
                unique_values_str += ", ".join(unique_values)
                unique_values_str += type_str
                print(wrapper.fill(unique_values_str))


    def add_data_transformation(self, function):
        """
        Add a transformation for the data that will be plotted on the y-column.

        :param function: Function that will be applied to the column
                        (pd.series object)
        """
        self.data_transformations.append(function)

    @staticmethod
    def _get_rows_matching_criteria(data, inclusion_criteria_dict,
                                    digits_round_all_columns=None,
                                   excluded_keys = None):
        """
        in a dataframe, get all rows for which values of certain columns match
        :param data: Dataframe
        :param inclusion_criteria_dict: Dict where each key is a column and each
                                        value is a list of values of which one
                                        must be matched in the column
                                        or a string that will be used
                                        as a dataframe.query statement
        :param excluded_keys: list, keys to ignore in the dict
        """
        # include only data that satifies the inclusion criteria
        #  new_included_data = copy.copy(data)
        new_included_data = data
        if type(excluded_keys) == type(None):
            excluded_keys = []
        for column, values in inclusion_criteria_dict.items():
            values_str = [str(value_for_str) for value_for_str in values]
            if column in excluded_keys:
                continue
            # if values is only one value convert to list to make it iterable
            if type(values) not in [list, tuple]:
                final_query = column + values
                included_indices = new_included_data.query(final_query).index
            else:
                # convert all values to to correct type if types differ
                if new_included_data[column].dtype != type(values[0]):
                    type_conv = type(new_included_data[column].iloc[0])
                    values = [type_conv(value) for value in values]
                # start = time.time()
                # new_included_data[column] = new_included_data[column].astype(str)
                # new_included_data[column] = new_included_data[column].values.astype(str)#.astype(str)
                # print(new_included_data[column])
                # print(11121, time.time() - start)
                data_type = new_included_data[column].dtype
                if ((digits_round_all_columns is not None) &
                        (data_type is not str)):
                    column_vals = new_included_data[column]
                    rounded_vals = column_vals.round(digits_round_all_columns)
                    new_included_data[column] = rounded_vals

                included_indices = None
                for value in values:
                    if type(included_indices) == type(None):
                        included_indices = new_included_data[column] == value
                    else:
                        included_indices = (included_indices |
                                            (new_included_data[column] == value))

                if len(new_included_data.loc[included_indices]) == 0:
                    raise ValueError (f"None of the values "
                                      f"'{', '.join(values_str)}' "
                                      f"found in the column '{column}' "
                                      f"for the inclusion criteria.")
            new_included_data = new_included_data.loc[included_indices]

        return new_included_data


    def _exclude_data(self, data, inclusion_criteria, digits_round_all_columns):
        included_data = None
        for inclusion_criteria_dict in inclusion_criteria:
            get_matching_rows = FigurePanel._get_rows_matching_criteria
            new_included_data = get_matching_rows(data,
                                                  inclusion_criteria_dict,
                                                  digits_round_all_columns)

            if type(included_data) == type(None):
                included_data = new_included_data
            else:
                included_data = pd.concat([included_data, new_included_data])


        if type(included_data) != type(None):
            data = included_data
        return data


    def _normalize_data(self, data, y, norm_cats, hue, col, row,
                       normalize_by="mean"):
        if normalize_by.lower() == "mean":
            normalize_func = lambda x: (x / x.mean())
        elif normalize_by.lower() == "median":
            normalize_func = lambda x: (x / x.mean())
        elif normalize_by.lower() == "max":
            normalize_func = lambda x: (x / x.max())
        elif normalize_by.lower() == "min":
            normalize_func = lambda x: (x / x.min())
        elif normalize_by.lower() == "first":
            normalize_func = lambda x: (x / x.iloc[0])
        elif normalize_by.lower() == "last":
            normalize_func = lambda x: (x / x.iloc[-1])
        else:
            raise ValueError(f"The normalization method {normalize_by} "
                             "is not implemented.")
            
        data_normalized = self._transform_y_data(data, y, normalize_func,
                                                norm_cats, hue, col, row)
        return data_normalized


    def _group_and_average_data(self, average_columns, data):
        # create new data by averaging units
        if type(average_columns) == type(None):
            return data
        # add x, hue, col and row so that these columns are
        # not dropped
        for new_average_column in [self.x, self.hue, self.col, self.row]:
            if not self._is_none(new_average_column):
                if new_average_column not in average_columns:
                    average_columns.append(new_average_column)
        data = data.groupby(average_columns).mean().reset_index()
        return data


    def _exclude_data_with_column_vals_not_in_all_groups(self,
                                                        columns_same_in_groups,
                                                        data,
                                                        x, hue, col):
        if type(columns_same_in_groups) == type(None):
            return data

        # exclude data with column values not present in all groups
        group_columns = []
        # append all group_columns that are not None
        for group_column in [x, hue, col]:
            if type(group_column) != type(None):
                group_columns.append(group_column)
        data_indexed = data.set_index(group_columns)
        # create list with data for each unique group_column combination
        all_groups = data[group_columns].drop_duplicates()
        all_group_data = []
        for group in all_groups.values:
            group = tuple(group)
            all_group_data.append(data_indexed.loc[group])

        # merge all group dataframes by using intersection
        # in the values of columns_same_in_groups
        # thereby get all the column values that are present
        # in all data groups
        data_same_in_groups = all_group_data[0]
        for group_nb in range(1, len(all_group_data)):
            group_data = all_group_data[group_nb]
            data_same_in_groups = data_same_in_groups.merge(group_data,
                                                            how="inner",
                                                            on=columns_same_in_groups)

        units_to_keep = data_same_in_groups[columns_same_in_groups].drop_duplicates().values
        units_to_keep = [tuple(unit) for unit in units_to_keep]
        data = data.set_index(columns_same_in_groups).loc[units_to_keep]
        return data

    def _smoothen_data(self, data, y, smoothen_cats, smoothing_rad,
                      hue, col, row):

        # smoothing_rad
        if type(smoothing_rad) == type(None):
            return data[y]
        data.reset_index(inplace=True)
        smoothen_func = lambda x: x.rolling(smoothing_rad).mean()
        data_normalized = self._transform_y_data(data, y, smoothen_func,
                                                smoothen_cats, hue, col, row)
        return data_normalized

    def _transform_y_data(self, data, y, transform_func,
                         cats, hue, col, row):
        if type(cats) == type(None):
            cats = []
        cols_cats = []
        for norm_cat in cats:
            if norm_cat == "hue":
                if type(hue) != type(None):
                    cols_cats.append(hue)
            elif norm_cat == "col":
                if type(col) != type(None):
                    cols_cats.append(col)
            elif norm_cat == "row":
                if type(row) != type(None):
                    cols_cats.append(row)
            else:
                cols_cats.append(norm_cat)

        data_transformed = data.groupby(cols_cats)[y].transform(transform_func)
        return data_transformed

    @staticmethod
    def _default_in_function(function_object, arg_name):
        signature = inspect.signature(function_object)
        default_value = signature.parameters[arg_name].default
        return default_value

    @staticmethod
    def _default_in_statannot(arg_name):
        target_function = statannot.plot_and_add_stat_annotation
        signature = inspect.signature(target_function)
        default_value = signature.parameters[arg_name].default
        return default_value

    @staticmethod
    def _from_kwargs_or_statannot_default(keyword_args, arg_name):
        default_val = FigurePanel._default_in_statannot(arg_name)
        return keyword_args.get(arg_name, default_val)

    def _get_row_label_width(self, row_value, ax, padding_keyword, **kwargs):
        # default for row label orientation in vert
        row_label_orientation = kwargs.get("row_label_orientation",
                                                 "vert")
        # get defined or default value of borderaxespad_
        borderaxespad_def = FigurePanel._default_in_statannot(padding_keyword)
        borderaxespad_ = kwargs.get(padding_keyword, borderaxespad_def)
        borderaxespad_px = 10 * borderaxespad_ * plt.gcf().dpi / 72
        row_label = statannot.add_row_label(row_value, self.font_size,
                                            row_label_orientation, ax,
                                            x_start=0)
        label_width = statannot.get_width_of_object(row_label,
                                                    borderaxespad_px,
                                                    plt.gcf())
        return label_width

    def set_data_params(self, x=None, y=None, hue=None, col=None, row=None):
        """
        Set data parameters for showing data.

        :param x: Column name of data to be used for x axis
        :param y: Column name or list of column names
                    of data to be used for y axis. Multiple y values will be
                    plotted as several rows.
        :param hue: column name of data to be used for hue
        :param col: column name of data used for plots in different columns
                    (generating a row of plots)
        :param row: column of data used for plots in different rows
                    (generating a columns of plots)
        """
        self.x = x
        self.y = y
        self.hue = hue
        self.col = col
        self.row = row

    def _count_by_criteria(self, data, criteria):
        for column, query in criteria.items():
            final_query = column + query
            data = data.query(final_query)
        return data.count()


    def calculate_fractions(self, group_criteria, 
                            new_group_name="fraction_group"):
        """
        Allow calculating the fraction of specific groups in the data.
        Will generate a new dataframe with different rows
        that also will be used to plot data afterwards.

        :param criteria: Dict of dicts. Each dict defines
                         one fraction to calculate
                         The key in the upper dict defines the name
                         of the new group
                         in each sub dict the key is a column and the value is
                         a string to be used in a "query" expression,
                         without the column e.g. for col_x to be larger than 10,
                         the dict should be like this: 'col_x' : '> 10'
        """
        # first get all data columns that were set before
        # if they were set (not None)
        group_columns = []
        possible_columns = [self.x, self.hue, self.col, self.row]
        for column in possible_columns:
            if not self._is_none(column):
                group_columns.append(column)

        data = self.data.dropna(subset=[self.y])

        # now group by param_cols
        grouped_data = data.groupby(group_columns)

        # get total counts to calculate fraction later
        total_counts = grouped_data[self.y].count()

        fraction_data = pd.DataFrame()
        # then for each dict count in each group how many rows match the criteria
        for name, criteria in group_criteria.items():
            counts = grouped_data.apply(self._count_by_criteria,
                                        criteria)[self.y]
            fraction = pd.DataFrame(counts / total_counts)
            fraction[new_group_name] = name
            fraction_data = pd.concat([fraction_data, pd.DataFrame(fraction)])
        self.data = fraction_data.reset_index()

    def _remove_outliers(self, data, y, nb_stds_outliers):
        std = data[y].std()
        mean = data[y].mean()
        max_data_val = mean + std * nb_stds_outliers
        min_data_val = mean - std * nb_stds_outliers
        data = data.loc[(data[y] > min_data_val) &
                        (data[y] < max_data_val)]
        return data


    def show_data(self, x=None, y=None, x_labels=[], hue=None, hue_labels=[],
                  col=None, col_labels=[], row=None, row_labels=[],
                  x_order=None, col_order=None, hue_order=None, row_order=None,
                  order_vals_before_changing_vals=False,
                  inclusion_criteria= None,show_legend=None,
                  round_columns=None,round_digits=0,
                  pair_unit_columns=None,
                  remove_outliers=False, nb_stds_outliers=4,
                    scale_columns=None, 
                    norm_y_cats=None, normalize_y_by="mean", normalize_y=False, 
                    norm_x_cats=None, normalize_x_by="mean", normalize_x=False, 
                    smoothing_rad = None,
                  average_columns = None,
                  baseline=0, columns_same_in_groups=None,
                  renaming_dicts = None,
                  width_y_axis = 0, col_labels_every_row = False,
                  sub_padding_y_factor = 0.25, show_y_label_in_all_rows = None,
                  normalize_after_data_exclusion=True,
                  video_frame=None,
                  use_same_y_ranges=True, increase_padding_above = True,
                  digits_round_all_columns=4,
                  for_measuring=False,
                  **kwargs):
        """
        Plot data of file for panel.
        All column names (e.g. x, x_order, x_labels, hue, etc. ) must be strings,
        independent of which type they are in the dataframe.
        Statistics will be performed automatically and annotated by statannot.
        For parameters that can be set additionally, see statannot package
        "add_stat_annotation" function.

        :param x: Column name of data to be used for x axis
        :param y: Column name or list of column names
                    of data to be used for y axis. Multiple y values will be
                    plotted as several rows.
        :param x_labels: list of tuples to change values in x column,
            first value in tuple is original name and second value
            is what the name should be replaced by
            (e.g. [("2", "No axon"), ("3", "With axon")] to replace
            "2" and "3" with the respective text).
            Alternatively each tuple can contain a standard text
            in which the placeholder __$$__ will be replaced by
            the column value.
            (e.g. [["Rate value = __$$__"]] would
            mean that each column value is replaced by the defined string
            with __$$__ replaced by the column value.
        :param hue: column name of data to be used for hue
        :param hue_labels: list of tuples to change values in hue column.
            See description of x_labels for details.
        :param col: column name of data used for plots in different columns
                    (generating a row of plots)
        :param col_labels: list of tuples to change values in col column.
            See description of x_labels for details.
        :param row: column of data used for plots in different rows
                    (generating a columns of plots)
        :param row_labels: list of tuples to change values in row column.
            See description of x_labels for details.
        :param x_order: list of x values after applying the changes
            of x_labels, if order_vals_before_changing_vals is False.
            If order_vals_before_changing_vals is True, x values should be
            the original values before applying the changes of x_labels.
            Determines the order of x values. Each value
            has to contain a unique part only present in one column value
            and not part of multiple different column values and does
            not need to contain the entire column value.
            Alternatively, can be a function that takes all unique values
            of the column and returns an iterable of strings of the unique
            values that defines the order. Can also be the string "ascending"
            or "descending" to sort values ascendingly or descendingly,
            respectively.
        :param col_order: list of col values after applying the changes
            of col_labels, if order_vals_before_changing_vals is False.
            If order_vals_before_changing_vals is True, col values should be
            the original values before applying the changes of col_labels.
            Determines the order of col values.
            Can also be a nested list in which case, the columns will be split
            in one row per nested list (e.g. [[1,2,3],[2,3,4],[5,6,7]], will
            be split into three rows, the first with the col values 1, 2 and 3.
            In that case, the values in the order must be the values before
            changes through col_labels are applied. Each row must have the
            same number of columns to allow the same size for each plot,
            otherwise plots in the row with fewer elements will be wider.
            For more details see "x_order".
        :param hue_order: list of hue values after applying the changes
            of hue_labels, if order_vals_before_changing_vals is False.
            If order_vals_before_changing_vals is True, hue values should be
            the original values before applying the changes of hue_labels.
            Determines the order of hue values.
            For more details see "x_order".
        :param row_order: list of row values after applying the changes
            of row_labels, if order_vals_before_changing_vals is False.
            If order_vals_before_changing_vals is True, row values should be
            the original values before applying the changes of row_labels.
            Determines the order of row values.
            For more details see "x_order".
        :param order_vals_before_changing_vals: Whether the _order parameters
            (e.g. x_order, hue_order, etc) include values before changing values
            with the _labels parameters or not. Default to allow compatibility
            with previous scripts is False (use values after replacing with
            _labels). This will be done automatically for col_order though when
            using nested lists for col_order to plot cols in different rows.
        :param inclusion_criteria: list of Dictionaries with columns as key
            and list of values or one value that the column should match,
            since value all matches from each dictionary will be concatanated.
            If no matches are found (ValueError 'The inclusion criteria [...]
            did not match with any data') but you expected matches and the
            matched values are numbers, try to use float numbers instead of int
            (e.g. 9.0 instead of 9, or 200529.0 instead of 200529). Columns
            might be converted from int to float if NaN values (e.g. empty
            cells) are found. This type conversion can also happen if some rows
            in excel are not complete deleted (some column values are left) or
            a single cell accidentally was added below the rows - this would be
            visible as rows added in the csv file which are mostly empty.
            BE CAREFUL NOT TO INTRODUCE DUPLICATES LIKE THIS!

        :param show_legend: Whether to show legend of plot for different values
                            in hue column (will not be shown if there is only
                            one hue value)
        :param pair_unit_columns: list of columns that uniquely identify one
                            set of dependent datapoints (needed to connect
                            paired datapoints and also needed as preprocessing
                            to allow statistics tests for paired data)
        :param remove_outliers: Whether outliers should be removed from data
        :param nb_stds_outliers: Number of stds that outliers need to differ
                                at least from the mean to be excluded
                                (if remove_outliers = True)
        :param scale_columns: Dictionary for scaling values, with key
                                as column name and value the factor by which
                                values are scaled (e.g. for changing the unit
                                of the y column)
        :param norm_y_cats: list of categories / data columns from which the groups
                    will be build (groupby object)
                    within which it should be normalized 
                    (e.g. to normalize values within neurites)
                    can be "hue" or "col" or "x" and will then take the
                    column names that were used for these
                    variables as arguments to the "show_data" function
                    can also be any other column name directly
        :param normalize_y_by: value form the group by which the group will be 
                            normalized; any function name that can be performed
                            on a series works
        :param norm_x_cats: See norm_y_cats, but will be applied to x column
        :param normalize_x_by: See normalize_y_by, but will be applied to x 
            column
        :param smoothing_rad: Radius for smoothing y values
        :param average_columns: List of column names;
                                create new data frame where data will be
                                averages for data rows with same values in
                                average_columns can be used e.g. to average all
                                values of the same neuron
        :param normalize: Whether to normalize y values
        :param baseline: value that will be subtracted from all y-values before
                        normalization, smoothing etc.
                        helpful e.g. for background subtraction
                        of data from images
        :param columns_same_in_groups: list of column names;
                                        exclude data with column values
                                        not present in all groups
                                        - allows to define
                                        for different plot groups
                                        (by hue, col and x) to only include
                                        rows with values in the defined
                                        columns that are present in all groups
        :param renaming_dicts: list of dicts,
                        IMPORTANT: renaming is done after replacing strings
                        through _labels (e.g. x_labels, hue_labels) parameters
                        each dict is for one renaming
                        one key in the dict has to be "__from__" and the value
                        determines what should be changed
                        one key in the dict has to be "__to__" and the value
                        determines the value it should be changed to
                        one key in the dict has to be
                        "__target_column__" and the value
                        determines in which column the change should occur
                        the other keys are column names
                        and the corresponding values
                        determine the value the column must have
                        for checking for matches, values must be lists
                        otherwise, it is assumed that it is a query
                        and will be executed as pandas dataframe query string
        :param col_labels_every_row: Bool; whether column labels above
                                    should be shown in every row
                                    of the facet plot
                                    only matters if row is not None
        :param sub_padding_y_factor: multiple of figure_panel padding for plots
                                    from multiple y values
        :param show_y_label_in_all_rows: Whether to show y axis label in all 
                                        rows (even though they all show the same
                                        y axis)
        :param normalize_after_data_exclusion: Boolean; whether data should
                                            be normalized after data exclusion
                                            normalization should usually be done
                                            before exclusion of data
                                            otherwise excluded units would
                                            change normalization depending on
                                            what is shown
        :param video_frame: Int; for animating data in a video; indicates
                            the current frame of the video
                            and thereby the current maximum x value
                            that should be plotted
        :param use_same_y_ranges: Use the same y ranges for all plots. Will use
                                    the range from the lowest y value in all
                                    groups to the highest y value in all
                                    groups
        :param increase_padding_above: Whether to increase padding above plots
                                        can sometimes be useful to improve
                                        layout
        :param digits_round_all_columns: Number of digits all columns for
            excluding data should be rounded to. Prevents floating point
            imprecisions that lead to mismatching during excluding data.
        :param for_measuring: INTERNAL PARAMETER, used when plots are plotted
                                to measure dimensions for perfect alignment,
                                while the plot is removed afterwards
                                again
        :param kwargs: Keyword arguments for plotting data
                        and adding annotations, passed to function
                        statannot.plot_and_add_stat_annotation.
        """
        if self._is_none(self.x) & self._is_none(x):
            raise ValueError("A column for 'x' must be supplied "
                             "or set beforehand.")

        if self._is_none(self.y) & self._is_none(y):
            raise ValueError("A column for 'y' must be supplied "
                             "or set beforehand.")

        if type(inclusion_criteria) == type(None):
            inclusion_criteria = []

        if self._is_none(x):
            x = self.x
        else:
            self.x = x

        if self._is_none(hue):
            hue = self.hue
        else:
            self.hue = hue

        self.col = col

        if self._is_none(row):
            row = self.row
        else:
            self.row = row

        if self._is_none(y):
            y = self.y
        else:
            self.y = y

        # get plot_type, needed for get_basic_statistics
        # to know if it is a continuous data plot type
        plot_type = self._default_in_statannot("plot_type")
        self.plot_type = kwargs.get("plot_type", plot_type)

        # create copy of inner border
        # since it is changed along the script
        # and otherwise for videos
        # it will be changed multiple frames
        inner_border = copy.copy(self.inner_border)

        use_nested_cols = False

        if col_order is not None:
            if type(col_order[0]) in [tuple, list]:
                self.row = "__group__"
                row = self.row
                self.data[self.row] = np.nan
                row_order = []
                for row_nb, row_list in enumerate(col_order):
                    for col_value in row_list:
                        self.data.loc[self.data[col] == col_value, row] = str(row_nb)
                    row_order.append(str(row_nb))
                col_order = [col_val
                             for col_list in col_order
                             for col_val in col_list]
                use_nested_cols = True

        # only overwrite,
        # if the current iteration is not just done
        # for measuring
        if not for_measuring:
            print("PLOT DATA FOR PANEL {}.................".format(self.letter))
            self.x_labels = x_labels
            self.x_labels= x_labels
            self.hue_labels = hue_labels
            self.col_labels = col_labels
            self.row_labels = row_labels
            self.x_order = x_order
            self.hue_order = hue_order
            self.col_order = col_order
            self.row_order = row_order
            self.inclusion_criteria = inclusion_criteria
            self.round_columns = round_columns
            self.round_digits = round_digits
            self.scale_columns = scale_columns
            self.smoothing_rad = smoothing_rad
            self.normalize_y = normalize_y
            self.normalize_x = normalize_x
            self.norm_y_cats = norm_y_cats
            self.norm_x_cats = norm_x_cats
            self.baseline = baseline
            self.columns_same_in_groups = columns_same_in_groups
            self.renaming_dicts = renaming_dicts
            self.increase_padding_above = increase_padding_above
            self.width_y_axis = width_y_axis
            self.col_labels_every_row = col_labels_every_row
            self.sub_padding_y_factor = sub_padding_y_factor
            self.show_y_label_in_all_rows = show_y_label_in_all_rows
            self.pair_unit_columns = pair_unit_columns
            self.use_same_y_ranges = use_same_y_ranges
        
        self._validate_data_file()

        data = self.data

        if normalize_after_data_exclusion:
            data = self._exclude_data(data, inclusion_criteria,
                                      digits_round_all_columns)

        # normalization should usually be done before exclusion of data
        # otherwise excluded units would change normalization
        # depending on what is shown
        # normalize values to within cateogiry
        # norm_cats is a list of categories for which normalization
        if normalize_y:
            data[y] = self._normalize_data(data, y, norm_y_cats, hue, col, row,
                                          normalize_y_by)
        
        if normalize_x:
            data[x] = self._normalize_data(data, x, norm_x_cats, hue, col, row,
                                          normalize_x_by)


        if not normalize_after_data_exclusion:
            data = self._exclude_data(data, inclusion_criteria,
                                      digits_round_all_columns)

        if len(data) == 0:
            raise ValueError("The inclusion criteria {} that were defined "
                             "did not match with "
                             "any data.".format(str(inclusion_criteria)))

        if self.animate_panel & (not self._is_none(video_frame)):
            data = data.loc[data[x] <= video_frame]

        if len(data) == 0:
            return

        data = self._group_and_average_data(average_columns, data)

        if remove_outliers:
            data_box_columns = []
            for data_box_column in [x, col, hue]:
                if data_box_column is not None:
                    data_box_columns.append(data_box_column)
            data = data.groupby(data_box_columns,
                                as_index = False).apply(self._remove_outliers,
                                                        y, nb_stds_outliers)

        # change data globally
        self.data = data

        # allow for multiple y to be plotted in separate rows
        # prepare y values to be list to i
        if (type(self.y) in self.itertypes):
            all_y = self.y
        else:
            all_y = [self.y]

        columns_to_drop_na_from = [*all_y, x, hue, col]
        for column in columns_to_drop_na_from:
            if column != None:
                data = data.dropna(subset=[column])

        # convert all categorisation columns to string in order
        #  to make replacing values possible
        for column in [x,hue,col]:
            if column != None:
                data[column] = data[column].apply(str)

        data = self._exclude_data_with_column_vals_not_in_all_groups(columns_same_in_groups,
                                                                    data, x,
                                                                    hue, col)

        # remove baseline from values before processing numbers further
        data[y] = data[y] - baseline

        data[y] = self._smoothen_data(data, y, ["hue", "col", "row"],
                                     smoothing_rad, hue, col, row)

        (data, round_columns,
         inclusion_criteria) = self._round_data(data, inclusion_criteria,
                                                round_columns, round_digits)

        self.inclusion_criteria = inclusion_criteria

        all_ordered_vals = {}
        all_ordered_vals[x] = self.x_order
        all_ordered_vals[hue] = self.hue_order
        all_ordered_vals[col] = self.col_order
        all_ordered_vals[row] = self.row_order
        sorted_ordered_vals = self._get_sorted_ordered_vals(data,
                                                            all_ordered_vals,
                                                            round_columns,
                                                            round_digits)

        self.x_order = sorted_ordered_vals[x]
        self.hue_order = sorted_ordered_vals[hue]
        self.col_order = sorted_ordered_vals[col]
        self.row_order = sorted_ordered_vals[row]

        # only replace row values now
        # this is needed since the row_value
        #  might be used as a label for a row
        # and will be given to the new sub_panel right away
        # and should be the final row label
        strs_to_replace = {}
        strs_to_replace[row] = row_labels
        data = self._replace_strs_in_data(data, strs_to_replace)

        #  apply data transformations
        for transformation in self.data_transformations:
            data[y] = transformation(data[y])

        if scale_columns == None:
            scale_columns = {}

        for column, scaling_factor in scale_columns.items():
            data[column] = data[column].astype(float)
            data[column] *= scaling_factor

        # check whether multiple columns for y were provided
        multiple_y = False
        if (type(self.y) in self.itertypes):
            multiple_y = True

        if hue is not None:
            nb_hue_x = len(self.data[[x, hue]].drop_duplicates())
            nb_x = len(self.data[x].drop_duplicates())
            nb_hue = len(self.data[x].drop_duplicates())
            # if x and hue are the same, hue categories are already
            # annotated and don't need to be by using a legend
            show_x_axis = self._from_kwargs_or_statannot_default(kwargs,
                                                                "show_x_axis")
            if show_legend is None:
                if (nb_hue_x > nb_x) & show_x_axis:
                    show_legend = True
                elif (nb_hue > 1) & (not show_x_axis):
                    show_legend = True

        # correct ordered vals to actual column values
        ordered_vals = {}
        ordered_vals[row] = self.row_order

        ordered_vals = self._correct_ordered_vals(data, ordered_vals)
        self.row_order = ordered_vals[row]

        if use_nested_cols | order_vals_before_changing_vals:
            all_ordered_vals = {}
            # when using nested columns to plot them in several rows
            # but in general order vals should not be before changing vals
            # through the _labels parameters, only use col_order values before
            # changing vals through col_labels.
            all_ordered_vals[col] = self.col_order
            if order_vals_before_changing_vals:
                all_ordered_vals[x] = self.x_order
                all_ordered_vals[hue] = self.hue_order
                all_ordered_vals[row] = self.row_order
            strs_to_replace = {}
            strs_to_replace[x] = x_labels
            strs_to_replace[hue] = hue_labels
            strs_to_replace[col] = col_labels
            all_ordered_vals = self._replace_strs_in_orders(all_ordered_vals,
                                                            strs_to_replace)
            self.col_order = all_ordered_vals[col]
            if order_vals_before_changing_vals:
                self.x_order = all_ordered_vals[x]
                self.hue_order = all_ordered_vals[hue]
                self.row_order = all_ordered_vals[row]

        #  create facet plot made out of several sub figure panels
        #  within the current figure panel
        #  based on values in the "row" column
        if ((not FigurePanel._is_none(row)) | multiple_y) & (not for_measuring):

            # set self.data so that normalization will be done correctly
            # in first execution
            # and not only done on subset of data
            # in addition, saves time since processing only has to be done once
            # and not for every row
            self.data = data
            self._plot_multi_rows(inner_border,  show_legend, **kwargs)
            return None

        # replace everything except the row values
        # for each row separately
        # otherwise, inclusion criteria would need to be updated
        # for each row depending on strings that were replaced
        strs_to_replace = {}
        strs_to_replace[x] = x_labels
        strs_to_replace[hue] = hue_labels
        strs_to_replace[col] = col_labels
        data = self._replace_strs_in_data(data, strs_to_replace)

        data = self._rename_column_values(data, renaming_dicts)

        # correct ordered vals to actual column values
        ordered_vals = {}
        ordered_vals[x] = self.x_order
        ordered_vals[hue] = self.hue_order
        ordered_vals[col] = self.col_order
        ordered_vals = self._correct_ordered_vals(data, ordered_vals)
        x_order = ordered_vals[x]
        hue_order = ordered_vals[hue]
        col_order = ordered_vals[col]
        # first remove all data defined through the _order variables
        property_names = ["col", "x", "hue"]
        column_infos = zip([col, x, hue], [col_order,
                                           x_order, hue_order])
        for prop_nb, (column_name, column_order) in enumerate(column_infos):
            if (column_name is None) | (column_order is None):
                continue
            kwargs[property_names[prop_nb] + "_order"] = column_order
            included_data_list = []
            for column_val in column_order:
                included_data_list.append(data.loc[data[column_name] ==
                                                   column_val])
            data = pd.concat(included_data_list)

        # without paired data do not connect data points
        if type(pair_unit_columns) == type(None):
            kwargs["connect_paired_data_points"] = False
        else:
            data = self._remove_unpaired_data(data, pair_unit_columns,
                                             col, x, hue)

        (axs_by_position,
         ax_annot) = self._plot_simple_row(data, x, y, hue, col, for_measuring,
                                          increase_padding_above,
                                          inner_border,
                                          show_legend, **kwargs)

        return axs_by_position, ax_annot

    def _plot_multi_rows(self, inner_border, show_legend, **kwargs):
        """
        Plot mulitple rows with different y values or different values
        in a defined row column (different y and different row values not 
        tested together
        :param inner_border: list of coordinates of inner border of panel 
        :param show_legend: boolean; whether to show legend or not
        :return:
        """
        # allow for multiple y to be plotted in separate rows
        # prepare y values to be list to i
        if (type(self.y) in self.itertypes):
            all_y = self.y
        else:
            all_y = [self.y]

        if self.row is None:
            row_values = [None]
        elif self.row_order is not None:
            row_values = self.row_order
        else:
            row_values = self.data[self.row].drop_duplicates().values

        # if there is only one hue value
        group_cols = []
        for group_col in [self.row, self.col, self.x]:
            if group_col is not None:
                group_cols.append(group_col)

        if self.hue is None:
            nb_hue_values = 0
        else:
            nb_hue_values = self.data.groupby(group_cols).apply(lambda x: 
                                                                len(x[self.hue].drop_duplicates())).max()
        if nb_hue_values <= 1:
            if "leave_space_for_legend" not in kwargs:
                kwargs["leave_space_for_legend"] = False


        (axs_for_measuring,
         max_y_axis_width_px,
         max_x_axis_height_px,
         max_row_label_width,
         max_col_label_height) = self._measure_max_dimensions_for_multi_row_plots(all_y,
                                                                                 row_values,
                                                                                 show_legend,
                                                                                 **kwargs)

        fig_size = plt.gcf().get_size_inches()
        max_x_axis_height = max_x_axis_height_px / (fig_size[1] * plt.gcf().dpi)
        height_x_axis = max_x_axis_height / self.fig_height_available

        max_width_y_axis = max_y_axis_width_px / (fig_size[0] * plt.gcf().dpi)

        sub_padding = [self.padding[0][0],
                       self.padding[1][0] * self.sub_padding_y_factor]

        self.sub_padding_x = sub_padding[0]
        self.sub_padding_y = sub_padding[1]

        nb_rows = len(row_values)
        # multiple number of rows from row column
        # by number of y that should be plotted
        nb_rows *= len(all_y)

        (height_sub_panel, 
         current_y_pos) = self._get_height_and_ypos_of_sub_panel(inner_border, 
                                                                height_x_axis,
                                                                max_col_label_height, 
                                                                nb_rows)

        self.max_row = nb_rows - 1
        self._set_max_col_for_multi_rows(row_values)

        x_padding_rel = self.xpadding[0] / fig_size[0]
        
        if type(self.col) != type(None):
            group_padding = self._from_kwargs_or_statannot_default(kwargs,
                                                                  "group_padding")
        else:
            group_padding = 0

        # get the first of the ax_for_measuring
        # there is one ax for measuring for each y value used
        # but since ax for measuring is for the x axis, any can be used
        # (x axis is the same independent of y column)
        ax_for_measuring = list(axs_for_measuring.values())[0]

        x_tick_overhang_rel = statannot.get_axis_tick_labels_overhang(ax_for_measuring,
                                                                      "x")
        #  calculate width per col based on widest row
        #  only in that row we know the total width while we also know the
        group_padding_rel = group_padding / fig_size[0]
        width_per_col = self._get_width_per_col_for_multi_row(max_width_y_axis,
                                                             group_padding_rel,
                                                             x_padding_rel)
        # print(group_padding, group_padding_rel)
        self._initialize_padding_factor_matrices()
        
        nb_col_vals = 0
        if type(self.col) == type(None):
            nb_col_vals = 1

        if "x_range" in kwargs:
            x_range = kwargs.pop("x_range")
        else:
            x_range = None

        # get all combinations of y and row
        # to iterate through them and create one row per combination
        y_row_combinations = []
        for y_nb, _ in enumerate(all_y):
            for row in row_values:
                y_row_combinations.append((y_nb, row))
                
        if (len(all_y) > 1) & (self.show_y_label_in_all_rows is None):
            self.show_y_label_in_all_rows = True

        show_x_axis = self._from_kwargs_or_statannot_default(kwargs,
                                                            "show_x_axis")

        if show_x_axis:
            kwargs["leave_space_for_x_tick_overhang"] = True

        for row_nb,( y_nb, row_value) in enumerate(y_row_combinations):

            # set y to a different value for each iteration
            # original y values are stored in "all_y"
            self.y = all_y[y_nb]

            tmp_kwargs = copy.deepcopy(kwargs)

            ax_for_measuring = axs_for_measuring[self.y]

            # for each parameter connected to the y axis
            # check whether an iterable was supplied
            # which then needs to be applied to the respective y
            tmp_kwargs = self._get_y_specific_kwargs(tmp_kwargs, y_nb)

            # y range in tmp kwargs is already a single value
            # if it was an iterable before,
            # it was already mapped to the correct y
            if "y_range" in tmp_kwargs:
                y_range = tmp_kwargs.pop("y_range")
            elif self.use_same_y_ranges:
                y_min = self.data[self.y].min()
                y_max = self.data[self.y].max()
                y_range = [y_min, y_max]
            else:
                y_range = None


            (all_axs,
             height_this_sub_panel) = self._plot_one_row(row_nb, row_value,
                                                        nb_rows, width_per_col,
                                                        height_sub_panel,
                                                        nb_col_vals,
                                                        current_y_pos,
                                                        sub_padding,
                                                        inner_border,
                                                        max_row_label_width,
                                                        x_tick_overhang_rel,
                                                        height_x_axis,
                                                        max_col_label_height,
                                                        max_width_y_axis,
                                                        x_padding_rel,
                                                        group_padding_rel,
                                                        x_range, y_range,
                                                        ax_for_measuring,
                                                        show_legend,
                                                        **tmp_kwargs)


            #  increase row pos by span of sub_panels
            current_y_pos += height_this_sub_panel

            # set new axis in global all_axs at correct position
            # (row and column position)
            all_positions = []
            for position, ax in all_axs.items():
                # ensure that no axis is overwritten
                assert (row_nb, position) not in all_positions
                all_positions.append((row_nb, position))
                self.all_axs[(row_nb, position[1])] = ax

        for ax_for_measuring in axs_for_measuring.values():
            # remove last remaining ax from measuring
            # row label width
            # only remove ax which are still on the figure
            if type(ax_for_measuring.figure) != type(None):
                ax_for_measuring.remove()

    def _measure_max_dimensions_for_multi_row_plots(self, all_y, row_values,
                                                   show_legend,
                                                   **kwargs):
        """
        Measure maximum dimensions for multi row plots considering all y values
        Specifically measure y axis width, x axis height, row label width and
        col label height
        :param all_y: list of all y column names
        :param show_legend: Boolean, whether legend should be shown
        :return: axes for measuring (any future values for specific y value)
                 maximum y axis width,
                 maimum x axis height,
                 maimum row label width,
                 maimum col label height
        """

        x_range = self._get_x_range(**kwargs)

        # set properties to measure maximum dimensions
        tmp_kwargs = copy.deepcopy(kwargs)
        tmp_kwargs["x_range"] = x_range
        if "show_x_axis" not in tmp_kwargs:
            tmp_kwargs["show_x_axis"] = True
        tmp_kwargs["add_background_lines"] = False
        # not sure why these values needed to be set to False
        # would think that this makes maximum dimensions wrong or
        # even determining them unnecessary...
        # tmp_kwargs["show_row_label"] = False
        # tmp_kwargs["show_col_labels_above"] = False

        axs_for_measuring = {}
        # make a test plot for each y to measure
        # height of x axis and width of y_axos
        # will not be accurate for rows with different
        # legend sizes!!! (since legend sizes are not compared!)
        for y_nb, y in enumerate(all_y):

            tmp_kwargs_y = self._get_y_specific_kwargs(tmp_kwargs, y_nb)

            all_test_axs, ax_annot = self.show_data(self.x, y,
                                                    x_labels=self.x_labels,
                                                    hue=self.hue,
                                                    hue_labels=self.hue_labels,
                                                    col=self.col,
                                                    col_labels=self.col_labels,
                                                    row=None,
                                                    baseline=0,
                                                    for_measuring=True,
                                                    increase_padding_above=False,
                                                    show_legend=show_legend,
                                                    **tmp_kwargs_y)
            max_y_axis_width_px = self._get_max_axis_dimension(all_test_axs,
                                                              "yaxis",
                                                              "width")
            max_x_axis_height_px = self._get_max_axis_dimension(all_test_axs,
                                                               "xaxis",
                                                              "height")

            axs_for_measuring = self._delete_all_axes_except_first(all_test_axs,
                                                                   axs_for_measuring,
                                                                   key=y)

            #  if show row label is in kwargs and is True
            #  then get the size of the widest row label
            #  for each row label then calculate the difference
            #  to the largest and subtract that value from its widths
            max_row_label_width = self._get_max_text_width(row_values,
                                                          axs_for_measuring[y],
                                                          padding_keyword ="borderaxespad_",
                                                          **tmp_kwargs_y)

            max_col_label_height = self._get_max_col_label_height(axs_for_measuring[y],
                                                                 row_values,
                                                                 **tmp_kwargs_y)

            ax_annot.remove()

        return (axs_for_measuring,
                max_y_axis_width_px,
                max_x_axis_height_px,
                max_row_label_width,
                max_col_label_height)

    def _get_x_range(self, **kwargs):
        x_range = None
        plot_type = self._from_kwargs_or_statannot_default(kwargs, "plot_type")
        if (plot_type == "line") | (plot_type == "regression"):
            x_values = self.data[self.x].astype(float)
            x_range = [min(x_values), max(x_values)]
            x_range = kwargs.get("x_range", x_range)
        return x_range

    def _get_y_specific_kwargs(self, kwargs, y_nb):
        """
        for each parameter connected to the y axis
        check whether an iterable was supplied
        which then needs to be applied to the respective y
        """
        tmp_kwargs = copy.deepcopy(kwargs)
        y_params = []
        # can be just string or tuple
        # where the first value is the param name
        # and the second value is the index at which it
        # should be checked whether it is an iterable
        # this is necessary since some parameters are an iterable
        # without multiple y values
        #  (e.g. y_range which has min and max in a list)
        y_params.append("y_tick_interval")
        y_params.append("y_axis_label")
        y_params.append(("y_range", 0))

        y_param_values = {}
        for y_param in y_params:
            if type(y_param) in self.itertypes:
                y_param_name = y_param[0]
            else:
                y_param_name = y_param
            y_param_values[y_param] = tmp_kwargs.get(y_param_name, None)

        #  if kwarg is iterable, use the kwarg corresponding to the current y
        #  otherwise leave it as is
        for y_param, y_param_value in y_param_values.items():
            multiple_y_considered = False
            if (type(y_param_value) in self.itertypes):
                # if y param is usually an iterable
                # then go one step deeper into iterable to check
                # whether any value is still an iterable
                if (type(y_param) in self.itertypes):
                    for y_param_to_check in y_param_value:
                        if (type(y_param_to_check) in self.itertypes):
                            multiple_y_considered = True
                            break
                    y_param = y_param[0]
                else:
                    multiple_y_considered = True

            if multiple_y_considered:
                tmp_kwargs[y_param] = y_param_value[y_nb]
        return tmp_kwargs



    def _get_max_axis_dimension(self, all_axs, axis_str, dimension):
        """
        Get maximum dimension of list of axes in pixels.
        :param all_axs: list of matplotlib axes
        :param axis_str: axis of which dimension should be used
                        only 'yaxis' or 'xaxis'
        :param dimension: dimension that should be extracted from axis
                            only 'width' or 'height'
        :return: maximum dimension of axis in dimension
        """
        allowed_axes = ["yaxis", "xaxis"]
        if axis_str not in allowed_axes:
            error_msg = ("As axis_str only 'yaxis' and 'xaxis' are allowed.")
            raise ValueError(error_msg)
        if dimension == "width":
            starting_pos_str = "x0"
        elif dimension == "height":
            starting_pos_str = "y0"
        else:
            raise ValueError("For 'dimension' only 'width' or 'height' "
                             "are allowed")
        max_dimension_px = 0
        for ax in all_axs.values():
            axis = getattr(ax, axis_str)
            starting_pos = getattr(ax.get_position(), starting_pos_str)
            dimension_px = statannot.get_axis_dimension(ax, axis,
                                                           dimension,
                                                           starting_pos)
            max_dimension_px = max(max_dimension_px, dimension_px)
        return max_dimension_px

    def _delete_all_axes_except_first(self, all_axs, axes_kept, key):
        """
        Delete axes in list except the first axis. The first axis is saved
        in a dict (axes_kept) under the defined key.
        :param all_axs: list of matplotlib axes
        :param axes_kept: dict of axes which are not deleted
        :param key: key under which axes which are not deleted are kept in dict
        :return: copy of dict with kept axes with newly added axis
        """
        axes_kept = copy.copy(axes_kept)
        for ax_nb, ax in enumerate(all_axs.values()):
            #  remove all but one ax, this will be kept
            #  to check for row label size
            if ax_nb == 0:
                axes_kept[key] = ax
            else:
                ax.remove()
        return axes_kept

    def _get_max_text_width(self, texts, ax_for_measuring,
                           padding_keyword, **kwargs):
        """
        Get maximum width of a list of texts in px.
        :param texts: List of texts (strings)
        :param ax_for_measuring: Matplotlib axes to measure size
        :return:
        """
        max_text_width = 0
        for text in texts:

            if self._is_none(text):
                continue

            # get width of row label or legend
            text_width = self._get_row_label_width(text,
                                                  ax_for_measuring,
                                                  padding_keyword=padding_keyword,
                                                  **kwargs)
            max_text_width = max(max_text_width, text_width)
        return max_text_width

    def _get_max_col_label_height(self, ax_for_measuring, row_values, **kwargs):
        max_col_label_height = 0
        #  there may not be any row values which need to be measured
        #  if only multiple y values are supplied but no column for rows
        if len(row_values) <= 1:
            return max_col_label_height
        arg_name = "show_col_labels_above"
        if not FigurePanel._from_kwargs_or_statannot_default(kwargs, arg_name):
            return max_col_label_height
        if self.col is None:
            return max_col_label_height
        #  get max col_val label
        first_row_data = self.data.loc[self.data[self.row] == row_values[0]]
        first_row_col_values = first_row_data[self.col].drop_duplicates()
        #  measure height of col labels
        get_default_value = FigurePanel._from_kwargs_or_statannot_default
        add_column_plot_title_above = statannot.add_column_plot_title_above
        for first_row_col_value in first_row_col_values:
            col_label_padding = get_default_value(kwargs, "col_label_padding")

            col_label_height = add_column_plot_title_above(ax_for_measuring,
                                                           first_row_col_value,
                                                           col_label_padding,
                                                           self.font_size)
            max_col_label_height = max(max_col_label_height, col_label_height)
        return max_col_label_height

    def _get_width_per_col_for_multi_row(self, max_width_y_axis,
                                        group_padding_rel,
                                        x_padding_rel):
        width_of_widest_col = (self.width * self.fig_width_available -
                               max_width_y_axis - x_padding_rel )

        #  deduct the group_padding which will be included between plots
        #  therefore will be included number of cols - 1
        width_of_widest_col -= group_padding_rel * (self.max_col)
        width_per_col = width_of_widest_col / (self.max_col + 1)
        return width_per_col

    def _get_height_and_ypos_of_sub_panel(self, inner_border, height_x_axis,
                                         max_col_label_height, nb_rows):
        fig_height = plt.gcf().get_size_inches()[1]
        figure_pad_rel_y = self.fig_padding[1]/fig_height
        sub_padding_y_rel = self.sub_padding_y / fig_height
        # add two frames sub_padding_y_rel to total height available for sub plots
        # to align the height of the sub plots with the inner_border
        height_sub_panel = (self.height - height_x_axis -
                            max_col_label_height +
                            2 * sub_padding_y_rel -
                            2 * self.padding[1][0] / fig_height) / nb_rows
        # current pos y must be starting from the inner_border
        # however, in the sub_panels which will be created
        # the ourder border will be created like this:
        # y0_border = 1 - ( self.panel_y * self.fig_height_available +
        #  height + fig_padding_rel_y - padding_rel_y)
        # current y_pos will be calculated so that y1 are aligned for the first sub_panel
        # and the current figurepanel
        current_y_pos = ((1 - inner_border[3]-
                         figure_pad_rel_y - sub_padding_y_rel) /
                         self.fig_height_available)

        return height_sub_panel, current_y_pos


    def _set_max_col_for_multi_rows(self, row_values):
        #  self.max_col will be set here when plotting multiple rows
        fig_size = plt.gcf().get_size_inches()
        self.max_col = 0
        for row_value in row_values:
            # if row value is none, use all the data to get number of cols
            # in that case there is only one value in row_values (None)
            # and multiple rows come from multiple y supplied
            if type(row_value) == type(None):
                row_data = self.data
            else:
                row_data = self.data.loc[self.data[self.row] == row_value]

            max_col = self._get_max_col_for_data(row_data, self.col)
            self.max_col = max(self.max_col, max_col)

    def _plot_one_row(self, row_nb, row_value, nb_rows,
                     width_per_col, height_sub_panel,
                     nb_col_vals, current_y_pos, sub_padding,
                     inner_border,
                     max_row_label_width, x_tick_overhang_rel,
                     height_x_axis, max_col_label_height,
                     max_width_y_axis, x_padding_rel,
                     group_padding_rel,
                     x_range, y_range,
                     ax_for_measuring,
                     show_legend, **kwargs):
        
        show_row_label = kwargs.get("show_row_label",
                                    self._default_in_statannot("show_row_label"))
        #  add to each inclusion criteria the row criteria
        # so that in each sub panel only the data from
        # a specific row value is used
        new_inclusion_criteria = copy.deepcopy(self.inclusion_criteria)

        if (row_value is not None):
            for inclusion_criterion in new_inclusion_criteria:
                inclusion_criterion[self.row] = [row_value]
            if len(new_inclusion_criteria) == 0:
                new_inclusion_criteria = [{self.row:[row_value]}]
            
        if (row_value is not None) & show_row_label:
                # [row_label_map.get(row_value, row_value)]

            #  measure width of row label
            #  difference of current row label and maximum row label
            #  will be deducted from width of this panel
            label_width = self._get_row_label_width(row_value,
                                                   ax_for_measuring,
                                                   padding_keyword="borderaxespad_",
                                                   **kwargs)
            label_width_diff = max_row_label_width - label_width
        else:
            label_width_diff = 0

        # measure y axis width
        # and add difference to maximum to label_width_diff
        # which will equalize plot width using this value
        y_axis_width_px = statannot.get_axis_dimension(ax_for_measuring,
                                                       ax_for_measuring.yaxis,
                                                       "width",
                                                       ax_for_measuring.get_position().x0)

        width_this_panel = self._get_width_of_plot_row(row_value, width_per_col,
                                                      max_width_y_axis,
                                                      x_padding_rel,
                                                      label_width_diff, row_nb,
                                                      nb_rows, nb_col_vals,
                                                      group_padding_rel,
                                                      x_tick_overhang_rel)

        if (show_legend is not None) and show_legend:
            kwargs["leave_space_for_legend"] = True
            if row_nb == 0:
                show_legend = True
            else:
                show_legend = False

        #  create sub panel with same parameters than current panel
        #  except row position and row span

        # set empty y axis label with correct amount of line breaks
        if (row_nb > 0) & ( not self.show_y_label_in_all_rows):
            kwargs = self._set_empty_y_axis_label_in_kwargs(**kwargs)

        x_axis_label = kwargs.get("x_axis_label", "")

        # for last row, add as much row_span to fully accomodate the x axis
        if row_nb == (nb_rows - 1):
            show_x_axis = True
            height_this_sub_panel = height_sub_panel + height_x_axis
            # only allow x axis label in last row
            if "x_axis_label" != "":
                kwargs["x_axis_label"] = x_axis_label
        else:
            if "x_axis_label" != "":
                kwargs["x_axis_label"] = ""
            show_x_axis = False
            height_this_sub_panel = height_sub_panel

        if row_nb == 0:
            height_this_sub_panel += max_col_label_height

        if "show_col_labels_below" not in kwargs:
            if kwargs.get("show_col_labels_above", False) == True:
                kwargs["show_col_labels_below"] = False

        # only show col labels in first column to prevent repetitions
        if (row_nb > 0) & (not self.col_labels_every_row):
            kwargs["show_col_labels_above"] = False

        # padding for sub panels in y should be only half
        sub_panel = FigurePanel(self.figure, self.fig, self.fig_width_available,
                                self.fig_height_available, self.fig_padding,
                                self.panel_file_paths, self.all_panel_imgs,
                                 self.panel_pptxs, self.data,
                                self.letter, y_pos = current_y_pos,
                                 height= height_this_sub_panel,
                                x_pos = self.panel_x, width = width_this_panel,
                                letter_fontsize=self.letter_fontsize,
                                 show_letter = False, padding = sub_padding,
                                 size_factor = self.size_factor,
                                increase_size_fac = self.increase_size_fac,
                                font_size=self.font_size,
                                video=self.video)

        fig = plt.gcf()
        y_axis_width = y_axis_width_px / (fig.get_size_inches()[0] * fig.dpi)

        y_axis_diff = max_width_y_axis - y_axis_width
        y_axis_diff = 0

        sub_panel.inner_border[0] += y_axis_diff

        # show data with same properties as current show_data
        # except for row which will be None
        # and except processing, since that was done already
        # and will be accessible for new figure panel
        # since data is used for __init__
        # TODO:
        #  should "width_y_axis_ parameter for show_data be max_width_y_axis?
        all_axs, _ = sub_panel.show_data(self.x, self.y, x_labels=self.x_labels,
                                         hue=self.hue,
                                         hue_labels=self.hue_labels,
                                         col=self.col,
                                        col_labels=self.col_labels,
                                         x_order=self.x_order,
                                         hue_order=self.hue_order,
                                         col_order=self.col_order, row=None,
                                        inclusion_criteria=new_inclusion_criteria,
                                        baseline=0, row_label_text=row_value,
                                        # add_background_lines=False,
                                        y_range=y_range,
                                         show_x_axis=show_x_axis,
                                         x_range = x_range,
                                         increase_padding_above=False,
                                        width_y_axis = max_width_y_axis,
                                        auto_scale_group_padding = False,
                                         show_legend=show_legend,
                                        **kwargs)


        return all_axs, height_this_sub_panel


    def _set_empty_y_axis_label_in_kwargs(self, **kwargs):
        #  create empty y axis label just containing the line breaks
        #  to get the right shift
        if "y_axis_label" in kwargs:
            y_axis_label = kwargs["y_axis_label"]
            nb_line_breaks = len(y_axis_label.split("\n")) - 1
            empty_y_axis_label = " ".join(["\n"] * nb_line_breaks) + " "

        # change y axis label to empty label for
        # every row except the first
        if "y_axis_label" in kwargs:
            kwargs["y_axis_label"] = empty_y_axis_label

        return kwargs

    def _get_width_of_plot_row(self, row_value, width_per_col, max_width_y_axis,
                              x_padding_rel, label_width_diff, row_nb, nb_rows,
                              nb_col_vals, group_padding_rel,
                              x_tick_overhang_rel):
        nb_col_vals = 1
        if self.col is not None :
            # calculate width of current row
            # based on how many col plots go there
            # in order to keep the width of all col plots the same
            if row_value is not None:
                all_col_vals = self.data.loc[self.data[self.row] == row_value,
                                             self.col].drop_duplicates()
            else:
                all_col_vals = self.data[self.col].drop_duplicates()

            if self.col_order is not None:
                all_new_col_vals = []
                for col_val in all_col_vals:
                    # if col val is string, check whether string is present
                    # in any of the order strings
                    if type(col_val) == str:
                        for col_order_val in self.col_order:
                            if col_val in col_order_val:
                                all_new_col_vals.append(col_val)
                                break
                    else:
                        if col_val in self.col_order:
                            all_new_col_vals.append(col_val)
                all_col_vals = all_new_col_vals
            nb_col_vals = len(all_col_vals)

        # no idea why this shouldnt be considered...
        width_this_panel = (nb_col_vals * width_per_col +
                            max_width_y_axis + x_padding_rel -
                            label_width_diff)

        width_this_panel += group_padding_rel * (nb_col_vals - 1)

        #for all rows except the last
        #reduce width by overhang of x tick labels
        #since those labels are only present in the last row and will
        #add to the width of the plot

        # if row_nb != (nb_rows - 1):
        #     width_this_panel -= x_tick_overhang_rel

        return width_this_panel


    def _get_max_col_for_data(self, data, col):
        if type(col) != type(None):
            nb_columns = len(data[col].drop_duplicates())
        else:
            nb_columns = 1
        max_col = nb_columns - 1
        return max_col


    def _remove_data(self, row, list_values_to_include):
        # exclude data for apply function
        # check for each column each list of values to include
        for column, values_to_include in list_values_to_include.items():
            if len(values_to_include) > 0:
                # if value of current row is not
                #  in values to include stop checkup and return 0
                if row[column] not in values_to_include:
                    return 0
        return 1


    def _plot_simple_row(self, data, x, y, hue, col,
                        for_measuring, increase_padding_above,
                        inner_border, show_legend, **kwargs):
        """
        Plot a single row of data plots.
        """
        self.max_col = self._get_max_col_for_data(data, col)
        self.max_row = 0

        if increase_padding_above:
            #  increase top by changing outer_border
            #  otherwise data plots tend to be too close in y
            fig_height = plt.gcf().get_size_inches()[1]
            # POTENTIAL BUG / PROBLEM! for top why is inner_border 3 changed?
            inner_border[3] -= self.padding[1][0] / 2 / fig_height

        #  if number of col values AND number of x valss is only 1
        #  increase padding below as well
        # since otherwise it looks squeezed
        # but only do that if plot type is not regression or line.
        plot_types_no_higher_pad_below = []
        plot_types_no_higher_pad_below.append("regression")
        plot_types_no_higher_pad_below.append("line")

        increase_padding_below = True
        if self.plot_type in plot_types_no_higher_pad_below:
            increase_padding_below = False


        if increase_padding_below:
            inner_border = self._do_increase_of_padding_below_plot(inner_border,
                                                                  data, x, col,
                                                                  fig_height,
                                                                  **kwargs)
        (axs_by_position,
         ax_annot) = self._plot_results(data, x, y, inner_border,
                                       hue=hue, col=col,
                                       for_measuring=for_measuring,
                                       show_legend=show_legend,
                                       **kwargs)


        # initiate label matrices for adding labels by position later
        self._initiate_label_matrices()

        # TODO: Improvde (shorten) function name
        self.included_data = self._get_data_in_order_params_for_representative_data(data,
                                                                                   x,
                                                                                   hue,
                                                                                   col,
                                                                                   kwargs)

        columns_for_grouping = [column for column in [x,hue,col]
                                if column != None]
        self.grouped_data = self.included_data.groupby(by=columns_for_grouping)

        self.all_axs = axs_by_position

        return axs_by_position, ax_annot


    def _do_increase_of_padding_below_plot(self, inner_border,
                                          data, x, col, fig_height,
                                          **kwargs):
        if "col_order" in kwargs:
            col_order = kwargs["col_order"]
        else:
            col_order= []
        if "x_order" in kwargs:
            x_order = kwargs["x_order"]
        else:
            x_order = []
        nb_col_vals = 1
        if type(col) != type(None):
            nb_col_vals = len(data[col].drop_duplicates())
            if nb_col_vals > 1:
                # number of col values
                # could also be restricted by the number of
                # values in col_order
                if len(col_order) > 0:
                    nb_col_vals = len(col_order)
        nb_x_vals = len(data[x].drop_duplicates())
        if nb_x_vals > 1:
            if len(x_order) > 0:
                nb_x_vals = len(x_order)

        # add padding to top of plot
        if (nb_col_vals == 1) & (nb_x_vals == 1):
            # POTENTIAL BUG / PROBLEM! for top why is inner_border 2 changed?
            inner_border[2] += self.padding[1][0]/2 / fig_height
        return inner_border


    def _get_data_in_order_params_for_representative_data(self, data, x, hue,
                                                         col, kwargs):
        # preparation for getting representative data?
        # exclude data with values not in order parameter
        columns_to_exclude_data_from = [x, hue, col]
        list_values_to_include = {}
        all_orders = ["x_order", "hue_order", "col_order"]
        for i, order in enumerate(all_orders):
            column = columns_to_exclude_data_from[i]
            if order in kwargs:
                list_values_to_include[column] = kwargs[order]
            else:
                list_values_to_include[column] = []


        data.loc[:,"include_row"] = data.apply(self._remove_data,
                                               args=([list_values_to_include]),
                                               axis=1)
        included_data = data.loc[data.loc[:,"include_row"] == 1]
        return included_data


    def get_representative_data(self, unit_columns=None, cols_to_show=None,
                                nb_of_measurements_matter=True,
                                sort_by_relative_difference=True,
                                print_results=True,
                                nb_vals_to_show=20,
                                column_suffix = "___d___"):
        """
        Get list of units (cells etc) that are closest to average of data.
        Data from one unit is in a single image, therefore cannot be separated
        the function will rank units than regarding their difference to the
        mean. If you want a representative neuron but did measure neurites,
        a unit should be a neuron but the function will account the difference
        from the mean of all measured neurites.
        It will weigh larger differences from the mean more
        (squared difference of mean).

        :param unit_column: columns which uniquely identify one "unit",
                            only necessary if there is more
                            than one datapoint in one image
                            with list_of_columns being the columns
                            that define one unit that was analyzed
                            (e.g. for a neurite it could be
                            ["date", "neuron", "neurite"]).
        :param cols_to_show: Columns to show in summary
        :param nb_of_measurements_matter: Whether representative data should be
                                            sorted by number of measurements.
                                            When one unit can have more than
                                            one datapoint, this means first
                                            showing the units with the most
                                            datapoints, independent of their
                                            deviation from the mean. This can
                                            be helpful when most units have e.g.
                                            2 datapoints and only a few 1, then
                                            you may only want to use units with
                                            2 datapoints.
        :param sort_by_relative_difference: Whether to sort by relative
                                            difference from the mean (if True)
                                            Otherwise will sort by absolute
                                            difference. When having more than
                                            one measure, relative difference
                                            can help making them comparable
                                            (keeping the contribution of all
                                            measures similar). But in that case
                                            a mean close to 0 might also
                                            artificially increase the relative
                                            difference.
        :param print_results: Whether to print results or just calculate them.
                                When printing comparisons for multiple plots
                                later, just calculating can be enough.
        :param nb_vals_to_show: Number of units to show for each group.
        :param column_suffix: suffix that should be added for difference columns
                                this should be something that is not present
                                in any current column name.

        """
        if cols_to_show == None:
            cols_to_show = []
        if unit_columns == None:
            unit_columns = []
        if (len(self.grouped_data) == 0) | (len(self.included_data) == 0):
            return



        grouped_means = self.grouped_data.mean()
        grouped_stds = self.grouped_data.std()
        group_columns = grouped_means.index.names
        group_indices = grouped_means.index
        included_data_indexed = self.included_data.set_index(group_columns)
        if len(cols_to_show) == 0:
            if len(unit_columns) > 0:
                cols_to_show = copy.copy(unit_columns)
            else:
                cols_to_show = [column
                                for column in list(self.included_data.columns)
                                if column not in group_columns]
        # get all group means in dictionary
        group_means = {}
        group_stds = {}
        for values in group_indices:
            one_group_data = included_data_indexed.loc[values]
            group_means[values] = grouped_means[self.y].loc[values]
            group_stds[values] = grouped_stds[self.y].loc[values]

        evaluated_data = copy.copy(self.included_data)
        evaluated_data.loc[:,'d_mean'] = evaluated_data.apply(self._get_d_mean,
                                                              args=[group_means,
                                                                     group_stds,
                                                                     group_columns],
                                                              axis=1)
        y_diff_column = self.y + column_suffix
        evaluated_data.loc[:, y_diff_column] = evaluated_data.apply(self._get_difference_to_mean,
                                                                       args=[group_means,
                                                                            group_columns],
                                                                       axis = 1)
        y_abs_diff_column = y_diff_column + "abs"
        evaluated_data.loc[:, y_abs_diff_column] = evaluated_data[y_diff_column].abs()
        # track number of measurements for
        evaluated_data.loc[:,"nb_measurements"] = 1
        cols_evaluated = []
        ascending_vals = []
        # always measure the number of measurements

        # but only if the number of measurements is important, sort by it

        cols_evaluated.append("nb_measurements")

        if nb_of_measurements_matter:
            ascending_vals.append(False)

        if sort_by_relative_difference:
            cols_evaluated.append("d_mean")
        else:
            cols_evaluated.append(y_abs_diff_column)

        ascending_vals.append(True)
        # move columns evaluated first so that they are shown first
        cols_to_show = cols_evaluated + cols_to_show

        # OLD: sum up; NEW: AVERAGE
        # deviation from mean for the same unit
        if len(unit_columns) > 0:
            sum_d_mean_dict = {}
            # order of columns determines what is sorted by first
            # in this case it is most important
            #  that there is there is the max nb of measurements
            for column in evaluated_data.columns:
                if ((column not in unit_columns) & 
                        (column not in cols_evaluated)):
                    sum_d_mean_dict[column] = "first"
            for column in cols_evaluated:
                if column == "d_mean":
                    sum_d_mean_dict[column] = "mean"
                else:
                    sum_d_mean_dict[column] = "sum"

            # sort by group_columns now so that "first" function
            #  always picks up the same value
            # so that each group is identified
            #  by a single set of values in group_columns
            evaluated_data = evaluated_data.sort_values(by=group_columns)
            evaluated_data = evaluated_data.groupby(by=(unit_columns)).agg(sum_d_mean_dict).reset_index()

        # print out units for each group,
        #  sorted for lowest deviation first with max measurements
        included_data_indexed = evaluated_data.set_index(group_columns)
        self.representative_data = included_data_indexed
        self.representative_diff_column = y_diff_column
        self.representative_data_groups = group_columns
        self.representative_unit_cols = unit_columns

        cols_to_show += [y_diff_column]

        cols_to_show = [column for column in cols_to_show
                        if column not in group_columns]

        # remove nb_measurements from cols_evaluated to not sort by it
        if not nb_of_measurements_matter:
            cols_evaluated = cols_evaluated[1:]

        if not print_results:
            return

        pd.set_option('display.width', 4000)
        pd.set_option('display.max_columns', 500)
        # also show y values and average
        for values in group_indices:
            # check if group index is in index of included data
            # it might have been removed by adding up values from same unit
            if values not in included_data_indexed.index:
                continue

            one_group_data = included_data_indexed.loc[values]
            one_group_data = one_group_data.sort_values(by=cols_evaluated,
                                                        ascending=ascending_vals)
            print(one_group_data.head(nb_vals_to_show)[cols_to_show])

    def _get_difference_to_mean(self, row, group_means, group_columns):
        group_index = self._get_group_index_from_data(row, group_columns)
        group_mean = group_means[group_index]
        return row[self.y] - group_mean

    def _get_d_mean(self, row, group_means,
                   group_stds, group_columns):
        
        group_index = self._get_group_index_from_data(row, group_columns)
        group_mean = group_means[group_index]
        group_std = group_stds[group_index]
        # # for finding cells good in several measures (from several panels):
        # use square of difference to weigh higher difference more
        # cells with a bit of deviation in each category is much preferred
        # over cell perfect in most and very bad in one measure
        # ADDITIONALLY: normalization by std to by group_mean
        # since group_mean could be close to zero and
        # thereby massively increase the importance of the measure
        d_mean = ( row[self.y] - group_mean )**2 / group_std**2
        return d_mean

    def _get_group_index_from_data(selfrow, row, group_columns):
        # get the index values for the group
        if len(group_columns) == 1:
            group_column = group_columns[0]
            group_index = row[group_column]
        else:
            group_values = []
            for group_column in group_columns:
                group_values.append(row[group_column])
            group_index = tuple(group_values)
        return group_index

    def _round_data(self, data, inclusion_criteria,
                    round_columns, round_digits):
        special_columns = {"__x__":self.x,
                           "__hue__":self.hue,
                           "__col__":self.col,
                           "__row__":self.row}
        if round_columns is None:
            return data, round_columns, inclusion_criteria
        correct_round_columns = []
        for round_column in round_columns:
            if round_column in special_columns.keys():
                round_column = special_columns[round_column]
            for inclusion_criteria_dict in inclusion_criteria:
                if round_column not in inclusion_criteria_dict:
                    continue
                allowed_col_vals = inclusion_criteria_dict[round_column]
                if round_digits == 0:
                    allowed_col_vals = [int(val) for val in allowed_col_vals]
                else:
                    allowed_col_vals = list(np.round(allowed_col_vals))
                inclusion_criteria_dict[round_column] = allowed_col_vals
            correct_round_columns.append(round_column)
            data[round_column] = data[round_column].astype(float)
            if round_digits == 0:
                data[round_column] = data[round_column].astype(int)
            else:
                data[round_column] = data[round_column].round(round_digits)
            data[round_column] = data[round_column].apply(str)

        return data, correct_round_columns, inclusion_criteria

    @staticmethod
    def _get_sorted_ordered_vals(data, all_ordered_vals, round_columns,
                                 round_digits):
        """
        Sort unique values of column in data instead of receiving
        a list with column values in defined order.
        Args:
            data:
            all_ordered_vals:

        Returns:

        """
        corrected_ordered_vals = {}
        for ordered_col, sort_func in all_ordered_vals.items():
            if sort_func is None:
                corrected_ordered_vals[ordered_col] = None
                continue

            if (not callable(sort_func)) & (type(sort_func) != str):
                corrected_ordered_vals[ordered_col] = sort_func
                continue
            unique_vals = data[ordered_col].drop_duplicates().values
            if not callable(sort_func):
                if sort_func == "ascending":
                    reverse = False
                elif sort_func == "descending":
                    reverse = True
                else:
                    raise ValueError("If the _order parameter for the "
                                     f"column {ordered_col} is a string, it "
                                     f"must be 'ascending' or 'descending'. "
                                     f"Instead it is {sort_func}.")
                sort_func = lambda x: list(map(str, sorted(map(float, x),
                                                      reverse=reverse)))
                sorted_values = sort_func(unique_vals)

                # since float was applied to the data column
                # make sure to round appropriately afterwards again
                # (might only be important for digits==0 actually
                if type(round_columns) in [list, tuple]:
                    if (ordered_col in round_columns) & (round_digits == 0):
                        sorted_values = list(map(str,
                                            map(int, map(float, sorted_values))))
            corrected_ordered_vals[ordered_col] = sorted_values
            
        return corrected_ordered_vals

    @staticmethod
    def _replace_strs_in_orders(orders, strs_to_replace):
        """
        replace strs in data, taking strings from dict strs_to_replace
        :param strs_to_replace: dict with columns as keys
                                and as values list in shape of
                                [(str1,str1_replaced),(str2,str2_replaced)]
        :param orders: dict of all "order" lists
        """
        raise_error = False
        for column, order_vals in orders.items():
            if order_vals is None:
                continue
            if column not in strs_to_replace:
                continue
            new_order_vals = []
            labels = strs_to_replace[column]
            for val in order_vals:
                val_replaced = False
                for label in labels:
                    if (type(label) not in [tuple, list]):
                        label = [label]
                    if label[0].find("__$$__") != -1:
                        new_label = label[0].replace("__$$__", val)
                        new_order_vals.append(new_label)
                        val_replaced = True
                        break
                    else:
                        if label[0] != val:
                            continue
                        new_order_vals.append(label[1])
                        val_replaced = True
                        break
                if not val_replaced:
                    # if val was not changed by any label
                    # add val unchanged
                    new_order_vals.append(val)
            orders[column] = new_order_vals
        return orders

    @staticmethod
    def _replace_strs_in_data(data, strs_to_replace):
        """
        replace strs in data, taking strings from dict strs_to_replace
        :param strs_to_replace: dict with columns as keys
                                and as values list in shape of
                                [(str1,str1_replaced),(str2,str2_replaced)]
        :param data: as dataframe, must contain all keys
                    in strs_to_replace as columns
        """
        raise_error = False
        for column in strs_to_replace:
            if column is None:
                continue
            labels = strs_to_replace[column]
            for label in labels:
                if (type(label) not in [tuple, list]):
                    label = [label]
                if label[0].find("__$$__") != -1:
                    all_column_vals = data[column].drop_duplicates().values
                    for val in all_column_vals:
                        new_label = label[0].replace("__$$__", val)
                        data.loc[data[column] == val, column] = new_label
                else:
                    data.loc[data[column] == label[0], column] = label[1]
            # if raise_error:
            #     raise ValueError(f"The label {str(label)} for the "
            #                      f"column {column} should be a tuple or"
            #                      f" list instead of a {str(type(label))}.")

        return data

    @staticmethod
    def _correct_ordered_vals(data, all_ordered_vals):
        """
        Correct ordered vals by checking column values in data that
        contain the ordered val and then replacing the incomplete
        (but unique) value in ordered vals with the complete value
        Args:
            all_ordered_vals: dict where keys are column names and values
                are lists of oredered column values

        Returns: corrected ordered vals

        """
        all_new_ordered_vals = {}
        for ordered_col, ordered_vals in all_ordered_vals.items():
            if ordered_vals is None:
                all_new_ordered_vals[ordered_col] = None
                continue
            new_ordered_vals = []
            for val in ordered_vals:
                all_col_vals = data[ordered_col].drop_duplicates().values
                match_found = False
                for col_val in all_col_vals:
                    if val in col_val:
                        match_found = True
                        break
                if not match_found:
                    print(f"WARNING: For the ordered values for the "
                                     f"column {ordered_col}, the value "
                                     f"{val} was not found in any column "
                                     f"value in the data and therefore "
                          f"excluded.")
                else:
                    new_ordered_vals.append(col_val)
            if len(new_ordered_vals) != len(set(new_ordered_vals)):
                raise ValueError("While trying to correct the values in the "
                                 f"_order parameter for the column "
                                 f"{ordered_col} for errors, at least one "
                                 f"_order value was found at least twice "
                                 f"in the data column values: "
                                 f"{new_ordered_vals}. Probably the supplied "
                                 f"value/s that occur/s more than once is "
                                 f"part of another column value and therefore "
                                 f"was found to be present more than once. "
                                 f"Please use unique values for the _order "
                                 f"parameters. Keep in mind that the _order "
                                 f"values should be data column values before "
                                 f"the _labels parameter is applied if "
                                 f"the paramter order_vals_before_changing_vals"
                                 f" is True.")
            all_new_ordered_vals[ordered_col] = new_ordered_vals
        return all_new_ordered_vals

    def _rename_column_values(self, data, renaming_dicts):
        #  renaming dict is a list of dicts
        #  each dict is for one renaming
        #  one key in the dict has to be "__from__" and the value
        #  determines what should be changed
        #  one key in the dict has to be "__to__" and the value
        #  determines the value it should be changed to
        #  one key in the dict has to be "__target_column__" and the value
        #  determines in which column the change should occur
        #  the other keys are column names and the corresponding values
        #  determine the value the column must have
        if type(renaming_dicts) == type(None):
            return data
        for renaming_dict in renaming_dicts:
            excluded_keys = ["__from__", "__to__", "__target-column__"]
            #  get all rows that match the conditions
            #  except in the excluded keys
            matched_data = FigurePanel._get_rows_matching_criteria(data,
                                                                  renaming_dict,
                                                                  excluded_keys)

            mached_indices = matched_data.index.values
            column = renaming_dict["__target-column__"]
            value_to_replace = renaming_dict["__from__"]
            replaced_value = renaming_dict["__to__"]
            #  replce values in target column from "from" to "to"
            new_column_values = data.loc[mached_indices,
                                         column].str.replace(value_to_replace,
                                                             replaced_value)
            data.loc[mached_indices, column] = new_column_values
        return data

    def _plot_results(self, data, x, y, inner_border, for_measuring, **kwargs):
        
        size_factor = self.size_factor * self.increase_size_fac
        # get box dicts of one group and plot data of that group
        output = statannot.plot_and_add_stat_annotation(data = data,
                                                        x=x, y=y, fig=self.fig,
                                                      letter=self.letter,
                                                      size_factor=size_factor,
                                                      outer_border=inner_border,
                                                        # padding=self.padding,
                                                      fontsize=self.font_size,
                                                        figure_panel = self,
                                                        hor_alignment = self.hor_alignment,
                                                        for_measuring = for_measuring,
                                                        pair_unit_columns =
                                                        self.pair_unit_columns,
                                                        **kwargs)

        (axs_by_position,
         ax_annotations,
         test_result_list) = output

        self.test_result_list = test_result_list

        return (axs_by_position, ax_annotations)

    def get_basic_statistics(self, N_columns = "date", n_columns = None,
                             show_stats=False, show_from_ungrouped_data=None,
                             show_from_grouped_data = None):
        """
        Get basic statistics of different datagroups.
        (mean, number of experiments, number of cells, etc).

        :param N_columns: is column or list of columns
                        in which the number of different values will
                        be calculated
        :param n_columns: is a column or list of columns
                            that define the number of n that should be returned
                            if not defined, will count number of measurements
        :param show_stats: Whether to show statistics test results
        :param show_from_ungrouped_data: Whether to show basic statistics from
                                        ungrouped data (particularly important
                                        for continuous data)
        :param show_from_grouped_data: Whether to show basic statistics from
                                        grouped data (when there are any
                                        data groups)
        """
        if type(N_columns) == str:
            N_columns = [N_columns]
        # get values for combined data

        if show_stats:
            print(self.test_result_list)

        continuous_plot_types = ["line", "regression", "scatter"]

        #for continuous plots by default show only statistics of
        #ungrouped data
        #for other other plots by default only stats of
        #grouped data
        if self.plot_type in continuous_plot_types:
            if self._is_none(show_from_ungrouped_data):
                show_from_ungrouped_data = True
            if self._is_none(show_from_grouped_data):
                show_from_grouped_data = False
        else:
            if self._is_none(show_from_ungrouped_data):
                show_from_ungrouped_data = False
            if self._is_none(show_from_grouped_data):
                show_from_grouped_data = True

        if show_from_ungrouped_data:
            columns = ["mean", "std", "sem", "n", "N"]
            data = self.grouped_data.obj
            combined_stat_vals = pd.DataFrame(columns=columns)
            combined_stat_vals.loc[0,"mean"] = data[self.y].mean()
            combined_stat_vals.loc[0,"std"] = data[self.y].std()
            combined_stat_vals.loc[:,"min"] = self.data[self.y].min()
            combined_stat_vals.loc[:,"max"] = self.data[self.y].max()
            combined_stat_vals.loc[0,"sem"] = data[self.y].sem()
            if type(n_columns) == type(None):
                combined_stat_vals.loc[0,"n"] = data[self.y].count()
            else:
                combined_stat_vals.loc[0,"n"] = len(data[n_columns]
                                                    .drop_duplicates())
            combined_stat_vals.loc[0,"N"] = len(data[N_columns]
                                                .drop_duplicates())
            print(combined_stat_vals)

        if not show_from_grouped_data:
            return

        # get values for separate groups
        grouped_means = self.grouped_data.mean()
        grouped_columns = list(grouped_means.index.names)
        grouped_means.reset_index(inplace=True)
        statistic_vals = grouped_means.loc[:,grouped_columns]
        statistic_vals.loc[:,"mean"] = self.grouped_data.mean().reset_index()[self.y]
        statistic_vals.loc[:,"min"] = self.grouped_data.min().reset_index()[self.y]
        statistic_vals.loc[:,"max"] = self.grouped_data.max().reset_index()[self.y]
        statistic_vals.loc[:,"std"] = self.grouped_data.std().reset_index()[self.y]
        statistic_vals.loc[:,"sem"] = self.grouped_data.sem().reset_index()[self.y]
        if type(n_columns) == type(None):
            statistic_vals.loc[:,"n"] = self.grouped_data.count().reset_index()[self.y]
        else:
            statistic_vals.loc[:,"n"] = self.grouped_data.apply(lambda x:
                                                                len(x[n_columns]
                                                                    .drop_duplicates())).reset_index()[0]
        statistic_vals.loc[:,"N"] = self.grouped_data.apply(lambda x:
                                                            len(x[N_columns]
                                                                .drop_duplicates())).reset_index()[0]
        print(statistic_vals)

    def add_text_within_at_coords(self, text, x, y, font_size=7, line_spacing=1,
                                  hor_align = "left", vert_align="bottom",
                                  orientation="hor",
                                  images=None, only_show_in_rows=None,
                                  only_show_in_columns=None,
                                  correct_for_cropping=True, color = "white"):
        """
        Add text on image at coordinates.

        :param text: String of text to add. Linebreaks can be added with \\n
        :param x: x coordinate at which to add the text
        :param y: y coordinate at which to add the text
        :param line_spacing: Line spacing when including a line break
        :param font_size: font size either in pt or as "small", "medium" or
                            "large"
        :param hor_align: horizontal alignment of text ("left, "center" and
                         "right" allowed
        :param vert_align: Vertical alignment of text ("bottom", "center" and
                            "top" allowed)
        :param orientation: Orientation of text ("hor" or "vert" or degrees)
        :param images: dict that specifies on which images should be drawn
                       the key is the category and the value
                       is the allowed value
        :param only_show_in_rows: List of rows in which to add the text on
                                  images
        :param only_show_in_columns: List of columns in which to add the text
                                        on images
        :param correct_for_cropping: Correct coordinates for applied cropping
        :param color: Font color
        """

        for position, ax in self.all_axs.items():
            row = position[0]
            column = position[1]

            pre_identity = self.pos_to_pre_identity_map[position]
            identity_matches = self._check_if_identity_matches_dict_criteria(pre_identity,
                                                                            images)


            grid_position_correct = False
            if identity_matches:
                grid_position_correct = self._check_if_pos_is_in_row_col_list(row, column,
                                                                         only_show_in_rows,
                                                                         only_show_in_columns)

            if (not identity_matches) | (not grid_position_correct):
                continue

            image_dim = self._get_img_from_axis(ax).shape
            image_width = image_dim[-2]
            image_height = image_dim[-3]

            # actually the correction for cropping is not needed here!
            # but positions are already optimized for cropping correction
            if correct_for_cropping:
                (x_corrected,
                 y_corrected) = self._correct_xy_for_cropping_and_zoom(x, y,
                                                                      position[0],
                                                                      position[1])
            else:
                x_corrected = x
                y_corrected = y

            x_rel = x_corrected/image_width
            y_rel = y_corrected/image_height

            if orientation.lower() == "vert":
                rotation = 90
            elif orientation.lower() == "hor":
                rotation = 0
            else:
                rotation = orientation

            self._add_text_within_image_at_coords(ax, text, x_rel, 1 - y_rel,
                                                  0, font_size, color,
                                                  rotation = rotation,
                                                  ha=hor_align,
                                                  va=vert_align,
                                                  line_spacing=line_spacing)


    def draw_on_image(self, targets, direction, images = None,
                      style="arrow",color="white", size = 40,
                      direction_from_head_to_tail=True,
                      arrow_width_factor=0.125,
                      arrow_head_width_factor=0.625,
                      arrow_head_length_factor=0.625, **kwargs):
        """
        Draw on each of the images specified.

        :param targets: target position in form [x,y] or list of positions,
                        will determine where the shape ends
        :param direction: direction of object from the target,
                            can be supplied in three different forms:
                            position in form [x,y], will determine direction,
                            starting from target
                            degrees as int, while 12o'clock is 0 degree
                            string like "top" or "top-left" or "bottom-right"
                            by default direction starts at head and goes
                            towards tail (see param direction_from_head_to_tail)
        :param images: dict that specifies on which images should be drawn
                       the key is the category and the value
                       is the allowed value
        :param style: can be "arrow" or "*"
        :param color: color of drawn shape
        :param size: size of marker in pt, also scaled for current figure size
                    to have a good standard value
        :param direction_from_head_to_tail: Bool; Whether direction supplied as
                                            string should be considered
                                            starting from the head going
                                            towards the tail (True) or the
                                            other way around (False)
        :param arrow_width_factor: width of arrow_tail in axes coords
                                    if style == arrow
        :param arrow_head_width_factor: width of arrow head in axes coords
                                        if style == arrow
        :param arrow_head_length_factor: length of arrow head in axes coords
                                        if style == arrow
        """
        size *= self.size_factor

        if images == None:
            images = {}

        # if direction was supplied as string, convert to degree first
        if type(direction) == str:
            direction = self._direction_string_to_degree(direction,
                                                        direction_from_head_to_tail)

        # if only one target was provided, convert to array
        if type(targets[0]) == int:
            targets = [targets]
        for target in targets:
            # if direction was supplied as degrees, convert to position,
            #  starting at target
            # 0 degrees is the 12 o'clock direction
            if (type(direction) == int) | (type(direction) == float):
                direction_pos = self._direction_degree_to_position(direction, 
                                                                  target)
            else:
                direction_pos = direction

            fig = plt.gcf()
            allowed_styles = ["arrow","*"]
            if style not in allowed_styles:
                raise ValueError("Style of drawn shape has to be one of "
                                 "the following for now: {}. More shapes will "
                                 "be implemented in the "
                                 "future.".format(", ".join(allowed_styles)))

            size_inch = size / 72

            for position, ax in self.all_axs.items():
                pre_identity = self.pos_to_pre_identity_map[position]
                identity_matches = self._check_if_identity_matches_dict_criteria(pre_identity,
                                                                                images)
                if not identity_matches:
                    continue

                image = self._get_img_from_axis(ax)

                # correct direction and target position for cropping of this image
                new_direction = self._correct_xy_for_cropping_and_zoom(direction_pos[0],
                                                                      direction_pos[1],
                                                                      position[0],
                                                                      position[1])
                new_target = self._correct_xy_for_cropping_and_zoom(target[0],
                                                                   target[1],
                                                                   position[0],
                                                                   position[1])

                # check that target is within the image, otherwise, dont draw this
                if not ((new_target[0] > 0) & (new_target[0] < image.shape[-2]) &
                        (new_target[1] > 0) & (new_target[1] < image.shape[-3])):
                    continue

                dX_inch, dY_inch = self._get_dX_dY_inch(new_target,
                                                       new_direction, size_inch)

                ax_coords = ax.get_position()
                width = image.shape[-2]
                height = image.shape[-3]
                ax_width_inch = ax_coords.width * fig.get_size_inches()[0]
                ax_height_inch = ax_coords.height * fig.get_size_inches()[1]
                new_target_inch = [new_target[0] / width * ax_width_inch,
                                   new_target[1] / height * ax_height_inch]

                if style == "arrow":
                    x0_inch = new_target_inch[0] + dX_inch
                    y0_inch = new_target_inch[1] + dY_inch
                    dX_data = dX_inch / ax_width_inch * width
                    x0_data = x0_inch / ax_width_inch * width
                    dY_data = dY_inch / ax_height_inch * height
                    y0_data = y0_inch / ax_height_inch * height
                    data_size = sqrt(dY_data**2 + dX_data**2)

                    width = data_size * arrow_width_factor
                    head_width = data_size * arrow_head_width_factor
                    head_length = data_size * arrow_head_length_factor

                    for key, value in kwargs:
                        arrow_props[key] = value

                    label = "___"
                    label += str(arrow_width_factor) + "_"
                    label += str(arrow_head_width_factor)+ "_"
                    label += str(arrow_head_length_factor)

                    # x0_ax, y0_ax = self._transform_coords_from_data_to_axes(x0_data,
                    #                                                        y0_data,
                    #                                                        ax)
                    #
                    # dx_ax, dy_ax = self._transform_coords_from_data_to_axes(dX_data,
                    #                                                        dY_data,
                    #                                                        ax)
                    
                    # transform coords subtracts transformed y value from 1
                    # since orientation of axes and data coords are opposite
                    # since dy is not based on orientation (its a relative diff)
                    # reverse this step
                    # dy_ax -= 1

                    # width,_ =self._transform_coords_from_data_to_axes(width,0,ax)
                    #
                    # head_width,_ =self._transform_coords_from_data_to_axes(head_width,
                    #                                                       0,ax)
                    #
                    # head_length,_ =self._transform_coords_from_data_to_axes(head_length,
                    #                                                        0,ax)

                    ax.arrow(x0_data, y0_data, - dX_data, - dY_data,
                             width=width, head_width=head_width,
                             head_length=head_length,
                            transform=ax.transData, color=color,
                             length_includes_head=True,lw=0,
                             label = label
                             )
                    # arrow automatically calls the
                    #  self._request_autoscale_view() function
                    # this function sets the following two values as True
                    # however, when this happens, the plots
                    #  are automatically rescaled
                    # this messes up the padding that figureflow defined
                    ax._stale_viewlim_x = False
                    ax._stale_viewlim_y = False

                elif style == "*":
                    # use half dX since the size of the marker is the radius
                    # therefore position should be ad half than what it should be
                    # if the marker size would be the diameter
                    dX_inch /= 2
                    dY_inch /= 2
                    x_inch = new_target_inch[0] + dX_inch
                    y_inch = new_target_inch[1] + dY_inch

                    x_img_px = x_inch / ax_width_inch * width
                    y_img_px = y_inch / ax_height_inch * height
                    ax.plot(x_img_px, y_img_px, marker="*",
                            markersize=size, mew=size/100, c=color)


    def _get_possible_direction_strings(self, direction_from_head_to_tail):
        possible_direction_strings = {}
        if direction_from_head_to_tail:
            possible_direction_strings["top"] = 180
            possible_direction_strings["top-right"] = 45
            possible_direction_strings["right"] = 90
            possible_direction_strings["bottom-right"] = 135
            possible_direction_strings["bottom"] = 0
            possible_direction_strings["bottom-left"] = 225
            possible_direction_strings["left"] = 270
            possible_direction_strings["top-left"] = 315
        else:
            possible_direction_strings["bottom"] = 180
            possible_direction_strings["bottom-left"] = 45
            possible_direction_strings["left"] = 90
            possible_direction_strings["top-left"] = 135
            possible_direction_strings["top"] = 0
            possible_direction_strings["top-right"] = 225
            possible_direction_strings["right"] = 270
            possible_direction_strings["bottom-right"] = 315
        return possible_direction_strings


    def _direction_string_to_degree(self, direction, direction_from_head_to_tail):
        """
        # if direction was supplied as string, convert to degree first
        """
        possible_direction_strings = self._get_possible_direction_strings(direction_from_head_to_tail)
        if direction not in possible_direction_strings:
            raise ValueError("The supplied string for the label direction '{}' "
                             "is not valid. Only the following strings "
                             "are valid: {}"
                             ".".format(direction,
                                        ", ".join(possible_direction_strings)))
        direction = possible_direction_strings[direction]
        return direction


    @staticmethod
    def _direction_degree_to_position(direction, target):
        """
        # if direction was supplied as degrees, convert to position,
        starting at target
        # 0 degrees is the 12 o'clock direction
        """
        dX = sin( np.deg2rad(direction) ) * 20
        dY = - cos( np.deg2rad(direction) ) * 20
        direction = [target[0] + dX, target[1] + dY]
        return direction


    def _get_dX_dY_inch(self, new_target, new_direction, size_inch):
        # define cases for no x and no y movement
        if (new_direction[0] - new_target[0]) == 0:
            dX_inch = 0
            if new_direction[1] > new_target[1]:
                dY_inch = - size_inch
            else:
                dY_inch = size_inch
        elif (new_direction[1] - new_target[1]) == 0:
            dX_inch = size_inch
            dY_inch = 0
        else:
            xy_ratio = ((new_direction[1] - new_target[1]) /
                        (new_direction[0] - new_target[0]))
            dX_inch = size_inch / sqrt(1 + xy_ratio * xy_ratio)
            dY_inch = dX_inch * xy_ratio
        # since dX_inch formula will always result in positive value
        # evaluate whether dX_inch value actually should have been negative
        # then adjust dY_inch accordingly
        if new_direction[0] < new_target[0]:
            dX_inch = - dX_inch
            dY_inch = - dY_inch
        return dX_inch, dY_inch


    def add_scale_bar(self, um_per_px, position=None,
                      only_in_first_image_of_each=None,
                      row=None, column=None,
                    lengths_um=10, color="white", padding=0.015,
                      line_width=3, always_draw_scale_bar = False):
        """
        Add scale bar to image/s.

        :param um_per_px: how large is one px in um
        :param position: define where the scale bar should be added
                            set as "first_dimension-second dimension"
                            - e.g. "bottom-left" or "top-right"
        :param only_in_first_image_of_each: Defines in which dimension
                                            only the first image should
                                            show scale bar,
                                            if None, all images will show
                                            scale bar
        :param row: row position that the image needs to be in grid
                            to draw scale bar
                            if None, any position in that dimension is allowed
                            can be used to apply different um_per_px settings
                            to different images
        :param column: column position that the image needs to be in grid
                            to draw scale bar
                            if None, any position in that dimension is allowed
                            can be used to apply different um_per_px settings
                            to different images
        :param lengths_um: list of lengths of scale bar in um, if more than one
                        and more than one scales of images
                        (e.g. with zoom) are there
                        smaller scale bars will be mapped on zooms
                        and larger on non-zooms
                        ideally provide as many
        :param color: color of scale bar
        :param padding: distance of scale bar from border of image in inches
                        can be single value (then used for both dimension)
                        or can be list of two values,
                        then the first will be for the x
                        and the second for the y axis
        :param line_width: line thickness in points
        :param always_draw_scale_bar: Whether to draw scale bars in every image
                                        even though they are the same scale.
                                        Only recommended in very special cases.
                                        Normally several scale bars for images
                                        with the same scale look like the scales
                                        are slightly different.
        """
        scale_bar_widths = np.zeros((self.max_row + 1, self.max_col +1))

        if type(lengths_um) not in self.itertypes:
            lengths_um = [lengths_um]

        # sort lengths descending
        lengths_um.sort(reverse=True)

        # get length of line in image px
        length = (lengths_um[0] / um_per_px)

        # create array of um per inch for each image
        for ax_position, ax in self.all_axs.items():
            image = self._get_img_from_axis(ax)
            width = image.shape[-2]
            height = image.shape[-3]

            fig = plt.gcf()
            fig_size = fig.get_size_inches()
            ax_coords = ax.get_position()

            length_fig_px = ((length / width) * ax_coords.width *
                             fig_size[0] * fig.dpi)

            scale_bar_widths[ax_position] = np.round(length_fig_px,3)

        # get unique values of scale bar widths
        positions_to_draw_scale_bar = []
        if always_draw_scale_bar:
            unique_scale_bar_widths = scale_bar_widths
        else:
            unique_scale_bar_widths = np.unique(scale_bar_widths)
        for unique_scale_bar_width in unique_scale_bar_widths:

            if unique_scale_bar_width == 0:
                continue

            pos_of_scale_bar = np.where(scale_bar_widths ==
                                        unique_scale_bar_width)
            # only if row and column are none
            #  have a single position to draw scale bar in
            if (type(row) == type(None)) & (type(column) == type(None)):
                left_most_col = min(pos_of_scale_bar[1])
                row_pos_of_scale_bar = np.where(scale_bar_widths[:,left_most_col]
                                                == unique_scale_bar_width)[0]
                top_most_row = min(row_pos_of_scale_bar)
                positions_to_draw_scale_bar.append((top_most_row, left_most_col))
            else:
                for pos_id in range(len(pos_of_scale_bar[0])):
                    row_position = pos_of_scale_bar[0][pos_id]
                    column_position = pos_of_scale_bar[1][pos_id]
                    positions_to_draw_scale_bar.append((row_position,
                                                        column_position))


        line_width *= self.size_factor

        standard_x_position = "left"
        standard_y_position = "bottom"
        # if nb of unique scale bar lengths is not the same
        # as number of lengths_um
        map_with_zoom = False
        if ((len(lengths_um) > 1) &
                (len(positions_to_draw_scale_bar) != len(lengths_um))):
            # check if there are two unique scale bar lengths and if zoom is defined
            if (len(lengths_um) == 2) & ("zooms" in self.map):
                # if so, map smaller length_um to zoom
                map_with_zoom = True
            else:
                # if not return ValueError for not being able to map
                lengths_um_msg = [str(length) for length in lengths_um]
                raise ValueError("Lengths for scale bar {} could not be mapped "
                                 "to {} different scales of images. If more "
                                 "scale bar lengths are defined, zooms and "
                                 "exactly two scale bar lengths need to be "
                                 "defined for mapping"
                                 ".".format(", ".join(lengths_um_msg),
                                            len(positions_to_draw_scale_bar)))

        for scale_bar_nb, ax_position in enumerate(positions_to_draw_scale_bar):
            if map_with_zoom:
                pre_identity = self.pos_to_pre_identity_map[ax_position]
                zoom_nb = pre_identity[self.map["zooms"]]
                # scale bar lengths_um are sorted descending,
                #  which means that smaller
                # lenghts are last and can therefore be mapped to zooms
                if zoom_nb == 0:
                    length = (lengths_um[0] / um_per_px)
                else:
                    length = (lengths_um[1] / um_per_px)
            elif len(lengths_um) > 1:
                # positions to draw scale bar are sorted with smaller scale bars
                # being first, followed by smaller scale bars
                # scale bar lengths_um are sorted descending,
                #  which means that smaller
                # therefore lengths_um can directly be mapped
                #  to positions_to_draw_scale_bar
                # since smaller scale bars should go on images with larger scales
                length = (lengths_um[scale_bar_nb] / um_per_px)
            else:
                # if there is just one lengths_um
                length = (lengths_um[0] / um_per_px)

            ax = self.all_axs[ax_position]
            row_pos = ax_position[0]
            column_pos = ax_position[1]

            position_correct = self._check_if_positions_match(row_pos,
                                                             column_pos,
                                                             row, column)
            if not position_correct:
                continue

            draw_scale_bar = True
            if only_in_first_image_of_each != None:
                if (only_in_first_image_of_each == "row") & (column_pos != 0):
                    draw_scale_bar = False
                elif (only_in_first_image_of_each == "column") & (row_pos != 0):
                    draw_scale_bar = False

            if not draw_scale_bar:
                continue

            image = self._get_img_from_axis(ax)
            width = image.shape[-2]
            height = image.shape[-3]

            fig = plt.gcf()
            fig_size = fig.get_size_inches()
            ax_coords = ax.get_position()
            ax_height_px = ax_coords.height * fig_size[1] * fig.dpi

            line_width_px = ( (line_width * fig.dpi / 72) /
                             ax_height_px * height / 2 )

            # padding is calculated in image dimensions

            if (type(padding) in self.itertypes):
                padding_x = padding[0] / (ax_coords.width * fig_size[0]) * width
                padding_y = padding[1] / (ax_coords.width * fig_size[1]) * width
            else:
                # padding in px should be the same in both dimensions,
                # therefore only calculate padding in one dimension
                padding_x = padding / (ax_coords.width * fig_size[0]) * width
                padding_y = padding_x


            bottom = False
            if position != None:
                if position.find("bottom") != -1:
                    bottom = True
            elif standard_y_position == "bottom":
                bottom = True

            if bottom:
                padding_y += line_width_px

            x0, x1, y0, y1 = FigurePanel._get_xy_from_position(position, length,
                                                              standard_x_position,
                                                              standard_y_position,
                                                              width, height,
                                                              padding_x,
                                                              padding_y ,
                                                              line_width_px)

            line_x, line_y = [x0/width, x1/width], [y0/height, y1/height]
            line = lines.Line2D(line_x, line_y, lw=line_width,
                                transform=ax.transAxes, c=color,
                                solid_capstyle="butt")
            ax.add_line(line)

    @staticmethod
    def _get_xy_from_position(position, length, standard_x_position,
                             standard_y_position, width, height,
                             padding_x, padding_y, obj_height):
        """
        :param length: width of object to add
        :param width: width of ax
        :param height: height of ax
        """
        (x_position,
         y_position) = FigurePanel._get_annotation_position_string(position,
                                                                   standard_x_position,
                                                                   standard_y_position)


        if x_position == "left":
            x0 = padding_x
            x1 = padding_x + length
        elif x_position == "right":
            x0 = width - (length + padding_x)
            x1 = width - padding_x
        if y_position == "bottom":
            y0 = padding_y
        elif y_position == "top":
            y0 = height - padding_y - obj_height
        y1 = y0
        return x0, x1, y0, y1


    def _get_maximum_font_size(self, extract_text_from_identity,
                              starting_font_size, padding,
                              only_show_in_rows = None,
                              only_show_in_columns = None):
        """
        :param only_show_in_rows: List of rows in which the label should be shown
                                    for which the font size should be determined
        """
        all_texts = []
        axs_to_plot = []
        for ax_position, ax in self.all_axs.items():
            position_correct = self._check_if_pos_is_in_row_col_list(ax_position[0],
                                                                    ax_position[1],
                                                                    only_show_in_rows,
                                                                    only_show_in_columns)
            if not position_correct:
                continue

            identity = self.pos_to_pre_identity_map[ax_position]
            text = extract_text_from_identity(identity)
            all_texts.append(text)
            axs_to_plot.append(ax)

        smallest_width = None
        for ax_to_plot in axs_to_plot:
            if smallest_width == None:
                smallest_width = ax_to_plot.get_position().width
            else:
                smallest_width = min(smallest_width,
                                     ax_to_plot.get_position().width)

        fig = plt.gcf()
        ax_width = smallest_width * fig.get_size_inches()[0] * fig.dpi
        # get padding on both sides of ax for text
        if (type(padding) in self.itertypes):
            ax_padding = ax_width * padding[0] * 2
        else:
            ax_padding = ax_width * padding * 2
        font_size = starting_font_size
        while True:
            root = tk.Tk()
            font_size_px = int (font_size * fig.dpi/72)
            font_to_measure_width = font.Font(family="DejaVu Sans",
                                              size= -font_size_px)
            max_text_width = 0
            for text in all_texts:
                text_width,_ = FigurePanel._get_dimension_of_text(text,
                                                                 font_size, ax)
                max_text_width = max(max_text_width, text_width)

            # Quick fix: include additional padding to prevent text
            # being to close to right border of image
            if max_text_width > (ax_width - ax_padding) * 0.95:
                font_size -= 0.2
            else:
                break
        return font_size

    def _get_width_of_space(self, font_size_pt, ax):
        # space by itself is not measured for length when at end of string
        # therefore get length of space by change of string with and without
        # space at the start
        width_with_space_px = FigurePanel._get_dimension_of_text(" a",
                                                                font_size_pt,
                                                                ax)[0]
        width_no_space_px = FigurePanel._get_dimension_of_text("a",
                                                              font_size_pt,
                                                              ax)[0]
        width_space_px = width_with_space_px - width_no_space_px
        return width_space_px


    def annotate_channel_within_image(self, channel_names, channel_colors = None,
                                      position=None, color="white",
                                      images=None, only_show_in_rows=None,
                                      only_show_in_columns=None, font_size=None,
                                      string_separating_channels=" / ",
                                      padding=0.015):
        """
        Extract channel number from file name (__cx..x-x...x-x...x).
        Annotate corresponding channel_names with corresponding color in image.
        Each file cannhave multiple channels specified (for overlap images
        with more than one channel in different colors).

        :param channel_names: Names of channels that will be annotated in image.
                             The index in the list corresponds
                             to the channel number in the image filename
        :param channel_colors: Colors in which names of channels
                                will be annotated in image.
                                The index in the list corresponds
                                to the channel number in the image filename
                                if None, defaults for colors to
                                cmaps used to display channel/s
        :param position: define where the timestamp should be added
                            set as "first_dimension-second dimension"
                            - e.g. "bottom-left" or "top-right"
        :param color: Color of label
        :param images: list of dict or dict
                        dict  specifies on which images should be drawn
                       the key is the category and the value
                       is a list of allowed values
        :param only_show_in_rows: list of rows in which the labels
                                should be displayed, if None display in all rows
        :param only_show_in_columns: list of columns in which the labels
                                    should be displayed,
                                    if None display in all columns
        :param string_separating_channels: For composites with multiple channels
                                            add this string between channels
                                            maximum one space in a row is allowed
        :param padding: Padding in inches of label from image edges
        """
        # potential feature to add:
        # allow supply of single channel images and plot them as composite
        #  if same positions, then get correct color from each single image
        if font_size == None:
            font_size = self.font_size

        standard_x_position = "right"
        standard_y_position = "bottom"
        fig = plt.gcf()
        fig_width_px = fig.get_size_inches()[0] * fig.dpi
        if not self._is_none(channel_colors):
            if len(channel_names) != len(channel_colors):
                raise ValueError("The lists for channel_names and "
                                 "channel_colors "
                                 "need to have the same length. Channel_names "
                                 "is {} long and channel_colors is "
                                 "{} long.".format(len(channel_names),
                                                   len(channel_colors)))

        func_get_channel_name = functools.partial(self._get_channelname_from_identity,
                                                  channel_names=channel_names,
                                                  string_separating_channels=
                                                  string_separating_channels)

        font_size = self._get_maximum_font_size(extract_text_from_identity=
                                               func_get_channel_name,
                                               starting_font_size=font_size,
                                               padding=padding,
                                               only_show_in_rows =
                                               only_show_in_rows,
                                               only_show_in_columns =
                                               only_show_in_columns)

        font_size_pt = FontProperties(size=font_size).get_size_in_points()

        if string_separating_channels.find(" ") != -1:
            string_between_with_space = True
        else:
            string_between_with_space = False
            width_space_px = 0

        if string_between_with_space:
            ax = list(self.all_axs.values())[0]
            width_space_px =  self._get_width_of_space(font_size_pt, ax)

        # keep track of all channels
        all_channels = []
        for ax_position, ax in self.all_axs.items():
            # check if current row and column should contain the label
            row = ax_position[0]
            column = ax_position[1]
            position_allowed = self._check_if_pos_is_in_row_col_list(row,
                                                                    column,
                                                                    only_show_in_rows,
                                                                    only_show_in_columns)

            identity = self.pos_to_pre_identity_map[ax_position]
            #  check if identity is from correct image
            if type(images) != type(None):
                image_idx = identity[self.map["images"]]
                if image_idx not in images:
                    position_allowed = False

            if not position_allowed:
                continue

            all_channels.append(1)

            if not self._is_none(channel_colors):
                channel_colors_one_file = self._get_info_for_channel_from_identity(identity,
                                                                                  channel_colors,
                                                                                  color)
            else:
                cmaps_for_img = self.cmaps_for_position[ax_position]
                channel_colors_one_file = [cmap(1.0) for cmap in cmaps_for_img]

            channel_names_one_file = self._get_info_for_channel_from_identity(identity,
                                                                             channel_names)
            channel_name  = self._get_channelname_from_identity(identity,
                                                               channel_names)

            total_txt_width_px,_ = FigurePanel._get_dimension_of_text(channel_name,
                                                                     font_size_pt,
                                                                     ax)

            x0, y0 = FigurePanel._get_xy_of_text_from_position(channel_name, ax,
                                                              position,
                                                              total_txt_width_px,
                                                              font_size_pt,
                                                              standard_x_position,
                                                              standard_y_position,
                                                              padding)

            # add channels one after another, in between add string
            # move x position for string continuously forward (by length of string)
            # in order to put the strings directly adjacent to each other
            ax_width_px = ax.get_position().width * fig_width_px
            x = x0
            string_between = string_separating_channels

            string_between_lengt_rel = (FigurePanel._get_dimension_of_text(string_between,
                                                                         font_size_pt,
                                                                         ax)[0]
                                         / ax_width_px)

            width_space_rel = width_space_px / ax_width_px

            for nb, channel_name in enumerate(channel_names_one_file):
                channel_color = channel_colors_one_file[nb]

                # plot " / " in between channels in color,
                # once x was moved the first frame (first channel was added)
                if x > x0:
                    ax.annotate(xy=(x,y0),text=string_between,
                                fontsize=font_size_pt, color=color,
                                label="label_channel",
                                xycoords="axes fraction", va="bottom")
                    x += string_between_lengt_rel

                self._add_text_within_image_at_coords(ax, channel_name, x,
                                                      y0, total_txt_width_px,
                                                      font_size_pt, channel_color,
                                                      label="label_channel"
                                                      )
                channel_name_length_rel = FigurePanel._get_dimension_of_text(channel_name,
                                                                            font_size_pt,
                                                                            ax)[0] / (ax_width_px)
                x += channel_name_length_rel

                if string_between_with_space:
                    x += width_space_rel

        if len(all_channels) == 1:
            print("WARNING: Only one channel was found and annotated.")


    def _add_text_within_image(self, ax, text, position, font_size_pt,
                               color, standard_x_position,
                               standard_y_position, padding,
                               ax_position, label=""):
        txt_width_px, _ = FigurePanel._get_dimension_of_text(text, font_size_pt,
                                                            ax)

        x0, y0 = FigurePanel._get_xy_of_text_from_position(text, ax, position,
                                                          txt_width_px,
                                                          font_size_pt,
                                                          standard_x_position,
                                                          standard_y_position,
                                                          padding)


        self._add_text_within_image_at_coords(ax, text, x0, y0,
                                              txt_width_px, font_size_pt, color,
                                              label=label)

    def _rel_ax_coords_to_px_coords(self, xy, ax):
        xy = list(xy)
        fig = plt.gcf()
        fig_size_inches = fig.get_size_inches()
        ax_size = ax.get_position()
        xy[0] *= ax_size.width * fig_size_inches[0] * fig.dpi
        xy[1] *= ax_size.height * fig_size_inches[1] * fig.dpi
        return xy

    def _px_coords_to_rel_ax_coords(self, xy, ax):
        xy = list(xy)
        fig = plt.gcf()
        fig_size_inches = fig.get_size_inches()
        ax_size = ax.get_position()
        xy[0] /= ax_size.width * fig_size_inches[0] * fig.dpi
        xy[1] *= ax_size.height * fig_size_inches[1] * fig.dpi
        return xy


    def _add_text_within_image_at_coords(self, ax, text, x, y,
                                         total_txt_width_px, font_size_pt, color,
                                         rotation = 0, ha="left", va="bottom",
                                         line_spacing=1, label=""):

        ax.annotate(xy=(x,y),text=text,fontsize=font_size_pt, color=color,
                    xycoords="axes fraction", va=va, ha=ha,
                    rotation = rotation, label=label+"_inside_image",
                    linespacing=line_spacing)

    @staticmethod
    def _get_dimension_of_text(text, font_size_pt, ax, rotation_degrees = 0):
        fig = plt.gcf()
        # get size of text by drawing it and then removing it again
        txt_width_measure = ax.annotate(xy=(0,0),text=text,
                                        fontsize=font_size_pt,
                                        rotation=rotation_degrees,
                                        xycoords="axes fraction", va="bottom",
                                        ha="left")
        # subtract one pixel since it is added as padding to bbox
        txt_width_px = txt_width_measure.get_window_extent(renderer = fig.canvas.renderer).width - 1
        txt_height_px = txt_width_measure.get_window_extent(renderer = fig.canvas.renderer).height - 1

        txt_width_measure.remove()
        return txt_width_px, txt_height_px

    def _get_info_for_channel_from_identity(self, identity,
                                           info_array, standard_value = None):
        """
        Extract info of one identity from info_array for all channels.
        If the array is None, all entries are filled with standard_value.
        """
        channels = identity[self.map["channels"]]
        if (type(channels) not in self.itertypes):
            channels = [channels]
        # get all channel_names and channel_colors for each channel in the image
        info_one_image = []
        for channel in channels:
            if channel == "":
                continue

            channel = int(channel)
            if info_array != None:
                if len(info_array) < (channel + 1):
                    error_msg = ("The specified channel {} from the "
                                 "channel-string {} is not specified in the "
                                 "channel_names list. The channel_names list "
                                 "is too short.".format(channel,channels[0]))
                    raise ValueError(error_msg)
                info_one_image.append( info_array[channel] )
            else:
                info_one_image.append( standard_value )

        return info_one_image


    def _get_channelname_from_identity(self, identity, channel_names,
                                      string_separating_channels = " / "):
        """
        Get full name of the channel from the identity.
        """
        channel_names_one_file = self._get_info_for_channel_from_identity(identity,
                                                                         channel_names)
        for channel_nb, one_channel_name in enumerate(channel_names_one_file):
            # add string that will be added in between channel names,
            #  except for the first channel
            if channel_nb > 0:
                channel_name += (string_separating_channels
                                + one_channel_name)
            else:
                channel_name = one_channel_name

        return channel_name


    def _find_and_validate_unit_of_timestamp_freq(self, time_per_frame, allowed_units):
        unit_finder = re.compile("[a-zA-Z]+")
        number_finder = re.compile("[\d]+")
        # extract unit of frame and number of units
        unit = unit_finder.search(time_per_frame)
        number_units = number_finder.search(time_per_frame)
        if not (unit and number_units):
            raise ValueError("time_per_frame string did not follow syntax "
                             "of a whole number for the value and "
                             "a letter/letters for the unit of the value.")
        unit = unit[0].lower()
        number_units = int(number_units[0])
        if unit not in allowed_units:
            raise ValueError("The unit {} supplied to time_per_frame "
                             "is not allowed. Only the following are allowed: "
                             "{}".format(unit,
                                         ", ".join(allowed_units)))
        return unit, number_units


    def _validate_timestamp_format(self, format, format_units_allowed):
        format_units_allowed = ["s","m","h"]
        format_units_not_used = copy.copy(format_units_allowed)
        format_steps = format.split(":")
        for format_step in format_steps:
            first_letter = format_step[0]
            if first_letter not in format_units_allowed:
                raise ValueError("The letter {} in the supplied format is "
                                 "not allowed. Only the following letters are "
                                 "allowed in the format: "
                                 "{}".format(first_letter,
                                             ", ".join(format_units_allowed)))
            # check whether the current unit is higher sized than a unit size_before_plot
            if first_letter not in format_units_not_used:
                raise ValueError("In the format different frame units "
                                 "separated by ':' need to increase in size "
                                 "from left to right. The supplied {} was "
                                 "a larger unit than a more left "
                                 "unit.".format(first_letter))
            index = format_units_not_used.index(first_letter)
            # delete all units bigger or equal sized as the current one, so that no higher sized unit can come after a lower sized unit (e.g. h after min)
            del format_units_not_used[index:]
            last_letter = first_letter
            for letter in format_step:
                if letter == last_letter:
                    continue

                raise ValueError("The supplied format step {} is not valid. "
                                 "Each step in the format needs to be "
                                 "separated by ':' and only contain the same "
                                 "letter.".format(format_step))


    def _get_number_of_units_from_seconds(self, frame_sec, unit):
        if unit == "s":
            unit_number = frame_sec
            frame_sec -= unit_number
        elif unit == "m":
            unit_number = (frame_sec - frame_sec % 60) / 60
            frame_sec = frame_sec % 60
        elif unit == "h":
            unit_number = (frame_sec - frame_sec % 3600) / 3600
            frame_sec = frame_sec % 3600

        return unit_number, frame_sec


    def _get_frame_string(self, frame, start_time,
                         time_per_frame, format, show_unit,
                        first_time_difference, frame_jumps,
                         long_unit_names, all_units_shown):

        if frame_jumps == None:
            frame_jumps = {}

        sec_units = ["s","sec"]
        min_units = ["m","min"]
        h_units = ["h"]
        allowed_units = [*sec_units,*min_units,*h_units]

        (unit,
         number_units) = self._find_and_validate_unit_of_timestamp_freq(time_per_frame,
                                                                        allowed_units)

        self._validate_timestamp_format(format,allowed_units)

        add_frame_diff = 0
        #  adjust actual frame by framejumps
        for framejump_frame, framejump_length in frame_jumps.items():
            if frame >= framejump_frame:
                add_frame_diff += framejump_length

        if frame > 0:
            add_frame_diff += first_time_difference - 1

        #  calculate frame of frame in units
        start_units = start_time * number_units
        frame_units = (start_units +
                       number_units * frame +
                       number_units * add_frame_diff)
        #  calculate frame of frame in seconds
        if unit in sec_units:
            frame_sec = frame_units
        elif unit in min_units:
            frame_sec = frame_units * 60
        elif unit in h_units:
            frame_sec = frame_units * 60 * 60
        format_steps = format.split(":")
        final_format_strings = []
        #  for each format step calculate how many full units are there
        #  then reduce frame_sec to the remainder of the full units division
        if frame_sec < 0:
            neg_frame = True
        else:
            neg_frame = False
        #  always use absolute nb of seconds for calculations
        #  but add negative sign to first calculated value then
        frame_sec = abs(frame_sec)
        for step, format_step in enumerate(format_steps):
            number_len = len(format_step)
            unit_step = format_step[0]

            (unit_number,
             frame_sec) = self._get_number_of_units_from_seconds(frame_sec,
                                                                unit_step)

            format_step_string = str(int(unit_number)).zfill(number_len)
            #  add negative sign if the frame should be negative
            if (step == 0) & neg_frame:
                format_step_string = "-" + format_step_string
            final_format_strings.append(format_step_string)

        #  string to be printed should again be separated by ":"
        final_format_string = ":".join(final_format_strings)

        if show_unit:
            unit_name_map = {}
            unit_name_map["s"] = "sec"
            unit_name_map["m"] = "min"
            unit_name_map["h"] = "hour"
            unit_strings = format_steps[0]
            for unit_nb, unit_string in enumerate(unit_strings):
                # take first letter in unit string
                unit_string = unit_string[0]
                if long_unit_names:
                    unit_string = unit_name_map[unit_string]
                if unit_nb > 0:
                    final_format_string += ":"
                else:
                    final_format_string += " "
                final_format_string += unit_string
                if not all_units_shown:
                    break

        return final_format_string


    def add_timestamp(self, time_per_frame, start_time=0,
                      format="mm:ss", color="white", show_only_in_zoom=False,
                      show_unit=False, first_time_difference = 1,
                       frame_jumps = None,
                      only_show_in_rows=None, only_show_in_columns=None,
                      show_unit_only_once=True, long_unit_names=False,
                      all_units_shown = False, position=None, font_size=None,
                    padding= 0.015, ):
        """
        Add timestamp text to each image in panel. 
        timestamps MUST be added after other annotations were added
        to the figure. Otherwise the timestamp might be cut off.

        :param time_per_frame: how much frame is between frames,
                                add as string with unit (s, sec, m, min or h)
                                after number
        :param start_time: what frame-frame does number 1 equal
                            (start at negative value positive to indicate it
                            was before e.g. a treatment)
        :param time_per_frame: string of number and unit ("m" for min,
                                "h" for hour, or "s" for second) for
                                time difference between frames
        :param format: format of how time should be displayed.
                        The number of letter indicates the number of digits
                        in that category. Possible categories are "s" for
                        seconds, "m" for minutes or "h" for hours.
        :param show_unit: Whether to show unit name in the label of the time
        :param first_time_difference: Difference of timesteps
                                        from first to second frame
                                        (helpful if after a first frame there
                                        was an imaging break, longer than the
                                        normal time between frames)
        :param frame_jumps: Dictionary with keys being timepoint before which
                            timejumps happened and values being number of frames
                            that the jump was long (e.g. {4: 2, 10:20} for a
                            timejump of 2 timeframes before timeframe 5 and a
                            timejump of 20 timeframes before timeframe 11)
        :param long_unit_names: Whether to use long unit names ("min" instead of
                                "m", "hour" instead of "h" and "sec" instead of
                                "s").
        :param all_units_shown: Whether to show the unit name of the
                                first unit in the format (e.g. "h" for "hh:mm)
                                (if False) or both unit names separated by ":"
                                (if True)
        :param position: define where the timestamp should be added
                            set as "first_dimension-second dimension"
                            - e.g. "bottom-left" or "top-right"
        :param font_size: font size of timestamp label
        :param padding: padding of timestamp from edges of image in inches
        """

        if font_size == None:
            font_size = self.font_size


        standard_x_position = "right"
        standard_y_position = "top"


        fig = plt.gcf()
        font_size_pt = int(FontProperties(size=font_size).get_size_in_points())
        root = tk.Tk()
        # need to set font size in px since dpi in tkinter
        #  is different from dpi in figure
        font_size_px = int (font_size_pt * fig.dpi/72)
        font_to_measure_width = font.Font(family="DejaVu Sans",
                                          size= -font_size_px)

        # track all frames annotated
        all_frames = []
        for ax_position, ax in self.all_axs.items():

            position_allowed = self._check_if_pos_is_in_row_col_list(ax_position[0],
                                                                    ax_position[1],
                                                                    only_show_in_rows,
                                                                    only_show_in_columns)

            if not position_allowed:
                continue

            # extract frame from file name
            identity = self.pos_to_pre_identity_map[ax_position]
            identity_correct = True
            if "zooms" in self.map:
                if show_only_in_zoom & (identity[self.map["zooms"]] == 0):
                    identity_correct = False
            if not identity_correct:
                continue

            frame = identity[self.map["frames"]]
            all_frames.append(frame)

            final_format_string = self._get_frame_string(frame, start_time,
                                                        time_per_frame, format,
                                                        show_unit,
                                                        first_time_difference,
                                                        frame_jumps,
                                                        long_unit_names,
                                                        all_units_shown)

            txt_width_px,_ = FigurePanel._get_dimension_of_text(final_format_string,
                                                               font_size_pt, ax)

            x0, y0 = FigurePanel._get_xy_of_text_from_position(final_format_string,
                                                              ax, position,
                                                              txt_width_px,
                                                              font_size_pt,
                                                              standard_x_position,
                                                              standard_y_position,
                                                              padding)


            ax.annotate(xy=(x0,y0), text=final_format_string,
                        fontsize=font_size_pt, color=color,
                        label="label_timestamp",
                        xycoords="axes fraction", va="bottom", ha="left")

            if show_unit_only_once:
                show_unit=False

        if len(all_frames) == 1:
            print("WARNING: Only one timepoint was annotated.")

    @staticmethod
    def _get_xy_of_text_from_position(text, ax, position, txt_width_px,
                                     font_size_pt, standard_x_position,
                                     standard_y_position, padding,
                                     orientation="hor"):
        """
        :param padding: value or list, if value: padding on all sides in inches
                        if list: first value padding in x, second in y
        """
        fig = plt.gcf()
        ax_coords = ax.get_position()
        ax_width_inch = ax_coords.width * fig.get_size_inches()[0]
        ax_height_inch = ax_coords.height * fig.get_size_inches()[1]

        if orientation.lower() == "vert":
            rotation = 90
        else:
            rotation = 0

        _, font_size_px = FigurePanel._get_dimension_of_text(text,
                                                            font_size_pt,
                                                            ax, rotation)

        _, y_position = FigurePanel._get_annotation_position_string(position,
                                                                     standard_x_position,
                                                                     standard_y_position)

        less_y_padding_inch = 0
        if y_position == "bottom":
            # if y position is bottom
            # then adjust y alignment for text without descenders
            # this will however, lead to different alignments
            #  when text with and without descenders are added!

            font_size_one_line_px = font_size_pt * fig.dpi / 78

            #  check whether text contains descender letters
            descender_letters = ["g", "j", "p", "q", "y", ","]
            contains_descender = False
            for letter in descender_letters:
                if letter in text:
                    contains_descender = True
                    break

            #  if no descender in text, remove 22% of text height
            #  manualy measured value for Arial
            if not contains_descender:
                descender_height = 0.22 * font_size_one_line_px
                # reduce padding_y by descender height
                less_y_padding_inch = descender_height / fig.dpi


        txt_width_rel = txt_width_px / (ax_width_inch * fig.dpi)
        # factor of 78 found by trial and error of aligning top y position
        #  of different font sizes
        # should actually be 72
        font_size_rel =  font_size_px/ (ax_height_inch * fig.dpi)
        width = 1
        height = 1

        if (type(padding) in [list, tuple]):
            padding_x = padding[0] / ax_width_inch
            padding_y = (padding[1] - less_y_padding_inch)/ ax_height_inch
        else:
            padding_x = padding / ax_width_inch
            padding_y = (padding - less_y_padding_inch) / ax_height_inch


        x0, _, y0, _ = FigurePanel._get_xy_from_position(position, txt_width_rel,
                                                        standard_x_position,
                                                        standard_y_position,
                                                        width, height,
                                                        padding_x, padding_y,
                                                        font_size_rel)

        return x0, y0


    @staticmethod
    def _get_annotation_position_string(position,
                                        standard_x_position,
                                        standard_y_position):
        """
        extract position of an annotation, standard position as fallback
        in case the dimension is not set in "position"
        :param position: positon string with structure "bottom-left"
        """
        x_position = None
        y_position = None
        if position == None:
            return standard_x_position.lower(), standard_y_position.lower()

        # split x and y position from string of position input
        xy_positions = position.split("-")
        allowed_x_positions = ["left","right"]
        allowed_y_positions = ["bottom","top"]
        # check which position is x and which is y,
        #  check if each position is set max. once
        for xy_position in xy_positions:
            if (xy_position.lower() in allowed_x_positions):
                if x_position != None:
                    raise ValueError("Only set each dimension for position "
                                     "of scale bar once. {} and {} are both "
                                     "in the x-dimension"
                                     ".".format(x_position,xy_position))
                x_position = xy_position
            elif (xy_position.lower() in allowed_y_positions):
                if y_position != None:
                    raise ValueError("Only set each dimension for position "
                                     "of scale bar once. {} and {} are both "
                                     "in the "
                                     "y-dimension.".format(y_position,
                                                            xy_position))
                y_position = xy_position
            else:
                raise ValueError("Only the following values are allowed "
                                 "for the x-dimension: {} and the following "
                                 "for the y-dimension"
                                 ": {}.".format(", ".join(allowed_x_positions),
                                                ", ".join(allowed_y_positions)))
        # set positions that were not set to standard values
        if x_position == None:
            x_position = standard_x_position
        if y_position == None:
            y_position = standard_y_position

        return x_position.lower(), y_position.lower()


    def _remove_placeholder_images(self):
        for ax_position, ax in self.all_axs.items():
            # do not try to remove a panel that was already removed
            if ax.figure is None:
                continue
            identity = self.pos_to_pre_identity_map[ax_position]
            if self._identity_is_placeholder(identity):
                ax.remove()

    def _identity_is_placeholder(self, identity):
        for cat_val in identity:
            if type(cat_val) == int:
                if cat_val == -1:
                    return True
        return False

    def draw_line_on_plots(self, positions, axis,
                            line_width = 1, color = "white",
                            line_style="-",**kwargs):
        """
        Draw lines on data plots.
        This is not implemented for multiple rows of data plots yet.

        :param positions: list of positions (x or y) of adding line
        :param axis: axis of positions ("x" or "y")
        :param line_width: line width in pt
        :param color: color of line
        :param line_style: linestyle as typical matplotlib linestyle
                            (e.g. "-" or "--" or "-.-")
        """
        if type(positions) not in [tuple, list]:
            positions = [positions]
        if axis.lower() == "x":
            for position in positions:
                self.draw_line_on_images(position, orientation="vert",
                                    line_width=line_width, color=color,
                                    line_style=line_style,
                                    **kwargs)
        elif axis.lower() == "y":
            # first add lines between plots due to split by col values
            ax_first = None
            first_x = np.inf
            ax_last = None
            last_x = 0
            for ax in self.all_axs.values():
                ax_coords = ax.get_position()
                if ax_coords.x0 < first_x:
                    first_x = ax_coords.x0
                    ax_first = ax
                if ax_coords.x1 > last_x:
                    last_x = ax_coords.x1
                    ax_last = ax
            statannot.add_background_grid_lines(ax_first, ax_last,
                                                line_width, self.letter, color,
                                                y_positions=positions)
            # then plot lines for actual plots
            for position in positions:
                self.draw_line_on_images(position, orientation="hor",
                                    line_width=line_width, color=color,
                                    line_style=line_style,
                                    **kwargs)

    def draw_line_on_images(self, position, orientation = "hor",
                            line_width = 1, color = "white",
                            line_style="-",
                            only_show_in_rows = None,
                            only_show_in_columns = None,
                            **kwargs):
        """
        Draw a line on images.

        :param position: positions (x or y) of adding line
        :param orientation:  either "hor" / "horizontal" or "vert" / "vertical"
        :param line_width: line width in pt
        :param color: color of line
        :param line_style: linestyle as typical matplotlib linestyle
                            (e.g. "-" or "--" or "-.-")
        :param only_show_in_rows: list of rows in which line should be added
        :param only_show_in_columns: list of columns in which line
                                     should be added
        """
        for ax_position, ax in self.all_axs.items():
            row = ax_position[0]
            column = ax_position[1]
            draw_line_here = self._check_if_pos_is_in_row_col_list(row, column,
                                                                  only_show_in_rows,
                                                                  only_show_in_columns)

            if not draw_line_here:
                continue

            if len(ax.images) > 0:
                image = self._get_img_from_axis(ax)
                min_y = 0
                # y dimension (height) is the first
                max_y = image.shape[-3] - 1
                min_x = 0
                # x dimension (width) is the second
                max_x = image.shape[-2] - 1
            else:
                min_y = ax.get_ylim()[0]
                max_y = ax.get_ylim()[1]
                min_x = ax.get_xlim()[0]
                max_x = ax.get_xlim()[1]

            if (orientation == "hor") | (orientation == "horizontal"):
                line_x = [min_x, max_x]
                line_y = [position, position]
            elif (orientation == "vert") | (orientation == "vertical"):
                line_x = [position, position]
                line_y = [min_y, max_y]
            else:
                raise ValueError("The supplied orientation {} is not "
                                 "supported.".format(orientation))

            line = lines.Line2D(line_x, line_y, lw=line_width,
                                transform=ax.transData, c=color,
                                solid_capstyle="butt",
                                linestyle=line_style,
                                **kwargs)

            ax.add_line(line)

    def add_text_on_image(self, texts, images =None,
                          show_in_rows=None, show_in_columns=None,
                          position_in_abs_data_coords=True):
        """
        Add text on image, also delete all text that was added by function
        "rescale_font_size". Therefore should be specifically used for 
        adding text on illustrations. Figure editor GUI will output code
        that uses this function.

        :param texts: list of dicts describing text.
                      Each key of dict is one parameter to axis.text function
                      and each value the corresponding parameter value
                      (x, y and s have to be defined. Other parameters
                      like font_size are optional. See matplotlib docs:
                      "https://matplotlib.org/stable/api/_as_gen/
                      matplotlib.axes.Axes.text.html")
                      Changing the font size is not recommended, so that
                      font size is uniform across the entire figure.
        :param images: list of dict or dict
                        dict  specifies on which images should be drawn
                       the key is the category and the value
                       is a list of allowed values
        :param show_in_rows: list of ints, In which row to show all texts
        :param show_in_columns: list of ints, In which row to show all texts
        :param position_in_abs_data_coords: Whether the position of the text
                                        is in data coordinates, which means
                                        that they will be at the same x,y
                                        coordinate position, for each zoom
                                        and the overview image -
                                        this can be at completely different
                                        positions in the axes and may
                                        not be in the axes at all (and
                                        will therefore not be shown); if False
                                        position is as axes fraction and will
                                        not be corrected for zoom
        """
        # define functions to prevent line length going over limit
        # but still keeping clear function names
        is_pos_in_list = self._check_if_pos_is_in_row_col_list
        correct_position = self._correct_xy_for_cropping_and_zoom
        coords_from_data_to_axes = self._transform_coords_from_data_to_axes
        identity_matches_criteria = self._check_if_identity_matches_dict_criteria

        for ax_position, ax in self.all_axs.items():
            position_allowed = is_pos_in_list(ax_position[0], ax_position[1],
                                           show_in_rows, show_in_columns)

            if not position_allowed:
                continue

            # delete text already added by function rescale_font_size
            for child in ax.get_children():
                if not isinstance(child, matplotlib.text.Text):
                    continue
                if child.get_label() == "__rescaled_text__":
                    child.remove()

            pre_identity = self.pos_to_pre_identity_map[ax_position]

            # copy text objects so that they stay the same across axes
            texts_this_ax = copy.deepcopy(texts)

            for text_nb, text in enumerate(texts_this_ax):

                if type(images) in [list, tuple]:
                    if len(images) > 1:
                        images_this_text = images[text_nb]
                    else:
                        images_this_text = images[0]
                else:
                    images_this_text = images

                identity_matches = identity_matches_criteria(pre_identity,
                                                             images_this_text)

                if not identity_matches:
                    continue

                if position_in_abs_data_coords:
                    text_position = correct_position(text["x"],text["y"],
                                                     ax_position[0],
                                                     ax_position[1])

                    text_position = coords_from_data_to_axes(text_position[0],
                                                             text_position[1], ax)
                    text["x"] = text_position[0]
                    text["y"] = text_position[1]

                # do not plot text that is outside of the axes
                if (text["x"] < 0) | (text["y"] < 0):
                    continue

                if "fontsize" not in text:
                    text["fontsize"] = self.font_size
                if "verticalalignment" not in text:
                    text["verticalalignment"] = "center"
                ax.text(**text, picker=True,
                        transform=ax.transAxes)


    def rescale_font_size(self, font_size_factor = None,
                          font_size=None,
                          linespacing=0.92):
        """
        Only possible for single images with single pptx files for now!
        Only the first slide of the pptx file will be considered.
        Text boxes in powerpoint MUST BE 99% opacity for this script
        to work properly... before saving it as an image!
        It therefore also just works with pngs saved from powerpoint
        (not with e.g. jpeg)
        Font sizes above 40 will be scaled according to font_size_factor.
        For all other text self.font_size will be used
        and optionally multiplied with font_size_factor

        :param font_size_factor: font_size factor by which to scale text
                                that has a font size > 40 pt in powerpoint
        :param font_size: font_size to use, if None, use default of figure_panel
        :param linespacing: spacing of lines when text includes line breaks
        """

        if FigurePanel._is_none(font_size):
           font_size = self.font_size


        if (len(self.all_axs) != 1) & (len(self.panel_pptxs) != 1):
            raise ValueError("Fonts can only be rescaled for single images "
                             "plotted in panel and a single pptx file supplied.")

        ax = list(self.all_axs.values())[0]
        pptx = self.panel_pptxs[0]

        # get dimensions of all elements in pptx
        # this can be used to find out where elements are positioned
        # and the relative coordinates can be used to change the underlying image
        # this is based on the assumption that not the entire pptx slide was
        # saved as image but instead all objects on the slide
        min_left = np.inf
        max_left = 0
        min_top = np.inf
        max_top = 0
        for shape in pptx.slides[0].shapes:
            left_start = shape.left
            min_left = min(min_left, left_start)
            left_end = left_start + shape.width
            max_left = max(max_left, left_end)

            top_start = shape.top
            min_top = min(min_top, top_start)
            top_end = top_start + shape.height
            max_top = max(max_top, top_end)

        #  max_top *= 1.02

        pptx_dim = {}
        pptx_dim["x0"] = min_left
        pptx_dim["x1"] = max_left
        pptx_dim["y0"] = min_top
        pptx_dim["y1"] = max_top
        pptx_dim["width"] = max_left - min_left
        pptx_dim["height"] = max_top - min_top

        # crop dimensions of powerpoint images
        # if cropping was defined
        if len(self.crop_params) > 0:
            crop_param = self.crop_params[0]
            pptx_dim["x0"] = int(pptx_dim["x0"] + crop_param['left'] *
                                 pptx_dim["width"])
            pptx_dim["x1"] = int(pptx_dim["x1"] - crop_param['right'] *
                                 pptx_dim["width"])
            #  switch top and bottom for 0 and 1
            #  since y counting starts at the top
            pptx_dim["y0"] = int(pptx_dim["y0"] + crop_param['top'] *
                                 pptx_dim["height"])
            pptx_dim["y1"] = int(pptx_dim["y1"] - crop_param['bottom'] *
                                 pptx_dim["height"])

        pptx_dim["width"] = pptx_dim["x1"] - pptx_dim["x0"]
        pptx_dim["height"] = pptx_dim["y1"] - pptx_dim["y0"]

        # find all text fields in pptx &
        # get position of each text field, relative on the dimensions
        all_texts = []
        for shape in pptx.slides[0].shapes:
            if not hasattr(shape,"text"):
                continue

            if shape.text == "":
                continue

            text_frame = shape.text_frame
            new_text = {}
            new_text["shape"] = shape
            # only making tighter from right appears to work,
            #  the rest exposes some text
            # dont know why...


            # get rotation, found by Karim Elgazar:
            xfrm = shape._element.spPr.get_or_add_xfrm()
            if xfrm.get("rot") is not None:
                rotation =  (180+ int(xfrm.get("rot")) // 60000)%360
            else:
                rotation = None
            # if rotation is None:
            new_text["x0"] = (shape.left - pptx_dim["x0"]) / pptx_dim["width"]  # + text_frame.margin_left
            # new_text["x0"] = (shape.left - pptx_dim["x0"]) / pptx_dim[
            #     "width"]  # + text_frame.margin_left
            new_text["x1"] = (shape.left + shape.width - pptx_dim["x0"]) / pptx_dim["width"]#  - text_frame.margin_right
            new_text["width"] = new_text["x0"] - new_text["x1"]
            new_text["y0"] = (shape.top- pptx_dim["y0"]) / pptx_dim["height"]# + + text_frame.margin_top
            new_text["y1"] = (shape.top + shape.height - pptx_dim["y0"]) / pptx_dim["height"] #
            new_text["height"] = new_text["y0"] - new_text["y1"]
            if rotation in [90, 270]:
                x0 = new_text["x0"] - new_text["width"]/2 + new_text["height"]/2
                new_text["x0"] = x0
                new_text["x1"] = x0 - new_text["height"]
                y0 = new_text["y0"] + new_text["width"]/2.5
                new_text["y0"] = y0
                new_text["y1"] = y0 - new_text["width"]

            new_text["text"] = shape.text
            new_text["margin_left"] = text_frame.margin_left / pptx_dim["width"]
            new_text["margin_right"] = text_frame.margin_right / pptx_dim["width"]
            new_text["margin_top"] = text_frame.margin_top / pptx_dim["height"]
            new_text["margin_bottom"] = text_frame.margin_bottom / pptx_dim["height"]

            
            new_text["rotation"] = rotation
            new_text["alignment"] = str(text_frame.paragraphs[0].alignment)
            new_text["fontsize"] = text_frame.paragraphs[0].runs[0].font.size.pt
            all_texts.append(new_text)

        # in ax image, delete portions of the image with text
        image = self._get_img_from_axis(ax)

        # cut out additional padding around the image by removing
        # everything that is transparent
        # this needs to be done since powerpoint adds an additional padding
        # around text boxes when saving as picture
        # text boxes are added in powerpoint with 99% opacity,
        #  therefore slightly above 0 in the alpha channel of the image
        image_alpha = image[:, :, 3]
        (height, width) = image_alpha.shape
        x_axis = image_alpha.any(0)
        y_axis = image_alpha.any(1)
        # [::-1] reverses the array, still,
        #  I like np.flip more because its more easily understandable
        x_slice = slice(x_axis.argmax(),width - np.flip(x_axis).argmax())#; 
        y_slice = slice(y_axis.argmax(),height - np.flip(y_axis).argmax())#; 
        image = image[y_slice, x_slice]

        image_width = image.shape[-2]
        image_height = image.shape[-3]
        for text in all_texts:
            x0 = int(text["x0"] * image_width)
            x1 = int(text["x1"] * image_width)
            y0 = int(text["y0"] * image_height)
            y1 = int(text["y1"] * image_height)
            fill_val_arrays = []
            if y0 > 0:
                fill_val_arrays.append(image[y0-1,x0:x1,:])
            if y1 < image.shape[0]-1:
                fill_val_arrays.append(image[y1+1,x0:x1,:])
            if x0 > 0:
                fill_val_arrays.append(image[y0:y1,x0-1,:])
            if x1 < image.shape[1]-1:
                fill_val_arrays.append(image[y0:y1,x1+1,:])
            fill_val = np.median(np.concatenate(fill_val_arrays), axis=[0,1])
            image[y0:y1, x0:x1, :] = fill_val
            
        ax.images[0]._A = image
        
        #  draw text in ax again at same position but new size
        for text in all_texts:
            rotation = text["rotation"]

            # for now assumes that alignment of "none" is "left"
            if text["alignment"].find("None") != -1:
                x0 = text["x0"] # + text["margin_left"]
                #  y0 = text["y0"] # + text["margin_top"]
                if rotation in [90, 270]:
                    y0 = text["y1"] + text["width"]/2
                else:
                    y0 = text["y1"] + text["height"] / 2
                hor_alignment = "left"
                vert_alignment = "center"

            elif text["alignment"].find("CENTER") != -1:
                if rotation in [90, 270]:
                    x0 = text["x0"] - text["height"] / 2
                    y0 = text["y1"] + text["width"] / 2
                else:
                    x0 = text["x0"] - text["width"] / 2
                    y0 = text["y1"] + text["height"] / 2
                hor_alignment = "center"
                vert_alignment = "center"
                
            elif text["alignment"].find("RIGHT") != -1:
                x0 = text["x1"] # - text["margin_right"]
                #  y0 = text["y0"] # + text["margin_top"]
                if rotation in [90, 270]:
                    if rotation == 270:
                        x0 = text["x0"]
                        hor_alignment = "left"
                    elif rotation==90:
                        # x0 = text["x0"]
                        hor_alignment = "right"
                    y0 = text["y1"] + text["width"] / 2
                    vert_alignment = "center"
                else:
                    y0 = text["y1"] + text["height"] / 2
                    hor_alignment = "right"
                    vert_alignment = "center"

            text_fontsize = copy.copy(font_size)

            if text["fontsize"] > 40:
                text_fontsize *= 2
            else:
                if not FigurePanel._is_none(font_size_factor):
                    text_fontsize *= font_size_factor

            new_text = ax.text(x0, 1-y0, text["text"],
                                picker=True,
                                rotation=text["rotation"],
                                horizontalalignment=hor_alignment,
                                verticalalignment=vert_alignment,
                                label="__rescaled_text__",
                                transform=ax.transAxes,
                                fontsize=text_fontsize,
                                linespacing=linespacing)

    def _transform_coords_from_axes_to_data(self, x, y, ax):
        x_lim = ax.get_xlim()
        ax_width_px = max(x_lim) - min(x_lim)
        y_lim = ax.get_ylim()
        ax_height_px = max(y_lim) - min(y_lim)
        x_trans = x * ax_width_px
        y_trans = y * ax_height_px
        return x_trans, y_trans


    def _transform_coords_from_data_to_axes(self, x, y, ax):
        x_lim = ax.get_xlim()
        ax_width_px = max(x_lim) - min(x_lim)
        y_lim = ax.get_ylim()
        ax_height_px = max(y_lim) - min(y_lim)
        x_trans = x / ax_width_px
        y_trans = y / ax_height_px
        return x_trans, 1-y_trans

    def draw_marker(self, frames = None, channels = None, images = None,
                    radius=0.15, color="white", show_only_in_zoom=False,
                    only_show_in_columns=None, only_show_in_rows = None,
                    position=None):
        """
        Add marker (circle) to specific upper left edge in images.

        :param frames: Will be deprecated
                    list, which frames the zoom should be applied to.
                    If None, it will be applied to all channels
        :param channels: Will be deprecated
                    list, which channels the zoom should be applied to.
                    If None, it will be applied to all channels
        :param images: dict with each key corresponding to one category
                        ("images", "channels" and "frames" allowed) and
                        the value being a list with all allowed values
                    Alternative use, will be deprecated:
                    list, which images the zoom should be applied on.
                    If None, it will be applied to all images
        :param radius: radius in inches
        :param color: color of circle
        :param show_only_in_zoom: Whether show marker only in zoomed images
        :param only_show_in_columns: List of columns of image grid in which
                                        to add the marker
        :param only_show_in_rows: List of rows of image grid in which
                                        to add the marker
        :param position: Not implemented
        """
        fig = plt.gcf()
        fig_size_inches = fig.get_size_inches()
        for ax_position, ax in self.all_axs.items():

            position_allowed = self._check_if_pos_is_in_row_col_list(ax_position[0],
                                                                    ax_position[1],
                                                                    only_show_in_rows,
                                                                    only_show_in_columns)

            if not position_allowed:
                continue

            # extract frame from file name
            identity = self.pos_to_pre_identity_map[ax_position]

            if type(images) == dict:
                identity_correct = self._check_if_identity_matches_dict_criteria(
                                                                        identity,
                                                                        images)
            else:
                identity_correct = True
                if "zooms" in self.map:
                    if show_only_in_zoom & (identity[self.map["zooms"]] == 0):
                        identity_correct = False
                if frames != None:
                    if identity[self.map["frames"]] not in frames:
                        identity_correct = False
                if channels != None:
                    if identity[self.map["channels"]] not in channels:
                        identity_correct = False
                if images != None:
                    if identity[self.map["images"]] not in images:
                        identity_correct = False
            if identity_correct:
                # calculate radius in inches
                image = self._get_img_from_axis(ax)
                inch_per_px = ( ax.get_position().width * fig_size_inches[0] ) \
                                / image.shape[-2]
                radius_px = int( np.round(radius / inch_per_px , 0) )
                circle = mpatches.Circle((radius_px, radius_px),
                                         radius=radius_px, color=color)
                ax.add_patch(circle)