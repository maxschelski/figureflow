Installation
=================

The package was developed in Windows and the exact package versions for the environment in Windows are available for Anaconda and pip.

1. Open a terminal, navigate to the folder where you want to put FigureFlow and clone the FigureFlow repository:
.. code:: sh 
git clone https://github.com/maxschelski/figureflow.git

2. Navigate into the folder of the repository (figureflow):
.. code:: sh 
cd figureflow

3. (Recommended on Mac/Linux) Create environment for FigureFlow with Anaconda:
.. code:: sh 
conda env create -f environment.yml
3. (Recommended on Windows) Create environment for FigureFlow with Anaconda:
.. code:: sh 
conda env create -f environment_windows.yml
3. (Alternatively on Windows, without Anaconda) Pip install all required packages:
.. code:: sh 
pip install -r requirements_windows.txt

4. Install FigureFlow locally using pip:
.. code:: sh 
pip install -e .

5. You can now import FigureFlow and use it to build figures and generate movies as figure objects
.. code:: sh 
from figureflow.figure import Figure