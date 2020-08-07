function setup_edit_field_turns_yellow(
    table_selector_or_elt, row_parent_finder, turn_on_edit_mode_callback,
    turn_off_edit_mode_callback) {
  /* This isn't strictly for tables. table_selector_or_elt can be an outer div
   * or something, and row_parent_finder can point to inner divs. It waits
   * until you change something, then colors the "row" yellow so the user can
   * easily see that there's an incomplete thought on the page. */
  var table = $(table_selector_or_elt);
  // In case there's more than one edit table on the page and this function
  // gets called once for each.
  var already_attr = 'data-setup-edit-field-turns-yellow';
  if (table.attr(already_attr)) {
    return;
  }
  table.attr(already_attr, 'yep');

  var elts = table.find('input,select,textarea');
  setup_saved_value(elts);

  var handle_row_maybe_changed = function(event) {
    var row = $(this).parents(row_parent_finder);
    calc_edit_mode(
        row, turn_on_edit_mode_callback, turn_off_edit_mode_callback);
  };

  anything_happened(elts, handle_row_maybe_changed);
}

function setup_saved_value(selector_or_elt) {
  $(selector_or_elt).each(function() {
    var elt = $(this);
    elt.attr('data-saved-value', val(elt));
  });
}

var calc_edit_mode = function(
    row, turn_on_edit_mode_callback, turn_off_edit_mode_callback) {
  var got_all_elts = all_elts(row);
  var any_editing = false;
  for (var i = 0; i < got_all_elts.length; i++) {
    any_editing = any_editing || is_editing($(got_all_elts[i]));
  }
  if (any_editing) {
    turn_on_edit_mode(row, turn_on_edit_mode_callback);
  } else {
    turn_off_edit_mode(row, turn_off_edit_mode_callback);
  }
};

function anything_happened(selector_or_elt, callback) {
  $(selector_or_elt).on('input', callback);
}

function val(elt) {
  if (elt.attr('type') == 'checkbox') {
    return elt.is(':checked');
  }
  return elt.val();
}

var all_elts = function(row) {
  // Wait to calculate this so all columns that want to edit get a chance
  // to wire up.
  return row.find('[data-saved-value]');
};

var is_editing = function(elt) {
  // Sometimes val(elt) is a boolean but I'm comparing it to a string version
  // of an earlier value.
  return elt.attr('data-saved-value') != (val(elt) + '');
};

var turn_on_edit_mode = function(row, turn_on_edit_mode_callback) {
  row.addClass('editing');
  if (turn_on_edit_mode_callback) {
    turn_on_edit_mode_callback(row);
  }
};


var turn_off_edit_mode = function(row, turn_off_edit_mode_callback) {
  row.removeClass('editing');
  if (turn_off_edit_mode_callback) {
    turn_off_edit_mode_callback(row);
  }
};

var buttons_cell = function(row) {
  var by_other_buttons = other_buttons(row).parents('td');
  if (by_other_buttons.length) {
    return by_other_buttons;
  }
  return row.find('.buttons');
};

var other_buttons = function(row) {
  return row.find('button,.button');
};
