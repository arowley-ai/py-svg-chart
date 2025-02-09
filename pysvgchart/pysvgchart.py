import collections.abc
import math
import datetime as dt


def default_format(value):
    return '{0:,}'.format(value)


def collapse_element_list(built_ins):
    return [e for built_in in built_ins for e in built_in.get_element_list()]


def safe_get_element_list(built_in):
    return built_in.get_element_list() if built_in is not None else []


def get_numeric_limits(values, max_ticks):
    value_min, value_max = min(values), max(values)
    raw_pad = (1.2 * value_max - 0.95 * value_min) / max_ticks
    remainder = math.log10(abs(raw_pad)) - int(math.log10(abs(raw_pad)))
    leader = 2 if remainder < 0.301 else (5 if remainder < 0.698 else 10)
    pad = leader * 10 ** int(math.log10(abs(raw_pad)))
    start = int(math.floor(0.95 * value_min / pad))
    end = int(math.ceil(1.2 * value_max / pad))
    return [y * pad for y in range(start, end + 1)]


def get_big_date_limits(dates, max_ticks=10):
    date_min, date_max = min(dates), max(dates)
    total_days = (date_max - date_min).days
    if total_days <= 0:
        raise ValueError("Dates must have a positive range.")

    approx_months = total_days / 30.0
    raw_interval = approx_months / max_ticks

    if raw_interval <= 1:
        interval_months = 1
    elif raw_interval <= 2:
        interval_months = 2
    elif raw_interval <= 3:
        interval_months = 3
    elif raw_interval <= 6:
        interval_months = 6
    else:
        interval_months = 12

    start = dt.datetime(date_min.year, date_min.month, 1)
    end = dt.datetime(date_max.year, date_max.month, 1) + dt.timedelta(days=31)
    end = dt.datetime(end.year, end.month, 1)

    ticks = []
    current_tick = start
    while current_tick <= end:
        ticks.append(current_tick.date())
        month = current_tick.month + interval_months
        year = current_tick.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        current_tick = dt.datetime(year, month, 1)

    return ticks


def get_limits(values, max_ticks):
    if values is None or not isinstance(values, collections.abc.Iterable) or len(set(values)) <= 1:
        raise ValueError("Values must be a non-empty iterable with at least two unique elements.")
    if all(isinstance(v, dt.datetime) or isinstance(v, dt.date) for v in values):
        return get_big_date_limits(values, max_ticks)
    elif all(isinstance(v, int) or isinstance(v, float) for v in values):
        return get_numeric_limits(values, max_ticks)
    else:
        raise ValueError("Invalid numeric data")


class Point:

    def __init__(self, x_position, y_position):
        self.x = x_position
        self.y = y_position


class Shape:

    def __init__(self, x_position, y_position):
        self.position = Point(x_position, y_position)
        self.styles = dict()

    @property
    def render_styles(self):
        return " ".join([style + '="' + self.styles[style] + '"' for style in self.styles])

    def get_element_list(self):
        raise NotImplementedError("Not implemented in generic shape.")


class Line(Shape):
    line_template = '<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" {styles}/>'

    def __init__(self, x_position, y_position, width, height, styles=None):
        super().__init__(x_position, y_position)
        self.end = Point(x_position + width, y_position + height)
        self.styles = dict() if styles is None else styles

    @property
    def start(self):
        return self.position

    def get_element_list(self):
        return [self.line_template.format(x1=self.start.x, y1=self.start.y, x2=self.end.x, y2=self.end.y, styles=self.render_styles)]


class Circle(Shape):
    circle_template = '<circle cx="{x}" cy="{y}" r="{r}" {styles}/>'

    def __init__(self,x_position, y_position, radius, styles=None):
        super().__init__(x_position, y_position)
        self.styles = dict() if styles is None else styles
        self.radius = radius

    def get_element_list(self):
        return [self.circle_template.format(x=self.position.x, y=self.position.y, r=self.radius, styles=self.render_styles)]

class Text(Shape):
    text_template = '<text x="{x}" y="{y}" {styles}>{content}</text>'

    def __init__(self, x_position, y_position, content, styles=None):
        super().__init__(x_position, y_position)
        self.styles = dict() if styles is None else styles
        self.content = content

    def get_element_list(self):
        return [self.text_template.format(x=self.position.x, y=self.position.y, content=self.content, styles=self.render_styles)]


