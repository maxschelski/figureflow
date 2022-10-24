from .group_plot import GroupPlot
from .swarm_plot import SwarmPlot
import seaborn as sns

class BoxPlot(GroupPlot):
    def __init__(self, x, y, hue, data, x_order, hue_order, plot_colors,
                 size_factor,  ax, plot_type,  swarm_plot_point_size=2,
                 show_data_points=True, connect_paired_data_points = True,
                 show_mean_line=True, show_outliers=False, fliersize=3,
                 line_width=1,
                 **kwargs):
        super().__init__(x, y, hue, data, x_order, hue_order, plot_colors,
                         size_factor,  ax, plot_type,
                         swarm_plot_point_size=swarm_plot_point_size,
                         show_data_points=show_data_points,
                         connect_paired_data_points=connect_paired_data_points,
                         **kwargs)
        self.show_mean_line = show_mean_line
        self.show_outliers = show_outliers
        self.fliersize = fliersize
        self.line_width = line_width
        self.ax = ax
        # needed to plot swarm plot in group_plot function plot
        self.SwarmPlot = SwarmPlot

    def plot(self):
        super().plot()
        box_plotter = self.create_box_plotter()

        meanline_props = dict(linestyle='-', linewidth=self.line_width * 2,
                             color='black', solid_capstyle="butt")
        plot_kwargs = dict(meanprops=meanline_props,
                           showfliers=self.show_outliers,
                           showmeans=self.show_mean_line,
                           meanline=self.show_mean_line)
        plot_kwargs.update(dict(whis=1.5, notch=False))
        box_plotter.plot(self.ax, plot_kwargs)
        self.create_space_between_subplots(self.ax)
        if self.connect_paired_data_points:
            self.add_lines_to_connect_paired_data_points()
        return box_plotter, []