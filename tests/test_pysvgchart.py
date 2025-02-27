import pytest
import pysvgchart as psc
import random
import os
import datetime as dt
import math


def write_out(chart, name):
    output_dir = "outputs"
    output_file = os.path.join(output_dir, name)
    os.makedirs(output_dir, exist_ok=True)
    with open(output_file, 'w+') as out_file:
        out_file.write(chart.render())
    return output_file


def test_simple_line_chart_creation():
    x_values = list(range(100))
    y_values = [4000]
    for i in range(99):
        y_values.append(y_values[-1] + 100 * random.randint(0, 1))

    line_chart = psc.SimpleLineChart(
        x_values=x_values,
        y_values=[y_values, [1000 + y for y in y_values]],
        y_names=['predicted', 'actual'],
        x_max_ticks=20,
        y_zero=True,
    )
    line_chart.add_grids(minor_y_ticks=4, minor_x_ticks=4)
    line_chart.add_legend()

    output_file = write_out(line_chart, name="simple.svg")

    assert os.path.exists(output_file), "SVG file was not created."
    assert 'svg' in line_chart.render().lower(), "SVG content is not in the render output."
    assert len(line_chart.y_axis.tick_text) > 0, "Y-axis ticks are missing."
    assert line_chart.y_axis.tick_text[-1].styles, "Y-axis tick styles are missing."
    assert isinstance(line_chart.series['predicted'].path_length, float), "Path length error"


def test_stylised_line_chart():
    def y_labels(num):
        num = float('{:.3g}'.format(num))
        magnitude = 0
        while abs(num) >= 1000:
            magnitude += 1
            num /= 1000.0
        rtn = '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])
        return rtn.replace('.00', '').replace('.0', '')

    def x_labels(date):
        return date.strftime('%b')

    dates = [dt.date.today() - dt.timedelta(days=i) for i in range(500) if (dt.date.today() + dt.timedelta(days=i)).weekday() == 0]
    actual = [(1 + math.sin(d.timetuple().tm_yday / 183 * math.pi)) * 50000 + 1000 * i + random.randint(-10000, 10000) for i, d in enumerate(dates)]
    expected = [a + random.randint(-10000, 10000) for a in actual]
    line_chart = psc.SimpleLineChart(x_values=dates, y_values=[actual, expected], y_names=['Actual sales', 'Predicted sales'], x_max_ticks=30, x_label_format=x_labels, y_label_format=y_labels, width=1200)
    line_chart.series['Actual sales'].styles = {'stroke': "#DB7D33", 'stroke-width': '3'}
    line_chart.series['Predicted sales'].styles = {'stroke': '#2D2D2D', 'stroke-width': '3', 'stroke-dasharray': '4,4'}
    line_chart.add_legend(x_position=700, element_x=200, line_length=35, line_text_gap=20)
    line_chart.add_y_grid(minor_ticks=0, major_grid_style={'stroke': '#E9E9DE'})
    line_chart.x_axis.tick_lines, line_chart.y_axis.tick_lines = [], []
    line_chart.x_axis.axis_line = None
    line_chart.y_axis.axis_line.styles['stroke'] = '#E9E9DE'
    line_end = line_chart.legend.lines[0].end
    styles = {'fill': '#FFFFFF', 'stroke': '#DB7D33', 'stroke-width': '3'}
    line_chart.add_custom_element(psc.Circle(x_position=line_end.x, y_position=line_end.y, radius=4, styles=styles))
    line_end = line_chart.legend.lines[1].end
    styles = {'fill': '#2D2D2D', 'stroke': '#2D2D2D', 'stroke-width': '3'}
    line_chart.add_custom_element(psc.Circle(x_position=line_end.x, y_position=line_end.y, radius=4, styles=styles))
    for limit, tick in zip(line_chart.x_axis.limits, line_chart.x_axis.tick_text):
        if tick.content == 'Jan':
            line_chart.add_custom_element(psc.Text(x_position=tick.position.x, y_position=tick.position.y + 15, content=str(limit.year), styles=tick.styles))

    write_out(line_chart, name="detailed.svg")
