Usage Examples
===========

Some documentation of how to generate movies can be found in the folder "scripts" in create_movies.py.
Many usage examples covering almost all of the features of figureflow can be found in the the folder "scripts" for generating figures (under "scripts/figures") or movies (under "scripts/movies").<br>
To find out which examples might be interesting to you, start by looking 
- in "data/example_figures" for generated figures (as .png file, e.g. data/example_figures/figure1.png) or 
- in "data/example_movies" for generated movies (as .mp4 file, e.g. data/example_movies/MovieS1.mp4) 

Check which examples contain features you would like to use. Then you can use the corresponding script for the example of interest (e.g. scripts/Figure1.py or scripts/MovieS1.py) to play around with the feature of interest and thereby understand the usage hands-on.<br><br>

The data used for the figures and movies is in the folder "data" in a subfolder with the same name as the name of the script (e.g. the data for scripts/figures/Figure1.py is in data/Figure1).<br><br>
The data for a figure can contain: 
- A .csv file named \_\_figure\_\_ followed by the figure number (e.g. "\_\_figure\_\_S1.csv") file that describes the layout of the panels
- .csv files for analyzed data
- .tif files for microscopy images 
- .png/.pptx files for illustrations.

Figureflow automatically assigns files to the respective panel by file name:<br>
The name of files for a specific panel starts with "panel" followed by the uppercase panel letter and then an underscore (e.g. a file for panel A starts with "panelA_"). Alternatively, files for a panel can be stored in a folder named "panel" followed by the uppercase panel letter ("e.g. "panelA").