Installation
=================

The package was developed in Windows and the exact package versions for the environment in Windows are available for Anaconda.

1. Open a terminal, navigate to the folder where you want to put FigureFlow and clone the FigureFlow repository:

.. code:: sh 

  git clone https://github.com/maxschelski/figureflow.git

2. Navigate into the folder of the repository (figureflow):

.. code:: sh 

  cd figureflow

3. Create environment for FigureFlow with Anaconda:

.. code:: sh 

  conda env create -f environment.yml

4. Install FigureFlow locally using pip:

.. code:: sh 

  pip install -e .

5. You can now import FigureFlow and use it to build figures and generate movies as figure objects

.. code:: sh 

  from figureflow.figure import Figure
