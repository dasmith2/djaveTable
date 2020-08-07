function resize_textarea(textarea) {
  var computed_style = getComputedStyle(textarea[0]);
  // min-height and max-height are set in all_sites.css min-height is the
  // height of a button.
  var min_height = px_to_int(computed_style.minHeight);
  var max_height = px_to_int(computed_style.maxHeight);

  var height_finder = get_height_finder(computed_style);
  height_finder.show();
  height_finder.html(textarea.val().replace(/\n/g, '<br>'));
  // If you try to get the height of the height_finder span, you'll only
  // get the height up to the first line break.
  var wants_to_be_height = height_finder.height();
  var use_height = wants_to_be_height;
  if (wants_to_be_height < min_height) {
    use_height = min_height;
  } else if (wants_to_be_height > max_height) {
    use_height = max_height;
  }
  textarea.height(use_height);
  height_finder.hide();  // To debug this stuff, comment out.
};

function get_height_finder(computed_style) {
  /* This assumes all textareas have the same font and padding, but they can
   * have different widths. */
  var height_finder = $('#height_finder');
  if (!height_finder.length) {
    height_finder = $('<div id="height_finder"/>').appendTo('body').css({
        'border': '1px solid',
        'font-size': computed_style.fontSize,
        'font-family': computed_style.fontFamily,
        'font-weight': computed_style.fontWeight,
        'padding-top': computed_style.paddingTop,
        'padding-right': computed_style.paddingRight,
        'padding-left': computed_style.paddingLeft,
        'padding-bottom': computed_style.paddingBottom});
  }
  var width = px_to_int(computed_style.width);
  return height_finder.width(width);
}

function resize_textareas() {
  // You have to wait until the page is visible in order to ask questions about
  // what dimensions things are. Resizing can work incorrectly if you do a hard
  // refresh because then the browser fetches the fonts from scratch. But if
  // you do normal refreshes it's fine.
  on_display(function() {
    var textareas = $('textarea');
    for (var i = 0; i < textareas.length; i++) {
      var textarea = $(textareas[i]);
      if (!textarea.attr('data-initial-resize')) {
        textarea.attr('data-initial-resize', 'yep').on('input', function() {
          resize_textarea($(this));
        });
        resize_textarea(textarea);
      }
    }
  });
}

$(resize_textareas);
