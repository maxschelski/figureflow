Figure API
===============

Figure level functions
------------------------

.. currentmodule:: figureflow.figure.Figure
.. autofunction:: __init__
.. autofunction:: create_panel
.. autofunction:: show_panels
.. autofunction:: edit_panel
.. autofunction:: edit_this_panel
.. autofunction:: get_representative_data_from_multiple_panels
.. autofunction:: get_representative_data_from_multiple_panels_from_scratch
.. autofunction:: save
.. autofunction:: save_video

Image panel functions
------------------------

.. currentmodule:: figureflow.figure_panel.FigurePanel
.. autofunction:: show_images
.. autofunction:: add_border
.. autofunction:: add_zoom
.. autofunction:: add_cropping
.. autofunction:: add_colorbars
.. autofunction:: add_rows_to_delete
.. autofunction:: add_scale_bar
.. autofunction:: add_text_within_at_coords
.. autofunction:: add_timestamp
.. autofunction:: set_image_scaling
.. autofunction:: add_x_axis
.. autofunction:: add_y_axis
.. autofunction:: annotate_channel_within_image
.. autofunction:: draw_line_on_images
.. autofunction:: draw_marker
.. autofunction:: draw_on_image
.. autofunction:: label
.. autofunction:: label_category
.. autofunction:: label_channels
.. autofunction:: label_frames
.. autofunction:: label_images
.. autofunction:: rescale_font_size
.. autofunction:: add_text_on_image


Dataplot panel functions
------------------------

.. currentmodule:: figureflow.figure_panel.FigurePanel
.. autofunction:: show_data

**KEYWORD ARGUMENTS FOR show_data (in plot_and_add_stat_annotation)----------------------------------------------------------------------------------------------------------------------------**

.. currentmodule:: figureflow.statannot
.. autofunction:: plot_and_add_stat_annotation

.. currentmodule:: figureflow.figure_panel.FigurePanel
.. autofunction:: set_data_params
.. autofunction:: show_data_columns
.. autofunction:: calculate_fractions
.. autofunction:: add_data_transformation
.. autofunction:: draw_line_on_plots
.. autofunction:: get_basic_statistics
.. autofunction:: get_representative_data