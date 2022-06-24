# -*- coding: utf-8 -*-
# from matplotlib.text import Text
import matplotlib.pyplot as plt
from matplotlib import lines
import matplotlib.transforms as mtransforms
from matplotlib import ticker as mplticker
from matplotlib.font_manager import FontProperties
import numpy as np
import pandas as pd
import seaborn as sns
from seaborn.utils import remove_na
import scikit_posthocs as posthocs
from scipy import stats
import statsmodels
import copy
import matplotlib as mpl
from matplotlib.patches import PathPatch
import scipy
import functools
import itertools

from scipy import stats

DEFAULT = object()

def create_column_subplot(outer_border, label, grid_columns=1, column=0, column_span=1):
    fig = plt.gcf()
    # plot data in one row, therefore height equals total height available
    ax = fig.add_subplot(label=label)
    width_available = outer_border[1] - outer_border[0]
    height_available = outer_border[3] - outer_border[2]
    width_per_plot = width_available / grid_columns

    left = outer_border[0] + (column * width_per_plot)
    # col_span equals number of boxes in current plot
    width = width_per_plot * column_span
    bottom = outer_border[2]

    ax.set_position( [left, bottom, width, height_available] )

    return ax


def adjust_figure_aesthetics(background_color):
    pass
    # sns.set_style("darkgrid",{
    #     'axes.facecolor':background_color,
    #     'figure.facecolor':'white'})

def pval_annotation_text(pvals, pvalue_thresholds):
    single_value = False
    if type(pvals) is np.array:
        pvals = pvals
    else:
        pvals = np.array([pvals])
        single_value = True

    # Sort the threshold array
    pvalue_thresholds = pd.DataFrame(pvalue_thresholds).sort_values(by=0,
                                                                    ascending=False).values
    x_annot = pd.Series(["" for _ in range(len(pvals))])
    for i in range(len(pvalue_thresholds)):
        if i < len(pvalue_thresholds)-1:
            # p value must be smaller than the threshold
            condition = (pvals < pvalue_thresholds[i][0]) & (pvalue_thresholds[i+1][0] <= pvals)
            x_annot[condition] = pvalue_thresholds[i][1]
        else:
            condition = pvals < pvalue_thresholds[i][0]
            x_annot[condition] = pvalue_thresholds[i][1]

    return x_annot if not single_value else x_annot.iloc[0]


def simple_text(pval, pvalue_format, pvalue_thresholds, test_short_name=None):
    """
    Generates simple text for test name and pvalue
    :param pval: pvalue
    :param pvalue_format: format string for pvalue
    :param test_short_name: Short name of test to show
    :param pvalue_thresholds: String to display per pvalue range
    :return: simple annotation
    """
    # Sort thresholds
    thresholds = sorted(pvalue_thresholds, key=lambda x: x[0])

    # Test name if passed
    text = test_short_name and test_short_name + " " or ""

    for threshold in thresholds:
        if pval < threshold[0]:
            pval_text = "p ≤ {}".format(threshold[1])
            break
    else:
        pval_text = "p = {}".format(pvalue_format).format(pval)

    return text + pval_text



def validate_arguments(perform_stat_test,test,pvalues,test_short_name,
                       box_pairs,loc,text_format,text_annot_custom):

    if (not box_pairs) & (perform_stat_test):
        print("Warning:No box pair was added - all groups will be compared.")
        box_pairs = []
    if perform_stat_test:
        if test is None:
            raise ValueError("If `perform_stat_test` is True, `test` must be specified.")
        if pvalues is not None or test_short_name is not None:
            raise ValueError("If `perform_stat_test` is True, custom `pvalues` "
                             "or `test_short_name` must be `None`.")
        valid_list = ['t-test_ind', 't-test_welch', 't-test_paired',
                      'Mann-Whitney', 'Mann-Whitney-gt', 'Mann-Whitney-ls',
                      'Levene', 'Wilcoxon', 'Kruskal', "Dunn"]
        if test not in valid_list:
            raise ValueError("test value should be one of the following: {}."
                             .format(', '.join(valid_list)))

    if text_annot_custom is not None and len(text_annot_custom) != len(box_pairs):
        raise ValueError("`text_annot_custom` should be of same length as `box_pairs`.")

    valid_list = ['inside', 'outside']
    if loc not in valid_list:
        raise ValueError("loc value should be one of the following: {}."
                         .format(', '.join(valid_list)))
    valid_list = ['full', 'simple', 'star']
    if text_format not in valid_list:
        raise ValueError("text_format value should be one of the following: {}."
                         .format(', '.join(valid_list)))

    return box_pairs


def set_pval_arguments(text_format,verbose,pvalue_thresholds,pvalue_format_string):


    # Set default values if necessary
    if pvalue_format_string is DEFAULT:
        pvalue_format_string = '{:.3e}'
        simple_format_string = '{:.2f}'
    else:
        simple_format_string = pvalue_format_string

    if pvalue_thresholds is DEFAULT:
        if text_format == "star":
            # [1e-4, "****"] removed
            pvalue_thresholds = [[1e-3, "***"],
                                 [1e-2, "**"], [0.05, "*"], [1, "ns"]]
        else:
            pvalue_thresholds = [[1e-5, "1e-5"], [1e-4, "1e-4"],
                                 [1e-3, "0.001"], [1e-2, "0.01"]]


    if verbose and text_format == 'star':
        print("p-value annotation legend:")
        pvalue_thresholds = pd.DataFrame(pvalue_thresholds).sort_values(by=0, ascending=False).values
        for i in range(0, len(pvalue_thresholds)):
            if i < len(pvalue_thresholds)-1:
                print('{}: {:.2e} < p <= {:.2e}'.format(pvalue_thresholds[i][1],
                                                        pvalue_thresholds[i+1][0],
                                                        pvalue_thresholds[i][0]))
            else:
                print('{}: p <= {:.2e}'.format(pvalue_thresholds[i][1], pvalue_thresholds[i][0]))
        print()

    return pvalue_thresholds, pvalue_format_string, simple_format_string

def get_all_vals_from_order_in_data(data, column, order):
        # remove hue vals from x_order that are not present in current group
        if column != "no_"+column+"_defined":
            new_order = []
            vals = data[column].drop_duplicates().dropna()
            for val in order:
                if val in vals.values:
                    new_order.append(val)
        else:
            new_order = order
        return new_order

def process_col_and_hue(data, col, x, hue, x_order, col_order, hue_order):
    if col == None:
        data["no_col_defined"] = "_-_-None-_-_"
        col = "no_col_defined"

    if hue == None:
        data["no_hue_defined"] = "_-_-None-_-_"
        hue = "no_hue_defined"

    if len(hue_order) == 0:
        hue_order = list(data[hue].drop_duplicates())

    # change hue value to None if none was given to allow colors being used for other things than hue
    if hue == "no_hue_defined":
        plot_hue = None
        hue_order = []
    else:
        plot_hue = hue

    all_cols = data[col].drop_duplicates()
    all_cols = all_cols.sort_values()

    if len(col_order) == 0:
        col_order = list(all_cols)

    total_nb_cols = 0
    for col_val in col_order:
        if col_val not in all_cols.values:
            raise Exception("One group in group_order not present in data:"+str(col_val))

    total_nb_cols = get_nb_of_boxes(data, x, x_order, hue, hue_order, col, col_order,)

    return col_order,col,hue,hue_order,plot_hue,total_nb_cols

def get_nb_of_boxes(data, x, x_order, hue=None, hue_order=None, col = None, col_order=None):
    """
    Get nb of all boxes in all plots considering column separation, x values and hue.
    If one of the values is None
    """
    if col == None:
        col_order = [None]
    total_nb_cols = 0
    for col_val in col_order:
        if col_val != None:
            col_data = data.loc[data[col] == col_val]
        else:
            col_data = data
        x_vals = get_all_vals_from_order_in_data(col_data, x, x_order)
        if hue != "no_hue_defined":
            for x_val in x_vals:
                x_data = col_data.loc[col_data[x] == x_val]
                hue_vals = get_all_vals_from_order_in_data(x_data, hue, hue_order)
                nb_cols = len(hue_vals)
                total_nb_cols += nb_cols
        else:
            nb_cols = len(x_vals)
            total_nb_cols += nb_cols
    return total_nb_cols


def find_x_position_box(box_plotter,box_name):
    if box_plotter.plot_hues is None:
        cat = box_name
        hue_offset = 0
    else:
        cat = box_name[0]
        hue = box_name[1]
        hue_offset = box_plotter.hue_offsets[
            box_plotter.hue_names.index(hue)]
    group_pos = box_plotter.group_names.index(cat)

    box_pos = group_pos + hue_offset
    return box_pos

def find_transformed_x_position_box(box_plotter, box_name,ax,ax_annot):
    """
    box_name can be either a name "cat" or a tuple ("cat", "hue")
    """
    box_pos = find_x_position_box(box_plotter,box_name)

    box_pos = transform=ax.transData.transform([box_pos,0])[0]

    box_pos = transform=ax_annot.transData.inverted().transform([box_pos,0])[0]

    return box_pos

def get_box_data(box_plotter, box_name):
    """
    box_name can be either a name "cat" or a tuple ("cat", "hue")
    Here we really have to duplicate seaborn code, because there is not
    direct access to the box_data in the BoxPlotter class.
    """
    cat = box_plotter.plot_hues is None and box_name or box_name[0]

    index = box_plotter.group_names.index(cat)
    group_data = box_plotter.plot_data[index]

    if box_plotter.plot_hues is None:
        # Draw a single box or a set of boxes
        # with a single level of grouping
        box_data = remove_na(group_data)
    else:
        hue_level = box_name[1]
        hue_mask = box_plotter.plot_hues[index] == hue_level
        box_data = remove_na(group_data[hue_mask])

    return box_data


def extract_cols_from_pairs(box_pairs):
    # if each of the pairs in a box_pair has more than 2 links, the first one is the group
    # isolate the group as one pair list
    pairs_grouped = False
    for box_pair in box_pairs:
        if len(box_pair[0]) == 3:
            pairs_grouped = True
            break

    col_pairs = []
    if pairs_grouped:
        box_pairs_no_col = []
        for box_pair in box_pairs:
            # only dissect
            if len(box_pair[0]) == 3:
                box_pair_no_col = ((box_pair[0][1],box_pair[0][2]),(box_pair[1][1],box_pair[1][2]))
                box_pairs_no_col.append(box_pair_no_col)
                col_pairs.append((box_pair[0][0],box_pair[1][0]))
            else:
                col_pairs.append(box_pair)
                col_pairs.append(())
        box_pairs = box_pairs_no_col

    # if no group_pairs were given, fill the array up with empty lists
    # (same length as box_pairs)
    if len(col_pairs) == 0:
        for i in range(0,len(box_pairs)):
            col_pairs.append(())
    return box_pairs, col_pairs

def transform_ymax(box_plotter,box_name,ax,ax_annot):
    box_data = get_box_data(box_plotter,box_name)
    if len(box_data) == 0:
        ymax = np.nan
    else:
        ymax = np.amax(box_data)
        # ymax = ax.transData.transform([0,ymax])[1]
        # ymax = ax_annot.transData.inverted().transform([0,ymax])[0]
    return ymax

def get_box_names_and_labels(box_plotter):
    group_names = box_plotter.group_names
    hue_names = box_plotter.hue_names

    if box_plotter.plot_hues is None:
        box_names = group_names
        labels = box_names
    else:
        box_names = [(group_name, hue_name) for group_name in group_names for hue_name in hue_names]
        labels = ['{}_{}'.format(group_name, hue_name) for (group_name, hue_name) in box_names]

    return box_names, labels

def complete_box_name(box_name, col_val, hue):
    if type(box_name) == str:
        box_name = [box_name]
    box_name = (col_val, *list(box_name))
    if hue == "no_hue_defined":
        box_name = (*box_name, "_-_-None-_-_")
    else:
        box_name

    return box_name


def build_box_structs_dic(box_plotter,col_val, hue,ax,ax_annot):
    # Build the list of box data structures with the x and ymax positions

    box_names, labels = get_box_names_and_labels(box_plotter)

    complete_box_names = tuple([complete_box_name(box_name, col_val, hue) for box_name in box_names])
    # guarantee that box_names always includeds x and hue (even if no hue is defined)
    # since box_pairs will always include both as well
    box_structs = [{'group':col_val,
                    'box':complete_box_names[i],
                    'label':labels[i],
                    'x':find_transformed_x_position_box(box_plotter, box_names[i],ax,ax_annot),
                    'x_orig':find_x_position_box(box_plotter, box_names[i]),
                    'box_data':get_box_data(box_plotter, box_names[i]),
                    'ymax':transform_ymax(box_plotter,box_names[i],ax,ax_annot)}
                   for i in range(len(box_names))]
    # Sort the box data structures by position along the x axis
    box_structs = sorted(box_structs, key=lambda x: x['x'])
    # Add the index position in the list of boxes along the x axis
    box_structs = [dict(box_struct, xi=i) for i, box_struct in enumerate(box_structs)]
    # Same data structure list with access key by box name
    box_structs_dic = {box_struct['box']:box_struct for box_struct in box_structs}
    return box_structs_dic,complete_box_names,box_structs

def get_axis_tick_labels_overhang(ax, axis):
    """
    Get the overhang of the axis tick labels over the axis area in pixels.
    :param ax: Axes object from matplotlib, current axes with plot
    :param axis: string, "x" or "y"
    """
    fig = plt.gcf()
    # draw figure since otherwise no ticklabels can be retrieved for the y axis
    # don't know why its only necessary for y but not for x for some cases
    # could potentially be specific for videos
    # (thats where the problem was noticed)
    fig.canvas.draw()

    lim_methods = {"x": ax.get_xlim(),
                   "y": ax.get_ylim()}
    tick_label_methods = {"x": ax.get_xticklabels(),
                          "y": ax.get_yticklabels()}
    fig_dimension = {"x": 0,
                      "y": 1}
    renderer = fig.canvas.renderer
    limits = lim_methods[axis]
    max_val = limits[1]
    # get all tick labels for axis
    tick_labels = list(tick_label_methods[axis])
    # reverse list of tick labels to start from the label
    tick_labels.reverse()
    # get highest tick label within axis limits
    for tick_label in tick_labels:
        tick_value = tick_label.get_text()
        # only try to convert tick label to float
        # if the value is not nothing
        if tick_value != "":
            tick_value = float(tick_value)
            if tick_value <= max_val:
                break

    # get bounding box of tick label
    tick_label_box = tick_label.get_tightbbox(renderer)

    # get end of tick label
    tick_end_px = getattr(tick_label_box, axis + "1")

    # .get_position will give the size of the axis without axes labels
    # while .get_tightbbox would give the size with axes labels
    # while for .get_position sizes are in relative figure dimension
    # therefore need to be converted to pixel
    fig_size_px = (fig.get_size_inches() * fig.dpi)[fig_dimension[axis]]
    axis_end_px = getattr(ax.get_position(), axis + "1") * fig_size_px

    tick_label_overhang_px = max(0, tick_end_px - axis_end_px)

    # convert pixel to relative figure dimension
    return tick_label_overhang_px / fig_size_px



