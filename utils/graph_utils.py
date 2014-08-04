#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygal
from pygal.style import Style


def make_trafficgraph(trafficdata):
    """Create a graph from the input trafficdata with pygal.
    The returned graph can then be rendered to a png byte blob
    and send as MIME image. This does not need a temporary file.
    """
    traffic_chart_style = Style(
        background='transparent',
        plot_background='transparent',
        foreground='black',
        foreground_light='black',
        foreground_dark='black',
        opacity='.9',
        colors=('#00C800', '#9696FF')
    )
    traffic_chart = pygal.Bar(
        height=350,
        show_legend=False,
        show_x_labels=False,
        show_y_guides=True,
        human_readable=False,
        major_label_font_size=12,
        label_font_size=12,
        print_values=False,
        style=traffic_chart_style,
        y_labels_major_every=2,
        show_minor_y_labels=False
    )
    traffic_chart.x_labels = trafficdata['history'][0]
    traffic_chart.add('Input', trafficdata['history'][1])
    traffic_chart.add('Output', trafficdata['history'][2])

    return traffic_chart