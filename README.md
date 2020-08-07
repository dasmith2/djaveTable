# djaveTable

Django tools for creating and displaying tables in html and csv.

Relational databases are basically glorified spreadsheets. Stay humble. All
html tables ought to be available as CSVs so folks can download the CSV and
tinker with the data to their heart's content. This is especially important to
accountants for some reason.

For heaven's sake, don't turn this table stuff into a poor man's type system.
Never write functions that dig around in the table and return data. Don't do
validation. Don't make tables of tables. These ideas are all too fancy. These
ideas are all at the wrong level of abstraction. This table is supposed to be
very close to the display layer and that's it. It's handy for displaying the
same table as either html or csv, and it's handy for testing that your code is
generating the table you expect.

The business-ey layers are the correct level to reuse code. Find whoever
generates the data for the table, and go THERE for the data, validation,
whatever.

Your models.py

    from djaveTable.table import Table
    from djaveTable.cell_content import InHref, Img

    def get_foos():
      return <a list of foos>

    def get_foo_table(foos):
      table = Table(['Raw string', 'Hyperlink img', 'Cell'])
      for foo in foos:
        row = table.create_row([
            'Hello world', InHref(Img(foo.get_thumbnail()), foo.get_url())])
        if foo.stuff():
          row.add(Cell(foo.stuff(), color="#f00"))
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
        self.assertEqual(['Raw string', 'Hyperlink img', 'Cell'], my_table.headers)
        my_table.rows[0].assertEqual(Row([
            'Hello world', InHref(Img('test_thumbnail.jpg'), '/my_foo'),
            Cell('Stuff!', color='#f00')]))
