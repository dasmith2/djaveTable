from datetime import datetime, date, timedelta, time

from django.utils.safestring import mark_safe
from djaveDT import tz_dt_to_str, time_to_time_str, d_to_str, tz_dt_to_tz_dt
from djmoney.money import Money


class CellContent(object):
  def as_html(self):
    raise NotImplementedError('as_html')

  def as_csv(self):
    raise NotImplementedError('as_csv')

  def __eq__(self, other):
    return self.as_html() == other.as_html()

  def __str__(self):
    return self.as_html()

  def __repr__(self):
    return self.as_html()


class Tooltip(CellContent):
  def __init__(self, label, help_text, width=None):
    self.label = label
    self.help_text = help_text
    self.width = width

  def as_html(self):
    width_str = ''
    if self.width:
      width_str = ' style="width: {}px;"'.format(self.width)
    template = (
        '<div class="tooltip">{}<span class="tooltiptext"{}>{}</span></div>')
    return mark_safe(template.format(self.label, width_str, self.help_text))

  def as_csv(self):
    return self.label


class Feedback(CellContent):
  def __init__(self, text, html_finder=None):
    self.text = text
    self.html_finder = html_finder

  def as_html(self):
    another_class = ''
    if self.html_finder:
      another_class = ' {}'.format(self.html_finder)
    return (
        '<span class="feedback{}">{}</span>'.format(another_class, self.text))


class DisappearingFeedback(Feedback):
  """ This is pretty much so I can briefly display "Saved!" on the page when
  the user clicks a Save button which causes a POST. """
  def __init__(self, text='Saved!', html_finder='hide_soon'):
    super().__init__(text, html_finder)

  def as_html(self):
    html = super().as_html()
    js = (
        '\n<script>'
        'setTimeout(function() {{ $(".{}").hide(); }}, 1000);'
        '</script>').format(self.html_finder)
    return mark_safe(html + js)


class InHref(CellContent):
  def __init__(self, cell_contents, url, classes=None, button=False):
    self.cell_contents = cell_contents
    self.url = url
    self.classes = classes or []
    if button:
      self.classes.append('button')

  def as_html(self):
    classes_str = ''
    if self.classes:
      classes_str = ' class="{}"'.format(' '.join(self.classes))
    return mark_safe('<a href="{}"{}>{}</a>'.format(
        self.url, classes_str, cell_contents_as_html(self.cell_contents)))

  def as_csv(self):
    return cell_contents_as_csv(self.cell_contents)


class ButtonInHref(InHref):
  def __init__(self, cell_contents, url, classes=[]):
    classes.append('button')
    super().__init__(cell_contents, url, classes=classes)


class StringContent(CellContent):
  def __init__(self, the_string):
    self.the_string = the_string

  def as_html(self):
    if not self.the_string:
      return '&nbsp;'
    return self.the_string

  def as_csv(self):
    if not self.the_string:
      return ''
    return self.the_string


class Paragraph(StringContent):
  def as_html(self):
    return mark_safe('<p>{}</p>'.format(super().as_html()))


class Img(CellContent):
  def __init__(self, img_src):
    self.img_src = img_src

  def as_html(self):
    return '<img src="{}" height="100">'.format(self.img_src)

  def as_csv(self):
    return self.img_src


class CellContentList(CellContent):
  def __init__(self, cell_contents):
    self.cell_contents = cell_contents

  def as_html(self):
    return cell_contents_as_html(self.cell_contents)

  def as_csv(self):
    return cell_contents_as_csv(self.cell_contents)


def assert_cell_contents_equal(
    expected_cell_contents, actual_cell_contents, message_prefix=''):
  if expected_cell_contents.__class__ != actual_cell_contents.__class__:
    raise AssertionError((
        '{}I am expecting cell contents to be of type {}, '
        'but instead it is {}').format(
            message_prefix, expected_cell_contents.__class__,
            actual_cell_contents.__class__))
  if isinstance(expected_cell_contents, list):
    if len(expected_cell_contents) != len(actual_cell_contents):
      raise AssertionError((
          '{}I am expecting {} cell content objects, but I got {} of '
          'them').format(
              message_prefix, len(expected_cell_contents),
              len(actual_cell_contents)))
    for i in range(len(expected_cell_contents)):
      assert_cell_content_equal(
          expected_cell_contents[i], actual_cell_contents[i],
          message_prefix='{} cell content {}'.format(message_prefix, i))
      return True
  return assert_cell_content_equal(
      expected_cell_contents, actual_cell_contents,
      message_prefix=message_prefix)


def assert_cell_content_equal(
    expected_cell_content, actual_cell_content, message_prefix=''):
  if expected_cell_content.__class__ != actual_cell_content.__class__:
    raise AssertionError((
        '{}I am expecting an object of type {} but got an object of '
        'type {}').format(
            message_prefix, expected_cell_content.__class__,
            actual_cell_content.__class__))
  if hasattr(expected_cell_content, 'assertEqual'):
    return expected_cell_content.assertEqual(
        actual_cell_content, message_prefix=message_prefix)
  if expected_cell_content != actual_cell_content:
    raise AssertionError('{}{} != {}'.format(
        message_prefix, expected_cell_content, actual_cell_content))


def cell_contents_as_html(cell_contents):
  to_return = []
  for cell_content in _cell_contents_as_list(cell_contents):
    to_return.append(cell_content.as_html())
  # Don't '\n'.join(to_return) because that will insert whitespace nodes
  # between buttons, causing the buttons to spread out more.
  return ''.join(to_return)


def cell_contents_as_csv(cell_contents):
  to_return = []
  for cell_content in _cell_contents_as_list(cell_contents, csv=True):
    to_return.append(cell_content.as_csv())
  return ''.join(to_return)


def _cell_contents_as_list(cell_contents, csv=False):
  if not isinstance(cell_contents, list):
    return _cell_contents_as_list([cell_contents], csv=csv)
  to_return = []
  for cell_content in cell_contents:
    to_return.append(obj_as_cell_content(cell_content, csv=csv))
  return to_return


def is_primitive(obj):
  return isinstance(obj, (int, str, bool, float))


def obj_as_cell_content(obj, csv=False):
  if isinstance(obj, CellContent):
    return obj
  if is_primitive(obj):
    if csv:
      return StringContent(str(obj).replace('\n', ' '))
    else:
      return StringContent(str(obj).replace('\n', '<br>'))
  if obj is None:
    return StringContent('')
  if isinstance(obj, datetime):
    if csv:
      return StringContent(tz_dt_to_tz_dt(obj).isoformat())
    else:
      return StringContent(tz_dt_to_str(obj))
  if isinstance(obj, date):
    if csv:
      return StringContent(obj.isoformat())
    else:
      return StringContent(d_to_str(obj))
  if isinstance(obj, timedelta):
    # Trim off microseconds.
    return StringContent(str(timedelta(days=obj.days, seconds=obj.seconds)))
  if isinstance(obj, time):
    return StringContent(time_to_time_str(obj))
  if isinstance(obj, list):
    return CellContentList([
        obj_as_cell_content(cell_content) for cell_content in obj])
  if isinstance(obj, Money):
    return StringContent(str(obj))
  raise Exception('I am not sure how to turn a {} into a CellContent'.format(
      obj.__class__))
