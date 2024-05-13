import seaborn as sns
import pandas as pd

class LinePlot():
    CONTINUOUS_X = True

    def __init__(self, x, y, hue, data, hue_order, plot_colors, ax,
                 x_range, **kwargs):
        data[x] = pd.to_numeric(data[x])
        data.sort_values(x, inplace=True)

        self.data = data
        self.x = x
        self.hue = hue
        self.hue_order = hue_order
        self.ax = ax
        self.x_range = x_range

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

    def plot(self):
        # sns.lineplot(data=self.data, x=self.x, y=self.variables["y"],
        #              ax=self.ax)
        plot = sns.relational._LinePlotter(
                data=self.data, variables=self.variables,
                estimator=None, ci=None, n_boot=None, seed=None,
                sort=None, err_style="band", err_kws=None, legend="full")
        
        plot.map_hue(palette=self.plot_colors, order=self.hue_order, norm=None)
        
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

        plot.plot(self.ax,kws)
        return plot, []