class Axis(Shape):
    default_axis_styles = {'stroke': '#2e2e2c'}

    def __init__(self, x_position, y_position, data_points, axis_length, label_format, max_ticks=10, axis_styles=None, tick_length=5):
        super().__init__(x_position, y_position)
        self.data_points = data_points
        self.length = axis_length
        self.limits = get_limits(data_points, max_ticks)
        self.label_format = label_format
        self.axis_line = None
        self.tick_lines, self.tick_text, self.grid_lines = [], [], []

    def proportion_of_range(self, value):
        return (value - min(self.limits)) / (max(self.limits) - min(self.limits))

    def get_element_list(self):
        return safe_get_element_list(self.axis_line) + collapse_element_list(self.tick_lines) + collapse_element_list(self.tick_text) + collapse_element_list(self.grid_lines)


class XAxis(Axis):
    default_tick_text_styles = {'text-anchor': 'middle', 'dominant-baseline': 'hanging'}

    def __init__(self, x_position, y_position, data_points, axis_length, label_format, max_ticks=10, axis_styles=None, tick_length=5):
        super().__init__(x_position, y_position, data_points, axis_length, label_format, max_ticks, axis_styles, tick_length)
        styles = axis_styles or self.default_axis_styles.copy()
        self.axis_line = Line(x_position=self.position.x, y_position=self.position.y, width=axis_length, height=0, styles=styles)
        for i, m in enumerate(self.limits):
            width_offset = i * self.length / (len(self.limits) - 1) + self.position.x
            self.tick_lines.append(Line(x_position=width_offset, width=0, y_position=self.position.y, height=tick_length, styles=styles))
            self.tick_text.append(Text(x_position=width_offset, y_position=self.position.y + 2 * tick_length, content=label_format(m), styles=self.default_tick_text_styles.copy()))

    def get_positions(self, values):
        return [self.position.x + self.proportion_of_range(v) * self.length for v in values]


class YAxis(Axis):
    default_tick_text_styles = {'text-anchor': 'end', 'dominant-baseline': 'middle'}

    def __init__(self, x_position, y_position, data_points, axis_length, label_format, max_ticks=10, axis_styles=None, tick_length=5):
        super().__init__(x_position, y_position, data_points, axis_length, label_format, max_ticks, axis_styles, tick_length)
        styles = axis_styles or self.default_axis_styles.copy()
        self.axis_line = Line(x_position=self.position.x, y_position=self.position.y, width=0, height=axis_length, styles=styles)
        for i, m in enumerate(self.limits):
            height_offset = (len(self.limits) - 1 - i) * self.length / (len(self.limits) - 1) + self.position.y
            self.tick_lines.append(Line(x_position=self.position.x - tick_length, width=tick_length, y_position=height_offset, height=0, styles=styles))
            self.tick_text.append(Text(x_position=self.position.x - 2 * tick_length, y_position=height_offset, content=label_format(m), styles=self.default_tick_text_styles.copy()))

    def get_positions(self, values):
        return [self.position.y + self.length * (1 - self.proportion_of_range(v)) for v in values]


class SimpleXAxis(XAxis):

    def get_positions(self, x_values):
        return [self.position.x + x * self.length / (len(x_values) - 1) for x in range(len(x_values))]


class SimpleLineSeries(Shape):
    path_default_styles = {'stroke-width': '2'}
    path_begin_template = '<path d="{path}" fill="none" {styles}/>'

    def __init__(self, points):
        super().__init__(points[0].x, points[0].y)
        self.points = points
        self.styles = self.path_default_styles.copy()

    def get_element_list(self):
        path = ' '.join(['{0} {1} {2}'.format("L" if i else "M", p.x, p.y) for i, p in enumerate(self.points)])
        return [self.path_begin_template.format(path=path, styles=self.render_styles)]

    @property
    def path_length(self):
        return sum(math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2) for p1, p2 in zip(self.points, self.points[1:])) if len(self.points) > 2 else 0


class LineLegend(Shape):
    default_line_legend_text_styles = {'alignment-baseline': 'middle'}

    def __init__(self, x_position, y_position, series, element_x, element_y, line_length, line_text_gap):
        super().__init__(x_position, y_position)
        self.series = series
        self.lines, self.texts = [], []
        x_pos, y_pos = self.position.x, self.position.y
        for index, series in enumerate(self.series):
            self.lines.append(Line(x_pos, y_pos, line_length, 0, styles=self.series[series].styles))
            self.texts.append(Text(x_pos + line_length + line_text_gap, y_pos, content=series, styles=self.default_line_legend_text_styles))
            x_pos += element_x
            y_pos += element_y

    def get_element_list(self):
        return collapse_element_list(self.lines) + collapse_element_list(self.texts)


