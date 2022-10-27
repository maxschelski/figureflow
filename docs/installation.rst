Installation
=================

The package was developed in Windows and the exact package versions for the environment in Windows are available for Anaconda and pip.

1. Open a terminal, navigate to the folder where you want to put FigureFlow and clone the FigureFlow repository:<br>
> git clone https://github.com/maxschelski/figureflow.git<br>

2. Navigate into the folder of the repository (figureflow):<br>
> cd figureflow<br>

3. (Recommended on Mac/Linux) Create environment for FigureFlow with Anaconda:<br>
> conda env create -f environment.yml<br>
3. (Recommended on Windows) Create environment for FigureFlow with Anaconda:<br>
> conda env create -f environment_windows.yml<br>
3. (Alternatively on Windows, without Anaconda) Pip install all required packages:<br>
> pip install -r requirements_windows.txt<br>

4. Install FigureFlow locally using pip:<br>
> pip install -e .<br>

5. You can now import FigureFlow and use it to build figures and generate movies as figure objects<br>
> from figureflow.figure import Figure<br>