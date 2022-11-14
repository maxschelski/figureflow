import seaborn as sns


class ScatterPlot():
    CONTINUOUS_X = True

    def __init__(self, x, y, hue, data, plot_colors, ax, size_factor, **kwargs):
        self.x = x
        self.y = y
        self.hue = hue
        self.data = data
        self.ax = ax
        self.size_factor = size_factor

        self.continuous = True

        self.data[x] = pd.to_numeric(self.data[self.x])
        if type(self.hue) != type(None):
            nb_colors = len(self.data[self.hue].drop_duplicates())
        else:
            nb_colors = 1
        self.plot_colors = sns.color_palette(plot_colors, n_colors=nb_colors)

    def plot(self):

        plot = sns.scatterplot(
            data=self.data, x=self.x, y=self.y, hue=self.hue, ax=self.ax,
            palette = self.plot_colors, color=self.plot_colors[0],
            alpha=0.5, sizes=[25 * size_factor]
        )
        return plot, []