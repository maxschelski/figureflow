import seaborn as sns
import pandas as pd
import numpy as np
import scipy
from matplotlib.font_manager import FontProperties
import functools

class RegressionPlot():
    def __init__(self, x, y, hue, data, plot_colors,size_factor, ax,
                 show_formula=True,
                 position_regression_text = "top-left",
                 show_regression_stats = True, figure_panel=None,**kwargs):
        """
        Plotter for a regression of two parameters in a single group (no "hue"
        supported, therefore coloring not supported)

        :param show_formula: Bool, Whether formula should be shown in plot for
                            plotting regressions (plot_type="regression")
        :param position_regression_text: String, Position where the formula should
                                be shown in plot in x and y dimension:
                                for x left and right and for y top and bottom,
                                both positions combined with a "-"
                                e.g. "bottom-left" or "top-right"
        """
        self.x = x
        self.y = y
        self.hue = hue
        self.plot_colors=plot_colors
        self.data = data
        self.ax = ax
        self.figure_panel = figure_panel

        self.show_formula = show_formula
        self.show_regression_stats = show_regression_stats
        self.position_regression_text = position_regression_text

        self.labels_to_add = []
        self.data[x] = pd.to_numeric(self.data[x])

        if type(hue) != type(None):
            raise ValueError("For regression plots no hue is supported. "
                             "Only one group of data can be plotted.")
            # nb_colors = len(data[hue].drop_duplicates())
        else:
            nb_colors = 1

        self.plot_colors = sns.color_palette(self.plot_colors,
                                             n_colors=nb_colors)

        self.line_kws = {}
        self.scatter_kws = {}

        if len(self.plot_colors) == 1:
            self.line_kws["color"] = self.plot_colors[0]
            self.scatter_kws["color"] = self.plot_colors[0]

        self.scatter_kws["sizes"] = [25 * size_factor]
        self.scatter_kws["alpha"] = 0.5

    def plot(self):
        plot = sns.regplot(
            data=self.data, x=self.x, y=self.y, line_kws=self.line_kws,
            scatter_kws=self.scatter_kws, ax=self.ax)

        if not (self.show_formula | self.show_regression_stats):
            return plot, self.labels_to_add

        txt_labels = []

        if self.show_formula:
            txt_labels.append(self.get_formula_string(plot))

        if self.show_regression_stats:
            txt_labels.append(self.get_regression_stat_string(self.data,
                                                              self.x, self.y))

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
            font_height_pt = self.add_text_to_be_plotted(label_nb, txt_label,
                                                         font_size_pt,
                                                         self.position_regression_text,
                                                         standard_x_position,
                                                         standard_y_position,
                                                         padding,
                                                         font_height_pt)

        return plot, self.labels_to_add

    def get_formula_string(self, plot):
        # get formulat of regression line
        x_line_vals = plot.get_lines()[0].get_xdata()
        y_line_vals = plot.get_lines()[0].get_ydata()
        results = scipy.stats.linregress(x_line_vals, y_line_vals)
        slope = np.round(results.slope, 2)
        intercept = np.round(results.intercept, 2)

        # make string of formula for regression line
        formula_txt = "y = " + str(slope) + "x + " + str(intercept)
        return formula_txt


    def get_regression_stat_string(self, data, x, y):
        r, p_val = scipy.stats.pearsonr(data[x], data[y])
        r = np.round(r,2)
        # round pval to two visible digits
        decimals_round = 1
        nb_non_zero = 0
        while True:
            p_val_rounded = np.round(p_val, decimals_round)
            decimals_round += 1
            if p_val_rounded > 0:
                nb_non_zero += 1
            if nb_non_zero == 2:
                break

        regression_text = "r = " + str(r) +"; p = " + str(p_val_rounded)
        return regression_text

    def add_text_to_be_plotted(self, label_nb, txt_label, font_size_pt,
                               position_regression_text, standard_x_position,
                               standard_y_position, padding, font_height_pt):
            font_height_pt += font_size_pt

            # increase font size by 10% to enable vertical padding
            # between first and second label
            font_height_pt += label_nb * font_size_pt * 0.1

            # add one number at end of string, seems that ax extends over the plot area by + 1.5 numbers
            txt_size_px = self.figure_panel.get_dimension_of_text(txt_label,
                                                              font_size_pt,
                                                              self.ax)
            txt_width_px = txt_size_px[0]

            self.labels_to_add.append({})
            # create function to get xy position when needed
            get_xy_of_text = self.figure_panel.get_xy_of_text_from_position
            self.labels_to_add[-1]["xy"] = functools.partial(get_xy_of_text,
                                                        txt_label, self.ax,
                                                        position_regression_text,
                                                        txt_width_px,
                                                        font_height_pt,
                                                        standard_x_position,
                                                        standard_y_position,
                                                        padding)
            self.labels_to_add[-1]["text"] = txt_label
            self.labels_to_add[-1]["fontsize"] = font_size_pt
            self.labels_to_add[-1]["xycoords"] = "axes fraction"
            self.labels_to_add[-1]["label_method"] = self.ax.annotate
            return font_height_pt