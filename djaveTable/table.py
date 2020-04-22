"""
Relational databases are basically glorified spreadsheet. Stay humble. All html
tables ought to be available as CSVs so folks can download the CSV and tinker
with the data to their heart's content. This is especially important to
accountants for some reason.

For heaven's sake, don't turn this table stuff into a poor man's type system.
Never assign IDs in this file. Columns, rows, cells, none of them have IDs.
Never write functions that dig around in the table and return data. Don't do
validation. Don't make tables of tables. These ideas are all too fancy. These
ideas are all at the wrong level of abstraction. This table is supposed to be
very close to the display layer and that's it.

The business-ey layers are the correct level to reuse code. Find whoever
generates the data for the table, and go THERE for the data, validation,
whatever. Go down one level. Don't be lazy. Understand the underlying code.

Your models.py

from djaveTable.table import Table

def get_foos():
  return <a list of foos>

def get_foo_table(foos):
  table = Table(['Column A', 'Column B'])
  for foo in foos:
    row = table.create_row([Cell(foo.pk, url=foo.get_url())])
    if foo.stuff():
      row.add(Cell(foo.stuff()))
    else:
      row.add(Cell())
  return table

Your views.py

from django.shortcuts import render
from foo.models import get_foos, get_foo_table

def get_foos(request):
  foos = get_foos()
  return render(
      request, 'foos.html', context={'foo_table': get_foo_table(foos)})

def get_foos_csv(request):
  foos = get_foos()
  return get_foo_table(foos).csv_response('foos.csv')

foos.html

{{ foo_table.as_html|safe }}

tests.py

class FooTests(TestCase):
  def test_get_foos(self):
  def test_get_foo_table(self):
    self.assertEqual(['Column A', 'Column B'], my_table.headers)
    my_table.rows[0].assertEqual(Row([Cell('stuff'), Cell()]))
"""

from datetime import datetime, timedelta

from django.utils.safestring import mark_safe
from djaveDT import tz_dt_to_str, tz_dt_to_tz_dt

from csv import csv_writer_and_response


class Table(object):
  def __init__(
      self, headers, rows=None, blank_td_text='&nbsp;', classes=[],
      title=None):
    self.headers = headers  # headers can be strings or Cells
    self.rows = rows or []
    self.blank_td_text = blank_td_text
    self.classes = classes
    self.title = title
    self._fields = None  # Table has a few form-like helper functions

  def set_fields(self, fields, values=None):
    self._fields = fields
    if values:
      for cell_content in self._fields:
        cell_content.set_value(values.get(cell_content.key()))

  def get_fields(self):
    return self._fields

  def is_valid(self):
    valid = True
    for cell_content in self._fields:
      valid = valid and cell_content.is_valid()
    return valid

  def create_row(self, cells=None, additional_attrs=None, classes=None):
    row = Row(cells=cells, additional_attrs=additional_attrs, classes=classes)
    self.rows.append(row)
    return row

  def csv_response(self, file_name):
    writer, response = csv_writer_and_response(file_name)
    header_row = []
    for header in self.headers:
      if isinstance(header, Cell):
        header_row.append(header.get_csv_content())
      else:
        header_row.append(header)
    writer.writerow(header_row)
    for row in self.rows:
      csv_row = []
      for cell in row.cells:
        if isinstance(cell, Cell):
          csv_row.append(cell.get_csv_content())
        else:
          csv_row.append(cell)
      writer.writerow(csv_row)
    return response

  def as_html(self):
    classes_str = ' class="{}"'.format(' '.join(self.classes + ['results']))
    title = ''
    if self.title:
      title = '<h3>{}</h3>'.format(self.title)
    to_return = [
        title,
        '<table{}>'.format(classes_str),
        '  <thead>',
        '    <tr>']
    for header in self.headers:
      if isinstance(header, Cell):
        to_return.append(header.as_html())
      else:
        to_return.append('<th>{}</th>'.format(header))
    to_return.extend([
        '    </tr>',
        '  </thead>',
        '  <tbody>'])

    for index, row in enumerate(self.rows):
      classes = row.classes + ['row1' if index % 2 == 0 else 'row2']
      row_start = ['    <tr class="{}"'.format(' '.join(classes))]
      for key, value in row.additional_attrs.items():
        row_start.append(' {}="{}"'.format(key, value))
      row_start.append('>')
      to_return.append(''.join(row_start))
      for cell in row.cells:
        if isinstance(cell, Cell):
          to_return.append(cell.as_html(blank_td_text=self.blank_td_text))
        else:
          to_return.append('<td>{}</td>'.format(_html_content_2_str(cell)))
      to_return.append('    </tr>')
    to_return.extend([
        '  </tbody>',
        '</table>'])
    to_return = '\n'.join(to_return)
    return to_return


