from django.utils.safestring import mark_safe


class SimpleList(object):
  def __init__(self, elements):
    self.elements = elements

  def as_html(self):
    divs = []
    for elt in self.elements:
      divs.append('<div class="margin-top-third">{}</div>'.format(
          elt.as_html()))
    return mark_safe('\n'.join(divs))
