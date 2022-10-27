Tutorial
===========

Usage Examples
-----------

Some documentation of how to generate movies can be found in the folder "scripts" in create_movies.py.
Many usage examples covering almost all of the features of figureflow can be found in the the folder "scripts" for generating figures (under "scripts/figures") or movies (under "scripts/movies").

To find out which examples might be interesting to you, start by looking 
  - in "data/example_figures" for generated figures (as .png file, e.g. data/example_figures/figure1.png) or 
  - in "data/example_movies" for generated movies (as .mp4 file, e.g. data/example_movies/MovieS1.mp4) 

Check which examples contain features you would like to use. Then you can use the corresponding script for the example of interest (e.g. scripts/Figure1.py or scripts/MovieS1.py) to play around with the feature of interest and thereby understand the usage hands-on.

The data used for the figures and movies is in the folder "data" in a subfolder with the same name as the name of the script (e.g. the data for scripts/figures/Figure1.py is in data/Figure1).

The data for a figure can contain: 
  - A .csv file named \_\_figure\_\_ followed by the figure number (e.g. "\_\_figure\_\_S1.csv") file that describes the layout of the panels
  - .csv files for analyzed data
  - .tif files for microscopy images 
  - .png/.pptx files for illustrations.

Figureflow automatically assigns files to the respective panel by file name:

The name of files for a specific panel starts with "panel" followed by the uppercase panel letter and then an underscore (e.g. a file for panel A starts with "panelA_"). Alternatively, files for a panel can be stored in a folder named "panel" followed by the uppercase panel letter ("e.g. "panelA").

Using the GUI to add elements (arrows, text, zooms, cropping) to images in panels
------------------

if you want to add zooms or arrows or text in a panel, you can also try the new GUI that I developed some weeks ago. Right after defining the figure object ("Figure(...)") you can write the following:

.. code:: sh 

  figure.edit_panel("C")

(where "C" is the panel you want to edit)

The GUI has a button to generate the code you can then copy paste into the script after you are done adding the elements you want. With the GUI you don't need to check at which coordinates you want to add an arrow or text in ImageJ.


Creating new plot types
-----------
New plot types can be created through a new file with a class for the plot type. These new files are automatically recognized by figureflow and can be used through supplying the correct name for the parameter "plot_type" in the "show_data" function.

Specifically, for each class there must be one .py file for it. This needs to be named according to PEP8 convention (just lower case letters and separating with "_").
The class must be named according to PEP8 convention as camelcase of the .py file name (removing "_" and starting the word followed by "_" with a capital letters - e.g. "group_plot.py" and "GroupPlot" as class name).

New dataplots classes need to have the following structure:

They can use the following parameters always supplied as kwargs to function:

.. code:: sh 

  x, y, hue, data, x_order, hue_order, plot_colors, size_factor, swarm_plot_point_size, plot_type, show_data_points, connect_paired_data_points

In addition, they can use the following parameter which will also be supplied to function:
  - data_plot_kwds (which should be a dictionary containing all parameters specific to the plot)

Since many parameters will be supplied to function, adding kwargs as parameter is necessary.

The object needs to have a plot function, which does not take any parameters (except self).

The plot function needs to return the plot object for group plots which needs to be of a similar structure then seaborns _BoxPlotter object. This _BoxPlotter is needed to extract the x groups (position, data, etc.). It also needs to either return an empty list or a list of strings which should be added to the plot (check in regression_plot.py in the add_text_to_be_plotted function how the variable labels_to_add is structured for details of how to structure the list).

They must define in the __init__ function whether they are continuous on the x axis or not (have continuous or categorical values). Non continuous data should only be used for group_plots, where an object similar to seaborns _BoxPlotter object is created and can be returned.

To use the plot the plot_type must equal the string before the "_plot.py" in the file name of the class or if no "_plot" is present in the file name it must equal the part before the filetype (before ".py").
