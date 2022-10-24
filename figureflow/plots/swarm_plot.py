from .group_plot import GroupPlot
import seaborn as sns

class SwarmPlot(GroupPlot):
    def __init__(self, x, y, hue, data, x_order, hue_order, plot_colors,
                 size_factor, ax, plot_type, swarm_plot_point_size = 2,
                 show_data_points=True,
                 connect_paired_data_points = True,
                 use_hue_colors_for_swarm_plot = False, **kwargs):
        super().__init__(x, y, hue, data, x_order, hue_order, plot_colors,
                         size_factor, ax, plot_type,
                         swarm_plot_point_size=swarm_plot_point_size,
                         show_data_points=show_data_points,
                         connect_paired_data_points=connect_paired_data_points,
                         **kwargs)
        self.use_hue_colors_for_swarm_plot = use_hue_colors_for_swarm_plot
        if hue != None:
            self.dodge = True
        else:
            self.dodge = False
        self.size = swarm_plot_point_size * size_factor
        # * 0.83  #0.83 is sqrt of 0.7
        self.swarm_plot_line_width = swarm_plot_point_size/3.5 * size_factor
        if not show_data_points:
            # if no datapoints should be shown but there should still be
            # connections between grouped datapoints, then datapoints
            # need to be plotted without being visible
            # to be then connected later
            self.alpha = 0
        else:
            self.alpha=0.55
        if plot_type == "points":
            self.alpha=1

    def plot(self):
        if self.use_hue_colors_for_swarm_plot:
            plot = sns.swarmplot(x=self.x, y=self.y, hue=self.hue,
                                 data=self.data, order=self.x_order,
                                 hue_order=self.hue_order, dodge=self.dodge,
                                 edgecolor="black",
                                 linewidth=self.swarm_plot_line_width,
                                 size = self.size, alpha=self.alpha,
                                 palette=self.plot_colors)
            # # fc="none" for empty markers
        else:
            plot = sns.swarmplot(x=self.x, y=self.y, hue=self.hue,
                                 data=self.data, order=self.x_order,
                                 hue_order=self.hue_order, dodge=self.dodge,
                                 edgecolor="black",
                                 linewidth=self.swarm_plot_line_width,
                                 size = self.size, alpha=self.alpha, fc="white")
        # if only points will be plotted, also create empty box plotter
        if self.plot_type == "points":
            box_plotter = self.create_box_plotter()
            if self.connect_paired_data_points:
                self.add_lines_to_connect_paired_data_points()
            return box_plotter, []