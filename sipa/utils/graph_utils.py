# -*- coding: utf-8 -*-

import pygal
from pygal.style import Style
from pygal.colors import hsl_to_rgb

from flask.ext.babel import gettext
from operator import add


def rgb_string(r, g, b):
    return "#{:02X}{:02X}{:02X}".format(int(r), int(g), int(b))


def hsl(h, s, l):
    return rgb_string(*hsl_to_rgb(h, s, l))


traffic_style = Style(
    background='transparent',
    plot_background='transparent',
    opacity='.6',
    opacity_hover='.9',
    transition='200ms ease-in',
    colors=(hsl(130, 80, 60), hsl(70, 80, 60), hsl(190, 80, 60)),
    font_family='default'
)


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
        title=gettext("Traffic (MiB)"),
        height=350,
        show_y_guides=True,
        human_readable=False,
        major_label_font_size=12,
        label_font_size=12,
        style=traffic_style,
        disable_xml_declaration=inline,   # for direct html import
        js=[],  # prevent automatically fetching scripts from github
    )

    days, in_values, out_values, credit = list(zip(*traffic_data['history']))
    traffic_chart.x_labels = days
    traffic_chart.add(gettext("Eingehend"), in_values,
                      stroke_style={'dasharray': '5'})
    traffic_chart.add(gettext("Ausgehend"), out_values,
                      stroke_style={'dasharray': '5'})
    traffic_chart.add(gettext("Gesamt"), list(map(add, in_values, out_values)),
                      stroke_style={'width': '2'})

    return traffic_chart


def render_traffic_chart(traffic_data, **kwargs):
    """Generate pure svg code ready to be included in HTML inside a <figure>.
    :param traffic_data: The traffic data as in generate_traffic_chart()
    :return: String
    """
    return generate_traffic_chart(traffic_data, **kwargs).render()