def set_offsets(line_offset,loc,line_offset_to_box,yrange):
    if line_offset is None:
        if loc == 'inside':
            line_offset = 0.05
            if line_offset_to_box is None:
                line_offset_to_box = 0.04
        # 'outside', see valid_list
        else:
            line_offset = 0.05
            if line_offset_to_box is None:
                line_offset_to_box = line_offset
    else:
        if loc == 'inside':
            if line_offset_to_box is None:
                line_offset_to_box = 0.04
        elif loc == 'outside':
            line_offset_to_box = line_offset
    y_offset = line_offset * yrange
    y_offset_to_box = line_offset_to_box * yrange
    return line_offset, loc, line_offset_to_box, yrange,y_offset,y_offset_to_box


def construct_all_box_pairs(data,col,col_order,x,x_order,hue,hue_order):
    # combine each box with every other box
    all_box_pairs = []
    for col_val1 in col_order:
        col_data1 = data.loc[data[col] == col_val1]
        x_vals1 = col_data1[x].drop_duplicates()
        for x_val1 in x_vals1:
            if (x_val1 in x_order) | (x_val1 == "_-_-None-_-_"):
                x_data1 = col_data1.loc[col_data1[x] == x_val1]
                hue_vals1 = x_data1[hue].drop_duplicates()
                for hue_val1 in hue_vals1:
                    if (hue_val1 in hue_order) | (hue_val1 == "_-_-None-_-_"):
                        for col_val2 in col_order:
                            col_data2 = data.loc[data[col] == col_val2]
                            x_vals2 = col_data2[x].drop_duplicates()
                            for x_val2 in x_vals2:
                                if (x_val2 in x_order) | (x_val2 == "_-_-None-_-_"):
                                    x_data2 = col_data2.loc[col_data2[x] == x_val2]
                                    hue_vals2 = x_data2[hue].drop_duplicates()
                                    for hue_val2 in hue_vals2:
                                        if (hue_val2 in hue_order) | (hue_val2 == "_-_-None-_-_"):
                                            col_different = (col_val1 != col_val2)
                                            x_different = (x_val1 != x_val2)
                                            hue_different = (hue_val1 != hue_val2)
                                            if col_different | x_different | hue_different:
                                                new_box_pair = [(col_val1,x_val1,hue_val1),(col_val2,x_val2,hue_val2)]
                                                # check if pair was already added
                                                box_pair_exists = False
                                                for box_pair in all_box_pairs:
                                                    if (new_box_pair[0] in box_pair) & (new_box_pair[1] in box_pair):
                                                        box_pair_exists = True
                                                        break
                                                if not box_pair_exists:
                                                    all_box_pairs.append(new_box_pair)
    return all_box_pairs



def plot_data(ax, x, y, hue, data,
              x_order, hue_order,
              plot_colors, show_data_points,
              line_width, size_factor, plot_type,
              fliersize, show_formula, position_regression_text,
                show_regression_stats,
              figure_panel, swarmplot_point_size,
              bar_plot_dodge, x_range,
              connect_paired_data_points):

    if plot_colors == -1:
        plot_colors = sns.xkcd_palette(["white","grey"])
    fig = plt.gcf()

    meanlineprops = dict(linestyle='-', linewidth=line_width*2, color='black',solid_capstyle="butt")

    labels_to_add = []

    if ((show_data_points | connect_paired_data_points) & ( (plot_type == "box") |
                                                     (plot_type == "bar") |
                                                     (plot_type.lower() == "points"))):
        show_outliers =False
        if hue != None:
            dodge = True
        else:
            dodge = False
        size = swarmplot_point_size * size_factor # * 0.83  # 0.83 is sqrt of 0.7
        swarmplot_line_width = swarmplot_point_size/3.5 * size_factor
        if not show_data_points:
            # if no datapoints should be shown but there should still be
            # connections between grouped datapoints, then datapoints
            # need to be plotted without being visible
            # to be then connected later
            alpha = 0
        else:
            alpha=0.55

        plot = sns.swarmplot(x=x, y=y, hue=hue, data=data, order=x_order, hue_order=hue_order,
                                    dodge=dodge, edgecolor="black", linewidth=swarmplot_line_width, size = size,
                                    alpha=alpha, fc="white")# # fc="none" for empty markers

    else:
        show_outliers= True

    # if hue is defined, bow_width needs to be 0.8 in order to align points with boxplot
    if (hue != None):
        box_width = 0.8
    else:
        box_width = 0.63

    if plot_type == "box":
        # Create the same BoxPlotter object as seaborn's boxplot
        plot = sns.categorical._BoxPlotter(
            x, y, hue, data, x_order, hue_order, orient=None, width=box_width, color=None,
             saturation=1, dodge=True,fliersize=fliersize, linewidth=line_width, palette=plot_colors)

        # set gray of boxplot manually since it is otherwise determined by the colors used in the plotted box_ends
        # this can lead to different grays for different subplots if only a part of the colors are plotted in one of them
        gray = mpl.colors.rgb2hex((0, 0, 0))
        plot.gray = gray

        kwargs = dict(meanprops=meanlineprops,showfliers=show_outliers,showmeans=True,meanline=True)
        kwargs.update(dict(whis=1.5, notch=False))
        plot.plot(ax,kwargs)

    elif plot_type == "bar":
        plot = sns.categorical._BarPlotter(x=x, y=y, hue=hue, data=data, order=x_order, hue_order=hue_order, palette=plot_colors,
                                estimator=np.mean, ci=None, n_boot=None, units=None, seed=None,
                                orient=None, color=None,saturation=1, errcolor=None, errwidth=0,
                                           capsize=None, dodge=bar_plot_dodge)
        # plot = sns.barplot(x=x, y=y, hue=hue, data=data, order=x_order, hue_order=hue_order, palette=plot_colors)
        # set gray of boxplot manually since it is otherwise determined by the colors used in the plotted box_ends
        # this can lead to different grays for different subplots if only a part of the colors are plotted in one of them
        gray = mpl.colors.rgb2hex((0, 0, 0))
        plot.gray = gray
        plot.plot(ax, {"linewidth":line_width,"edgecolor":"black"})

    elif plot_type == "line":

        data[x] = pd.to_numeric(data[x])

        if type(hue) == type(None):
            nb_colors = 1
        else:
            if len(hue_order) > 0:
                nb_colors = len(hue_order)
            else:
                nb_colors = len(data[hue].drop_duplicates())

        plot_colors = sns.color_palette(plot_colors, n_colors=nb_colors)
        variables = {}
        variables["x"] = x
        variables["y"] = y
        variables["hue"] = hue

        plot = sns.relational._LinePlotter(
                data=data, variables=variables,
                estimator=None, ci=None, n_boot=None, seed=None,
                sort=None, err_style="band", err_kws=None, legend="full")
        plot.map_hue(palette=plot_colors, order=hue_order, norm=None)

        plot._attach(ax)

        # only set x range if x_range is not fixed
        if type(x_range) == type(None):
            min_x = data[x].min()
            max_x = data[x].max()
            ax.set_xlim(min_x, max_x)

        plot.plot(ax,{})

    elif plot_type == "scatter":


        data[x] = pd.to_numeric(data[x])
        if type(hue) != type(None):
            nb_colors = len(data[hue].drop_duplicates())
        else:
            nb_colors = 1
        plot_colors = sns.color_palette(plot_colors, n_colors=nb_colors)


        plot = sns.scatterplot(
            data=data, x=x, y=y, hue=hue, ax=ax,
            palette = plot_colors, color=plot_colors[0],
            alpha=0.5, sizes=[25 * size_factor]
        )

    elif plot_type == "regression":

        data[x] = pd.to_numeric(data[x])

        if type(hue) != type(None):
            nb_colors = len(data[hue].drop_duplicates())
        else:
            nb_colors = 1

        plot_colors = sns.color_palette(plot_colors, n_colors=nb_colors)

        line_kws = {}
        scatter_kws = {}

        if len(plot_colors) == 1:
            line_kws["color"] = plot_colors[0]
            scatter_kws["color"] = plot_colors[0]

        scatter_kws["sizes"] = [25 * size_factor]
        scatter_kws["alpha"] = 0.5

        plot = sns.regplot(
            data=data, x=x, y=y,line_kws=line_kws,
            scatter_kws=scatter_kws, ax=ax)

        if show_formula | show_regression_stats:


            txt_labels = []

            if show_formula:
                # get formulat of regression line
                x_line_vals = plot.get_lines()[0].get_xdata()
                y_line_vals = plot.get_lines()[0].get_ydata()
                results = scipy.stats.linregress(x_line_vals, y_line_vals)
                slope = np.round(results.slope, 2)
                intercept = np.round(results.intercept, 2)

                # make string of formula for regression line
                formula_txt = "y = " + str(slope) + "x + " + str(intercept)
                txt_labels.append(formula_txt)

            if show_regression_stats:
                r, p_val = scipy.stats.pearsonr(data[x], data[y])
                r = np.round(r,2)
                p_val = np.round(p_val, 4)
                regression_text = "r = " + str(r) +"; p = " + str(p_val)
                txt_labels.append(regression_text)

            standard_x_position = "top"
            standard_y_position = "right"
            # define padding of txt label from sites (horizontal and vertical)
            padding = 0.03

            # calculate where the formula should displayed within the plot
            font_size_pt = FontProperties(size="medium").get_size_in_points()

            # initialize txt size in px as zero
            # but increase for each text label
            # so that they are shown below each other
            # the first text label is shown on the top

            # reduce font size to start with to add to reduce vertical padding
            # value determined through trial and error
            # good value depends on padding defined above
            font_height_pt = - font_size_pt * 0.5
            for label_nb, txt_label in enumerate(txt_labels):

                font_height_pt += font_size_pt

                # increase font size by 10% to enable vertical padding
                # between first and second label
                font_height_pt += label_nb * font_size_pt * 0.1

                # add one number at end of string, seems that ax extends over the plot area by + 1.5 numbers
                txt_size_px = figure_panel.get_dimension_of_text(txt_label,
                                                                  font_size_pt,
                                                                  ax)
                txt_width_px = txt_size_px[0]
                
                labels_to_add.append({})
                # create function to get xy position when needed
                labels_to_add[-1]["xy"] = functools.partial(figure_panel.get_xy_of_text_from_position,
                                                            txt_label, ax,
                                                            position_regression_text,
                                                            txt_width_px,
                                                            font_height_pt,
                                                            standard_x_position,
                                                            standard_y_position,
                                                            padding)
                labels_to_add[-1]["text"] = txt_label
                labels_to_add[-1]["fontsize"] = font_size_pt
                labels_to_add[-1]["xycoords"] = "axes fraction"
                labels_to_add[-1]["label_method"] = ax.annotate

    if (hue != None) & ( (plot_type == "box") | (plot_type == "bar") ):
        # code from stackoverflow (https://stackoverflow.com/questions/56838187/how-to-create-spacing-between-same-subgroup-in-seaborn-boxplot)
        fac = 0.8
        # iterating through axes artists:
        for c in ax.get_children():

            # searching for PathPatches
            if isinstance(c, PathPatch):
                # getting current width of box:
                p = c.get_path()
                verts = p.vertices
                verts_sub = verts[:-1]
                xmin = np.min(verts_sub[:, 0])
                xmax = np.max(verts_sub[:, 0])
                xmid = 0.5*(xmin+xmax)
                xhalf = 0.5*(xmax - xmin)

                # setting new width of box
                xmin_new = xmid-fac*xhalf
                xmax_new = xmid+fac*xhalf
                verts_sub[verts_sub[:, 0] == xmin, 0] = xmin_new
                verts_sub[verts_sub[:, 0] == xmax, 0] = xmax_new

                # setting new width of median line
                for l in ax.lines:
                    if np.all(l.get_xdata() == [xmin, xmax]):
                        l.set_xdata([xmin_new, xmax_new])

    return plot, labels_to_add


