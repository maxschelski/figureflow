# FigureFlow
A Python package to allow fast, modular and reproducible generation of publication quality scientific figures and movies with only a few lines of code. <br/>
<br/>
A lot of the code to plot data and add significance information (in statannot.py) is from statannot https://github.com/webermarcolivier/statannot created by Marc Weber.<br/>
<br/>
FigureFlow was used to generate all figures and all movies from Schelski and Bradke 2021 (examples from paper at the bottom of this page):<br/>
https://www.biorxiv.org/content/10.1101/2021.09.01.458567v1.full <br/>
<br/>
Documentation and code base under development.<br/>

For any questions or an introduction of how to use the package please contact me via E-Mail to max.schelski@googlemail.com. I am very happy to help people starting to use the package and I am very open to any feedback. 

# Usage Examples
Some documentation of how to generate movies can be found in the folder "scripts" in create_movies.py. <br/><br/>
Many usage examples covering almost all of the features of figureflow can be found in the the folder "scripts" for generating figures (under "scripts/figures") or movies (under "scripts/movies").<br/>
To find out which examples might be interesting to you, start by looking in the "data" folder for generated figures (as .png file, e.g. data/Fig1/figure1.png) or generated movies (as .mp4 file, e.g. data/MovieS1/MovieS1.mp4) and check which examples contain features you would like to use. Then you can use the corresponding script for the example of interest (e.g. scripts/figure1.py or scripts/MovieS1.py) to play around with the feature and thereby understand its usage hands-on.<br/><br/>

The data used for the figures and movies is in the folder "data" in a subfolder with the same name as the name of the script (e.g. the data for scripts/figures/Fig1.py is in data/Fig1).<br/><br/>
The data for a figure can contain: 
- as mentioned above the output of figureflow as a .png file (for figures, e.g. figure1.png) or .mp4 file (for movies, e.g. MovieS1.mp4)
- a .csv file named \_\_figure\_\_ followed by the figure number (e.g. "\_\_figure\_\_S1.csv") file that describes the layout of the panels
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
- Add annotations (star, asterisk, arrow, lines,text)
- Define regions to be zoomed in, crop images
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

The package was developed in Windows and the exact package versions for the environment in Windows are available for Anaconda and pip.
<br/>
1. Open a terminal, navigate to the folder where you want to put FigureFlow and clone the FigureFlow repository:
> git clone https://github.com/maxschelski/figureflow.git
2. Navigate into the folder of the repository (figureflow):
> cd figureflow
3. (Recommended on Mac/Linux) Create environment for FigureFlow with Anaconda:
> conda env create -f environment.yml
3. (Recommended on Windows) Create environment for FigureFlow with Anaconda:
> conda env create -f environment_windows.yml
3. (Alternatively on Windows, without Anaconda) Pip install all required packages:
> pip install -r requirements_windows.txt
4. Install FigureFlow locally using pip:
> pip install -e .
5. You can now import FigureFlow and use it to build figures and generate movies as figure objects
> from figureflow.figure import Figure

For any questions feel free to contact me via E-Mail to max.schelski@googlemail.com.
# Examples
Example code for using the package will follow once the corresponding research paper is published in a peer-reviewed journal. Examples are not displayed to scale on this website but were all generated with 4.75 inch width.
For now, examples are available upon request via Github or via E-Mail to max.schelski@googlemail.com.<br/>
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
