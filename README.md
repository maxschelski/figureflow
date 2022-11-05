# FigureFlow
A Python package to allow fast, modular and reproducible generation of publication quality scientific figures and movies with only a few lines of code. <br/>
<br/>
A lot of the code to plot data and add significance information (in statannot.py) is from statannot https://github.com/webermarcolivier/statannot created by Marc Weber.<br/>
<br/>
Figureflow was used to generate all 26 figures (10 main, 16 supplementary) and 22 movies for Schelski and Bradke 2022:<br/>
https://www.science.org/doi/10.1126/sciadv.abo2336 <br/>
FigureFlow was also used to generate all figures and all movies from the corresponding preprint Schelski and Bradke 2021 (examples from preprint at the bottom of this page):<br/>
https://www.biorxiv.org/content/10.1101/2021.09.01.458567v1.full <br/>
<br/>
Documentation and code base under development.<br/>

For any questions or an introduction of how to use the package please contact me via E-Mail to max.schelski@googlemail.com. I am very happy to help people starting to use the package and I am very open to any feedback - including anything not working properly or easily. 

# Usage Examples
Some documentation of how to generate movies can be found in the folder "scripts" in create_movies.py. <br/><br/>
Many usage examples covering almost all of the features of figureflow can be found in the the folder "scripts" for generating figures (under "scripts/figures") or movies (under "scripts/movies"). The figures and movies are from Schelski and Bradke 2022.<br/>
To find out which examples might be interesting to you, start by looking 
- in "data/example_figures" for generated figures (as .png file, e.g. data/example_figures/figure1.png) or 
- in "data/example_movies" for generated movies (as .mp4 file, e.g. data/example_movies/MovieS1.mp4) 

Check which examples contain features you would like to use. Then you can use the corresponding script for the example of interest (e.g. scripts/Figure1.py or scripts/MovieS1.py) to play around with the feature of interest and thereby understand the usage hands-on.<br/><br/>

The data used for the figures and movies is in the folder "data" in a subfolder with the same name as the name of the script (e.g. the data for scripts/figures/Figure1.py is in data/Figure1).<br/><br/>
The data for a figure can contain: 
- A .csv file named \_\_figure\_\_ followed by the figure number (e.g. "\_\_figure\_\_S1.csv") file that describes the layout of the panels
- .csv files for analyzed data
- .tif files for microscopy images 
- .png/.pptx files for illustrations.

Figureflow automatically assigns files to the respective panel by file name:<br/>
The name of files for a specific panel starts with "panel" followed by the uppercase panel letter and then an underscore (e.g. a file for panel A starts with "panelA_"). Alternatively, files for a panel can be stored in a folder named "panel" followed by the uppercase panel letter ("e.g. "panelA").

# Selected Features

#### General features:
- create figure according to exact size necessary for desired journal in inches
- automatically perfectly aligns plots and images in figure panels
- Display illustrations as png file; or as powerpoint file to unify font size
- ...

#### Features to display images:
- Provide images as single Hyperstack or single images
- Define which timepoints, channels etc. to display
- Position of images is automatically determined... but can be customized as well
- Contrast set in ImageJ is automatically extracted from Hyperstack
- Add annotations (star, asterisk, arrow, lines,text), *also using GUI*
- Define regions to be zoomed in, crop images, *also using GUI*
- Add timestamp, scale bar, channel names
- Annotate outside of image based on dimension (e.g. Annotate on the outside all timepoints)
- ...

#### Features to display quantifications:
- Provide .csv file
- Plot data automatically in the allocated space (Boxplot with overlaying data points)
- Calculate significance and annotate in image (Largely based on Statannot from Marc Weber)
- Show statistics (e.g. Mean, median, SEM, etc) for each data group (Largely based on Statannot from Marc Weber)
- Show sorted list of representative cells (closest to average)
- ...

#### Features to create Movie 
- Movies can be generated as full-fledged figure objects 
- Images can be supplied as ImageJ Hyperstack with the "frames" attribute being animated
- Lineplots of quantifications (.csv file) can be animated based on the x-attribute 
- Add title pages to movies with introductory text
- Precisely define movie quality (resolution and bitrate) 
- ...
<br/>


# Installation

The package was developed in Windows and the exact package versions for the environment in Windows are available for Anaconda.
<br/>
1. Open a terminal, navigate to the folder where you want to put FigureFlow and clone the FigureFlow repository:
> git clone https://github.com/maxschelski/figureflow.git
2. Navigate into the folder of the repository (figureflow):
> cd figureflow
3. (Recommended on Mac/Linux) Create environment for FigureFlow with Anaconda:
> conda env create -f environment.yml
3. (Recommended on Windows) Create environment for FigureFlow with Anaconda:
> conda env create -f environment_windows.yml
4. Install FigureFlow locally using pip:
> pip install -e .
5. You can now import FigureFlow and use it to build figures and generate movies as figure objects
> from figureflow.figure import Figure

For any questions feel free to contact me via E-Mail to max.schelski@googlemail.com.

# Creating a layout for a figure

The layout of a figure is created by defining the position and size of the panels. This can either be done by setting the parameters x, y, width and height separately for each figure panel or by creating a csv file the following way:

The csv needs to be in the main folder of the figure with the name __figure__ followed by the "number" and ".csv"
A grid with letters of the panels where
if a panel should span several cells
the corresponding letter should be written in several cells.

Widths and heights can be defined by two possible ways:
  1) In which the first row is the width of each column and the last column is the height of each row
  2) In which above every panel letters there is a number corresponding to the relative width of the panel in that row and the last column of the csv contains the height of each row
  3) In which widths are defined as in the second point but heights are defined for every panel by a number right of the panel letter           

# Using the GUI to add/edit elements

If you want to add text, arrows, zooms or cropping to an image in a panel, you can also use the GUI for one panel at the time. The GUI also allows you to adjust the position of elements you added already. 

To use the GUI, right after defining the figure object:

> Figure(...)
  
you can write the following:

> figure.edit_panel("C")

(where "C" is the panel you want to edit)

The GUI has a button to generate the code after you are done adding the elements you want you can then copy paste into the script of the figure/movie. 

With the GUI you don't need to check at which coordinates you want to add an arrow or text in ImageJ.


# Examples
Examples are not displayed to scale on this website but were all generated with 4.75 inch width.<br/>
<br/>
<br/>
Examples from Schelski and Bradke 2021 fully generated with the package without Adobe Illustrator etc:<br/>
<br/>
![Figure 1 generated with FigureFlow](https://www.biorxiv.org/content/biorxiv/early/2021/09/03/2021.09.01.458567/F1.large.jpg)<br/>
<br/>
<br/>
![Figure 2 generated with FigureFlow](https://www.biorxiv.org/content/biorxiv/early/2021/09/03/2021.09.01.458567/F2.large.jpg)<br/>
<br/>
<br/>
![Figure 3 generated with FigureFlow](https://www.biorxiv.org/content/biorxiv/early/2021/09/03/2021.09.01.458567/F3.large.jpg)<br/>
<br/>
<br/>
![Figure 4 generated with FigureFlow](https://www.biorxiv.org/content/biorxiv/early/2021/09/03/2021.09.01.458567/F4.large.jpg)<br/>
<br/>