def add_lines_to_connect_paired_data_points(col_data, ax, nb_x_vals, x, y, hue,
                                     new_x_order, new_hue_order,
                                     connecting_line_color,
                                     connecting_line_alpha,
                                     connecting_line_width,
                                            pair_unit_columns):
    if nb_x_vals <= 1:
        return
    # Code to connect paired points from S.A. on stackoverflow:
    # https://stackoverflow.com/questions/51155396/plotting-colored-lines-connecting-individual-data-points-of-two-swarmplots
    # go through each set of two groups out of all groups
    # get all groups from new_x_order and new_hue_order combinations
    if len(new_hue_order) == 0:
        sorted_hue_vals = np.unique(col_data[hue].values)
    else:
        sorted_hue_vals = new_hue_order

    col_data = col_data.sort_values(pair_unit_columns)

    # without hue there is only one group containing all x values
    all_x_vals = col_data[x].drop_duplicates().values
    all_data_groups = []
    if len(new_hue_order) == 0:
        all_data_groups.append(list(itertools.product(all_x_vals,
                                                      sorted_hue_vals)))
    else:
        # with hue there are as many groups as there are x values
        # and for each x there are as many groups
        for x_val in new_x_order:
            new_groups = itertools.product(x_val, sorted_hue_vals)
            all_data_groups.append(new_groups)

    current_group_start_number = 0
    for data_group in all_data_groups:
        sub_group_numbers = list(range(len(data_group)))
        # go through all group numbers in pairs of two
        # by taking the group number and one further
        # therefore stop one before the last group number
        for sub_group_nb in sub_group_numbers[:-1]:

            # get x and hue values of first group
            data_group1 = data_group[sub_group_nb]
            data_group1_vals = col_data.loc[(col_data[x] == data_group1[0]) &
                                            (col_data[hue] == data_group1[1]), y].values
            # get x and hue values of second group
            data_group2 = data_group[sub_group_nb + 1]
            data_group2_vals = col_data.loc[(col_data[x] == data_group2[0]) &
                                            (col_data[hue] == data_group2[1]), y].values
            # do not connect groups if there is only one datapoint
            if (len(data_group1_vals) <= 1) | (len(data_group2_vals) <= 1):
                return

            # get the number of the current data group
            # with respect to the start number
            data_group_nb1 = current_group_start_number + sub_group_nb
            data_group_nb2 = data_group_nb1 + 1

            locs1 = ax.get_children()[data_group_nb1].get_offsets()
            locs2 = ax.get_children()[data_group_nb2].get_offsets()

            # before plotting, we need to sort so that the data points
            # correspond to each other as they did in the original data
            # since in the plot the data points are sorted ascendingly
            # by their value
            sort_group1 = np.argsort(data_group1_vals)
            sort_group2 = np.argsort(data_group2_vals)

            # revert "ascending sort" through sort_group2.argsort(),
            # and then sort into order corresponding with data_group2_vals
            locs2_sorted = locs2[sort_group2.argsort()][sort_group1]

            for data_point_nb in range(locs1.shape[0]):
                # the first column corresponds to the x coordinates
                x_for_line = [locs1[data_point_nb, 0],
                              locs2_sorted[data_point_nb, 0]]
                # the second column corresponds to the y coordinates
                y_for_line = [locs1[data_point_nb, 1],
                              locs2_sorted[data_point_nb, 1]]
                ax.plot(x_for_line, y_for_line, color=connecting_line_color,
                        alpha=connecting_line_alpha,
                        lw=connecting_line_width)

        # increase the current group start number for next groups
        current_group_start_number += len(data_group)


def add_column_plot_title_above(ax_annot, col_val, col_label_padding, fontsize):
    fig = plt.gcf()
    # set title and move plot down (by decreasing height) accordingly afterwards

    # first set title to get the height of it which is necessary as padding
    # to move it into the border of the panel
    title = ax_annot.set_title(col_val, pad = col_label_padding,
                               loc="center", fontsize=fontsize,
                               x=0.5, ha="center")

    col_label_height_px = title.get_window_extent( fig.canvas.get_renderer() ).height
    fig = plt.gcf()
    # not sure why divided by 10... little bit of confusion why this works well
    col_label_padding_px = points_to_pixels(col_label_padding) / 10
    # padding_to_move_into_borders = pixels_to_points(col_label_height_px +
    #                                                 col_label_padding_px)*10
    # # set final title with correct padding
    # title = plt.title(col_val, pad = -padding_to_move_into_borders,
    #                   fontsize=fontsize)
    # col_label_height_px = title.get_window_extent( fig.canvas.get_renderer() ).height
    # fig = plt.gcf()
    # # not sure why divided by 10... little bit of confusion why this works well
    # col_label_padding_px = points_to_pixels(col_label_padding) / 10
    col_label_height = ((col_label_height_px +col_label_padding_px) /
                        (fig.get_size_inches()[0] * fig.dpi))
    return col_label_height



def get_all_box_pairs(box_pairs,data,col,col_order,x,x_order,hue,hue_order):
    max_level_of_pairs = 0
    if len(box_pairs) == 0:
        all_box_pairs = construct_all_box_pairs(data,col,col_order,x,x_order,hue,hue_order)
        max_level_of_pairs = 3
    else:
        all_box_pairs = []
        for box_pair in box_pairs:
            if (type(box_pair[0]) != tuple):
                box_pair[0] = [box_pair[0]]
            if(type(box_pair[1]) != tuple):
                box_pair[1] = [box_pair[1]]
            if (len(box_pair[0]) != len(box_pair[1])):
                raise ValueError("Two parts '"+str(box_pair[0])+"' and '"+str(box_pair[1])+"' need to have the same number of items.")
            # if no "col" is in box_pair, then repeat pair over all "col"
            if (len(box_pair[0]) < 3):
                if len(box_pair[0]) == 2:
                    # level of statistics is 2, compare within each group but not outside of it
                    max_level_of_pairs = max(max_level_of_pairs,2)

                for col_val in col_order:
                    # if each elements in  pair only contains one group, repeat over group
                    if (len(box_pair[0]) == 1):
                        # level of statistics is 1, compare within hue but not outside of it
                        max_level_of_pairs = max(max_level_of_pairs,1)
                        # if hue is not defined, add third group in element of pair as no_hue_defined
                        if (hue == "no_hue_defined"):
                            new_box_pair = [(col_val,box_pair[0][0],"_-_-None-_-_"),(col_val,box_pair[1][0],"_-_-None-_-_")]
                            all_box_pairs.append(new_box_pair)
                        else:
                            # if no "x" is in box_pair, but "hue" is defined, repeat pair over all "x" & "col"
                            col_data = data.loc[data[col] == col_val]
                            x_vals = col_data[x].drop_duplicates().dropna()
                            for x_val in x_vals:
                                new_box_pair = [(col_val,x_val,box_pair[0][0]),(col_val,x_val,box_pair[1][0])]

                                all_box_pairs.append(new_box_pair)
                    else:
                        new_box_pair = [(col_val,box_pair[0][0],box_pair[0][1]),(col_val,box_pair[1][0],box_pair[1][1])]

                        all_box_pairs.append(new_box_pair)
            else:
                # otherwise just add the box_pair as it is
                # level of statistic is 3
                max_level_of_pairs = max(max_elevel_of_pairs,3)
                all_box_pairs.append(box_pair)
    return all_box_pairs, max_level_of_pairs


def build_box_struct_pairs(all_box_pairs, all_box_names,
                           all_box_structs_dics,  col):
    # Build the list of box data structure pairs

    box_struct_pairs = []
    for i_box_pair, (box1, box2) in enumerate(all_box_pairs):
        # box must have the col value as first element!
        # temporary fix
        # if col is not defined, add None to the front
        # if (col == "no_col_defined") & (box1[0] != '_-_-None-_-_'):
        #     box1 = ['_-_-None-_-_', *box1]
        #     box2 = ['_-_-None-_-_', *box2]

        # get all box names for column of each box
        box_names1 = all_box_names[box1[0]]
        box_names2 = all_box_names[box2[0]]
        box_structs_dic1 = all_box_structs_dics[box1[0]]
        box_structs_dic2 = all_box_structs_dics[box2[0]]
        # change box
        # if len(box1) == 3:
        #     box1 = (box1[1],box1[2])
        #     box2 = (box2[1],box2[2])
        # else:
        #     box1 = box1[1]
        #     box2 = box2[1]

        valid = ((box1 in box_names1) and (box2 in box_names2))
        if valid:

            # i_box_pair will keep track of the original order of the box pairs.
            box_struct1 = dict(box_structs_dic1[box1], i_box_pair=i_box_pair)
            box_struct2 = dict(box_structs_dic2[box2], i_box_pair=i_box_pair)

            if box_struct1['x'] <= box_struct2['x']:
                pair = (box_struct1, box_struct2)
            else:
                pair = (box_struct2, box_struct1)
            box_struct_pairs.append(pair)

    return box_struct_pairs


def exclude_data(data,col,col_order,x,x_order,hue,hue_order):
    # get all column values that are excluded from data because they are missing in order
    missing_vals_in_column = {}
    missing_vals_in_column[col] = get_excluded_column_vals(data,col,col_order)
    missing_vals_in_column[x] = get_excluded_column_vals(data,x,x_order)
    missing_vals_in_column[hue] = get_excluded_column_vals(data,hue,hue_order)

    included_data = copy.copy(data)
    for missing_val_column,missing_vals in missing_vals_in_column.items():
        for missing_val in missing_vals:
            exclude_by_column_val = True
            if type(missing_val) == float:
                if (np.isnan(missing_val)):
                    included_data = included_data.dropna(axis=0,subset=[missing_val_column])
                    exclude_by_column_val = False
            if exclude_by_column_val:
                included_data = included_data.loc[included_data[missing_val_column] != missing_val]
    return included_data


def get_stats_and_exclude_nonsignificant(included_data,col,x,y,hue,all_box_pairs,
                                         max_level_of_pairs,test_short_name,
                                         test_result_list,annotate_nonsignificant,
                                         verbose):
    
    test_short_name = test_short_name if test_short_name is not None else ''
    included_pairs = []
    p_values = {}
    # create dict with data according to level of pairs for statistical analysis
    # max_level of pairs == 1: only compare within x
    # max_level of pairs == 2: only compare within group
    # max_level of_pairs == 3: compare all groups
    all_data = {}
    # for each group in all_data comparisons will be performed
    # if the maximum level of pairs is 3 then ALL data will be compared
    # therefore, the data will not be split into groups
    # if the maximum level of pairs is smaller than 3, split the data into groups
    # if the level of pairs is smaller than 2 AND hue is defined
    # then compare only within each col and x_val group
    # however, if the maximum level is 2 then compare everything 
    # within each different col val group
    if (max_level_of_pairs < 3):
        all_cols = included_data[col].drop_duplicates()
        for col_val in all_cols:
            # hue needs to be defined since otherwise there is only one group for each x_val
            # if (max_level_of_pairs < 2) & (hue != "no_hue_defined"):
            if (max_level_of_pairs < 2) & (hue != "no_hue_defined"):
                col_data = included_data[included_data[col] == col_val]
                all_xs = col_data[x].drop_duplicates()
                for x_val in all_xs:
                    x_data = col_data[col_data[x] == x_val]
                    all_data[(str(col_val),str(x_val))] = x_data
            else: # was not included in initial script
                all_data[(str(col_val))] = included_data[included_data[col] == col_val]
    else:
        all_data[0] = included_data

    for data_key in all_data:
        group_check_vals = []
        if type(data_key) == str:
            group_check_vals.append(data_key)
        elif type(data_key) == tuple:
            group_check_vals.append(data_key[0])
            group_check_vals.append("")
            group_check_vals.append(data_key[1])
        one_group_data = all_data[data_key]

        # create new column to separate groups for statistic analysis
        col_strings = one_group_data[col].astype(str) + "___"
        hue_strings = "___"+one_group_data[hue].astype(str)
        # hue_strings = "___"+one_group_data[hue].astype(str)
        
        one_group_data.loc[:,'constructed_group'] = col_strings+one_group_data[x].astype(str)+hue_strings
        # construct list with one list with all data points from each box
        # for statistical multi-comparison of all groups
        group_data_list = []
        for group in one_group_data['constructed_group'].drop_duplicates():
            
            one_box_data = one_group_data.loc[one_group_data['constructed_group'] == group, y]
            group_data_list.append( list(one_box_data) )
        # check if group comparison using non parametric kruskal wallis is significant
        group_stat_results = stats.kruskal(*group_data_list)
        a = 1
        group_test_below_thresh = (group_stat_results.pvalue < 0.05)
        if group_test_below_thresh | annotate_nonsignificant:
            

            # group_col = "constructed_group"
            # group_vals = one_group_data[group_col].drop_duplicates()
            # stat_results = pd.DataFrame()
            # stat_results["test"] = group_vals
            # stat_results.set_index("test", inplace=True)
            # for group_val in group_vals:
            #     stat_results[group_val] = 1
            # nb_groups = len(group_vals)
            # nb_tests = math.factorial(nb_groups) / (2 * math.factorial(nb_groups - 2))
            # for first_group_val in group_vals:
            #     first_group = one_group_data.loc[one_group_data[group_col] == first_group_val]
            #     for second_group_val in group_vals:
            #         if first_group_val != second_group_val:
            #             second_group = one_group_data.loc[one_group_data[group_col] == second_group_val]
            #             print(first_group)
            #             print(second_group)
            #             p_val = stats.mannwhitneyu(first_group[y], second_group[y]).pvalue
            #             # add the corrected pval
            #             stat_results.loc[first_group_val, second_group_val] = p_val * nb_tests

            stat_results = posthocs.posthoc_dunn(one_group_data,val_col=y,
                                                 group_col="constructed_group",
                                                 p_adjust="bonferroni")
            # stat_results = posthocs.posthoc_nemenyi_friedman(one_group_data,
            #                                                  y_col=y,
            #                                                  group_col="constructed_group",
            #                                                  block_col=col,
            #                                                  melted=True)
            # one_group_data.to_csv("C:\\Users\\Maxsc\\Desktop\\data_"+str(a)+".csv")
            # a += 1
            # print(stat_results)
            # stat_results.to_csv("C:\\Users\\Maxsc\\Desktop\\tests.csv")
            # print(type(stat_results))
            
            for box_pair in all_box_pairs:
                box_pair = tuple(box_pair)
                box1 = box_pair[0]
                box2 = box_pair[1]

                # check if box pair comes from same group values (col and/or x) tha
                # not sure what this should do... commented out for now.
                use_box_pair = True

                # print(group_check_vals)
                # for i,group_check_val in enumerate(group_check_vals):
                #     print("BOX:", box1[i])
                #     print("GROUO CHECK:", group_check_val)
                #     if (box1[i] != group_check_val) & (group_check_val != ""):
                #         use_box_pair = False
                #         break

                stat_column = str(box1[0]) + "___" + str(box1[1]) + "___" + str(box1[2])
                stat_row = str(box2[0]) + "___" + str(box2[1]) + "___" + str(box2[2])
                
                if stat_column not in stat_results.index:
                    use_box_pair = False

                if stat_row not in stat_results.columns:
                    use_box_pair = False
                
                if use_box_pair:

                    pval = stat_results.loc[stat_column,stat_row]
                    formatted_output = ("Custom statistical test, {}, P_val={:.3e}"
                                        .format(test_short_name, pval))

                    # set pval as above 0.05 if group test was not below threshold!
                    if (not group_test_below_thresh) & (pval < 0.05):
                        pval = 0.051

                    test_result_list.append({'pvalue': pval, 'test_short_name': test_short_name,
                                             'formatted_output': formatted_output, 'box1': box1,
                                             'box2': box2})
                    if verbose:
                        print("{} v.s. {}: {}".format(box1, box2, formatted_output))
                    if (pval < 0.05) | (annotate_nonsignificant == True):
                        included_pairs.append(box_pair)
                        p_values[box_pair] = (pval)
    return included_pairs, p_values, test_result_list