def _html_content_2_str(str_content):
  if isinstance(str_content, datetime):
    return tz_dt_to_str(str_content)
  if isinstance(str_content, timedelta):
    # Trim off microseconds.
    return str(timedelta(days=str_content.days, seconds=str_content.seconds))
  if str_content is False:
    return 'False'
  if str_content in ('', None):
    return '&nbsp;'
  return str(str_content)


class CellContent(object):
  def render_html(self):
    raise NotImplementedError('render_html')

  def render_csv(self):
    raise NotImplementedError('render_csv')


class Cell(object):
  def __init__(
      self, str_content='', html_content=None, csv_content=None, cell_content=None,
      url=None, classes=[], is_header=False, img_url=None,
      additional_attrs=None, color=None):
    if cell_content:
      if not isinstance(cell_content, CellContent):
        raise Exception('cell_content should inherit from CellContent')
      if str_content or html_content or url or img_url:
        raise Exception(
            'You specified a cell_content so you shouldn\'t specify str_content, '
            'html_content, url, or img_url')
    if str_content:
      if html_content or csv_content:
        raise Exception(
            'You specified str_content, so you shouldn\'t specify html_content or '
            'csv_content')
    self.url = url
    self.classes = classes
    self.is_header = is_header
    self.img_url = img_url
    self.additional_attrs = additional_attrs
    self.html_content = html_content or str_content
    self.csv_content = csv_content or str_content
    self.cell_content = cell_content
    self.color = color

  def as_html(self, blank_td_text='&nbsp;'):
    t_what = 'td'
    inner_content_str = blank_td_text
    if self.is_header:
      t_what = 'th'
      inner_content_str = '&nbsp;'
    if self.cell_content:
      inner_content_str = self.cell_content.as_html()
    elif self.html_content is not None and self.html_content != '':
      inner_content_str = _html_content_2_str(self.html_content)
    elif self.img_url:
      inner_content_str = '<img src="{}" height="100">'.format(self.img_url)
    elif self.url:
      inner_content_str = 'Hyperlink'
    el
    content_str = inner_content_str
    if self.url or self.img_url:
      content_str = '<a href="{}">{}</a>'.format(
          self.url or self.img_url, inner_content_str)

    open_tag_parts = [t_what]
    if self.classes:
      open_tag_parts.append('class="{}"'.format(' '.join(self.classes)))
    if self.color:
      use_color = self.color
      if use_color[0] != '#':
        use_color = '#{}'.format(use_color)
      open_tag_parts.append('style="background-color: {}"'.format(use_color))
    if self.additional_attrs:
      for (key, value) in self.additional_attrs.items():
        open_tag_parts.append("{}='{}'".format(key, value))
    open_tag_str = ' '.join(filter(None, open_tag_parts))

    return mark_safe(
        '<{}>{}</{}>'.format(open_tag_str, content_str, t_what))

  def get_csv_content(self):
    if self.cell_content:
      return self.cell_content.render_csv()
    if self.csv_content is None or self.csv_content == '':
      return self.url or self.img_url or ''
    return self.csv_content

  def assertEqual(self, expected_cell, message_prefix=''):
    """ Handy for tests. """
    if not isinstance(expected_cell, Cell):
      raise AssertionError(
          '{}I\'m a Cell but the expected_cell is a {}'.format(
              message_prefix, expected_cell.__class__))
    if self.html_content != expected_cell.html_content:
      raise AssertionError(
          '{}I\'ve got {} but expected_cell\'s got {}'.format(
              message_prefix, self.html_content, expected_cell.html_content))
    if self.csv_content != expected_cell.csv_content:
      raise AssertionError(
          '{}I\'ve got csv {} but expected_cell\'s got {}'.format(
              message_prefix, self.csv_content, expected_cell.csv_content))
    if self.url != expected_cell.url:
      raise AssertionError(
          '{}My url is {} but expected_cell\'s url is {}'.format(
              message_prefix, self.url, expected_cell.url))
    if self.img_url != expected_cell.img_url:
      raise AssertionError(
          '{}My img_url is {} but expected_cell\'s img_url is {}'.format(
              message_prefix, self.img_url, expected_cell.img_url))
    if self.classes != expected_cell.classes:
      raise AssertionError(
          '{}My classes are {} but expected_cell\'s classes are {}'.format(
              message_prefix, self.classes, expected_cell.classes))
    if self.is_header != expected_cell.is_header:
      if self.is_header:
        raise AssertionError('I\'m a header but expected_cell isn\'t.')
      raise AssertionError('I\'m not a header but expected_cell is.')
    return True

  def __str__(self):
    return self.__repr__()

  def __repr__(self):
    attrs = []

    if self.html_content == self.csv_content:
      str_content = self.html_content
      if str_content:
        if isinstance(str_content, datetime):
          str_content = tz_dt_to_tz_dt(str_content)
        attrs.append(str_content.__repr__())
    else:
      attrs.append("html_content='{}', csv_content='{}'".format(
          self.html_content, self.csv_content))
    if self.url:
      attrs.append("url='{}'".format(self.url))
    if self.classes:
      attrs.append("classes={}".format(self.classes))
    if self.is_header:
      attrs.append("is_header=True")
    if self.img_url:
      attrs.append("img_url='{}'".format(self.img_url))
    if self.additional_attrs:
      for (key, value) in self.additional_attrs.items():
        attrs.append("{}='{}'".format(key, value))
    return "Cell({})".format(', '.join(attrs))

  def __eq__(self, other):
    try:
      return self.assertEqual(other)
    except AssertionError:
      return False


