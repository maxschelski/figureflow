Installation
=================

The package was developed in Windows and the exact package versions for the environment in Windows are available for Anaconda.

1. If you don't already have Anaconda installed: Download and install Anaconda from https://www.anaconda.com/.

2. If you don't already have git installed: Download and install git from https://git-scm.com/downloads

3. Open a terminal, navigate to the folder where you want to put FigureFlow and clone the FigureFlow repository:

.. code:: sh 

  git clone https://github.com/maxschelski/figureflow.git

4. Navigate into the folder of the repository (figureflow):

.. code:: sh 

  cd figureflow

5. Create environment for FigureFlow with Anaconda:

.. code:: sh 

  conda env create -f environment.yml

6. Activate environment with Anaconda:

.. code:: sh 

  conda activate figureflow

7. Install FigureFlow locally using pip:

.. code:: sh 

  pip install -e .

8. Optional: If needed, install spyder to create, edit and run scripts:

.. code:: sh 

  conda install spyder

9. Optional: start spyder

.. code:: sh 

  spyder

10. You can now import FigureFlow and use it to build figures and generate movies as figure objects

.. code:: sh 

  from figureflow.figure import Figure

11. Open and execute example scripts from repository in the folders figureflow\scripts\figures and figureflow\scripts\movies
