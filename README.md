# FastFig
A Python package to allow fast, modular and reproducible generation of publication-grade scientific figures and movies.<br/>
<br/>
#### Selected features
- automatically perfectly aligns plots and images in figure panels
- Images (including Hyperstacks from ImageJ) can be automatically displayed in grids depending on ImageJ-defined channels, frames and slices
- Zoomed regions to be shown of images can be defined
- Images can be easily annotated
- Movies can be generated as full-fledged figure objects (with the "frame" attribute for images or the x-attribute for lineplots changing at each movie-frame) 
- ...
<br/>
A lot of the code to plot data and add significance information (statannot.py) is from statannot https://github.com/webermarcolivier/statannot created by Marc Weber.<br/>
<br/>
FastFig was used to generate all figures and all movies from Schelski and Bradke 2021:<br/>
https://www.biorxiv.org/content/10.1101/2021.09.01.458567v1.full <br/>
<br/>
Documentation and code base under development.<br/>

# Installation

The package was developed in Windows and the exact package versions for the environment in Windows are available for Anaconda and pip.
<br/>
1. Open a terminal, navigate to the folder where you want to put fastfig and clone the fastfig repository:
> git clone https://github.com/maxschelski/fastfig.git
2. Navigate into the folder of the repository (fastfig):
> cd fastfig
3. (Recommended on Mac/Linux) Create environment for fastfig with Anaconda:
> conda env create -f environment.yml
3. (Recommended on Windows) Create environment for fastfig with Anaconda:
> conda env create -f environment_windows.yml
3. (Alternatively on Windows, without Anaconda) Pip install all required packages:
> pip install -r requirements_windows.txt
4. Install fastfig locally using pip:
> pip install -e .
5. You can now import fastfig and use it to build figures and generate movies as figure objects
> from fastfig import figure

For any questions feel free to contact me via E-Mail to max.schelski@googlemail.com.
# Examples
Example code for using the package will follow once the corresponding research paper is published in a peer-reviewed journal. Examples are not displayed to scale on this website but were all generated with 4.75 inch width.
For now, examples are available upon request via Github or via E-Mail to max.schelski@googlemail.com.<br/>
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
