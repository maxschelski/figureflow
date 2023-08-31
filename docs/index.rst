Figureflow
===============

**Figureflow** is a Python package to allow fast, modular and reproducible generation of publication quality scientific figures and movies with only a few lines of code. 

| Figureflow was used to generate all 26 figures (10 main, 16 supplementary) and 22 movies for Schelski and Bradke 2022:
| https://www.science.org/doi/10.1126/sciadv.abo2336
| FigureFlow was also used to generate all figures and all movies from the corresponding preprint Schelski and Bradke 2021 (examples from preprint at the bottom of this page):
| https://www.biorxiv.org/content/10.1101/2021.09.01.458567v1.full

|
| Figureflow also includes a GUI for image modifications (add zoom, arrow, text etc.) to generate code that can be copied and pasted into the script to apply the modifications:


.. raw:: html

   <iframe width="560" height="315" src="https://github.com/maxschelski/figureflow/assets/44224661/36a852ad-19cc-44f6-9030-ab82f737e62e" frameborder="0" allowfullscreen></iframe>



A lot of the code to plot data and add significance information (in statannot.py) is from statannot https://github.com/webermarcolivier/statannot created by Marc Weber.

For any questions or an introduction of how to use the package please contact me via E-Mail to max.schelski@googlemail.com. I am very happy to help people starting to use the package and I am very open to any feedback. 

Examples from Schelski and Bradke 2021 fully generated with the package without Adobe Illustrator etc:

Figure 1:

.. image:: https://www.biorxiv.org/content/biorxiv/early/2021/09/03/2021.09.01.458567/F1.large.jpg

Figure 2:

.. image:: https://www.biorxiv.org/content/biorxiv/early/2021/09/03/2021.09.01.458567/F2.large.jpg

Figure 3:

.. image:: https://www.biorxiv.org/content/biorxiv/early/2021/09/03/2021.09.01.458567/F3.large.jpg

Figure 4:

.. image:: https://www.biorxiv.org/content/biorxiv/early/2021/09/03/2021.09.01.458567/F4.large.jpg


.. toctree::
   :caption: Documentation
   :maxdepth: 2
   :hidden:

   Features <features>
   Installation <installation>
   Tutorial <tutorial>


.. toctree::
   :caption: API
   :maxdepth: 2
   :hidden:

   All functions <api>
   Figure level <api_figure>
   Image panel <api_image_panel>
   Dataplot panel <api_dataplot_panel>
