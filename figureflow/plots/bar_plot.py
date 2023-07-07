from .group_plot import GroupPlot
from .swarm_plot import SwarmPlot
import seaborn as sns
import numpy as np
import matplotlib as mpl


class BarPlot(GroupPlot):
    CONTINUOUS_X = False

    def __init__(self, x, y, hue, data, x_order, hue_order, plot_colors,
                 size_factor, ax, plot_type, line_width, swarmplot_point_size = 2,
                 show_data_points=True, connect_paired_data_points = True,
                 bar_plot_dodge = True, **kwargs):
        """
        :param bar_plot_dodge: Bool; dodge parameter for barplot, will lead to
                                stacked barplots if hue is defined
        """
        super().__init__(x, y, hue, data, x_order, hue_order, plot_colors,
                         size_factor, ax, plot_type,
                         swarm_plot_point_size=swarmplot_point_size,
                         show_data_points=show_data_points,
                         connect_paired_data_points=connect_paired_data_points,
                         **kwargs)
        self.bar_plot_dodge = bar_plot_dodge
        self.line_width = line_width
        # needed to plot swarm plot in group_plot function plot
        self.SwarmPlot = SwarmPlot
        self.ax = ax

    def plot(self):
        super().plot()
        plot = sns.categorical._BarPlotter(x=self.x, y=self.y, hue=self.hue,
                                           data=self.data, order=self.x_order,
                                           hue_order=self.hue_order,
                                           palette=self.plot_colors,
                                           estimator=np.mean, ci=None,
                                           n_boot=None, units=None, seed=None,
                                           orient=None, color=None,
                                           saturation=1, errcolor=None,
                                           errwidth=0, capsize=None,
                                           dodge=self.bar_plot_dodge)
        # plot = sns.barplot(x=x, y=y, hue=hue, data=data, order=x_order, hue_order=hue_order, palette=plot_colors)
        # set gray of boxplot manually since it is otherwise determined by the colors used in the plotted box_ends
        # this can lead to different grays for different subplots if only a part of the colors are plotted in one of them
        gray = mpl.colors.rgb2hex((0, 0, 0))
        plot.gray = gray
        plot.plot(self.ax, {"linewidth":self.line_width,"edgecolor":"black"})
        if self.connect_paired_data_points:
            self.add_lines_to_connect_paired_data_points()
        return plot, []