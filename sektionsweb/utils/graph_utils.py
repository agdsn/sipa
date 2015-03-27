#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygal
from pygal.style import BlueStyle
from _locale import gettext
from operator import add


def generate_traffic_chart(traffic_data, inline=True):
    """Create a graph object from the input traffic data with pygal.
     If inline is set, the chart is being passed the option to not add an xml
     declaration header to the beginning of the `render()` output, so it can
      be directly included in HTML code (wrapped by a `<figure>`)
    :param traffic_data: The traffic data as given by `query_trafficdata()`
    :param inline: Determines the option `disable_xml_declaration`
    :return: The graph object
    """
    traffic_chart = pygal.Bar(
        title=gettext("Traffic (MB)"),
        height=350,
        show_y_guides=True,
        human_readable=False,
        major_label_font_size=12,
        label_font_size=12,
        style=BlueStyle,
        disable_xml_declaration=inline,   # for direct html import
        js=[],  # prevent automatically fetching scripts from github
    )

    days, in_values, out_values, credit = zip(*traffic_data['history'])
    traffic_chart.x_labels = days
    traffic_chart.add(gettext('Input'), in_values)
    traffic_chart.add(gettext('Output'), out_values)
    traffic_chart.add(gettext('Gesamt'), map(add, in_values, out_values))

    return traffic_chart


def render_traffic_chart(traffic_data, **kwargs):
    """Generate pure svg code ready to be included in HTML inside a <figure>.
    :param traffic_data: The traffic data as in generate_traffic_chart()
    :return: String
    """
    return generate_traffic_chart(traffic_data, **kwargs).render()