def get_max_ylim_yrange(all_ax_data):
    max_ylim = 0
    max_yrange = 0
    for ax_data in all_ax_data.values():
        ylim = ax_data.get_ylim()
        yrange = ylim[1] - ylim[0]
        if yrange > max_yrange:
            max_ylim = ylim
            max_yrange = yrange
    ylim = max_ylim
    yrange = max_yrange
    return ylim, yrange

def plot_text(ax, text, y, x1, x2, text_offset, fontsize, h,
              use_fixed_offset, ann_list):

    figure = plt.gcf()
    y_top_annot = y + h

    if (type(text) == type(None)):
        return ann_list, y_top_annot, ax

    fontsize_pt = FontProperties(size=fontsize).get_size_in_points()
    if text.find("*") != -1:
        text_offset = text_offset - fontsize_pt / 2
    else:
        text_offset = text_offset - fontsize_pt / 10
    ann = ax.annotate(
        text, xy=(np.mean([x1, x2]), y+h),
        xytext=(0, text_offset), textcoords='offset points',
        xycoords='data', ha='center', va='bottom',
        fontsize=fontsize,fontweight='bold', clip_on=False,
        annotation_clip=False)
    ann_list.append(ann)

    plt.draw()
    y_top_annot = None
    got_mpl_error = False
    if not use_fixed_offset:
        try:
            bbox = ann.get_window_extent()
            bbox_data = bbox.transformed(ax.transData.inverted())
            y_top_annot = bbox_data.ymax
        except RuntimeError:
            got_mpl_error = True

    if not (use_fixed_offset or got_mpl_error):
        return ann_list, y_top_annot, ax

    if verbose:
        print("Warning: cannot get the text bounding box. "
              "Falling back to a fixed"
              " y offset. Layout may be not optimal.")
    # We will apply a fixed offset in points,
    # based on the font size of the anperties(size='medium').get_size_in_points()
    fontsize_pt = FontProperties(size=fontsize).get_size_in_points()
    offset_trans = mtransforms.offset_copy(ax.transData, fig=figure,
                                           x=0, y=(1.0 * fontsize_pt +
                                                   text_offset),
                                           units='points')
    # user additional buffer for text above line
    y_top_display = offset_trans.transform((0, y + h))
    y_top_annot = ax.transData.inverted().transform(y_top_display)[1]

    return ann_list, y_top_annot, ax


def get_px_size_rel_to_subplot(ax, width, height):
    fig = plt.gcf()
    ax_size = ax.get_window_extent()
    subplot_size = ax_size.transformed(fig.dpi_scale_trans.inverted())
    subplot_height = subplot_size.height * fig.dpi
    subplot_width = subplot_size.width * fig.dpi
    # add x_spacing to relative width
    rel_width = (width) / subplot_width
    rel_height = (height) / subplot_height
    return (rel_width,rel_height)




def change_plot_size_to_standardize_box_size(ax, nb_x_vals, box_width, hue,
                                            hue_order):
    """
    Change size of plot to standardize size of boxes to box_width
    :param ax: subplot whichs size should be changed
    :param nb_x_vals: nb of boxes in the subplots (current col)
    :param box_width: size in inch that should be used per box
    :param hue: hue column, only used to check whether hue is set or not
    """

    fig = plt.gcf()

    if (hue != None) & (len(hue_order) > 1):
        nb_x_vals *= 0.95

    rel_target_width = nb_x_vals * box_width / fig.get_size_inches()[0]
    ax_coords = ax.get_position()

    # surplus width is relative amount of width that is too much to fit into ax
    # this relative width change was therefore done automatically by matplotlib
    # will be used to scale space between groups
    if rel_target_width > ax_coords.width:
        auto_width_reduction_factor = ax_coords.width / rel_target_width
    else:
        auto_width_reduction_factor = 1

    # width difference can never be below zero,
    # since plots are not increased in size then
    # (they already use up all available space)
    width_difference = max(0,ax_coords.width - rel_target_width)

    if width_difference > 0:
        ax.set_position([ax_coords.x0, ax_coords.y0,
                         rel_target_width, ax_coords.height])

    return ax, width_difference, auto_width_reduction_factor


def add_row_label(row_label_text, fontsize_points,
                  orientation, ax, x_start):
    if orientation.find("vert") != -1:
        rotation = 90
    else:
        rotation = 0
    label = ax.text(x=x_start, y=0.5, s=row_label_text, transform=ax.transAxes,
                     verticalalignment="center",
                         fontsize = fontsize_points, rotation=rotation)
    return label


def get_width_of_object(legend, borderaxespad_px, fig):
    legend_coords = legend.get_window_extent( fig.canvas.get_renderer() )
    if legend_coords.width > 0:
        legend_width_px = legend_coords.width + borderaxespad_px
        legend_width = legend_width_px / (fig.get_size_inches()[0] * fig.dpi)
    else:
        legend_width = 0
    return legend_width

def points_to_pixels(points):
     # 10 is the basic unit for the spacing in font size (based on rcParams)
    return points * 10 * plt.gcf().dpi / 72

def pixels_to_points(pixels):
    # 10 is the basic unit for the spacing in font size (based on rcParams)
    return pixels / ( 10* plt.gcf().dpi / 72)

def set_legend_and_axes(ax, col_order, plot_nb, hue_order,
                        y_axis_label,
                        x_order, fontsize, legend_spacing,
                        longest_legend_handles, show_x_axis,
                        x_axis_label, legend_title,
                        show_row_label,
                        row_label_text, row_label_orientation,
                        show_legend,
                        borderaxespad_, legend_handle_length,
                        show_x_label_in_all_columns,
                        _leave_space_for_legend,
                        data_is_continuous,
                        show_data_points, connect_paired_data_points):

    fig = plt.gcf()

    # get fontsize in points based on string description of font size
    fontsize_points = FontProperties(size=fontsize).get_size_in_points()

    # set handles and labels of legend as first to in the legend,
    # position legend upper right corner next to plot
    handles, labels = ax.get_legend_handles_labels()
    # If datapoints should not be shown but only connected
    # then datapoints are in fact plotted but with alpha=0 (not visible)
    # therefore, the first part of the legend still corresponds to the
    # datapoints
    # to prevent this remove the part of the legend corresponding to the
    # points
    if (len(hue_order) > 0) & (not show_data_points) & connect_paired_data_points:
        handles = handles[len(hue_order):]
        labels = labels[len(hue_order):]
    if len(handles) < len(longest_legend_handles):
        handles = longest_legend_handles

    # for lines remove handles that have no corresponding line since they dont
    # have corresponding data in the plot
    # otherwise, the legend will be shifted
    # FIND A MORE GENERAL SOLUTION THAN THIS!
    if len(handles) > 0:
        if type(handles[0]) == lines.Line2D:
            handles = [handle for handle in handles
                       if handle.get_color() != "w" ]

    nb_labels = len(hue_order)

    # add spacing between legend and ax to legend width
    borderaxespad_px = points_to_pixels(borderaxespad_)

    legend = None

    if not show_row_label:

        legend = plt.legend(handles[0:nb_labels], hue_order,
                            bbox_to_anchor=(1, 1), loc=2,
                            fontsize=fontsize_points, frameon=False,
                            borderpad=0, handletextpad=legend_spacing,
                            borderaxespad=borderaxespad_, title=legend_title,
                            handlelength=legend_handle_length)
        # set font size of legend title same as rest of legend
        plt.setp(legend.get_title(),fontsize=fontsize_points)
        legend._legend_box.align = "left"
        ax.set_xlabel("")

    else:
        ax.set_xlabel("")

        if type(ax.legend_) != type(None):
            ax.legend_.remove()

        # only plot verticle title at last plot (very right)
        if plot_nb == (len(col_order)):
            # set right headline here for plot instead of legend
            ax_coords = ax.get_position()
            ax_width_px = ax_coords.width * fig.dpi * fig.get_size_inches()[1]
            x_start = 1 + borderaxespad_px / ax_width_px
            legend = add_row_label(row_label_text, fontsize_points,
                                   row_label_orientation, ax, x_start)


    if type(legend) != type(None):
        # get width of legend, needed to set width_reduction
        # in move_plot_into_borders_and_center_it function
        # legend_coords =ax.legend_.get_window_extent(fig.canvas.get_renderer())
        legend_width = get_width_of_object(legend, borderaxespad_px, fig)

    else:
        legend_width = 0

    if not show_row_label:
        # remove legend now for all except the last subplot
        # Also remove legend if there is only one item in the legends
        if ((plot_nb != len(col_order)) |
                (len(handles) < 2) |
                (not show_legend)):
            if not (type(ax.legend_) == type(None)):
                show_legend = False
        if not show_legend:
            ax.legend_.remove()
            if not _leave_space_for_legend:
                legend_width = 0

    # remove y axis label and title for all subplots except the first one
    if plot_nb > 1:
        ax.yaxis.set_ticklabels([])
        ax.set_ylabel("")
    else:
        if y_axis_label != "":
            ax.set_ylabel(y_axis_label, labelpad=borderaxespad_)

    # remove border around axis
    ax.spines['bottom'].set_color('None')
    ax.spines['top'].set_color('None')
    ax.spines['right'].set_color('None')
    ax.spines['left'].set_color('None')

    # show x label for column if should be shown in all columns
    # of if the current column is the first
    if ((x_axis_label != None) &
            ((show_x_label_in_all_columns) |
             (plot_nb == 1))):
        ax.set_xlabel(x_axis_label, labelpad=borderaxespad_)
    elif data_is_continuous:
        ax.set(xticklabels=[])

    if not show_x_axis:
        ax.set(xticklabels=[])

    # if there is only one x tick label in ALL plots, dont show xticklabels
    if (len(x_order) == 1) & (not data_is_continuous):
        ax.set(xticklabels=[])

    return legend_width, handles


def set_axis_label_paddings(inner_padding, axis_padding, ax, plot_nb,
                            outer_border, size_factor):
    # set axis_padding for all plots in the first plot,
    # since only this plot has the
    if plot_nb == 1:
        # calculate padding of tick labels
        axis_padding = get_accurate_y_tick_padding(ax, axis_padding,
                                                   size_factor)

    ax.tick_params(axis="both",which="both",pad=axis_padding) # REACTIVATE

    #remove tick lines from plot
    ax.tick_params(left=False, bottom=False)
    # set padding for y, label
    # (is lower than default padding for width
    #  of one position in grid less than about 2 inches)
    ax.set_ylabel(ax.get_ylabel(),labelpad=inner_padding)

    return axis_padding

def get_accurate_y_tick_padding(ax, target_padding, size_factor = None):
    """
    Gets axis_pading in points and return in points
    """
    if size_factor == None:
        size_factor = 1
    # get x1 position (rightmost border of tick labels) of bbox of tick labels
    # set padding of y-axis zero first to get real difference
    # in position between ticks and ax
    ax.tick_params(axis="y",which="both",pad=0) # REACTIVATE
    fig = plt.gcf()
    bbox = ax.yaxis._get_tick_bboxes(ax.yaxis.majorTicks,
                                     fig.canvas.get_renderer())
    tick_x1 = bbox[0][0].x1
    # get start of x0
    ax_x0 = ax.get_position().x0 * fig.get_size_inches()[0] * fig.dpi #outer_border[0]
    # target padding is the actual distance between tick labels and plot
    target_padding *= size_factor
    axis_padding = (tick_x1 - ax_x0 + target_padding) * 72 / fig.dpi
    return axis_padding


def get_accurate_x_tick_padding(ax, target_padding, size_factor = None):
    """
    Gets axis_pading in points and return in points
    """
    if size_factor == None:
        size_factor = 1
    # get y1 position (rightmost border of tick labels) of bbox of tick labels
    # set padding of y-axis zero first
    # to get real difference in position between ticks and ax
    ax.tick_params(axis="x",which="both",pad=0) # REACTIVATE
    fig = plt.gcf()
    bbox = ax.xaxis._get_tick_bboxes(ax.xaxis.majorTicks,
                                     fig.canvas.get_renderer())
    tick_y1 = bbox[0][0].y1
    # get start of x0
    ax_y0 = ax.get_position().y0 * fig.get_size_inches()[0] * fig.dpi #outer_border[0]
    # target padding is the actual distance between tick labels and plot
    target_padding *= size_factor
    axis_padding = (tick_y1 - ax_y0 + target_padding) * 72 / fig.dpi
    return axis_padding

def get_y_shift_to_vert_fill_outer_border(ax, col, col_order,
                                          max_nb_col_val_lines, y_shift, inner_padding,
                                          fontsize, outer_border,
                                          show_col_labels_below,
                                          always_show_col_label):
        ax_coords = ax.get_position()
        # if col is used to group data for plotting
        # get fontsize for col value (title on x axis)
        # based on string fontsize description (e.g. "medium")
        if (((col == "no_col_defined") | len(col_order) <= 1) & 
            (not always_show_col_label)):
            title_fontsize = 0
            nb_title_lines = 1
            inner_padding = 0
        else:
            title_fontsize = FontProperties(size=fontsize).get_size_in_points()

        fig = plt.gcf()

        # adjust position of axes for additional space
        # needed by x axes label and y axes labels (including title)
        text_height = get_axis_dimension(ax, ax.xaxis, "height",
                                         outer_border[2])

        _, rel_height_text = get_px_size_rel_to_subplot(ax, width=0,
                                                        height=text_height)


        # if there is no x label (0 text height),
        # then only add one inner_padding instead of two
        # otherwise there are one before the line and one after the line,
        # without label there is no line above the title
        if text_height == 0:
            inner_padding /= 2

        # only take title (col_val ploted below plot)
        # into account when col labels should be shown below
        # col labels plotted above must be accounted for with y shift from top
        # this y shift will be from bottom
        # (usually for box plots, bar plots, since labeling there below)
        # col label above is more often for continuous plots

        if (show_col_labels_below) & (col != "no_col_defined"):
            # to get nb of px of fontsize normalize to current dpi,
            # fontsize is nb of px for dpi of 72
            _ , rel_height_title = get_px_size_rel_to_subplot(ax, width=0,
                                                              height= (title_fontsize *
                                                                       max_nb_col_val_lines +
                                                                       inner_padding * 2) *
                                                                      (fig.dpi/72) )
        else:
            rel_height_title = 0

        y_shift += (rel_height_text + rel_height_title) * ax_coords.height

        return y_shift


