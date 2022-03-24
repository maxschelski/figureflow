# FastFig
A Python package to allow fast, modular and reproducible generation of publication-grade scientific figures and movies.<br/>
<br/>
#### Selected features
- perfectly aligning plots and images into figure panels
- Images (including Hyperstacks from ImageJ) can be automatically displayed in grids depending on ImageJ-defined channels and frames
- Images can be easily annotated
- Movies can be generated as full-fledged figure objects with the "frame" attribute for images or the x-attribute for lineplots changing at each movie-frame. 
- ...
<br/>
A lot of the code to plot data and add significance information (statannot.py) is from statannot https://github.com/webermarcolivier/statannot created by Marc Weber.<br/>
<br/>
FastFig was used to generate all figures and all movies from Schelski and Bradke 2021:<br/>
https://www.biorxiv.org/content/10.1101/2021.09.01.458567v1.full <br/>
<br/>
Requirements (.txt) for package available for pip and for conda as well as yml file from conda for windows (environment_windows.yml) with specific versions for all packages and for other operating systems (environment.yml; tested on Mac OS) with version numbers only for critical packages.<br/>
<br/>
Documentation and code base under development.<br/>

# Installation

1. Open a terminal and clone the repository for fastfig:
> git clone https://github.com/maxschelski/fastfig.git
2a. (Recommended) Navigate into the folder of the repository (fastfig) and create environment for fastfig with Anaconda :
> conda env create -f environment.yml
<br/>When using windows you can also create the exact environment fastfig was developed in:
> conda env create -f environment_windows.yml
2b. (Alternatively) Pip install all required packages from the requirements.txt file
> pip install -r requirements.txt
When using windows you can also install the exact package versions of the environment in which fastfig was developed:
> pip install -r requirements_windows.txt
3. Navigate into the folder of the repository (fastfig) and install locally using pip:
> cd fastfig
> pip install -e .
4. You can now import fastfig and use it to build figures and generate movies as figure objects
> from fastfig import figure

# Examples
Example code for using the package will follow once the corresponding research paper is published in a peer-reviewed journal. Examples are not displayed to scale on this website but were all generated with 4.75 inch width.
For now, examples are available upon request via Github or via E-Mail to max.schelski@dzne.de.<br/>
<br/>
<br/>
Examples from Schelski and Bradke 2021 fully generated with the package without Adobe Illustrator etc:<br/>
<br/>
![Figure 1 generated with Fastfig](https://www.biorxiv.org/content/biorxiv/early/2021/09/03/2021.09.01.458567/F1.large.jpg)<br/>
<br/>
<br/>
![Figure 2 generated with Fastfig](https://www.biorxiv.org/content/biorxiv/early/2021/09/03/2021.09.01.458567/F2.large.jpg)<br/>
<br/>
<br/>
![Figure 3 generated with Fastfig](https://www.biorxiv.org/content/biorxiv/early/2021/09/03/2021.09.01.458567/F3.large.jpg)<br/>
<br/>
<br/>
![Figure 4 generated with Fastfig](https://www.biorxiv.org/content/biorxiv/early/2021/09/03/2021.09.01.458567/F4.large.jpg)<br/>
<br/>
