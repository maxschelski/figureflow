import seaborn as sns
import matplotlib as mpl
from matplotlib.patches import PathPatch
import numpy as np
import itertools

class GroupPlot():
    def __init__(self, x, y, hue, data, x_order, hue_order, plot_colors,
                 size_factor, ax, plot_type, nb_x_vals=1, pair_unit_columns=None,
                 connect_paired_data_points=True, connect_points_hue=None,
                 swarm_plot_point_size = 2,
                 show_data_points=True, connecting_line_color="black",
                 connecting_line_width=1, connecting_line_alpha=0.1, **kwargs):
        self.x = x
        self.y = y
        self.hue = hue
        self.connect_points_hue = connect_points_hue
        self.data = data
        self.x_order = x_order
        self.hue_order = hue_order
        self.plot_colors = plot_colors
        self.size_factor = size_factor
        self.fliersize = 0
        self.line_width = 0
        self.show_mean_line = False
        self.ax = ax
        self.nb_x_vals = nb_x_vals


        self.show_data_points = show_data_points
        self.connect_paired_data_points = connect_paired_data_points
        self.swarm_plot_point_size = swarm_plot_point_size
        self.show_data_points = show_data_points
        self.plot_type = plot_type

        self.pair_unit_columns = pair_unit_columns
        self.connecting_line_color = connecting_line_color
        self.connecting_line_alpha = connecting_line_alpha
        self.connecting_line_width = connecting_line_width

        # if hue is defined, bow_width needs to be 0.8 in order to align points with boxplot
        if (hue != None):
            self.box_width = 0.8
        else:
            self.box_width = 0.63

    def plot(self):
        if (self.show_data_points | self.connect_paired_data_points):
            self.swarm_plot = self.SwarmPlot(self.x, self.y, self.hue, self.data,
                                        self.x_order, self.hue_order,
                                        self.plot_colors, self.size_factor,
                                             self.ax,self.plot_type,
                                        swarm_plot_point_size=
                                             self.swarm_plot_point_size,
                                        show_data_points=
                                             self.show_data_points)
            self.swarm_plot.plot()
            self.show_outliers = False
        else:
            self.show_outliers = True


    def create_box_plotter(self):
        # Create the same BoxPlotter object as seaborn's boxplot
        plot = sns.categorical._BoxPlotter(
            self.x, self.y, self.hue, self.data,
            self.x_order, self.hue_order, orient=None, width=self.box_width,
            color="black", saturation=1, dodge=True, fliersize=self.fliersize,
            linewidth=self.line_width, palette=self.plot_colors)


        # set gray of boxplot manually since it is otherwise determined by the colors used in the plotted box_ends
        # this can lead to different grays for different subplots if only a part of the colors are plotted in one of them
        gray = mpl.colors.rgb2hex((0, 0, 0))
        plot.gray = gray

        return plot

    def create_space_between_subplots(self, ax):
        # code from stackoverflow
        # (https://stackoverflow.com/questions/56838187/how-to-create-spacing-between-same-subgroup-in-seaborn-boxplot)
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

    def add_lines_to_connect_paired_data_points(self):
        if self.nb_x_vals <= 1:
            return
        # Code to connect paired points from S.A. on stackoverflow:
        # https://stackoverflow.com/questions/51155396/
        # plotting-colored-lines-connecting-individual-data-points-of-two-swarmplots
        # go through each set of two groups out of all groups
        # get all groups from x_order and hue_order combinations
        if len(self.hue_order) == 0:
            sorted_hue_vals = np.unique(self.data[self.connect_points_hue].values)
        else:
            sorted_hue_vals = self.hue_order

        col_data = self.data.sort_values(self.pair_unit_columns)

        # without hue there is only one group containing all x values
        all_x_vals = self.data[self.x].drop_duplicates().values
        all_data_groups = []
        if len(self.hue_order) == 0:
            all_data_groups.append(list(itertools.product(all_x_vals,
                                                          sorted_hue_vals)))
        else:
            # with hue there are as many groups as there are x values
            # and for each x there are as many groups
            for x_val in self.x_order:
                new_groups = itertools.product(x_val, sorted_hue_vals)
                all_data_groups.append(new_groups)

        current_group_start_number = 0
        for data_group in all_data_groups:
            data_group = list(data_group)
            sub_group_numbers = list(range(len(data_group)))
            # go through all group numbers in pairs of two
            # by taking the group number and one further
            # therefore stop one before the last group number
            for sub_group_nb in sub_group_numbers[:-1]:

                # get x and hue values of first group
                data_group1 = data_group[sub_group_nb]
                data_group1_vals = self.data.loc[
                    (self.data[self.x] == data_group1[0]) &
                    (self.data[self.connect_points_hue] ==
                     data_group1[1]), self.y].values
                # get x and hue values of second group
                data_group2 = data_group[sub_group_nb + 1]
                data_group2_vals = self.data.loc[
                    (self.data[self.x] == data_group2[0]) &
                    (self.data[self.connect_points_hue] ==
                     data_group2[1]), self.y].values
                # do not connect groups if there is only one datapoint
                if (len(data_group1_vals) <= 1) | (len(data_group2_vals) <= 1):
                    return

                # get the number of the current data group
                # with respect to the start number
                data_group_nb1 = current_group_start_number + sub_group_nb
                data_group_nb2 = data_group_nb1 + 1

                locs1 = self.ax.get_children()[data_group_nb1].get_offsets()
                locs2 = self.ax.get_children()[data_group_nb2].get_offsets()

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
                    self.ax.plot(x_for_line, y_for_line,
                                 color=self.connecting_line_color,
                                 alpha=self.connecting_line_alpha,
                                 lw=self.connecting_line_width)

            # increase the current group start number for next groups
            current_group_start_number += len(data_group)