def vert_fill_outer_border(ax, y_shift, rel_height_change):
    """
    adjust position and size of plot to have vertical padding
    to nearby panels and own panel letter
    center the plot vertically
    """

    ax_coords = ax.get_position()

    bottom = ax_coords.y0 + y_shift
    height = ax_coords.height - y_shift
    rel_height_change += ax_coords.height / height

    ax.set_position([ax_coords.x0,bottom,ax_coords.width,height])

    return rel_height_change

def adjust_annotation_plot_height_and_y(ax_annot, y_shift, rel_height_change):
    ax_annot_coords = ax_annot.get_position()
    ax_annot.set_position([ax_annot_coords.x0, ax_annot_coords.y0 + y_shift,
                           ax_annot_coords.width,
                           ax_annot_coords.height/rel_height_change])


def px(rel):
    fig = plt.gcf()
    fig_size_px = fig.get_size_inches()[0] * fig.dpi
    px_size = rel * fig_size_px
    return px_size


def get_axis_dimension(ax, axis, type, baseline):
    """
    Calculate the accurate axis dimension by getting the size of the axis label
    using normal pyplot functions
    and by getting the size of the ticks including the actual padding in px
    by getting the start position of the bbox for ticks and calculating the
    difference to the end point of the axis (baseline)
    :param base: baseline is the starting point in the correct dimension of the
                axis in relative figure coords
    """
    fig = plt.gcf()

    if axis.label.get_text() != "":
        label_padding = axis.labelpad * fig.dpi / 72
        label_fontsize = axis.label.get_size() * fig.dpi / 72
        label_lines = len(axis.label.get_text().split("\n"))
        label_size = label_padding + label_fontsize * label_lines
    else:
        label_size = 0

    # update ticks first and then get correct bboxes
    if type == "height":
        # box = axis._get_tick_bboxes(axis._update_ticks(),
        # fig.canvas.get_renderer())[0][0]
        box = axis.get_tightbbox(plt.gcf().canvas.renderer)
        baseline_px_y = baseline * fig.get_size_inches()[1] * fig.dpi
        # if the label has no text, there is no label
        # and therefore dont consider its height
        if axis.get_major_ticks()[0].label.get_text() == "":
            y0 = baseline_px_y
        else:
            y0 = box.y0
        dimension = (baseline_px_y - y0)# + label_size
        # if len(ax.get_xticklabels()) > 1:
        #     print(ax.xaxis)
            # print(dimension)
            # tick_label_bbox = ax.get_xticklabels()[1].get_tightbbox(plt.gcf().canvas.renderer)
            # print(box.y0 - tick_label_bbox.y0)
            # print(baseline_px_y - tick_label_bbox.y0)
            # print(label_size)
            # print(ax.get_xticklabels()[1].get_tightbbox(plt.gcf().canvas.renderer).height)

    elif type == "width":
        box = axis.get_tightbbox(plt.gcf().canvas.renderer)
        baseline_px_x = baseline * fig.get_size_inches()[0] * fig.dpi
        # if the label has no text, there is no label and therefore dont consider its height
        if axis.get_major_ticks()[0].label.get_text() == "":
            x0 = baseline_px_x
        else:
            x0 = box.x0
        dimension = (baseline_px_x - x0)# + label_size

    return dimension


def finetune_plot(ax, box_structs, col, col_order, perform_stat_test,
                  line_width, line_width_thin, inner_padding, fontsize,
                  col_val, plot_type, vertical_lines, show_col_labels_below,
                  always_show_col_label):

    # add vertical light-grey line for each box
    # to see better to which plot a statistic annotation refers
    fig = plt.gcf()
    y_lim = ax.get_ylim()[1]
    if perform_stat_test & vertical_lines:
        for box_struct in box_structs:
            x = box_struct['x_orig']
            line_x, line_y = [x, x], [0,y_lim]
            line = lines.Line2D(line_x, line_y, lw=line_width_thin, c="0.8",
                                transform=ax.transData, zorder=0,
                                solid_capstyle="butt")
            line.set_clip_on(False)
            ax.add_line(line)

    if col == "no_col_defined":
        return ax

    # draw line over title below x value
    if len(box_structs) > 1:
        dX = box_structs[1]['x_orig'] - box_structs[0]['x_orig']
        x0 = box_structs[0]['x_orig'] - dX/2 * 0.9
        x1 = box_structs[-1]['x_orig'] + dX/2 * 0.9
    else:
        x0 = box_structs[0]['x_orig'] - 0.4
        x1 = box_structs[0]['x_orig'] + 0.4

    if (len(col_order) <= 1) & (not always_show_col_label):
        return ax

    y0_ax = ax.get_position().y0
    text_height = get_axis_dimension(ax, ax.xaxis, "height", y0_ax)

    _ , rel_height_text = get_px_size_rel_to_subplot(ax, 0,
                                                     text_height +
                                                     (inner_padding *
                                                      fig.dpi / 72) )

    # only plot a line if x tick labels are actually there,
    # to show the start of the second level of label
    # if col is the only level, then dont add a line
    if (col_val == "") & (not show_col_labels_below):
        return ax

    x_axis_ticks = ax.xaxis.get_ticklabel_extents(fig.canvas.get_renderer())
    if (x_axis_ticks[0].height > 0):
        line_x = [x0, x1]
        line_y_pos = (ax.get_ylim()[0] - rel_height_text *
                      (y_lim - ax.get_ylim()[0]))
        line_y = [line_y_pos, line_y_pos]

        # line_y = - rel_height_text
        ax = draw_line(line_x=line_x, line_y=line_y,
                       line_width=line_width, color="black", ax=ax)


    title_fontsize = FontProperties(size=fontsize).get_size_in_points()
    nb_lines_title = len(col_val.split("\n"))
    if text_height == 0:
        inner_padding /= 2

    _, rel_height_title = get_px_size_rel_to_subplot(ax, 0,
                                                     height= ((title_fontsize *
                                                               nb_lines_title +
                                                               inner_padding) *
                                                              fig.dpi / 72)
                                                     )
    # set title as column for which subplots are created (Sep)
    # with uppercase start, position below graph (y=)
    y_pos_title = (ax.get_ylim()[0] -
                   (rel_height_text + rel_height_title) *
                   (y_lim - ax.get_ylim()[0]))
    ax.text(s=str(col_val), x=(x0+x1)/2, y=y_pos_title,
            fontsize=title_fontsize, ha="center", va="bottom")

    return ax

def add_annotation_subplot(letter, outer_border, ax_reference=None):

    # create_subplot(fig,column,row,fig_columns,fig_rows,
    # col_span,row_span,label)
    ax = create_column_subplot(outer_border,
                               label="annotation plot "+str(letter))
    if ax_reference != None:
        ax_ref_coords = ax_reference.get_position()
        ax.set_position(ax_ref_coords)
    ax.set_axis_off()
    return ax

def get_excluded_column_vals(data,column,column_vals):
    # check if in column_vals some values of data in column are missing
    all_vals = data[column].drop_duplicates()
    missing_vals = []
    if len(column_vals) > 0:
        if len(all_vals) != len(column_vals):
            for val in all_vals:
                if val not in column_vals:
                    missing_vals.append(val)
    return missing_vals


def get_x_pos_of_other_box(box_struct_pair,box):
    box_struct1, box_struct2 = box_struct_pair
    if box_struct1['box'] == box:
        x = box_struct2['x']
    else:
        x = box_struct1['x']
    return x

def group_box_pairs_in_same_x(all_box_pairs):
    # sort box pairs with same x vals first
    box_pairs_grouped = {}
    for box1, box2 in all_box_pairs:
        if (box1[1] == box2[1]) & (box1[0] == box2[0]):
            if box1[1] not in box_pairs_grouped:
                box_pairs_grouped[box1[1]] = []
            box_pairs_grouped[box1[1]].append((box1,box2))
        else:
            if "different_x" not in box_pairs_grouped:
                box_pairs_grouped["different_x"] = []
            box_pairs_grouped["different_x"].append((box1,box2))
    return box_pairs_grouped


def get_annotated_text_dict(p_values,pvalue_format_string,test_short_name,
                            pvalue_thresholds,show_test_name,text_format):
    pval_texts = {}
    for box_pair,pval in p_values.items():

        # if text_annot_custom is not None:
        #     text = text_annot_custom[i_box_pair]
        # else:
        if text_format == 'full':
            text = ("{} p = {}".format('{}', pvalue_format_string)
                    .format(test_short_name, pval))
        elif type(text_format) == type(None):
            text = None
        elif text_format is 'star':
            text = pval_annotation_text(pval, pvalue_thresholds)
        elif text_format is 'simple':
            test_short_name = show_test_name and test_short_name or ""
            text = simple_text(pval, simple_format_string, pvalue_thresholds, test_short_name)

        pval_texts[box_pair] = text
    return pval_texts


def plot_comparison_to_control_within_x(box_pairs_of_x, hue_order, x_val, hue,
                                        col, pval_texts, all_box_names,
                                        all_box_structs_dics, ann_list, ax,
                                        text_offset, y_offset_to_box, fontsize,
                                        all_ax_data, annotated_pairs,
                                        y_stack_arr, h, use_fixed_offset, loc):

    # remove box_pairs that involve control in comparison within same x_val,
    # if hue is defined only

    box_pairs_of_x_no_control = []
    box_pairs_of_x_control = []
    control_hue = hue_order[0]
    for box_pair in box_pairs_of_x:
        if (control_hue == box_pair[1][2]) | (control_hue == box_pair[0][2]):
            box_pairs_of_x_control.append(box_pair)
        else:
            box_pairs_of_x_no_control.append(box_pair)
    box_dict_pairs_of_x_control = build_box_struct_pairs(box_pairs_of_x_control,
                                                         all_box_names,
                                                         all_box_structs_dics,
                                                         col)
    # plot star on top of significant boxes
    for i, (box_dict1, box_dict2) in enumerate(box_dict_pairs_of_x_control):
        box_pair = box_pairs_of_x_control[i]
        if box_dict1['box'][1] == control_hue:
            box_dict = box_dict2
        else:
            box_dict = box_dict1
        x = box_dict['x']
        y = box_dict['ymax'] + y_offset_to_box
        text = pval_texts[box_pair]
        ann_list, y_top_annot,ax = plot_text(ax, text, y, x, x, text_offset,
                                             fontsize, h, use_fixed_offset,
                                             ann_list)

        (all_ax_data,
         annotated_pairs,
         y_stack_arr,
         ax) = update_plot_and_arrays(y_stack_arr, y_top_annot,
                                        x, x, all_ax_data, ax,
                                        annotated_pairs, y,
                                        text, (box_dict1, box_dict2), loc)
    # only use box_pairs without contorl
    box_pairs_of_x = box_pairs_of_x_no_control
    return (box_pairs_of_x, ann_list, ax, all_ax_data,
            annotated_pairs, y_stack_arr)


def count_occurences_of_boxes_in_pairs(box_pairs_of_x,pval_texts):
    # count number of times each box occurs
    # in all pair groups with same pval group
    # (for each x val and for different x vals)
    box_counter = {}
    for box_pair in box_pairs_of_x:
        pval_text  = pval_texts[box_pair]
        if (box_pair[0],pval_text) not in box_counter:
            box_counter[(box_pair[0],pval_text)] = 1
        else:
            box_counter[(box_pair[0],pval_text)] += 1
        if (box_pair[1],pval_text) not in box_counter:
            box_counter[(box_pair[1],pval_text)] = 1
        else:
            box_counter[(box_pair[1],pval_text)] += 1
    all_boxes = box_counter.keys()
    return box_counter, all_boxes


def get_box_dict_pairs_grouped_by_ranking(all_boxes_sorted,
                                          box_pairs_of_x,
                                          pval_texts,
                                          all_box_names,
                                          all_box_structs_dicts,
                                          col):
    # group box pairs with pval information by ranking

    used_box_pairs_of_x = []
    box_pairs_sorted = {}
    # all boxes sorted is a list of 
    for box_tuple in all_boxes_sorted:
        box = box_tuple[0]
        pval1_text = box_tuple[1]
        for box_pair in box_pairs_of_x:
            pval2_text = pval_texts[box_pair]
            if ((pval1_text == pval2_text) & (box in box_pair) &
                    (box_pair not in used_box_pairs_of_x)):
                used_box_pairs_of_x.append(box_pair)
                if box_tuple not in box_pairs_sorted:
                    box_pairs_sorted[box_tuple] = []
                box_pairs_sorted[box_tuple].append(box_pair)
    box_struct_pairs_grouped = {}
    for box_tuple,box_pairs in box_pairs_sorted.items():
        # get box_struct_pairs for pairs
        box_struct_pairs = build_box_struct_pairs(box_pairs, all_box_names,
                                                  all_box_structs_dicts, col)
        box_struct_pairs_grouped[box_tuple] = box_struct_pairs
    return box_struct_pairs_grouped


def draw_line(line_x,line_y,line_width,color,ax, transform=None):
    if type(transform) == type(None):
        transform= ax.transData
    line = lines.Line2D(line_x, line_y, lw=line_width, c=color,
                        transform=transform, solid_capstyle="projecting")
    line.set_clip_on(False)
    ax.add_line(line)
    return ax


def update_plot_and_arrays(y_stack_arr, y_top_annot, x1, x2, all_ax_data,
                           ax, annotated_pairs, ymax_in_range,
                           text, box_dict_pair, loc):

    # save annotation
    annotated_pairs[(box_dict_pair[0]['box'],text)] = [ymax_in_range,text]
    annotated_pairs[(box_dict_pair[1]['box'],text)] = [ymax_in_range,text]
    xi1 = box_dict_pair[0]['xi']
    xi2 = box_dict_pair[1]['xi']

    # Fill the highest y position of the annotation into the y_stack array
    # for all positions in the range x1 to x2
    y_stack_arr[1, ((x1 <= y_stack_arr[0, :]) &
                    (y_stack_arr[0, :] <= x2))] = y_top_annot
    # Increment the counter of annotations in the y_stack array
    y_stack_arr[2, xi1:xi2 + 1] = y_stack_arr[2, xi1:xi2 + 1] + 1

    if text.find("*") != -1:
        buffer_for_text = 0.15
    else:
        buffer_for_text = 0.12
    y_stack_max = np.max(y_stack_arr[1,:]) + buffer_for_text

    for ax_data in all_ax_data.values():
        ylim = ax_data.get_ylim()
        if loc == 'inside':
            if (0.98 * y_stack_max) > (ylim[1]):
                ax_data.set_ylim((ylim[0], 0.98*y_stack_max))
            else:
                ax_data.set_ylim((ylim[0], ylim[1]))
        elif loc == 'outside':
            ax_data.set_ylim((ylim[0], ylim[1]))

    if loc == 'inside':
        if (0.98 * y_stack_max) > (ylim[1]):
            ax.set_ylim((ylim[0], 0.98*y_stack_max))
        else:
            ax.set_ylim((ylim[0], ylim[1]))
    elif loc == 'outside':
            ax.set_ylim((ylim[0], ylim[1]))

    return all_ax_data,annotated_pairs,y_stack_arr,ax


