from .group_plot import GroupPlot

class BoxPlot(GroupPlot):
    def __init__(self, x, y, hue, data, x_order, hue_order, plot_colors,
                 size_factor, swarm_plot_point_size, plot_type,
                 show_data_points, connect_paired_data_points, ax,
                 show_mean_line, show_outliers, fliersize, **kwargs):
        super().__init__(x, y, hue, data, x_order, hue_order, plot_colors,
                         size_factor, swarm_plot_point_size, plot_type,
                         show_data_points, connect_paired_data_points)
        self.show_mean_line = show_mean_line
        self.show_outliers = show_outliers
        self.fliersize = fliersize
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
        return box_plotter