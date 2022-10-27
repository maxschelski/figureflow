Introduction
===============


Features
----------

- General features:

  - create figure according to exact size necessary for desired journal in inches
  - automatically perfectly aligns plots and images in figure panels
  - Display illustrations as png file; or as powerpoint file to unify font size
  - ...

Features to display images:
- Provide images as single Hyperstack or single images
- Define which timepoints, channels etc. to display
- Position of images is automatically determined... but can be customized as well
- Contrast set in ImageJ is automatically extracted from Hyperstack
- Add annotations (star, asterisk, arrow, lines,text)
- Define regions to be zoomed in, crop images
- Add timestamp, scale bar, channel names
- Annotate outside of image based on dimension (e.g. Annotate on the outside all timepoints)
- ...

Features to display quantifications:
- Provide .csv file
- Plot data automatically in the allocated space (Boxplot with overlaying data points)
- Calculate significance and annotate in image (Largely based on Statannot from Marc Weber)
- Show statistics (e.g. Mean, median, SEM, etc) for each data group (Largely based on Statannot from Marc Weber)
- Show sorted list of representative cells (closest to average)
- ...

Features to create Movie 
- Movies can be generated as full-fledged figure objects 
- Images can be supplied as ImageJ Hyperstack with the "frames" attribute being animated
- Lineplots of quantifications (.csv file) can be animated based on the x-attribute 
- Add title pages to movies with introductory text
- Precisely define movie quality (resolution and bitrate) 
- ...