# -*- coding: utf-8 -*-
import pygal
from flask_babel import gettext
from pygal.colors import hsl_to_rgb
from pygal.style import Style

from sipa.units import (format_as_traffic, max_divisions,
                        reduce_by_base)
from sipa.utils.babel_utils import get_weekday


def rgb_string(r, g, b):
    return "#{:02X}{:02X}{:02X}".format(int(r), int(g), int(b))


def hsl(h, s, l):
    return rgb_string(*hsl_to_rgb(h, s, l))


traffic_style = Style(
    background='transparent',
    opacity='.6',
    opacity_hover='.9',
    transition='200ms ease-in',
    colors=(hsl(130, 80, 60), hsl(70, 80, 60), hsl(190, 80, 60)),
    font_family='default'
)


def default_chart(chart_type, title, inline=True, **kwargs):
    return chart_type(
        fill=True,
        title=title,
        height=350,
        show_y_guides=True,
        human_readable=False,
        major_label_font_size=12,
        label_font_size=12,
        style=traffic_style,
        disable_xml_declaration=inline,   # for direct html import
        js=[],  # prevent automatically fetching scripts from github
        **kwargs,
    )


def generate_traffic_chart(traffic_data, inline=True):
    """Create a graph object from the input traffic data with pygal.
     If inline is set, the chart is being passed the option to not add an xml
     declaration header to the beginning of the `render()` output, so it can
      be directly included in HTML code (wrapped by a `<figure>`)
    :param traffic_data: The traffic data as given by `user.traffic_history`
    :param inline: Determines the option `disable_xml_declaration`
    :return: The graph object
    """
    # choose unit according to maximum of `throughput`
    divisions = max_divisions(max(day['throughput'] for day in traffic_data))

    traffic_data = [{key: (reduce_by_base(val, divisions=divisions)
                           if key in ['input', 'output', 'throughput']
                           else val)
                     for key, val in entry.items()
                     }
                    for entry in traffic_data]

    traffic_chart = default_chart(
        pygal.Bar,
        gettext("Traffic (MiB)"),
        inline,
        # don't divide, since the raw values already have been prepared.
        # `divide=False` effectively just appends the according unit.
        value_formatter=lambda value: format_as_traffic(value, divisions, divide=False),
    )

    traffic_chart.x_labels = (get_weekday(day['day']) for day in traffic_data)
    traffic_chart.add(gettext("Eingehend"),
                      [day['input'] for day in traffic_data],
                      stroke_style={'dasharray': '5'})
    traffic_chart.add(gettext("Ausgehend"),
                      [day['output'] for day in traffic_data],
                      stroke_style={'dasharray': '5'})
    traffic_chart.add(gettext("Gesamt"),
                      [day['throughput'] for day in traffic_data],
                      stroke_style={'width': '2'})

    return traffic_chart


def generate_credit_chart(traffic_data, inline=True, max_credit=(63 * 1024 ** 2)):
    """Create a graph object from the input traffic data with pygal.
     If inline is set, the chart is being passed the option to not add an xml
     declaration header to the beginning of the `render()` output, so it can
      be directly included in HTML code (wrapped by a `<figure>`)
    :param traffic_data: The traffic data as given by `user.traffic_history`
    :param inline: Determines the option `disable_xml_declaration`
    :return: The graph object
    """
    raw_max = max_credit
    divisions = max_divisions(raw_max)
    max = reduce_by_base(raw_max, divisions)

    credit_chart = default_chart(
        pygal.Line,
        gettext("Credit (GiB)"),
        inline,
        value_formatter=lambda value: format_as_traffic(value, divisions, divide=False),
    )
    credit_chart.range = (0, max)

    credit_chart.x_labels = (get_weekday(day['day']) for day in traffic_data)
    credit_chart.add(gettext("Credit"),
                     [reduce_by_base(day['credit'], divisions=divisions)
                      for day in traffic_data])
    credit_chart.add(gettext("Maximum"),
                     [max]*len(traffic_data),
                     stroke_style={'dasharray': '7', 'width': '2'},
                     fill=False,
                     show_dots=False)

    return credit_chart


def provide_render_function(generator):
    def renderer(data, **kwargs):
        return generator(data, **kwargs).render()

    return renderer