def annotate_box_pair_group(box_struct_pairs, box_tuple, box, y_stack_arr,
                            all_ax_data, ax,annotated_pairs, text_offset,
                            fontsize, h, ann_list, line_width, loc,
                            y_offset_to_box, y_offset, color, use_fixed_offset,
                            show_data_points, fliersize):

    # if show_data_points is False, outliers will be plotted
    # fliersize is the size in pt of these outliers

    pval_text = box_tuple[1]
    box = box_tuple[0]

    # sort within each group by x position from left to right
    box_struct_pairs_sorted = sorted(box_struct_pairs,
                                     key=lambda x:get_x_pos_of_other_box(x,box))

    turn_point = len(box_struct_pairs_sorted)
    # get id at which left of reference box changes to right of reference box
    for i, box_struct_pair in enumerate(box_struct_pairs_sorted):
        box_struct1 = box_struct_pair[0]
        # temporary fix for comparing something WITHOUT any col for grouping
        box2 = box_struct1['box']
        # if type(box_struct1['box']) == str:
        #     box2 = (box_struct1['group'], box_struct1['box'], "_-_-None-_-_")
        # else:
        #     box2 =  (box_struct1['group'],
        #     box_struct1['box'][0], box_struct1['box'][1])
        if box2 == box:
            turn_point = i
            break

    # split into left and right of reference box
    box_struct_pairs_split = {}

    if turn_point > 0:
        box_struct_pairs_split['left'] = box_struct_pairs_sorted[0:turn_point]

    if turn_point < len(box_struct_pairs):
        box_struct_pairs_split['right'] = box_struct_pairs_sorted[turn_point:]

    # if (turn_point > 0) & (turn_point < len(box_struct_pairs)):
    #     both_sites_have_boxes = True
    # else:
    #     both_sites_have_boxes = False

    # if there is only one pair to compare, use smaller h
    if (len(box_struct_pairs) == 1):
        h = h/2
        y_offset -= h/2
        # y_offset_to_box -= h/2

    h = h / 2
    for site in box_struct_pairs_split:
        # set index of box to which comparison is done
        # reference box is box that is more common
        # box_index and re_box_index were reversed
        # but somehow the most common box in the initial indices was
        # at the other position - therefore the indexes were flipped
        if site == "left":
            box_index = 0
            ref_box_index = 1
        else:
            box_index = 1
            ref_box_index = 0

        box_struct_pairs_sorted = box_struct_pairs_split[site]
        # get middle x position of all box significant to often occuring box


        if site == "left":
            x_outer = box_struct_pairs_sorted[0][box_index]['x']
            x_inner = box_struct_pairs_sorted[-1][box_index]['x']
        else:
            x_outer = box_struct_pairs_sorted[-1][box_index]['x']
            x_inner = box_struct_pairs_sorted[0][box_index]['x']

        x_mid = (x_outer+x_inner)/2

        x_box = box_struct_pairs_sorted[0][ref_box_index]['x']

        if site == "left":
            x1 = x_outer
            x2 = x_box
        else:
            x1 = x_box
            x2 = x_outer

        # get start y position
        # Find y maximum for all the y_stacks *in between* the box1 and the box2
        ymax_in_range_x1_x2 = np.max(y_stack_arr[1, np.where((x1 <= y_stack_arr[0, :]) &
                                                             (y_stack_arr[0, :] <= x2))
                                     ])
        i_ymax_in_range_x1_x2 = np.where(y_stack_arr[1, :] ==
                                         ymax_in_range_x1_x2)[0][0]

        # Choose the best offset depending on wether there is an annotation below
        # at the x position in the range [x1, x2] where the stack is the highest
        if y_stack_arr[2, i_ymax_in_range_x1_x2] == 0:
            # there is only a box below
            offset = y_offset_to_box * 2
            # offset = y_offset * 1.2# 1.4
        else:
            # there is an annotation below
            offset = y_offset * 2

        y = ymax_in_range_x1_x2 + offset

        # if fliers are shown in boxplot add additional y offset
        if show_data_points == False:
            # calculate what the fliersize in pt is in plot dimensions
            # its the fliersize in px divided by the plot height in px
            # and this multiplied by y_lim
            # plot_ax = all_ax_data["_-_-None-_-_"]
            # y_lim = all_ax_data["_-_-None-_-_"].get_ylim()[1]
            # fliersize_px = fliersize * 72
            # pot_ax_width = plot_ax.bbox.width
            # print(fliersize_px, plot_ax.bbox.height)
            # additional_y_offset = fliersize_px / plot_ax.bbox.height * y_lim
            # y += additional_y_offset
            # HOWEVER, code did not work well.
            # size of fliers seems to be not pt but something else
            # temporary fix:
            y += y_offset*1.5

        # draw line from box to mid point
        # from there go down and draw line from outer to inner significant box
        line_x = [x_box, x_box, x_mid, x_mid, x_outer, x_inner]
        line_y = [y, y + h, y + h, y+h/2,y+h/2,y+h/2]
        ax = draw_line(line_x, line_y, line_width, color, ax)

        # annotate significance
        # more label closer to line for stars
        if pval_text.find("*") != -1:
            y_text = y - y_offset/5
        else:
            y_text = y

        ann_list, y_top_annot, ax = plot_text(ax, pval_text, y_text, x_mid,
                                             x_box,text_offset,
                                             fontsize, h, use_fixed_offset,
                                             ann_list)

        if (site == "right") | ("right" not in box_struct_pairs_split):
            (all_ax_data,
             annotated_pairs,
             y_stack_arr,
             ax) = update_plot_and_arrays(y_stack_arr, y_top_annot, x1,x2 ,
                                          all_ax_data, ax, annotated_pairs,
                                          ymax_in_range_x1_x2, pval_text,
                                          box_struct_pair, loc)

        # if only one pair is in box_struct_pairs_sorted, don't draw line down,
        # there is already a line down to half the height
        # dont understand comment above anymore -
        # only draw line down for plots which were not annotated yet
        # if (len(box_struct_pairs_sorted)== 1) | (both_sites_have_boxes):
        # draw line down for each box
        for box_struct_pair in box_struct_pairs_sorted:
            box_struct = box_struct_pair[box_index]
            line_x  = [box_struct['x'], box_struct['x']]
            line_y = [y +h/2, y]

            ax = draw_line(line_x, line_y, line_width, color, ax)

        
    return ax, all_ax_data,annotated_pairs,y_stack_arr,ann_list


def get_x_shift_to_hor_center_plot(ax, col_order, nb_x_vals, total_nb_columns,
                                   outer_border, group_padding,
                                   auto_width_reduction_factor, legend_width,
                                   auto_scale_group_padding, hor_alignment):

    x_shift = 0

    ax_coords = ax.get_position()
    fig = plt.gcf()

    # adjust position of axes for additional space needed
    # by x axes label and y axes labels (including title)
    text_width = get_axis_dimension(ax, ax.yaxis, "width", outer_border[0])

    rel_width_text, _ = get_px_size_rel_to_subplot(ax,text_width,0)

    available_width = outer_border[1] - outer_border[0]

    # calculate width of all plots combined
    # by adding width of y axis to scaled up width of all plots
    # add space between groups to width of all plots
    total_width_between_groups = (group_padding * (len(col_order) - 1) /
                                  fig.get_size_inches()[0])
    if auto_scale_group_padding:
        total_width_between_groups *= auto_width_reduction_factor
    width_yaxis_text = rel_width_text * ax_coords.width
    width_all_plots = (ax_coords.width / nb_x_vals * total_nb_columns +
                       width_yaxis_text +
                       legend_width +
                       total_width_between_groups)
    rel_width_reduction = 1
    # check whether width of all plots is more than available width
    if available_width > width_all_plots:
        # if it is not more than available,
        # get space on both sides to center plots horizontally
        # dont reduce width if there is enough space available for all plots
        space_each_site = (available_width - width_all_plots) / 2
        if hor_alignment.lower() == "left":
            space_each_site = 0
        if hor_alignment.lower() == "right":
            space_each_site *= 2
        x_shift += space_each_site + rel_width_text * ax_coords.width

    elif available_width < width_all_plots:
        x_shift += rel_width_text * ax_coords.width
        # if it is more than available width,
        # reduce width by difference accordingly
        # TODO output warning that width available
        #  is not enough for plot and that boxes will be squeezed...
        print("WARNING: The width provided for the plot is not sufficient. "
              "Boxes will be squeezed.")
        # get relative width reduction for parts of the plot
        # for which width can be reduced
        # legend width and y axis width cannot be reduced due to fixed font size
        total_width_reduction = (width_all_plots - available_width)
        width_all_plots_reducible = (width_all_plots - width_yaxis_text -
                                     legend_width)
        rel_width_reduction = (width_all_plots_reducible /
                               (width_all_plots_reducible -
                                total_width_reduction))

    return x_shift, rel_width_reduction


def hor_center_plot(ax, x_shift, rel_width_reduction):
    """
    adjust position and size of plot to have padding to nearby panels and own panel letter horizontally
    """

    ax_coords = ax.get_position()

    # for first plot (leftmost with y axis ticks and label)
    # set the total amount of x-shift necessary to have sufficient padding on the right

    left = ax_coords.x0 + x_shift
    width = ax_coords.width / rel_width_reduction

    # reduce x_shift according to how much shift was already done now
    x_shift -= (ax_coords.width - width)

    ax.set_position([left,ax_coords.y0,width,ax_coords.height])

    return x_shift

def move_plot_into_hor_borders_and_center_it(all_axs, ax_annot, ax_labels,
                                             data, hue,
                                             hue_order, col, col_order, x,
                                             x_order, total_nb_columns,
                                            outer_border, group_padding,
                                             auto_width_reduction_factor,
                                            legend_width,
                                             auto_scale_group_padding,
                                             data_is_continuous,
                                             hor_alignment):
    fig = plt.gcf()
    # get width of all axs together


    for plot_nb, col_val in enumerate(col_order):
        ax = all_axs[col_val]
        col_data = data.loc[data[col] == col_val]
        if plot_nb == 0:
            if data_is_continuous:
                # for continuous plot types, the width of each
                # plot should not depend on the x values
                # but should be the same for all plots
                nb_boxes = total_nb_columns / len(col_order)
            else:
                nb_boxes = get_nb_of_boxes(data, x, x_order, hue, hue_order,
                                           col, col_order=[col_val])

            (x_shift,
             rel_width_reduction) = get_x_shift_to_hor_center_plot(ax, col_order,
                                                                   nb_boxes,
                                                                   total_nb_columns,
                                                                   outer_border,
                                                                   group_padding,
                                                                   auto_width_reduction_factor,
                                                                   legend_width,
                                                                   auto_scale_group_padding,
                                                                   hor_alignment)
            # adjust width and x position annotation plot accordingly
            ax_annot_coords = ax_annot.get_position()
            left = ax_annot_coords.x0 + x_shift
            width = ax_annot_coords.width / rel_width_reduction
            ax_annot.set_position([left, ax_annot_coords.y0,
                                   width, ax_annot_coords.height])

            # adjust width and x position annotation plot accordingly
            ax_labels_coords = ax_labels.get_position()
            left = ax_labels_coords.x0 + x_shift
            width = ax_labels_coords.width - x_shift
            ax_labels.set_position([left, ax_labels_coords.y0,
                                   width, ax_labels_coords.height])


            # coords = ax_annot.get_position()
            # # uncomment to see the borders of the panel
            # # helpful to judge if boxes are properly aligned
            # bg_ax = plt.gcf().add_axes([coords.x0,
            #                             coords.y0,
            #                             coords.width,
            #                             coords.height
            #                             ])

        x_shift = hor_center_plot(ax, x_shift, rel_width_reduction)

        # adjust x_shift to accomodate change in group_padding
        rel_group_padding = group_padding / fig.get_size_inches()[0]
        if auto_scale_group_padding:
            rel_group_padding *= auto_width_reduction_factor
            # reduce x_shift to account for changed space between plots
            x_shift -= rel_group_padding * (1 - 1 / rel_width_reduction)


def add_background_grid_lines_to_plots(all_axs, col_order, line_width, letter):
    # add grid lines for background when increasing space between groups
    # to have continuous grid lines
    fig = plt.gcf()
    ax_first = all_axs[col_order[0]]
    ax_last = all_axs[col_order[-1]]

    add_background_grid_lines(ax_first, ax_last, line_width,
                              letter, color="0.8")


def add_background_grid_lines(ax_first, ax_last, line_width, letter, color,
                              excluded_ytick_id = None):
    """
    :param excluded_ytick_ids: list of list-ids in yticks
                                that should be removed from y_ticks
    """
    fig = plt.gcf()
    ax_first_coords = ax_first.get_position()
    ax_last_coords = ax_last.get_position()
    y_lim = ax_first.get_ylim()
    yticks = ax_first.get_yticks()
    ylim_low = min(y_lim[0], y_lim[1])
    ylim_high = max(y_lim[0], y_lim[1])
    yticks = [tick for tick in yticks
              if (tick >= ylim_low) & (tick <= ylim_high)]
    grid_ax = fig.add_subplot(label="grid for letter " +letter,zorder=-1)
    grid_ax.set_ylim(y_lim[0],y_lim[1])
    grid_ax.set_position([ax_first_coords.x0, ax_first_coords.y0,
                          ax_last_coords.x1 - ax_first_coords.x0,
                          ax_first_coords.height])
    # grid_ax.set_axis_off()
    # remove border around axis
    grid_ax.spines['bottom'].set_color('None')
    grid_ax.spines['top'].set_color('None')
    grid_ax.spines['right'].set_color('None')
    grid_ax.spines['left'].set_color('None')
    grid_ax.set_xticks([])
    grid_ax.set_yticks([])
    # grid_ax.set_facecolor("white")
    if excluded_ytick_id != None:
        del yticks[excluded_ytick_id]
    for y_tick in yticks:
        line_x, line_y = [0, 1], [y_tick,y_tick]
        line = lines.Line2D(line_x, line_y, c=color,  zorder=-1,
                            lw=line_width, solid_capstyle="butt")
        line.set_clip_on(False)
        grid_ax.add_line(line)