class Chart:
    # height="{height}" width="{width}"
    svg_begin_template = '<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
    default_major_grid_styles = {'stroke': '#2e2e2c'}
    default_minor_grid_styles = {'stroke': '#2e2e2c', 'stroke-width': "0.4"}

    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.y_axis = None
        self.x_axis = None
        self.legend = None
        self.series = []
        self.custom_elements = []

    def add_custom_element(self, custom_element):
        self.custom_elements.append(custom_element)

    def render(self):
        return '\n'.join([
            self.svg_begin_template.format(height=self.height, width=self.width),
            *self.get_element_list(),
            '</svg>'
        ])

    def get_element_list(self):
        target_names = ['x_axis', 'y_axis', 'legend']
        targets = [getattr(self, target) for target in target_names if getattr(self, target) is not None]
        targets.extend(self.series[s] for s in self.series)
        targets.extend(self.custom_elements)
        return [e for t in targets for e in t.get_element_list()]

    def add_grids(self, minor_x_ticks=0, minor_y_ticks=0, major_grid_style=None, minor_grid_style=None):
        self.add_y_grid(minor_y_ticks, major_grid_style, minor_grid_style)
        self.add_x_grid(minor_x_ticks, major_grid_style, minor_grid_style)

    def add_y_grid(self, minor_ticks=0, major_grid_style=None, minor_grid_style=None):
        major_style = major_grid_style.copy() if major_grid_style is not None else self.default_major_grid_styles.copy()
        minor_style = minor_grid_style.copy() if minor_grid_style is not None else self.default_minor_grid_styles.copy()
        for i, m in enumerate(self.x_axis.limits[1:]):
            width_offset = (i + 1) * self.x_axis.length / (len(self.x_axis.limits) - 1) + self.y_axis.position.x
            self.y_axis.grid_lines.append(
                Line(
                    x_position=width_offset,
                    y_position=self.x_axis.position.y - self.y_axis.length,
                    width=0,
                    height=self.y_axis.length,
                    styles=major_style
                )
            )
            minor_step = self.x_axis.length / (len(self.x_axis.limits) - 1) / (minor_ticks + 1)
            for j in range(1, minor_ticks + 1):
                minor_offset = width_offset - j * minor_step
                self.y_axis.grid_lines.append(Line(
                    x_position=minor_offset,
                    y_position=self.x_axis.position.y - self.y_axis.length,
                    width=0,
                    height=self.y_axis.length,
                    styles=minor_style
                ))

    def add_x_grid(self, minor_ticks=0, major_grid_style=None, minor_grid_style=None):
        major_style = major_grid_style.copy() if major_grid_style is not None else self.default_major_grid_styles.copy()
        minor_style = minor_grid_style.copy() if minor_grid_style is not None else self.default_minor_grid_styles.copy()
        for i, m in enumerate(self.y_axis.limits[1:]):
            height_offset = (len(self.y_axis.limits) - 2 - i) * self.y_axis.length / (len(self.y_axis.limits) - 1) + self.x_axis.position.y
            self.x_axis.grid_lines.append(
                Line(
                    x_position=self.y_axis.position.x,
                    y_position=height_offset - self.y_axis.length,
                    width=self.x_axis.length,
                    height=0,
                    styles=major_style
                )
            )
            minor_step = self.y_axis.length / (len(self.y_axis.limits) - 1) / (minor_ticks + 1)
            for j in range(1, minor_ticks + 1):
                minor_offset = height_offset + j * minor_step
                self.y_axis.grid_lines.append(Line(
                    x_position=self.y_axis.position.x,
                    y_position=minor_offset - self.y_axis.length,
                    width=self.x_axis.length,
                    height=0,
                    styles=minor_style
                ))


class SimpleLineChart(Chart):
    __line_colour_defaults__ = ['green', 'red', 'blue']

    def __init__(self, x_values, y_values, y_names=None, x_max_ticks=12, y_max_ticks=12, x_margin=100, y_margin=100, height=600, width=800, x_labels=default_format, y_labels=default_format):
        super().__init__(height, width)
        series_names = y_names if y_names is not None else ['Series {0}'.format(range(len(y_values)))]
        all_y_values = [v for series in y_values for v in series]
        self.y_axis = YAxis(x_position=x_margin, y_position=y_margin, data_points=all_y_values, axis_length=height - 2 * y_margin, label_format=y_labels, max_ticks=y_max_ticks)
        self.x_axis = SimpleXAxis(x_position=x_margin, y_position=height - y_margin, data_points=x_values, axis_length=width - 2 * x_margin, label_format=x_labels, max_ticks=x_max_ticks)
        self.series = {name: SimpleLineSeries([Point(x, y) for x, y in zip(self.x_axis.get_positions(x_values), self.y_axis.get_positions(y_value))]) for name, y_value in zip(series_names, y_values)}
        for index, series in enumerate(self.series):
            self.series[series].styles['stroke'] = self.__line_colour_defaults__[index]

    def add_legend(self, x_position=500, y_position=60, element_x=100, element_y=0, line_length=20, line_text_gap=5):
        self.legend = LineLegend(x_position, y_position, self.series, element_x, element_y, line_length, line_text_gap)