class Row(object):
  def __init__(self, cells=None, classes=None, additional_attrs=None):
    self.cells = cells or []  # cells can be strings or Cells
    self.classes = classes or []
    self.additional_attrs = additional_attrs or {}

  def __str__(self):
    return self.__repr__()

  def __repr__(self):
    attrs = []
    if self.cells:
      attrs.extend([cell.__repr__() for cell in self.cells])
    if self.classes:
      attrs.append('classes={}'.format(self.classes))
    return 'Row({})'.format(', '.join(attrs))

  def add(self, cell):
    self.cells.append(cell)

  def extend(self, cells):
    self.cells.extend(cells)

  def add_class(self, css_class):
    self.classes.append(css_class)

  def assertEqual(self, expected_row):
    """ Handy for tests. """
    if set(self.classes) != set(expected_row.classes):
      raise AssertionError(
          'I\'m expecting classes {} on this row but I have {}'.format(
              expected_row.classes, self.classes))
    if self.additional_attrs != expected_row.additional_attrs:
      raise AssertionError((
          'I\'m expecting additional_attrs {} on this row but I '
          'have {}').format(
              expected_row.additional_attrs, self.additional_attrs))
    if len(self.cells) != len(expected_row.cells):
      message = 'I have {} cells but the expected_row has {} cells'.format(
          len(self.cells), len(expected_row.cells))
      raise AssertionError(message)
    for i, cell in enumerate(self.cells):
      if isinstance(cell, Cell):
        cell.assertEqual(
            expected_row.cells[i],
            message_prefix='Cell {} explains: '.format(i))
      elif cell != expected_row.cells[i]:
        raise AssertionError(
            'I have {} at cell {} but the expected_row has {}'.format(
                cell, i, expected_row.cells[i]))