def add_labels_within_ax(all_labels_to_add):
    """
    adds labels that should go within plot at very last step.
    This way, the labels are not affected by repositioning of the plot
    that happened between adding the label and the plot being done
    :param all_labels_to_add: List of dicts
                    with the method by which the label should be added as
                    value with the key "label_method"
                    and all parameters of the label method
                    as other key with value
                    value can also be a partial function,
                    in which case the value will be retrieved
                    at the time of adding the label
                    this should usually be done
                    for the position of the label since this position
                    will change if the ax is changed (resized etc.)
    """
    for label_to_add in all_labels_to_add:
        params = {}
        for key, value in label_to_add.items():
            if key != "label_method":
                if type(value) == functools.partial:
                    params[key] = value()
                else:
                    params[key] = value

        label_to_add["label_method"](**params)

def plot_and_add_stat_annotation(data=None, x=None, y=None, hue=None, x_order=[],
                        hue_order=[], box_pairs=[], col=None, col_order=[],
                        y_range = None, x_range = None, hor_alignment ="left",
                        show_col_labels_above = False,
                                 show_col_labels_below=True,
                        perform_stat_test=True,
                        pvalues=None, test_short_name=None,
                        test="Dunn", text_format='star', pvalue_format_string=DEFAULT,
                        text_annot_custom=None, outer_border=None,# padding=0.5,
                        loc='inside', show_test_name=True,
                        figure_panel=None, always_show_col_label=False,
                        meanline_props=None, plot_type="box", bar_plot_dodge=True,
                        pvalue_thresholds=DEFAULT, stats_params=dict(),
                        y_axis_label=None, fig=None, show_x_axis=True,
                        show_y_axis=True,
                        letter=None, annotate_nonsignificant=False,
                        use_fixed_offset=False, line_offset_to_box=None,
                        line_offset=None, line_height=0.15, text_offset=1,
                        color='0.2', line_width=0.8, line_width_thin=0.3,
                        fontsize='medium', verbose=False, plot_colors=-1,
                        show_data_points=True, connect_paired_data_points=True,
                        pair_unit_columns=None,
                        connecting_line_width=1, connecting_line_alpha=0.1,
                        connecting_line_color="black",
                        neg_y_vals=True, inner_padding=1, box_width=0.4,
                                 background_color="0.98",
                        size_factor=1, group_padding=0.04, legend_spacing = 0.25,
                        x_axis_label = None, x_tick_interval=None, y_tick_interval=None,
                        axis_padding=10, fliersize=3,
                        show_formula=True, position_formula="top-right",
                                 show_regression_stats = True, legend_title=None,
                        show_legend=True, col_label_padding=4,
                        swarmplot_point_size = 2, show_row_label = False,
                        row_label_text=None, row_label_orientation = "vert",
                        auto_scale_group_padding = True,
                        plot_title = None, show_y_minor_ticks=False,
                        borderaxespad_ = 0.2,
                        add_background_lines = True, vertical_lines=False,
                        show_stats_to_control_without_lines=False,
                        show_x_label_in_all_columns=True,
                        legend_handle_length=2,
                        x_tick_label_rotation=False,
                        _leave_space_for_legend=False,
                                 for_measuring=False):
    """
    Optionally computes statistical test between pairs of data series, and add statistical annotation on top
    of the boxes. Uses the same exact arguments `data`, `x`, `y`, `hue`, `order`,
    `hue_order` as the seaborn boxplot function.
    This function works in one of the two following modes:
    a) `perform_stat_test` is True: statistical test as given by argument `test` is performed.
    b) `perform_stat_test` is False: no statistical test is performed, list of custom p-values `pvalues` are
       used for each pair of boxes. The `test_short_name` argument is then used as the name of the
       custom statistical test.
    :param line_height: in axes fraction coordinates
    :param text_offset: in points
    :param box_pairs: can be of either form:
        For non-grouped boxplot: `[[cat1, cat2], [cat3, cat4]]`.
        For boxplot grouped by hue: `[[(cat1, hue1), (cat2, hue2)], [(cat3, hue3), (cat4, hue4)]]`
        For boxplots grouped by hue and an additional column (col):
            '[[(col1,cat1, hue1), (col2,cat2, hue2)], [(col3,cat3, hue3), (col4,cat4, hue4)]]'
    :param col: group that is plotted in columns of plot for a three-level plot
    :param hor_alignment: "right", "left" or "center", horizontal alignment of plots in panel
                        plots always will the entire y space but not necessarily the entire x space.
                        therefore alignment in x matters but not in y

    :param bar_plot_dodge: Bool; dodge parameter for barplot, will lead to
                            stacked barplots if hue is defined
    :param pvalue_format_string: defaults to `"{.3e}"`
    :param pvalue_thresholds: list of lists, or tuples. Default is:
                                For "star" text_format: `[[1e-4, "****"],
                                [1e-3, "***"], [1e-2, "**"], [0.05, "*"],
                                [1, "ns"]]`. For "simple" text_format :
                                `[[1e-5, "1e-5"], [1e-4, "1e-4"],
                                [1e-3, "0.001"], [1e-2, "0.01"]]`
    :param pvalues: list of p-values for each box pair comparison.
    :param neg_y_vals: are there data points below zero, if not lowest y axis
                        value is 0 (margin settings will make it lower
                        than zero otherwise)
    :param padding: padding between panels in inches (is autoscaled by size factor in figure script)
    :param box_width: maximum box width in inches - scaled by width of one column in inches / 2
    :param group_padding: space between two cols in inches - scaled by width of one column in inches / 2
    :param legend_spacing: space between legend handles (color boxes) and legend text
    :param axis_padding: padding between plot and y_axis ticks in points (really?)
    :param show_formula: Bool, Whether formula should be shown in plot for plotting regressions (plot_type="regression")
    :param position_formula: String, Position where the formula should be shown in plot in x and y dimension:
                            for x left and right and for y top and bottom, both positions combined with a "-"
                            e.g. "bottom-left" or "top-right"
    :param auto_scale_group_padding: Bool; Whether defined group_padding should be scaled automatically
                                            Autoscaling scales space between plots as much as the size of plots
                                            Thereby boxes becoming too small due to group padding is prevented
                                            automatically
                                            this reduces a bit of manual work, however, for facet plots it cannot
                                            be used since the exact size of the group padding is necessary
                                            for a proper grid-like arrangement
    :param show_row_label: Bool; Whether there should be a label displayed right of the rightmost plot
                            when True, legend will not be displayed automatically
                            (both together is not implemented at the moment)
    :param borderaxespad_: in points, padding of legend from plot and also of row label from plot
    :param vertical_lines: Boolean, Whether thin vertical lines should be drawn for each box
    :param x_tick_label_rotation: Boolean, Whether the x tick labels
                                    should be rotated by 45 degree
    :param _leave_space_for_legend: Internal parameter to indicate whether space for legend should be kept free
                                    even if legend was removed
    :param plot_title: String; Title of the plot that will be added above the plot

    """

    continuous_plot_types = ["line", "regression", "scatter"]

    if show_col_labels_above:
        show_col_labels_below = False

    # do not scale group padding for continuous plots
    if plot_type in continuous_plot_types:
        data_is_continuous = True
    else:
        data_is_continuous = False

    if data_is_continuous:
        auto_scale_group_padding = False
        show_data_points = False


    # convert all values according to size factor
    # inner_padding *= size_factor
    # text_offset *= size_factor
    # line_width *= size_factor
    # line_width_thin *= size_factor
    box_width *= size_factor
    # group_padding *= size_factor

    adjust_figure_aesthetics(background_color)

    if len(x_order) == 0:
        x_order = data[x].drop_duplicates().values

    (col_order, col, hue,
     hue_order, plot_hue,
     total_nb_columns) = process_col_and_hue(data, col, x, hue,
                                             x_order, col_order, hue_order)

    # especially important for facet plots using row parameter in FigurePanel
    # if x_range is defined, it will be the same between all
    if type(x_range) != type(None):
        total_nb_columns = len(col_order) * np.abs(x_range[1] - x_range[0])



    # dont perform stat test if there is only one group ploted
    if total_nb_columns == 1:
        perform_stat_test = False

    # Validate arguments
    box_pairs = validate_arguments(perform_stat_test,test,pvalues,test_short_name,
                           box_pairs,loc,text_format,text_annot_custom)

    (pvalue_thresholds,
     pvalue_format_string,
     simple_format_string) = set_pval_arguments(text_format, verbose,
                                                pvalue_thresholds,
                                                pvalue_format_string)

    ax_annot = add_annotation_subplot(letter, outer_border)

    ax_labels = add_annotation_subplot(letter + "_labels", outer_border)

    # initiate variables
    (all_box_structs_dics, all_box_names,
     all_box_structs, all_axs, axs_by_position) = ({}, {}, {}, {}, {})

    # start counter of current subplot
    plot_nb = 1
    # start counter of current column (not current subpot!) and initialize other variables
    # y_shift is shift iny  from the bottom
    (current_column, max_yrange, min_y, max_y,
     x_shift, y_shift, rel_width_reduction) = (0, 0, 0, 0, 0, 0, 0)
    auto_width_reduction_factor = 0
    longest_legend_handles = []

    # set y_range
    # allow for y lim being manually set
    # used to unify ylim when row is defined for showing data in figure_panel
    if type(y_range) == type(None):
        # ax needs to be created in same position as it will be afterwards
        # that way the realistic y range can be determined
        # and also that way no other data will be overlapped by plot
        # which can lead to deleted segments in videos
        ax = create_column_subplot(outer_border = outer_border,
                                   column=current_column,
                                   grid_columns=total_nb_columns,
                                   column_span= 1,
                                   label="y_range_measure_plot")
        # plot data to measure y_lim
        plot_data(ax, x, y, plot_hue, data,
                  x_order, hue_order, plot_colors,
                  show_data_points, line_width, size_factor, plot_type,
                  fliersize, show_formula, position_formula,
                  show_regression_stats, figure_panel,
                  swarmplot_point_size, bar_plot_dodge, x_range,
                  connect_paired_data_points)
        y_range = ax.get_ylim()
        ax.remove()

    yrange = y_range[1] - y_range[0]
    # use offsets based on highest yrange for all plots
    max_yrange = yrange

    (line_offset, loc,
     line_offset_to_box,
     yrange, y_offset,
     y_offset_to_box) = set_offsets(line_offset, loc,
                                    line_offset_to_box, yrange)

    # get maximum number of lines in col val
    max_nb_col_val_lines = 0
    for col_val in col_order:
        nb_lines_col_val = len(col_val.split("\n"))
        max_nb_col_val_lines = max(max_nb_col_val_lines, nb_lines_col_val)

    all_labels_to_add = []
    for col_nb, col_val in enumerate(col_order):

        col_data = data.loc[data[col] == col_val]

        # get number of x values that will be plotted (defines width of subplot)
        # remove x vals from x_order that are not present in current group

        new_x_order = get_all_vals_from_order_in_data(col_data, x, x_order)
        nb_x_vals = len(new_x_order)

        new_hue_order = get_all_vals_from_order_in_data(col_data, hue, hue_order)

        # TODO: get number of x vals for each hue instead of assuming
        # that each hue is present for each x!
        if (not data_is_continuous):
            if (hue != "no_hue_defined"):
                nb_x_vals *= len(new_hue_order)
        else:
            # for continuous x data
            # every plot should have the same size
            # independent of the number of x values
            nb_x_vals = total_nb_columns / len(col_order)

            # if type(x_range) != type(None):
            #     nb_x_vals = np.abs(x_range[1] - x_range[0])

        # create axes subplot in standard grid
        # label has to be unique to create new axes object
        # other old axes object will be reused!
        # (this only applies to older matplotlib versions)
        ax = create_column_subplot(outer_border = outer_border,
                                   column=current_column,
                                   grid_columns=total_nb_columns,
                                   column_span= nb_x_vals,
                                   label=("data_plot " +
                                           str(col_val) + " " +
                                           letter +
                                            str(y) +
                                            str(x) +
                                           str(row_label_text) +
                                           str(for_measuring) +
                                           str(max(data[x]))))

        ax.set_ylim(y_range[0], y_range[1])

        if show_y_minor_ticks:
            ax.minorticks_on()
            ax.xaxis.set_tick_params(which='minor', bottom=False)

        if type(x_tick_interval) != type(None):
            new_locator = mplticker.MultipleLocator(base=x_tick_interval)
            ax.xaxis.set_major_locator(new_locator)

        if type(y_tick_interval) != type(None):
            new_locator = mplticker.MultipleLocator(base=y_tick_interval)
            ax.yaxis.set_major_locator(new_locator)

        if type(x_range) != type(None):
            ax.set_xlim(x_range[0], x_range[1])


        # advance currentColumn ticker
        current_column += nb_x_vals

        if (not data_is_continuous):
            # adjust size of ax to standardize size of box, needs to be done before plotting data
            # if done after plotting data, swarmplot will be squeezed, leading to overlap of points
            (ax,
             width_reduction_by_changing_box_size,
             auto_width_reduction_factor) = change_plot_size_to_standardize_box_size(ax,
                                                                                     nb_x_vals,
                                                                                     box_width,
                                                                                     hue,
                                                                                     new_hue_order)
        else:
            width_reduction_by_changing_box_size = 0
            auto_width_reduction_factor = 0


        # plot boxplot and swarmplot and get box_plotter object (necessary to extract information about boxes later)
        box_plotter, labels_to_add = plot_data(ax, x, y, plot_hue, col_data,
                                                new_x_order, new_hue_order, plot_colors,
                                                show_data_points, line_width, size_factor, plot_type,
                                                fliersize, show_formula, position_formula,
                                               show_regression_stats, figure_panel,
                                                swarmplot_point_size, bar_plot_dodge, x_range,
                                               connect_paired_data_points)

        if (connect_paired_data_points):
            add_lines_to_connect_paired_data_points(col_data, ax, nb_x_vals, x, y, hue,
                                             new_x_order, new_hue_order,
                                                connecting_line_color,
                                                connecting_line_alpha,
                                                connecting_line_width,
                                                    pair_unit_columns)

        all_labels_to_add = [*all_labels_to_add, *labels_to_add]

        rel_height_change = 0

        # get overflow of y-axis tick labels (going above axis)
        # and correct for that

        # rotate x axis labels
        if x_tick_label_rotation == True:
            # rotate x labels
            for label in ax.get_xticklabels():
                label.set_ha("right")
                label.set_rotation(45)

        # set the legend as well as axes labels and padding
        (legend_width,
         longest_legend_handles) = set_legend_and_axes(ax, col_order, plot_nb,
                                                       hue_order, y_axis_label,
                                                       x_order, fontsize,
                                                       legend_spacing,
                                                       longest_legend_handles,
                                                       show_x_axis, x_axis_label,
                                                       legend_title, show_row_label,
                                                       row_label_text,
                                                       row_label_orientation,
                                                       show_legend, borderaxespad_,
                                                       legend_handle_length,
                                                       show_x_label_in_all_columns,
                                                       _leave_space_for_legend,
                                                       data_is_continuous,
                                                       show_data_points,
                                                       connect_paired_data_points)

        # if y axis should not be shown
        # until now only used if x axis without anythoing else should be plotted
        if not show_y_axis:
            ax.yaxis.set_visible(False)

        # ax.annotate(xy=(0.5, 0.5), text="this is a test",fontsize=12, xycoords="axes fraction")

        # if there are ticklabels on x axis, increase inner padding by line width
        # only with tick labels the line will be added and therefore needs to be considered

        if (plot_nb == 1) & (ax.xaxis.get_ticklabel_extents(fig.canvas.get_renderer())[0].height > 0):
            inner_padding += line_width
        

        axis_padding = set_axis_label_paddings(inner_padding, axis_padding, ax,
                                                plot_nb, outer_border, size_factor)

        if plot_nb == 1:
            # for first plot (leftmost with y axis ticks and label)
            # set the total amount of y-shift necessary to have sufficient padding on top and bottom
            y_shift = get_y_shift_to_vert_fill_outer_border(ax, col,
                                                            col_order,
                                                            max_nb_col_val_lines,
                                                            y_shift, inner_padding,
                                                            fontsize, outer_border,
                                                            show_col_labels_below,
                                                            always_show_col_label)

        rel_height_change = vert_fill_outer_border(ax, y_shift, rel_height_change)

        # shift ax to get padding between groups
        ax_coords = ax.get_position()
        ax.set_position([ax_coords.x0 + x_shift, ax_coords.y0, ax_coords.width, ax_coords.height])


        # adjust height of annotation plot once (for the first plot)
        if plot_nb == 1:
            adjust_annotation_plot_height_and_y(ax_annot, y_shift, rel_height_change)
            adjust_annotation_plot_height_and_y(ax_labels, y_shift, rel_height_change)


        plot_nb += 1

        # increase space of next group by group_padding value (in inches)
        # scale with rel_surplus_width to account
        # for reduction in size to lower than box_width
        # which was automatically done by matplotlib since not enough space was available
        # do not scale group padding anymore!
        if auto_scale_group_padding:
            x_shift += group_padding / fig.get_size_inches()[0] * auto_width_reduction_factor
        else:
            x_shift += group_padding / fig.get_size_inches()[0]

        # reduce x shift if subplot was made narrower in the process of
        # standardizing the box size to keep subplots close together
        x_shift -= width_reduction_by_changing_box_size

        # Always extract group information since it's also needed to plot
        # col values below
        # get box structs containing all information about boxes plotted in this group (col)
        box_structs_dic,box_names,box_structs = build_box_structs_dic(box_plotter,
                                                                      col_val,
                                                                      hue, ax,
                                                                      ax_annot)

        # add parameters to dict with group name as key
        all_box_structs[col_val] = box_structs
            
        all_box_structs_dics[col_val] = box_structs_dic
        all_box_names[col_val] = box_names
        all_axs[col_val] = ax
        # first position is row
        # set row to 0 in case only one row was plotted
        # if more than one row was plotted
        # the row value will be updated in a separate dict
        axs_by_position[(0, col_nb)] = ax

    # add ax_annot again with same position to make it appear on top of all other plots
    ax_annot = add_annotation_subplot(letter+"_new",outer_border,ax_annot)

    # exclude data based on order given for different columns
    included_data = exclude_data(data,col,col_order,x,x_order,hue,hue_order)

    ann_list = []
    test_result_list = []
    annotated_pairs = {}
    if perform_stat_test:

        # get all box pairs depending on grouping of data (group, hue) and whether pairs were added
        # get maximum level of pairs for comparison, will determine where statistics will be performed on
        all_box_pairs, max_level_of_pairs = get_all_box_pairs(box_pairs, data,
                                                              col, col_order,
                                                              x, x_order,
                                                              hue, hue_order)

        # do statistics on correct level (within group or within x, depending on how pairs look like)
        # if annotate_nonsignificant is False, also exclude non significant box_pairs
        # TO ADD: CHOICE OF STAT TEST
        # POSSIBLY TO ADD: automatic choice of test depending on normal distribution of data
        (all_box_pairs,
         p_values,
         test_result_list) = get_stats_and_exclude_nonsignificant(included_data,col, x, y, hue,
                                                                    all_box_pairs, max_level_of_pairs,
                                                                    test_short_name, test_result_list,
                                                                    annotate_nonsignificant,verbose)

        # Build array that contains the x and y_max position of the highest annotation or box data at
        # a given x position, and also keeps track of the number of stacked annotations.
        # This array will be updated when a new annotation is drawn.
        # combine all arrays from all subplots
        y_stack_arr = np.array([[box_struct['x'] for box_structs in all_box_structs.values() for box_struct in box_structs],
                                [box_struct['ymax'] if not np.isnan(box_struct['ymax']) else 0 for box_structs in all_box_structs.values() for box_struct in box_structs],
                                [0 for box_structs in all_box_structs.values() for i in range(len(box_structs)) ]])

        if loc == 'outside':
            y_stack_arr[1, :] = ylim[1]

        # within pairs with same x val and pairs with different x val sort separately:
        box_pairs_grouped = group_box_pairs_in_same_x(all_box_pairs)

        # create dict with all texts to be annotated
        pval_texts =  get_annotated_text_dict(p_values,pvalue_format_string,
                                              test_short_name,pvalue_thresholds,
                                              show_test_name,text_format)

        h = line_height * max_yrange
        for x_val, box_pairs_of_x in box_pairs_grouped.items():
            if (x_val != "different_x") & (hue != "no_hue_defined") & show_stats_to_control_without_lines:
                (box_pairs_of_x,
                 ann_list,
                 ax_annot,
                 all_axs,
                 annotated_pairs,
                 y_stack_arr) = plot_comparison_to_control_within_x(box_pairs_of_x,
                                                hue_order,x_val,hue, col,
                                                pval_texts, all_box_names, all_box_structs_dics,
                                                ann_list, ax_annot, text_offset, y_offset_to_box,
                                                fontsize, all_axs, annotated_pairs,
                                                y_stack_arr, h, use_fixed_offset, loc)


            box_counter, all_boxes = count_occurences_of_boxes_in_pairs(box_pairs_of_x,
                                                                        pval_texts)

            # sort pairs by number of occurence of most occuring box in pair
            # make ranking of all boxes
            all_boxes_sorted = sorted(all_boxes, reverse=True,
                                      key=lambda x: box_counter[x])

            box_struct_pairs_grouped = get_box_dict_pairs_grouped_by_ranking(all_boxes_sorted,
                                                                             box_pairs_of_x,
                                                                             pval_texts,
                                                                             all_box_names,
                                                                             all_box_structs_dics,
                                                                             col)

            # sort groups by max y so that lower positioned annotations are done first
            max_y_groups = {}
            for box_tuple, box_struct_pairs in box_struct_pairs_grouped.items():
                max_y_group = 0
                for box_struct_pair in box_struct_pairs:
                    for box_struct in box_struct_pair:
                        max_y = box_struct["box_data"].max()
                        max_y_group = max(max_y_group, max_y)
                max_y_groups[box_tuple] = max_y_group

            box_struct_pairs_grouped = {k: v for k, v in
                                        sorted(box_struct_pairs_grouped.items(),
                                               key=lambda item:
                                               max_y_groups[item[0]])}

            # go through each of the groups ranked by commonly occuring boxes
            for (annot_number,
                 (box_tuple,
                  box_struct_pairs)) in enumerate(box_struct_pairs_grouped.items()):

                # if x_val == "different_x":
                #     # calculate correction factor for increased height of plot after adding plots
                #     correction_factor = (1 + ((len(box_struct_pairs_grouped) -
                #                                annot_number) *
                #                               (line_height +
                #                                y_offset / yrange)))
                #     h *= correction_factor / 1.5
                #     y_offset *= correction_factor
                #     y_offset_to_box *= correction_factor

                # if annot_number == 1:
                #     dasd

                box = box_tuple[0]
                # annotate all box_pairs in a group
                (ax_annot,
                 all_axs,
                 annotated_pairs,
                 y_stack_arr,
                 ann_list) = annotate_box_pair_group(box_struct_pairs, box_tuple,
                                                     box, y_stack_arr,
                                                     all_axs, ax_annot,
                                                     annotated_pairs, text_offset,
                                                     fontsize, h, ann_list,
                                                     line_width, loc,
                                                     y_offset_to_box,
                                                     y_offset, color,
                                                     use_fixed_offset,
                                                     show_data_points, fliersize)

    # plot a title above all plots (in ax_labels)
    if (type(plot_title) != type(None)):
        # plt.title(title_above)
        col_label_height = add_column_plot_title_above(ax_labels,
                                                       plot_title,
                                                       col_label_padding,
                                                       fontsize)
        # move all data plots down
        for ax in all_axs.values():
            coords = ax.get_position()
            ax.set_position([coords.x0, coords.y0, coords.width,
                             coords.height - col_label_height])
        for ax in [ax_annot, ax_labels]:
            coords = ax.get_position()
            ax.set_position([coords.x0, coords.y0, coords.width,
                                 coords.height - col_label_height])

    # move overhanging axis tick labels into inner_border
    for ax_nb, ax in enumerate(all_axs.values()):

        # only the first ax has a y column, therefore
        # get values fom that ax
        if ax_nb == 0:
            y_axis_ticks_overhang_rel = get_axis_tick_labels_overhang(ax, "y")
            # do the same for the x axis but with x and width instead of y and height
            # however, only if the plot is a continuous plot
            # meaning that it has a continuous x axis where values can be at the end
            if data_is_continuous:
                x_axis_tick_overhang_rel = get_axis_tick_labels_overhang(ax, "x")
            else:
                x_axis_tick_overhang_rel = 0

        axis_size = ax.get_position()
        # then set new axis position with reduced height and reduced width
        ax.set_position([axis_size.x0, axis_size.y0,
                        axis_size.width - x_axis_tick_overhang_rel,
                        axis_size.height - y_axis_ticks_overhang_rel])

    for ax in [ax_annot, ax_labels]:
        # also move ax_annot to have consistent positioning of annotations
        axis_size = ax.get_position()
        # then set new axis position with reduced height and reduced width
        ax.set_position([axis_size.x0, axis_size.y0,
                         axis_size.width - x_axis_tick_overhang_rel,
                         axis_size.height - y_axis_ticks_overhang_rel])

    # Finetuning plot needs to happen after final height is set
    # otherwise the line collides with text
    for col_val,box_structs in all_box_structs.items():
        # if any data was plotted for this col_val
        if (len(box_structs) == 0) & (col_val != "_-_-None-_-_"):
            continue
        ax = all_axs[col_val]
        # adjust several parameters of plots to improve visuals and used labels
        # ALSO add column labels below plot
        ax = finetune_plot(ax, box_structs,col, col_order, perform_stat_test,
                            line_width, line_width_thin, inner_padding,
                            fontsize, col_val, plot_type, vertical_lines,
                           show_col_labels_below, always_show_col_label)

    # if no neg_y_vals are in the plot
    # set lower ylim as slightly below 0
    # so that no points are cut off
    # this will be overwritten when supplying a y_range
    if not neg_y_vals:
        for ax in all_axs.values():
            ax.set_ylim(-0.05, ax.get_ylim()[1])

    for ax in all_axs.values():

        if type(y_range) == type(None):
            continue

        # ax.set_ylim(y_range[0], y_range[1])
        # ax.tick_params(axis="y", which="minor", )
        # ax.tick_params(axis='y', which='minor', bottom=False)
        # ax.set_yticks([0.75, 0.85, .95], minor=True)

        if plot_type == "line":
            line_color = "0.7"
        else:
            line_color = "0.8"

        ax.grid(b=True, color=line_color, linestyle='-', which="major",
                axis="y", linewidth=line_width)

        if plot_type == "line":
            # visible needs to be set True for line plots
            # it seems that somewhere the grid is switched off
            # and therefore just supplying kwargs to the function
            # does not automatically turn the grid visibility on
            ax.grid(visible=True,color=line_color, linestyle='-', which="major",
                    axis="x", linewidth=line_width)

        if show_y_minor_ticks:
            ax.grid(visible=True, b=False, color=line_color, linestyle='-',
                    which="minor", axis="y", linewidth=line_width_thin)

    # move plot to within outer_border horizontally (axes labeling is outside of ax and thereby of outer_border)
    # center the plot then horizontally
    # if the whole plot is wider than the available space (the axs fill up the outer border space),
    # then reduce width of all plots together by the width of the y axes label that needs to move into the outer_border
    # needs to be last step since x shift and width reduction depend on y tick label
    # which are adjusted while ylim is changed and when annotations are added
    move_plot_into_hor_borders_and_center_it(all_axs, ax_annot,
                                             ax_labels, data, hue,
                                             hue_order, col, col_order, x,
                                             x_order, total_nb_columns,
                                             outer_border, group_padding,
                                             auto_width_reduction_factor,
                                             legend_width,
                                             auto_scale_group_padding,
                                             data_is_continuous, hor_alignment)

    add_labels_within_ax(all_labels_to_add)
    if add_background_lines:
        # add lines at yticks in background to allow for space between plots of different cols
        # otherwise there would not be grid lines between plots
        add_background_grid_lines_to_plots(all_axs, col_order,
                                           line_width, letter)

    return axs_by_position, ax_annot, test_result_list