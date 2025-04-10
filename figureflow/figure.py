# -*- coding: utf-8 -*-
"""
Created on Fri Feb  7 14:15:34 2020
@author: Maxsc
"""

import os
import re
import sys
import glob
import copy
import string
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import animation
from matplotlib.gridspec import GridSpec
from contextlib import suppress

#for changed matplotlib function:
from matplotlib import backend_bases

import functools
import seaborn as sb
import shutil
from . import figure_panel
from .figure_editor import figure_editor_gui

import sys
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets

from moviepy import editor
import pptx
from skimage import io
import importlib
from matplotlib.transforms import Bbox
from inspect import getmembers, isfunction
#reloading is necessary to load changes made in the other script since the editor was started
importlib.reload(figure_panel)
FigurePanel = figure_panel.FigurePanel
FigureEditorGUI = figure_editor_gui.FigureEditorGUI

import time

class Figure():

    def __init__(self,folder,height=1,number=1,dpi=600,padding="DEFAULT",letter_fontsize=9,
                width=4.75, font_size=7, video = False,
                 video_batch_mode=False, batch_mode_folder_depth=0,
                 save_batch_in_sub_folder=True,
                 name="Figure", video_name_from_folder=False, video_name_from_file=False,
                 script_path=None,
                file_format="png", show_panel_letters=True,
                dark_background = False, panel_str = "panel", relative_height=True):
        """
        The structure of the figure can also be defined in a csv.
        The csv needs to be in the main folder of the figure
        with the name __figure__ followed by the "number" and ".csv"
        The csv
        A grid with letters of the panels where
        if a panel should span several cells
        the corresponding letter should be written in several cells.
        Widths and heights can be defined by three possible ways:
          1) in which the first row is the width of each column and the last
          column is the height of each row

          2) in which above every panel letters there is a number corresponding
          to the relative width of the panel in that row and the last column of
          the csv contains the height of each row

          3) in which widths are defined as in 2) but heights are defined for
          every panel by a number right of the panel letter

        :param folder: Absolute path to folder with files for figure
        :param letter_fontsize: Fontsize in pt for panel letters in figure
        :param number: Number of the figure, which will be used for the file
                        name. Can also be a string which is added for the
                        file name instead of the number (also for supplementary
                        figures something like "S1")
        :param name: string of file name start (will be followed by value
                    of parameter "number")
        :param video: Whether the Figure object is a video or not. For videos,
                        no panel letters will be added.
        :param video_batch_mode: Create separate videos for all files. For
            example, if the same kind of videos should be created for many
            similar files, this can be done with one set of settings in one
            single script and only one figure object. All similar files
            must have a name with the same panel letter. Additional files in
            other panels can still be added to each video. However, there can
            only be one file for each of these other panels (that stay the same
            for each batch). If there is more than one file, the script will
            assume that these files should also be batched. If there are more
            files for one panel than for another panel, the script will iterate
            through the files together. When the end of files is reached for one
            panel, only the first file will be used for this panel.
        :param batch_mode_folder_depth: For the video_batch_mode, files don't
            necessarily have to be in the same folder. They can also be in
            subfolders with a defined depth. A depth of 0 means that files are
            only in the main folder. A depth of 1 means that files are in
            sub-folders in the main folder. A depth of 2 means that files are in
            sub-folders of sub-folders in the main folder. Importantly, only
            files at exactly that depth will be used and not all files until
            this depth.
        :param save_batch_in_sub_folder: Whether for the video_batch_mode,
            final files should be saved in the folder in which the batch_file
            was.
        :param video_name_from_folder: Whether the name of the parent folder that
            the file is in should be used to name the final file (e.g. movie).
        :param video_name_from_file: Whether the name of the file (if only one panel
            with one file was used) should be used for the final file name
            (e.g. name of movie file).
        :param file_format: String of file format to be used in .savefig
            File format can also be defined when executing figure.save(), but 
            if one of the file formats is pdf or svg and the other is not,
            then .rescale_font_size will lead to problems for some 
            illustrations with text added in powerpoint since for .pdf files
            a padding needs to be applied around the image to prevent cutoff of
            edges.
        :param dark_background: Whether the background of the figure should be
                                dark instead of white. This will also change the
                                default font color on the background from black
                                to white
        :param relative_height: Whether the height is defined as multiples of
                                the width (True) or as inches (False).
        :param panel_str: panel string that is searched for in file names
                            to find files belonging to specific panel
        :param height: height of the figure in inches or in multiples of width
                        if relative_height is True
                        Default is same height as width, will be adjusted when
                        saving the figure automatically.
                        However, for videos height needs to be set and will
                        not be changed at the end
                        (matplotlib requires defining the size of the figure
                        for videos beforehand)
        :param width: width of the figure in inches
        :param padding: float "DEFAULT" or list, in inches
                        if "DEFAULT", will be half of the letter fontsize
                        determines the padding on the outside of the figure
                        as float even padding on all sites of figure
                        as list, first value for x dimension (width)
                        and second value for y dimension (height)
                        However, only the x value will be used
                        for an even border around the figure.
                        will also be used as default padding for all panels created
                        as space between panels (in x and y)

        """
        self.dpi = dpi
        self.number = number
        self.width_inch = width
        self.height = height
        self.folder = os.path.abspath(folder)
        self.script_path = script_path
        self.font_size = font_size
        self.letter_fontsize = letter_fontsize
        self.all_panels = {}
        self.name = name
        self.file_format = file_format
        self.current_panel = None
        self.video = video
        self.panel_str = panel_str
        self.max_height = 0
        self.column_widths = []
        self.row_heights = []
        self.panel_dimensions = {}
        self.figure_csv = None
        self.padding_factor_video = 1/6
        self.panel_letters_to_show = None
        self.panel_to_edit = None
        self.panel_edit_kwargs = None
        self.change_cropping = False
        self.show_panel_letters = show_panel_letters

        self.video_batch_mode = video_batch_mode
        self.batch_mode_folder_depth = batch_mode_folder_depth
        self.save_batch_in_sub_folder = save_batch_in_sub_folder
        self.video_name_from_folder = video_name_from_folder
        self.video_name_from_file = video_name_from_file

        #for videos make sure that the height is defined
        if video & (type(self.height) == type(None)):
            raise ValueError("For Videos, the height of the figure must be defined"
                             "in order to pre-define the Figure size."
                             "Figure size cannot be dynamically changed at the end"
                             "for Videos.")

        if relative_height:
            height_inch = height * self.width_inch
        else:
            height_inch = height
            #define relative height in multiples of width_inch
            self.height = height_inch / self.width_inch

        if dark_background:
            plt.style.use("dark_background")
        else:
            plt.style.use("seaborn")
            sb.set_style("whitegrid")

        self.dark_background= dark_background

        self.all_video_frames = None


        self.fig = plt.figure(figsize=(self.width_inch,height_inch),dpi=dpi)
        #initiate renderer of the figure since its used in
        #"get_dimension_of_text" function in figure_panel
        #can only be left out if first panel that is drawn does not use that function
        self.fig.canvas.draw()

        # self.size_factor = size_per_panel / 2
        #why do I still want to scale anything? Hm.
        #why was it scaled with the size per panel before?
        #Smaller panels mean smaller padding etc? Don't think it should.
        #factor is defined as a standard value that scaled well
        # in figures built so fatr current
        self.size_factor = 0.198 #4.75 / 12 / 2

        letter_fontsize_inch = self.letter_fontsize / 72
        if padding == "DEFAULT":
        #     divide by two to have half of the padding on each side of the plot
            self.padding = [letter_fontsize_inch / 2,
                            letter_fontsize_inch / 2]

            if self.video:
                self.padding[0] *= self.padding_factor_video
                self.padding[1] *= self.padding_factor_video

        else:
            if (type(padding) == list) | (type(padding) == tuple):
                self.padding = padding
            else:
                self.padding = [padding, padding]

        self.grid = None
        #Only allow files with one of the following extensions
        self.allowed_extensions = (".csv",
                                   ".png",
                                   ".jpg",
                                   ".tiff",
                                   ".tif",
                                   ".pptx",
                                   ".feather")
        if os.path.exists(folder):
            self.all_files = os.listdir(folder)
            if self.video_batch_mode:
                if self.batch_mode_folder_depth > 0:
                    folder_depth = ["*"] * self.batch_mode_folder_depth
                    deeper_files = glob.glob(os.path.join(self.folder,
                                                          *folder_depth,
                                                          "*"))
                    self.all_files = [*self.all_files, *deeper_files]
        else:
            raise Exception("folder not found")

        #filter files for either having allowed extension
        #or for being a folder
        #add paths to files / Folders to list
        all_files_filtered = []
        potential_figure_csvs = []
        for file in self.all_files:
            file_path = os.path.join(self.folder, file)

            # read figure csv that will give the structure
            # of the entire figure
            if (file.lower().find("__figure__") != -1) & (file.lower().find(".csv") != -1):
                potential_figure_csvs.append(file)
            elif (file.lower().find("__figure__") != -1) & (file.lower().find(".feather") != -1):
                self.figure_csv = pd.read_feather(file_path)

            #allow folders also
            if os.path.isdir(file_path):
                all_files_filtered.append(file_path)
            else:
                if self._file_has_allowed_extension(file):
                    all_files_filtered.append(file_path)

        # if multiple figure csvs are in the folder, take the one that contains
        # the number of the figure (if that one exists, otherwise take the
        # last one in the list)
        figure_csv_found = False
        for potential_figure_csv in potential_figure_csvs:
            if str(self.number) in potential_figure_csv:
                figure_csv_found = True
                break

        if not figure_csv_found:
            raise ValueError("No csv file for figure layout found. Please "
                             "create a csv file with the name '__figure__X' "
                             "with X being the number of the figure and the "
                             "required layout to define the position and size"
                             " of panels. Check example figure layout files on"
                             " the github repository in the folder "
                             "'data' if needed.")

        file_path = os.path.join(self.folder, potential_figure_csv)
        self.figure_csv = Figure._open_csv_with_unknown_seperator(file_path,
                                                                  header= None)

        self.all_files = all_files_filtered
        if len(self.all_files) == 0:
            raise Exception("No allowed files in folder.")

        if type(self.figure_csv) != type(None):
            self.figure_csv = self.figure_csv.fillna(0)
            figure_structure = self.figure_csv.values
            #replace nan in figure
            figure_structure = np.nan_to_num(figure_structure)
            number_regex = re.compile("[\d]")

            column_widths = self._extract_non_nan_num_array(figure_structure)

            row_heights = self._extract_non_nan_num_array(figure_structure.T)

            all_letters = []
            max_nb_columns = 0
            for row in figure_structure:
                row_num = np.genfromtxt(np.array(row, dtype=str))
                letter_idxs = np.where(np.isnan(row_num))[0]
                new_letters = row[letter_idxs]
                if len(new_letters) > 0:
                    all_letters.append(list(new_letters))
                    max_nb_columns = max(max_nb_columns, len(new_letters))

            #fill in too few letters by repating last letter in row
            #necessary to make numpy array afterwards
            for letter_row in all_letters:
                nb_elements_missing =  max_nb_columns - len(letter_row)
                if nb_elements_missing > 0:
                    letter_row.extend([letter_row[-1]] * nb_elements_missing)

            all_letters = np.array(all_letters)
            all_unique_letters = np.unique(all_letters)

            #initiate dicts to track in which rows and columns
            #a panel was, important to not increase height or
            #width multiple times for the same dimension
            # (see below for more detailed explanation)
            panel_rows = {}
            panel_columns = {}
            for unique_letter in all_unique_letters:
                #create empty panel dimension dict
                #x0, y0, width and height will be defined
                # in this dict later
                self.panel_dimensions[unique_letter] = {}
                #initiate height and width as 0
                #will be increased for each occurence of the panel
                self.panel_dimensions[unique_letter]["height"] = 0
                self.panel_dimensions[unique_letter]["width"] = 0
                panel_rows[unique_letter] = set()
                panel_columns[unique_letter] = set()

            #get the size of the arrays
            #to not go outside of the dimensions
            #since arrays could also only be one row
            #that would be applied across the entire figure

            nb_width_rows = column_widths.shape[0] - 1
            nb_height_rows = row_heights.shape[0] - 1
            #each panel will only increase its width and height
            #once for each position in the dimension
            #e.g. if the panel is in multiple rows
            #but in the same column
            #width will only be increased once
            #or if panel is in multiple columns
            #but all in the same row
            #height will only be increased once
            for row_nb, row in enumerate(all_letters):

                for column_nb, cell_letter in enumerate(row):

                    #check if panel height was NOT already increased
                    # for the current row
                    if row_nb not in panel_rows[cell_letter]:
                        #get the index of the first dimension the size arrays
                        height_idx = min(nb_height_rows, column_nb)
                        cell_height = row_heights[height_idx, row_nb]
                        self.panel_dimensions[cell_letter]["height"] += cell_height

                    #check if panel width was NOT already increased
                    #for the current column
                    if column_nb not in panel_columns[cell_letter]:
                        width_idx = min(nb_width_rows, row_nb)
                        cell_width = column_widths[width_idx, column_nb]
                        total_width_in_row = np.sum(column_widths[width_idx, :])
                        cell_width_rel = cell_width / total_width_in_row
                        self.panel_dimensions[cell_letter]["width"] += cell_width_rel

                    panel_rows[cell_letter].add(row_nb)
                    panel_columns[cell_letter].add(column_nb)
                    #only set first position that the letter is found in
                    #this corresponds to the top left start position
                    #of the panel

                    #and is sufficient to define the position later
                    if "x0" not in self.panel_dimensions[cell_letter]:
                        cell_x = np.sum(column_widths[width_idx, :column_nb])
                        cell_x_rel = cell_x / total_width_in_row
                        cell_y = np.sum(row_heights[height_idx, :row_nb])
                        self.panel_dimensions[cell_letter]["x0"] = cell_x_rel
                        self.panel_dimensions[cell_letter]["y0"] = cell_y

        fig_size = self.fig.get_size_inches()
        padding_size_x = self.padding[0] / fig_size[0]
        padding_size_y = self.padding[1] / fig_size[1]
        #padding_size_x determines border around entire figure
        #width per plot is factor in fraction of figure width

        self.fig_width_available = 1 - padding_size_x * 2

        #width per plot equals height for plot
        #this is possible since the height will be preset in figure to be the same as the width
        #when saving the figure at the end, the height will be re-adjusted to the actual height
        #since everything is plotted at that point, this does not change any placement

        self.fig_height_available = self.fig_width_available * (fig_size[0] / fig_size[1])


        # if self.video:
        #     self.fig_width_available += padding_size_x * 2
        #     self.fig_height_available += padding_size_x * (fig_size[0] / fig_size[1]) *2

        self._add_all_figure_panel_functions()
        #necessary to initiate renderer
        if video:
            self.fig.canvas.draw()

    def move_panel_and_shift_other_letters(self, letter_from, letter_to):
        """

        :param moved_letter_map: Dict with the original letter as key and the
                target letter as value (e.g. {"B":"C", "A":"B"} will change B
                to C and A to B.
        """
        self.rename_panel_letters({letter_from:"tmp"})
        if ord(letter_from) > ord(letter_to):
            # if a letter is moved to an earlier letter
            # shift all letters from the new position until
            # the original positions - 1
            self._shift_letters(letter_to, distance = 1,
                               last_letter = chr(ord(letter_from) - 1))
        else:
            # if a letter is moved forward (to a later position)
            # shift all letters from the original position + 1 to the
            # new position - 1 one position back
            self._shift_letters(chr(ord(letter_from) + 1), distance = -1,
                               last_letter = letter_to)

        self.rename_panel_letters({"tmp":letter_to})
        self._stop_script_after_renaming_panels()

    def _stop_script_after_renaming_panels(self):
        print("Files were successfully renamed, "
              "and the script was successfully changed. The execution of the "
              "script is stopped, since it would execute the script before "
              "the change and thus the file names would not match with the "
              "panels defined in the script.")
        sys.exit()

    def _reexecute_script(self):
        if self.script_path is not None:
            # with open(self.script_path, "r") as script_file:
            #     script = script_file.read()
            # exec(script)
            os.system(self.script_path)
            sys.exit()


    def shift_panels_after_adding_new_panel(self, added_letters):
        """
        Shift all panel letters for folder / file names and in the figure
        script (if the path is defined) if a panel (letter) was removed.

        :param added_letters: String of letter or letter range to add.
        """
        # When panels are added, all panels after the added panels
        # should be shifted forward by then number of panels that were added.

        # create a list of all panel letters to be shifted and the letter
        # they should be shifted to.

        first_and_last_added_letter = added_letters.split("-")
        first_letter_added = first_and_last_added_letter[0]
        if len(first_and_last_added_letter) > 1:
            last_letter_added = first_and_last_added_letter[1]
        else:
            last_letter_added = first_and_last_added_letter[0]

        letter_distance = (ord(last_letter_added) - ord(first_letter_added)) + 1
        self._shift_letters(first_letter_added, letter_distance)
        self._stop_script_after_renaming_panels()


    def shift_panels_after_removing_panel(self, removed_letters):
        """
        Shift all panel letters for folder / file names and in the figure
        script (if the path is defined) if a panel (letter) was removed.

        :param removed_letters: String of letter or letter range that were
            removed.
        """
        # When a panel is removed, all panels after the removed panels
        # should be shifted backward by then number of panels that were removed.

        # create a list of all panel letters to be shifted and the letter
        # they should be shifted to.

        first_and_last_removed_letter = removed_letters.split("-")
        first_letter_removed = first_and_last_removed_letter[0]
        if len(first_and_last_removed_letter) > 1:
            last_letter_removed = first_and_last_removed_letter[1]
        else:
            last_letter_removed = first_and_last_removed_letter[0]

        letter_distance = ((ord(last_letter_removed) -
                            ord(first_letter_removed)) + 1)
        self._shift_letters(chr(ord(last_letter_removed)+1),
                            - letter_distance)
        self._stop_script_after_renaming_panels()

    def _shift_letters(self, first_letter, distance, last_letter=None):
        # the last letter is set so that after shifting the last letter becomes
        # Z (the last letter in the alphabet)
        if last_letter is None:
            last_letter = chr(ord("Z") - distance)
        letter_range_to_shift = self._letter_range(first_letter,
                                                   last_letter)
        letter_range_shifted = [chr(ord(letter) + distance)
                                for letter in letter_range_to_shift]

        letter_map = dict(zip(letter_range_to_shift, letter_range_shifted))
        self.rename_panel_letters(letter_map)


    def rename_panel_letters(self, panel_letter_map):
        """
        Rename panel letters for the current figure using a map
        - instead of manually renaming in the file explorer. Renaming will also
        be done in the script path (if it is defined).

        :param panel_letter_map: Dict with the original letter as key and the
                target letter as value (e.g. {"B":"C", "A":"B"} will change B
                to C and A to B.

        """
        if self.script_path is not None:

            def replace_panel_letters(match):
                """
                Replacement of panel letters as defined in the panel_letter_map
                in the figure script.
                """
                entire_match = match.group(0)
                letter = match.group(1)
                if letter in panel_letter_map:
                    return entire_match.replace(letter,
                                                panel_letter_map[letter])
                else:
                    return entire_match

            panel_letter_finder = re.compile('create_panel\(\"([\w])\"')
            with open(self.script_path, "r+") as script_file:
                script = script_file.read()
                # replace all panel letters simultaneously
                script = panel_letter_finder.sub(replace_panel_letters, script)

            # create a temporary script file that will be used to overwrite
            # the original file
            file_extension = self.script_path.split(".")[-1]
            tmp_file_path = self.script_path.replace("."+file_extension,
                                                     "___tmp."+file_extension)
            with open(tmp_file_path, "w+") as tmp_script_file:
                tmp_script_file.write(script)

            os.replace(tmp_file_path, self.script_path)

        panel_finder = re.compile("panel([\w]+?)_")
        all_files = os.listdir(self.folder)
        for panel_file in all_files:
            path = os.path.join(self.folder, panel_file)
            # check that the current panel file/folder is actually
            # a panel file/folder
            panel_letter = panel_finder.search(panel_file)
            if panel_letter is None:
                continue
            whole_string = panel_letter.group(0)
            panel_letter = panel_letter.group(1)

            new_panel_letter = ""
            # go through each string element in case
            # the panel letter is actually multiple panel letters
            # add either the original panel letter (if it is not in the map)
            # or the new panel letter (if it is in the map
            for letter in panel_letter:
                # should the panel letter be remapped
                if letter not in panel_letter_map:
                    new_panel_letter += letter
                    continue
                new_panel_letter += panel_letter_map[letter]

            print(panel_letter, new_panel_letter)

            new_panel_file = panel_file.replace("panel"+panel_letter+"_",
                                                "panel"+new_panel_letter+"_")
            new_path = os.path.join(self.folder, new_panel_file)
            os.rename(path, new_path)


    def _extract_non_nan_num_array(self, array):
        #generate a matrix with all num values
        rows_of_num_array = []
        max_row_length = 0
        for row in array:
            row_numeric = np.genfromtxt(np.array(row, dtype=str))
            #use row if no cell is nan (was a letter before)
            #empty cells should be replaced with zeros before!
            if not np.isnan(row_numeric).any():
                non_zero_row = row_numeric[row_numeric > 0]
                rows_of_num_array.append(list(non_zero_row))
                max_row_length = max(max_row_length, len(non_zero_row))

        #even out size of rows by appending 0
        for row in rows_of_num_array:
            nb_elements_missing = max_row_length - len(row)
            if nb_elements_missing > 0:
                row.extend([0] * nb_elements_missing)

        return np.array(rows_of_num_array)

    def _file_has_allowed_extension(self, file, extensions=None):
        """
        Checks if file contains the full extension with the "."
        And if the end of the filename is the extension without the "."
        """
        if type(extensions) == type(None):
            extensions = self.allowed_extensions

        for extension in extensions:
            if file.find(extension) != -1:
                if file.split(".")[-1] == extension.replace(".",""):
                    return True


    def _get_next_panel_letter(self):
        all_used_letters = list(self.all_panels.keys())
        all_used_letters.sort()
        if len(all_used_letters) == 0:
            letter = "A"
        else:
            last_letter = all_used_letters[-1]
            alphabet = "abcdefghijklmnopqrstuvwxyz"
            last_letter_idx = alphabet.find(last_letter.lower())
            if last_letter_idx == len(alphabet) - 1:
                raise ValueError("There is no letter after 'Z' in the alphabet."
                                 " Please add a panel without a letter before "
                                 "adding a panel with the letter Z.")
            next_letter = alphabet[last_letter_idx + 1]
            letter = next_letter.upper()
        return letter

    def _get_all_panel_files(self, letter):
        # get all files belonging to the new panel panel
        panel_files = []
        files_in_separate_folders = False
        # panel_finder = re.compile(self.panel_str+letter)
        # match also multiple letters for one file
        panel_finder = re.compile(self.panel_str.lower()+
                                  f"[A-Za-z]*[{letter.lower()}][A-Za-z]*")
        for file_path in self.all_files:
            file_name = os.path.basename(file_path)
            full_panel_str = (self.panel_str + letter).lower()
            #exclude temporary windows files
            if file_name.find("~$") != -1:
                continue

            if panel_finder.search(file_name.lower()) is None:
                continue
            # check if current file_path is a folder
            if os.path.isdir(file_path):
                files_in_separate_folders = True
                # files in folder do not need to follow the panel+letter at beginning
                # however, they do need to have an allowed extension
                for file_in_folder in os.listdir(file_path):
                    file_path_in_folder = os.path.join(file_path, file_in_folder)
                    if self._file_has_allowed_extension(file_path_in_folder):
                        panel_files.append(file_path_in_folder)
            else:
                if files_in_separate_folders:
                    print("WARNING: Files for panel {} are in separte folder/s "
                          "and also in main folder.".format(
                        letter))
                panel_files.append(file_path)

        if len(panel_files) == 0:
            raise Exception("no files found for panel")

        # case insensitive alphanumerical sorting based on filename
        panel_files.sort(key=lambda
            panel_file:os.path.basename(panel_file).lower())

        return panel_files

    def get_representative_data_from_multiple_panels(self, panels,
                                                     nb_vals_to_show=20):
        """
        Get representative data matching data from multiple panels best.
        Only works after representative data was already calculated for the
        defined panels.
        Get list of units (cells etc) that are closest to average of data.
        Data from one unit is in a single image, therefore cannot be separated
        the function will rank units
        than regarding their difference to the mean.
        If you want a representative neuron but did measure neurites,
        a unit should be a neuron but the function will account the difference
        from the mean of all measured neurites.
        It will weigh larger differences from the mean more
        (squared difference of mean).

        :param panels: list of strings of panel letters, capitalization matters
        :param nb_vals_to_show: Number of datapoints to show in the list
        """
        #sum all representative data for each unit
        #in order to get total deviations of all cells
        #from data in all defined panels
        summed_representative_data = pd.DataFrame()
        for panel_letter in panels:
            #check whether supplied panel letter is defined
            if not (panel_letter in self.all_panels):
                error_msg = ("The letter '{}' for multi-panel representative "
                             "data is not a defined "
                             "panel.".format(panel_letter))
                raise ValueError(error_msg)
            panel = self.all_panels[panel_letter]
            #check if representative data was calculated for panel
            if not hasattr(panel,"representative_data"):
                error_msg = ("For the panel '{}' no representative data was "
                             "calculated yet.".format(panel_letter))
                raise ValueError(error_msg)
            if len(summed_representative_data) == 0:
                unit_cols = panel.representative_unit_cols
                cols_to_show = [*unit_cols, "d_mean"]
                panel_data_indexed = panel.representative_data.reset_index().set_index(unit_cols)
                summed_representative_data = panel_data_indexed
                data_groups = panel.representative_data_groups
            else:
                panel_data_indexed = panel.representative_data.reset_index().set_index(unit_cols)
                #sum all d_mean data
                summed_representative_data["d_mean"] += panel_data_indexed["d_mean"]
            #add y difference from mean column from panel
            diff_to_mean_column = panel.representative_diff_column
            cols_to_show.append(diff_to_mean_column)
            summed_representative_data[diff_to_mean_column] = panel_data_indexed[diff_to_mean_column]

        summed_representative_data = summed_representative_data.reset_index().set_index(data_groups)

        group_indices = summed_representative_data.index.drop_duplicates()
        # print(unit_cols)

        for group_index in group_indices:
            data_to_show = summed_representative_data.loc[group_index]
            data_to_show = data_to_show.sort_values(by="d_mean", ascending=True)
            print(data_to_show.head(nb_vals_to_show)[cols_to_show])

    def _letter_range(self, first_letter, last_letter):
        new_panel_letters = [chr(letter_nb)
                             for letter_nb in range(ord(first_letter),
                                                    ord(last_letter)+1
                                                    )]
        return new_panel_letters


    def show_panels(self, panel_letters):
        """
        Only show panels with the defined panel letters. Even if other
        panels are defined in the script they won't be shown.

        :param panel_letters: list of panel letters to show or string of range
            of panel letters (e.g. "A-D")
        """
        all_panel_letters = []
        for panel_letter in panel_letters:
            if panel_letter.find("-") != -1:
                first_letter = panel_letter.split("-")[0]
                second_letter = panel_letter.split("-")[1]
                new_panel_letters = self._letter_range(first_letter,
                                                       second_letter)
                all_panel_letters = [*all_panel_letters, *new_panel_letters]
            else:
                all_panel_letters.append(panel_letter)

        self.panel_letters_to_show = all_panel_letters

    def edit_panel(self, panel_letter, change_cropping=True,
                   coord_decimals=2, color="white",
                   include_all_labels=False, arrow_props=None,
                   plot_row_col_pos_of_cropping=False,
                   get_text_pos_as_abs_data_coords=True,
                   **kwargs
                   ):
        """
        Edit one panel with designated letter. Will enter editing mode
        after panel has been fully plotted: right before the next panel
        is created or alternatively before the figure is saved (for the last
        panel)

        :param panel_letter: panel letter that should be edited
        :param change_cropping: Whether you want to change cropping. If True
                                no cropping will be done. Instead the region
                                that would have been cropped will be a rectangle
                                which you can change.
        :param coord_decimals: For printing code for generating objects
                                number of decimals plotted
                                for each number (e.g. coordinates, width etc)
        :param color: Standard color used for added elements.
        :param include_all_labels: Whether all labels on an image should be
                                    available to change (including channel
                                    names on the image etc). Changing these
                                    labels will result in code printed
                                    out that uses a different function to
                                    add the label, then the function that was
                                    used initially.
        :param arrow_props: dict with arrow parameters as keys and values in pt
                            possible parameters: width, head_width, head_length.
                            Arrows added in the GUI will be added using these
                            properties.
        :param plot_row_col_pos_of_cropping: Whether to plot row and column
                                            position for code to add cropping
                                            images= information will always be
                                            plotted regardless
        :param get_text_pos_as_abs_data_coords: Whether the text position
                                                    when the code for adding is
                                                    is plotted should be as
                                                    absolute data coordinates
                                                    which means that they will
                                                    be on the same position in
                                                    the data, regardless of
                                                    zoom etc. - this means
                                                    that it might not show up in
                                                    a zoom image. Otherwise, the
                                                    position is in relative
                                                    position in the axis
                                                    (e.g. top left of axis)
        """
        if type(panel_letter) is not str:
            raise ValueError("For defining a panel to edit the panel_letter "
                             "has to be defined as string and not as "
                             f"{type(panel_letter)}.")

        self.panel_to_edit = panel_letter
        self.change_cropping = change_cropping
        self.panel_edit_kwargs = {"coord_decimals": coord_decimals,
                                  "color": color,
                                  "include_all_labels": include_all_labels,
                                  "arrow_props": arrow_props,
                                  "change_cropping":change_cropping,
                                  "plot_row_col_pos_of_cropping":
                                      plot_row_col_pos_of_cropping,
                                  "get_text_pos_as_abs_data_coords":
                                      get_text_pos_as_abs_data_coords
                                  }
        self.panel_edit_kwargs.update(kwargs)

    def create_panel(self, letter=None, x=None, y=None,  width=None,
                     height=None, padding = None, **kwargs):
        """
        Create panel with defined letter.

        :param letter: panel letter as string, if None get the letter following
                        the highest panel letter used so far
        :param x: relative x position
        :param y: relative y position
        :param width: width in inches
        :param height: height as multiples of  width (or in inches if
                        parameter "relative_height" == False when creating
                        figure object)
        :param padding: list or float, if list, first value is xpadding,
                        second is ypadding if float,
                        is padding for both xpadding and ypadding
                        xpadding and ypadding can each also be a float
                        or list. if list, the first value is for padding
                        left / top and the second value is for padding
                        right / bottom.
        :return: FigurePanel
        """
        if hasattr(self.current_panel, "pos_to_pre_identity_map"):
            # panel with data plots do not have the attribute
            # and does not have placeholder images
            self.current_panel._remove_placeholder_images()

        if (self.panel_to_edit is not None) & (not self.video):
            if self.panel_to_edit in self.all_panels.keys():
                self.edit_this_panel(**self.panel_edit_kwargs)

        print("CREATING PANEL {}...................".format(letter))
        if (type(padding) == tuple) | (type(padding) == list):
            expanded_padding = []
            # seperate by x an y dimension
            for dim_nb, pad_val in enumerate(padding):
                expanded_padding.append([])
                if (type(pad_val) == tuple) | (type(pad_val) == list):
                    # separate by padding from each site
                    # for x: first left then right
                    # for y: first top then bottom
                    for pad_site_val in pad_val:
                        if type(pad_site_val) == type(None):
                            expanded_padding[dim_nb].append(self.padding[dim_nb])
                        else:
                            expanded_padding[dim_nb].append(pad_site_val)
                elif type(pad_val) == type(None):
                    expanded_padding[dim_nb] = [self.padding[dim_nb],
                                                self.padding[dim_nb]]
                else:
                    expanded_padding[dim_nb] = [padding[dim_nb],
                                                 padding[dim_nb]]
            padding = expanded_padding
        elif (type(padding) == type(None)):
            padding_copy = copy.copy(self.padding)
            padding = [[padding_copy[0], padding_copy[0]],
                       [padding_copy[1], padding_copy[1]]]


        #check if dimensions should be taken from csv
        #therefore from self.panel_dimensions
        #only one value has to be None to get ALL values from csv
        if ((x is None) | (y is None) | (width is None) | (height is None)):
            if len(list(self.panel_dimensions)) == 0:
                raise ValueError("Not all necessary parameters for the panel "
                                 "{} were supplied."
                                 "'x', 'y', 'width' and 'height' must be defined."
                                 "Or alternative dimensions can be defined in csv"
                                 "in figure folder with the name '__figure__NUMBER' "
                                 "with 'NUMBER' being the number of the figure.".format(letter))
            if letter not in self.panel_dimensions:
                raise ValueError("The panel {} was not found in the csv".format(letter))
            panel_dimension = self.panel_dimensions[letter]
            if x is None:
                x = panel_dimension["x0"]
            if y is None:
                y = panel_dimension["y0"]
            if width is None:
                width = panel_dimension["width"]
            if height is None:
                height = panel_dimension["height"]

        self.max_height = max(self.max_height, y + height)

        #automatically choose the panel letter after the highest used panel letter
        #highest = letter latest in the alphabet
        #last letter that can be used is Z - don't think you will ever need more panels than that.
        #if so could use multi-letter panel names. Not implemented yet though.
        if letter is None:
            letter = self._get_next_panel_letter()

        if self.panel_letters_to_show is not None:
            if letter not in self.panel_letters_to_show:
                self.current_panel = None
                return None

        panel_file_paths = self._get_all_panel_files(letter)

        all_panel_imgs = []
        panel_pptxs = []
        for panel_file_path in panel_file_paths:
            if self._file_has_allowed_extension(panel_file_path, [".tif",".jpg", ".png",".gif"]):
                all_panel_imgs.append(io.imread(panel_file_path))
            if self._file_has_allowed_extension(panel_file_path, [".pptx"]):
                file_name = os.path.basename(panel_file_path)
                if not file_name.startswith("~$"):
                    panel_pptxs.append(pptx.Presentation(panel_file_path))

        #load data
        data = []
        for panel_file_path in panel_file_paths:
            file_name = os.path.basename(panel_file_path)
            if file_name.find(".csv") != -1:
                data.append(Figure._open_csv_with_unknown_seperator(panel_file_path))
            if file_name.find(".feather") != -1:
                data.append(pd.read_feather(panel_file_path))
        if len(data) == 0:
            data = None
        else:
            data = pd.concat(data)

        #for videos set the default to center aligned
        # (for hor and vert)
        if self.video:
            if "hor_alignment" not in kwargs:
                kwargs["hor_alignment"] = "center"
            if "vert_alignment" not in kwargs:
                kwargs["vert_alignment"] = "center"

        self.current_panel = FigurePanel(self, self.fig,
                                         self.fig_width_available,
                                         self.fig_height_available,
                                         self.padding,
                                         panel_file_paths, all_panel_imgs,
                                         panel_pptxs, data,
                                         letter, y, height, x, width,
                                         padding=padding,
                                         letter_fontsize=self.letter_fontsize,
                                         size_factor=self.size_factor,
                                         font_size = self.font_size,
                                         video=self.video,
                                         show_letter = self.show_panel_letters,
                                         **kwargs)
        self.all_panels[letter] = self.current_panel

        return self.current_panel

    @staticmethod
    def _open_csv_with_unknown_seperator(csv_file, header="infer"):
        seps = [";", ",", "\t"]
        for sep in seps:
            data = pd.read_csv(csv_file, sep=sep, header=header)
            if len(data.columns) > 1:
                break
        return data

    def edit_this_panel(self, coord_decimals=2, color="white",
                        change_cropping=True,
                       include_all_labels=False, arrow_props=None,
                        plot_row_col_pos_of_cropping=False,
                        get_text_pos_as_abs_data_coords=True, **kwargs
                        ):
        """
        Open editor window to allow adding text, arrows, zoom rectangles
        and cropping to panel images. This will stop plotting further panels.

        :param coord_decimals: For printing code for generating objects
                                number of decimals plotted
                                for each number (e.g. coordinates, width etc)
        :param color: Standard color used for added elements.
        :param change_cropping: Whether you want to change cropping. If True
                                no cropping will be done. Instead the region
                                that would have been cropped will be a rectangle
                                which you can change.
        :param include_all_labels: Whether all labels on an image should be
                                    available to change (including channel
                                    names on the image etc). Changing these
                                    labels will result in code printed
                                    out that uses a different function to
                                    add the label, then the function that was
                                    used initially.
        :param arrow_props: dict with arrow parameters as keys and values in pt
                            possible parameters: width, head_width, head_length.
                            Arrows added in the GUI will be added using these
                            properties.
        :param plot_row_col_pos_of_cropping: Whether to plot row and column
                                            position for code to add cropping
                                            images= information will always be
                                            plotted regardless
        :param get_text_pos_as_abs_data_coords: Whether the text position
                                                    when the code for adding is
                                                    is plotted should be as
                                                    absolute data coordinates
                                                    which means that they will
                                                    be on the same position in
                                                    the data, regardless of
                                                    zoom etc. - this means
                                                    that it might not show up in
                                                    a zoom image. Otherwise, the
                                                    position is in relative
                                                    position in the axis
                                                    (e.g. top left of axis)
        """
        panel_to_edit = self.all_panels[self.panel_to_edit]

        if hasattr(panel_to_edit, "pos_to_pre_identity_map"):
            # panel with data plots do not have the attribute
            # and does not have placeholder images
            panel_to_edit._remove_placeholder_images()

        app = QtWidgets.QApplication(sys.argv)
        self.change_cropping = change_cropping
        main = FigureEditorGUI(panel_to_edit, font_size=self.font_size,
                               coord_decimals=coord_decimals, color=color,
                               include_all_labels=include_all_labels,
                               arrow_props=arrow_props,
                               change_cropping=change_cropping,
                               plot_row_col_pos_of_cropping=
                               plot_row_col_pos_of_cropping,
                               get_text_pos_as_abs_data_coords=
                               get_text_pos_as_abs_data_coords,
                               **kwargs)
        main.show()
        sys.exit(app.exec_())


    def relabel_panels(self, relabel_dict):
        """
        Function to relabel all files with a certain panel letter for
        another panel letter
        Be careful to not execute it more than once, otherwise it will
        obviously be mixed up.

        :param relabel_dict: dict in which the key is the origin label
                              and the value is the target label
        """
        for target, source in relabel_dict.items():
            for file_name in os.listdir(self.folder):
                panel_string_to_match = self.panel_str + str(target)
                new_panel_string = self.panel_str + str(source)

                new_file_name = file_name.replace(panel_string_to_match, new_panel_string)
                source_file = os.path.join(self.folder, file_name)
                target_file = os.path.join(self.folder, new_file_name)
                shutil.move(source_file, target_file)

    def save(self,file_format = None):
        """
        Save entire figure object as figure/image file.

        :param file_format: Any file_format that is allowed for the matplotlib 
            safefig function (e.g. "png", "jpg", "tiff"). 
            But if the format differs 
            from the file_format defined when creating the Figure object and
            if one of the file formats is pdf or svg and the other is not,
            then .rescale_font_size will lead to problems for some 
            illustrations with text added in powerpoint since for .pdf files
            a padding needs to be applied around the image to prevent cutoff of
            edges.
        """
        #remove all placeholder images in figure_panel

        if self.panel_to_edit is not None:
            if self.panel_to_edit in self.all_panels.keys():
                self.edit_this_panel(**self.panel_edit_kwargs)

        for figure_panel in self.all_panels.values():
            if hasattr(figure_panel, "pos_to_pre_identity_map"):
                #panel with data plots do not have the attribute
                #and does not have placeholder images
                figure_panel._remove_placeholder_images()

        #temp fix, delete after checking below
        plt.style.use("classic")
        sb.set_style("whitegrid")
        
        if file_format is None:
            file_format = self.file_format

        figure_path = os.path.join(self.folder, 
                                   self.name+str(self.number)+"."+file_format)


        #define borders of bbox to save figure
        fig_size = self.fig.get_size_inches()

        actual_height_figure = self.max_height * self.fig_height_available * fig_size[1]

        #tried adjusting the bbox, but didn't work
        #now getting the bbox_inches via matplotlib method
        #and then only using the y values of it

        #MATPLOTLIB METHOD TO GET BBOX_INCHES FOLLOWS:
        canvas = self.fig.canvas._get_output_canvas(None, file_format)
        print_method = getattr(canvas, 'print_%s' % file_format)

        renderer = backend_bases._get_renderer(
            self.fig,
            functools.partial(
                print_method, orientation="portrait")
        )
        ctx = (renderer._draw_disabled()
               if hasattr(renderer, '_draw_disabled')
               else suppress())
        with ctx:
            self.fig.draw(renderer)

        bbox_inches = self.fig.get_tightbbox(
            renderer)#, bbox_extra_artists=bbox_extra_artists)

        x_min = 0
        x_max = fig_size[0]
        # y_min = actual_height_figure#fig_size[1] - actual_height_figure/2 - self.padding[0] * 3
        # y_max = fig_size[1] + actual_height_figure/2#fig_size[1] + actual_height_figure/2 - self.padding[0] #fig_size[1]#max(np.abs(fig_size[1] - actual_height_figure),actual_height_figure)


        
        bbox_inches = Bbox([[x_min, bbox_inches.y0 - self.padding[1]], 
                            [x_max, bbox_inches.y1 + self.padding[1] ]])
        
        kwargs = {}
        if figure_path.endswith(".pdf"):
            kwargs["resolution"] = self.dpi
        else:
            kwargs["dpi"] = self.dpi
        self.fig.savefig(figure_path,
                         facecolor=self.fig.get_facecolor(),
                         bbox_inches=bbox_inches, pad_inches=0,
                         **kwargs#self.padding[0]
                         # bbox_inches=Bbox([[x_min, y_min],[x_max,y_max]])
                         )


    def get_representative_data_from_multiple_panels_from_scratch(self,
                                                                  panel_letters,
                                                                  unit_columns,
                                                                  group_columns,
                                                                  column_suffix =
                                                                  "___d___",
                                                                  merge_suffixes=None,
                                                                  nb_vals_to_show=20):
        """
        Get representative data matching data from multiple panels best.
        Also works if representative data for panels was not calculated already.

        Get list of units (cells etc) that are closest to average of data.
        Data from one unit is in a single image, therefore cannot be separated
        the function will rank units
        than regarding their difference to the mean.
        If you want a representative neuron but did measure neurites,
        a unit should be a neuron but the function will account the difference
        from the mean of all measured neurites.
        It will weigh larger differences from the mean more
        (squared difference of mean).

        :param panel_letters: list of strings of panel letters,
                                capitalization matters
        :param unit_columns: list of columns which uniquely identify one "unit".
                            (e.g. for a neurite it could be
                            ["date", "neuron", "neurite"]).
        :param group_columns: List of columns which uniquely identify one group.
                                Representative datapoints should be identified
                                separately for each group.
        :param column_suffix: Suffix to use for newly calculated columns used
                                for ranking datapointsthis
                                should be something that is not present
                                in any current column name.
        :param merge_suffixes: Suffixes of columns for merging data, needed
                                since merging of data with same columns
                                must lead to columns with new names
                                default (if None) is: ["___xXx___", "___yYy___"]
        :param nb_vals_to_show: Number of datapoints to show in the list

        """

        panels_to_use = []
        for panel_letter in panel_letters:
            if panel_letter not in self.all_panels:
                raise ValueError("For getting representative data all panels"
                                 "supplied must have been defined before."
                                 f"However, panel {panel_letter} is not defined.")
            panels_to_use.append(self.all_panels[panel_letter])

        # get unit columns to use as for each unit column
        # the first in the iterable
        # or if it is not an iterable just the string directly
        unit_columns_to_use = [unit_column[0]
                               if type(unit_column) in [tuple, list]
                               else unit_column
                               for unit_column in unit_columns]
        if merge_suffixes is None:
            merge_suffixes = ["___xXx___", "___yYy___"]

        all_representative_data = pd.DataFrame(columns=unit_columns_to_use)
        for panel_to_use in panels_to_use:
            grouped_data_panel = panel_to_use.grouped_data.mean()
            data_columns = grouped_data_panel.columns
            unit_columns_for_panel = []
            for unit_column_list in unit_columns:
                if type(unit_column_list) not in [tuple, list]:
                    unit_columns_for_panel. append(unit_column_list)
                    continue
                for one_unit_column in unit_column_list:
                    if one_unit_column in data_columns:
                        unit_columns_for_panel. append(one_unit_column)
                        continue

            panel_to_use.get_representative_data(unit_columns=
                                                 unit_columns_for_panel,
                                                 print_results=False,
                                                 column_suffix=column_suffix)

            representative_data = panel_to_use.representative_data.reset_index()
            representative_data_columns = representative_data.columns
            # since columns with the same value might have diffeent names
            # in different data panels, allow unit columns supplied as
            # multiple possible column names in a list
            # for each data use the column name which is used there
            # by adding a new data column with the first name in the list
            # of possible ones
            for unit_column_list in unit_columns:
                if type(unit_column_list) not in [tuple, list]:
                    continue
                # only change data if the first unit column is not in
                # representative data
                if unit_column_list[0] in representative_data_columns:
                    continue
                for one_unit_column in unit_column_list[1:]:
                    if one_unit_column in representative_data_columns:
                        representative_data[unit_column_list[0]] = representative_data[one_unit_column]

            # get representative data for all supplied panels
            # and merge based on unit columns
            # also make unique suffixes which should not be found in any column
            # names
            all_representative_data = all_representative_data.merge(representative_data,
                                                                    how="outer",
                                                                    on=unit_columns_to_use,
                                                                     suffixes=merge_suffixes)

            # get all column names and check which columns are doubled
            # which means they are the same except a _letter addition
            # (e.g. _x or _x_y)
            # for those columns add their values together
            for column in all_representative_data.columns:
                # column might have been removed already
                # therefore check if it is still present
                if column not in all_representative_data.columns:
                    continue
                merged_column_found = False
                for merge_suffix_nb, merge_suffix in enumerate(merge_suffixes):
                    if column.find(merge_suffix) != -1:
                        suffix_not_in_column = merge_suffixes[merge_suffix_nb - 1]
                        base_column = column.replace(merge_suffix, "")
                        other_column = base_column + suffix_not_in_column
                        merged_column_found = True
                        break
                if not merged_column_found:
                    continue

                # only combine numeric columns, for other values use the first
                # one and remove the other
                if pd.api.types.is_numeric_dtype(all_representative_data[column]):
                    combined_column = (all_representative_data[column].fillna(0) +
                                       all_representative_data[other_column].fillna(0))
                else:
                    combined_column = all_representative_data[column]
                all_representative_data[base_column] = combined_column
                all_representative_data.drop(column, axis=1,
                                         inplace=True)
                all_representative_data.drop(other_column, axis=1,
                                         inplace=True)

        # get columns that should be shown
        # as all unit columns
        columns_to_be_shown = unit_columns_to_use
        columns_to_be_shown.append("d_mean")
        columns_to_be_shown.append("nb_measurements")
        for new_column in all_representative_data.columns:
            if new_column.find(column_suffix) != -1:
                columns_to_be_shown.append(new_column)

        if len(group_columns) > 0:
            all_groups = all_representative_data[group_columns].drop_duplicates()
            print(all_groups)
            all_representative_data.set_index(group_columns, inplace=True)
            pd.set_option('display.max_columns', 500)
            pd.set_option('display.width', 5000)
            group_data_list = []
            for group in all_groups.values:
                group_data_list.append(all_representative_data.loc[tuple(group)])
        else:
            group_data_list = [all_representative_data]

        for group_data in group_data_list:
            sorted_group_data = group_data.sort_values(by=["nb_measurements",
                                                           "d_mean"],
                                                       ascending=[False,
                                                                  True])
            data_to_print = sorted_group_data[columns_to_be_shown]
            print(data_to_print.head(nb_vals_to_show))


    def _add_all_figure_panel_functions(self):
        #add copies of all figure_panel functions here
        #to allow function calls on the figure automatically being done on current_panel
        all_functions = [module_function
                         for module_function in getmembers(FigurePanel)
                         if isfunction(module_function[1])]

        for one_function in all_functions:
            function_name = one_function[0]
            #check if function is not a private function
            if not function_name.startswith("_"):
                function_obj = one_function[1]
                setattr(self, function_name,
                        self._execute_function_on_current_panel(function_name))

    def _execute_function_on_current_panel(self, function_name, *args, **kwargs):
        def wrapper(*args, **kwargs):
            # if the current panel should not be shown
            # (e.g. not included in panel letter list in function "show_panels")
            # do not execute functions for it
            if self.current_panel is None:
                return
            module_function = getattr(self.current_panel,function_name)
            #if figure is for videos
            #dont execute function if it does not contain "vid_" in the function_name???
            #AFTER show_images was called
            #show functions that trigger recording all functions afterwards:
            show_functions = []
            show_functions.append("show_images")
            show_functions.append("show_data")
            if ((function_name in show_functions) & self.video):
                self.current_panel.show_function_called = True
            if ((function_name in show_functions)  &
                (self.current_panel.animate_panel == True)):
                # self.current_panel.show_function_called = True
                if "frames" not in kwargs:

                    all_nb_frames = []
                    for file_path in self.current_panel.panel_file_paths:
                        # update video frames for figure panel
                        # so that when no frames are supplied,
                        # the maximum number of frames is displayed in movie
                        data_dict, img_width, img_height = self.current_panel._get_image_properties(
                            file_path)
                        if "frames" in data_dict:
                            all_nb_frames.append(int(data_dict["frames"]))
                        else:
                            all_nb_frames.append((data_dict["slices"]))
                    kwargs["frames"] = list(range(min(all_nb_frames)))
                self.current_panel.video_frames = kwargs["frames"]
                self.all_video_frames = kwargs["frames"]
            if ((function_name.find("vid_") == -1) &
                    (self.current_panel.show_function_called)):
                #instead save the function with arguments in panel
                #execute these functions later for each iteration of animate
                self.current_panel.functions_for_video.append((function_name,
                                                               module_function,
                                                               args, kwargs))
            else:
                module_function(*args, **kwargs)

        return wrapper


    def save_video(self, fps = 10, bitrate = -1,
                   title_page_text = "",
                   duration_title_page=3,
                   repeats = 1,
                   frames_to_show_longer=None,
                   seconds_to_show_frames=1,
                   min_final_fps=10):
        """
        Save entire figure object as video.

        :param fps: Data frames per second of video.
        :param bitrate: Bitrate of video. -1 means matplotlib will find the
                        best bitrate automatically. For non-grey movies
                        matplotlib does not find great bitrates. Choose a high
                        bitrate manually.
        :param title_page_text: String for the text on the title page of the
                                video (can also include linebreaks as "\\n")
        :param duration_title_page: Seconds the title page will be shown
        :param repeats: Number of times the data part of the movie is repeated
                        (helpful for movies in publications so that the title
                        is not replayed and that the movie is replayed without
                        the user needing to click on the play button)
        :param frames_to_show_longer: List of numbers; Which frames to show
                                    longer than just one videoframe
        :param seconds_to_show_frames: how many seconds to show
                                        frames_to_show_longer
        :param min_final_fps: Minimum final fps that the video will be saved in.
                                is important to be >10 for the title frame
                                to prevent a black frame at the beginning
                                (for fps=2 of 2s!)
        """


        if self.name == "":
            self.name = "Video"

        # self.fig.set_size_inches(self.fig.get_size_inches()[0], self.fig.get_size_inches()[1] * 2, forward=True)

        nb_frames = 0
        self.title_page_text = title_page_text
        self.fps = fps
        self.duration_title_page = duration_title_page
        self.title_page = None

        video_name = self.name + "S" + str(self.number)
        self.video_file_name_details = ""

        if self.video_batch_mode:
            all_nb_files = []
            for figure_panel in self.all_panels.values():
                all_nb_files.append(len(figure_panel.panel_file_paths_orig))
            max_nb_files = max(all_nb_files)
            all_batches = list(range(max_nb_files))
        else:
            all_batches = [None]
            if self.video_name_from_folder:
                self.video_file_name_details = os.path.basename(os.path.dirname(self.folder))

        self.video_folder = self.folder


        for batch_nb in all_batches:

            self.tmp_video_folder = os.path.join(self.folder,
                                                 video_name + "_tmp")
            if not os.path.exists(self.tmp_video_folder):
                os.mkdir(self.tmp_video_folder)

            all_videos = []
            #if there should be a title page with text
            #increase the number of frames
            #by the duration multiplied by fps
            if self.title_page_text != "":
                nb_frames_title_page = int(self.duration_title_page * self.fps)
                title_video_path = self._create_video(self._animate_title_page,
                                                     nb_frames_title_page,
                                                     bitrate = bitrate,
                                                     name = "title")
                all_videos.append(editor.VideoFileClip(title_video_path))
                self.title_page.remove()

            for figure_panel in self.all_panels.values():
                #length of video_frames is the number of timepoints available
                nb_frames = max(nb_frames, len(figure_panel.video_frames))

            #if frames should be shown longer
            #add number of frames to use
            additional_videoframes = 0
            if type(frames_to_show_longer) != type(None):
                #sort to have ascending frames
                frames_to_show_longer.sort()
                for frame_to_show_longer in frames_to_show_longer:
                    additional_videoframes = int(seconds_to_show_frames * fps)
                    #round additional videoframes to ints
                    additional_videoframes = int(additional_videoframes)
                    #add one frame less since there is already one videoframe
                    # of the frame
                    nb_frames += additional_videoframes - 1

            #give paramters to animate_video function
            animate_data = functools.partial(self._animate_video,
                                             frames_to_show_longer,
                                             additional_videoframes,
                                             batch_nb=batch_nb)

            data_video_path = self._create_video(animate_data,
                                                nb_frames,
                                                bitrate=bitrate)

            all_videos.append(editor.VideoFileClip(data_video_path))

            #copy video file as often as there are repeats - 1
            for repeat in range(1, repeats):
                new_data_video_path= data_video_path.replace(".mp4", "_" + str(repeat) + ".mp4")
                shutil.copyfile(data_video_path, new_data_video_path)
                all_videos.append(editor.VideoFileClip(new_data_video_path))

            complete_video = editor.concatenate_videoclips(all_videos)
            video_file_name = video_name
            if batch_nb is not None:
                video_file_name += "_"+str(batch_nb)
            video_file_name += self.video_file_name_details
            video_file_name += ".mp4"
            video_path = os.path.join(self.video_folder, video_file_name)

            #set bitrate to None (automatically determine)
            #for moviepy
            if (bitrate == -1) | (bitrate is None):
                bitrate = None
            else:
                bitrate = str(bitrate)

            # Manual  workaround for floating point error in the package "moviepy".
            # Fix by Aidas Liaudanskas (https://github.com/Zulko/moviepy/issues/646)
            try:
                complete_video.write_videofile(video_path,
                                               fps=max(self.fps,min_final_fps),
                                               remove_temp=True, bitrate=bitrate)
            except IndexError:
                print("\n\nCRITICAL WARNING: "
                      "The combination of repeats and fps leads to a "
                      "floating point error in the 'moviepy' package. "
                      "\nTHE LAST FRAME OF THE MOVIE WAS REMOVED to still save the "
                      "movie. If the last frame should not be removed, change the "
                      "fps or the number of repeats. Even very small changes are "
                      "usually sufficient.\n")
                # Short by one frame, so get rid on the last frame:
                complete_video = complete_video.subclip(
                    t_end=(complete_video.duration - 1.0 / complete_video.fps))
                complete_video.write_videofile(video_path,
                                               fps=max(self.fps,min_final_fps),
                                               remove_temp=True, bitrate=bitrate)


            shutil.rmtree(self.tmp_video_folder)
            # reset video file name details and the video folder
            self.video_folder = self.folder

    def _create_video(self, animate_function, nb_frames,
                     bitrate=-1, name=""):

        #get maximum number of frames by looking at video_frames parameter of each figure_panel
        #what is init_func doing actually?
        video = animation.FuncAnimation(self.fig, animate_function,
                                        # init_func=functools.partial(animate_function,
                                        #                             0),
                                        frames=nb_frames, repeat=True)
        video_writer = animation.writers['ffmpeg']
        #let matplotlib determine the best bitrate automatically with bitrate=-1
        video_writer = video_writer(fps=self.fps, metadata=dict(artist="Me"),
                                    bitrate=bitrate) #codec="libx264",#

        if name != "":
            name = "_" + name
        video_path = os.path.join(self.tmp_video_folder,
                                  str(self.name) + "S" +
                                  str(self.number) + name + ".mp4")

        video.save(video_path, writer=video_writer)


        return video_path


    def _animate_title_page(self, frame):
        # print(frame)
        if frame == 0:
            #first remove old title page
            # before adding new one
            if self.title_page != None:
                self.title_page.remove()
            #add a title page that fills the entire figure
            self.title_page = self.fig.add_axes([0, 0, 1, 1])
            self.title_page.text(0.5, 0.5, self.title_page_text,
                            horizontalalignment='center',
                            verticalalignment='center',
                            transform=self.title_page.transAxes)
            self.title_page.set_axis_off()



    def _animate_video(self,
                   frames_to_show_longer,
                   additional_videoframes,
                    frame, batch_nb = None):
        if type(frames_to_show_longer) != type(None):
            for frame_to_show_longer in frames_to_show_longer:
                #if the current frame is larger than
                #the frame to show longer but smaller than
                #the frame plus the amount of videoframes it should be shown
                #then set frame as frame to show longer
                if ((frame >= frame_to_show_longer) &
                        (frame < (frame_to_show_longer + additional_videoframes))):
                    frame = frame_to_show_longer
                elif frame >= (frame_to_show_longer + additional_videoframes):
                    frame -= (additional_videoframes - 1)

        #start animation of video
        print("Rendering frame {}".format(frame))
        #go through each added figure_panel
        for figure_panel in self.all_panels.values():
            # even for not animated panels the first timeframe
            # should be shown
            if (not figure_panel.animate_panel) & (frame > 0):
                continue

            if batch_nb is not None:
                if len(figure_panel.panel_file_paths_orig) > batch_nb:
                    batch_file_path = figure_panel.panel_file_paths_orig[
                        batch_nb]
                    figure_panel.panel_file_paths = [batch_file_path]
                    figure_panel.all_panel_imgs = [
                        figure_panel.all_panel_imgs_orig[batch_nb]]
                    if self.save_batch_in_sub_folder:
                        self.video_folder = os.path.dirname(batch_file_path)
                    if self.video_name_from_file:
                        batch_file_name = os.path.basename(batch_file_path)
                        # remove first part of the batch file name, that
                        # contains the panel information (e.g. "panelA")
                        batch_file_name = batch_file_name.split("_")[1:]
                        batch_file_name = "_".join(batch_file_name)
                        batch_file_name = batch_file_name.split(".")[:-1]
                        batch_file_name = ".".join(batch_file_name)
                        self.video_file_name_details = "_"+batch_file_name
                    elif self.video_name_from_folder:
                        batch_file_folder = os.path.dirname(batch_file_path)
                        batch_file_folder = os.path.basename(batch_file_folder)
                        self.video_file_name_details = "_"+batch_file_folder
                else:
                    figure_panel.panel_file_paths = [figure_panel.panel_file_paths_orig[0]]
                    figure_panel.all_panel_imgs = [figure_panel.all_panel_imgs_orig[0]]

            figure_panel.data = figure_panel.data_orig
            #delete all labels in self.label_axs[site] (for each site)
            for label_site in figure_panel.label_axs:
                for label_ax in figure_panel.label_axs[label_site]:
                    label_ax.remove()
            #delete all plots in self.all_axs
            for img_ax in figure_panel.all_axs.values():
                if type(img_ax.figure) != type(None):
                    img_ax.remove()

            # for colorbar_ax in figure_panel.all_colorbars.values():
                # if type(colorbar_ax.ax.figure) != type(None):
                #     colorbar_ax.remove()

            figure_panel.cropped_positions = {}

            #go through and execute each function in function_for_video list
            for function_name, function, args, kwargs in figure_panel.functions_for_video:
                # print("FUNCTION FOR VIDEO: ", function_name)
                #for show_image modify the "frames" parameter
                if function_name == "show_images":
                    if "frames" in kwargs:
                        #frames should be the frame'th option in video_frames of the figure_panel
                        kwargs["frames"] = [figure_panel.video_frames[frame]]
                if function_name == "show_data":
                    kwargs["video_frame"] = self.all_video_frames[frame]
                function(*args, **kwargs)

        if self.panel_to_edit is not None:
            if self.panel_to_edit in self.all_panels.keys():
                self.edit_this_panel(**self.panel_edit_kwargs)