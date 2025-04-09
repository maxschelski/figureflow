import seaborn as sns
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np

class LinePlot():
    CONTINUOUS_X = True

    def __init__(self, x, y, hue, data, hue_order, plot_colors, ax,
                 x_range, ci=95, plot_line_group_cols=None,
                 plot_line_group_alpha=0.1, dashes=None,
                 use_dashes_for_hue=False, estimator="mean",
                 **kwargs):
        """

        :param plot_line_group_cols: List of columns for which unique combinations
            (only for plot_type == line)
        """
        data[x] = pd.to_numeric(data[x])
        data.sort_values(x, inplace=True)

        self.data = data
        self.x = x
        self.hue = hue
        self.hue_order = hue_order
        self.ax = ax
        self.x_range = x_range
        self.ci = ci
        self.plot_line_group_cols = plot_line_group_cols
        self.plot_line_group_alpha = plot_line_group_alpha
        self.dashes = dashes
        self.use_dashes_for_hue = use_dashes_for_hue
        self.estimator = estimator

        if type(hue) == type(None):
            nb_colors = 1
        else:
            if len(hue_order) > 0:
                nb_colors = len(hue_order)
            else:
                nb_colors = len(data[hue].drop_duplicates())

        self.plot_colors = sns.color_palette(plot_colors, n_colors=nb_colors)
        self.variables = {}
        self.variables["x"] = x
        self.variables["y"] = y
        if hue is not None:
            self.variables["hue"] = hue
            if self.use_dashes_for_hue:
                self.variables["style"] = hue
                if self.dashes is None:
                    self.dashes = True

    def plot(self):
        # sns.lineplot(data=self.data, x=self.x, y=self.variables["y"],
        #              ax=self.ax)

        plot = sns.relational._LinePlotter(
                data=self.data, variables=self.variables,
                estimator=self.estimator, ci=self.ci, n_boot=1000, seed=None,
                sort=None, err_style="band", err_kws=None, legend="full")

        plot.map_hue(palette=self.plot_colors, order=self.hue_order, norm=None)

        if self.use_dashes_for_hue:
            plot.map_style(markers=None, dashes=self.dashes,
                           order=self.hue_order)
        
        plot._attach(self.ax)

        # only set x range if x_range is not fixed
        if type(self.x_range) == type(None):
            min_x = self.data[self.x].min()
            max_x = self.data[self.x].max()
            self.ax.set_xlim(min_x, max_x)

        if self.hue is None:
            kws = {"color": self.plot_colors[0]}
        else:
            kws = {}

        if self.plot_line_group_cols is not None:
            groups = self.data[self.plot_line_group_cols].drop_duplicates()
            if len(groups) > 1:
                for group in groups.values:
                    # exclude groups where all group vals are NaN
                    all_groups_nan = True
                    for group_val in group:
                        if not np.isnan(group_val):
                            all_groups_nan=False
                            break
                    if all_groups_nan:
                        continue
                    plot_data = self.data.set_index(self.plot_line_group_cols)
                    plot_data = plot_data.loc[tuple(group)]

                    self.ax.plot(plot_data[self.variables["x"]],
                                 plot_data[self.variables["y"]],
                                 color="Silver", alpha=self.plot_line_group_alpha)

        plot.plot(self.ax,kws)

        return plot, []