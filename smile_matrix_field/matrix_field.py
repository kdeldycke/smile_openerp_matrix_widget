# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Smile. All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

from copy import deepcopy
import datetime

from osv import osv, fields, orm
from tools.func import wraps
from tools.translate import _



# List of values supported by the default_line_rendering parameter
LINE_RENDERING_MODES = [
    ('increment', 'Increment button'),
    ('boolean', 'Check box'),
    ('float', 'Float field'),
    ('selection', 'Selection drop-down menu'),
    ('spacer', 'Blank matrix-wide line'),
    ('header', 'Matrix-wide header line'),
    ]



def _get_prop(obj, prop_name, default_value=None):
    """ Get a property value
    """
    if not prop_name or obj is None or prop_name not in obj._columns:
        return default_value
    prop_value = getattr(obj, prop_name, default_value)
    if prop_value is None:
        raise osv.except_osv('Error !', "%r has no %s property." % (obj, prop_name))
    return prop_value



def _get_date_range(base_object, date_range_property, visible_date_range_property, editable_date_range_property):
    """ Utility method to get the displayed date range and the visible date range.
        This piece of code was moved in its own method as date range extraction requires some special handling.
    """
    # Get on the current object the date range bounding the timeline
    date_range = _get_prop(base_object, date_range_property)
    # Get the visible date range. Default is to let all dates of the displayed range.
    visible_date_range = _get_prop(base_object, visible_date_range_property, date_range)
    # Get the editable date range. Default is to align this range on the visible date range.
    editable_date_range = _get_prop(base_object, editable_date_range_property, visible_date_range)

    # date_range and visible_date_range values may be stored as text (or selection, which is the same). In this case, we need to evaluate them. It's bad, but it works.
    if isinstance(date_range, (str, unicode)):
        date_range = eval(date_range)
    if isinstance(visible_date_range, (str, unicode)):
        visible_date_range = eval(visible_date_range)
        if not visible_date_range:
            visible_date_range = date_range
    if isinstance(editable_date_range, (str, unicode)):
        editable_date_range = eval(editable_date_range)
        if not editable_date_range:
            editable_date_range = visible_date_range

    # Check the data structure returned by date ranges
    for (range_name, range_data) in [(date_range_property, date_range), (visible_date_range_property, visible_date_range), (editable_date_range_property, editable_date_range)]:
        if type(range_data) is not type([]):
            raise osv.except_osv('Error !', "%s must return a list of datetime.date objects." % range_name)
        for d in range_data:
            if not isinstance(d, datetime.date):
                raise osv.except_osv('Error !', "%s must return a list of datetime.date objects." % range_name)

    return (date_range, visible_date_range, editable_date_range)




class matrix(fields.dummy):
    """ A custom field to prepare data for, and mangle data from, the matrix widget.
        If you need help, read the _parse_conf() method below to get the list of parameters and their purpose.
    """

    def _parse_conf(self, conf_dict):
        """ Utility method to get the matrix configuration from itself or from any other place.
            The returned configuration is normalized and parsed.
        """
        conf = {
            # TODO:
            # Add a visibility option that accept 'hidden', 'readonly', 'editable' (default) or 'inactive'

            # TODO: guess line_type, cell_type and resource_type based on their xxx_property parameter counterparts
            # XXX Haven't found a cleaner way to get my matrix parameters... Any help is welcome ! :)
            # Property name from which we get the lines composing the matrix
            'line_property': conf_dict.get('line_property', None),
            'line_type': conf_dict.get('line_type', None),
            'line_inverse_property': conf_dict.get('line_inverse_property', None),
            'line_removable_property': conf_dict.get('line_removable_property', None),

            # Get line tree definition
            'tree_definition': conf_dict.get('tree_definition', None),

            # Line rendering mode (can be 'float', 'boolean', 'increment' or 'selection')
            'default_line_rendering': conf_dict.get('default_line_rendering', 'float'),
            'line_rendering_dynamic_property': conf_dict.get('line_rendering_dynamic_property', None),
            # Widget customizations
            'increment_values': conf_dict.get('increment_values', None),

            # Property name from which we get the cells composing the matrix.
            # Cells are fetched from the lines as defined above.
            'cell_property': conf_dict.get('cell_property', None),
            'cell_type': conf_dict.get('cell_type', None),
            'cell_inverse_property': conf_dict.get('cell_inverse_property', None),
            'cell_value_property': conf_dict.get('cell_value_property', None),
            'cell_date_property': conf_dict.get('cell_date_property', None),
            'cell_visible_property': conf_dict.get('cell_visible_property', 'active'),
            'cell_readonly_property': conf_dict.get('cell_readonly_property', None),
            'cell_default_value': conf_dict.get('cell_default_value', 0.0),
            # Value range can be set per-cell
            # TODO: this parameter only works for selection field, make it work with all widgets
            'cell_value_range': conf_dict.get('cell_value_range', None),
            'cell_value_default_range': conf_dict.get('cell_value_default_range', None),

            # Property name of the relation field on which we'll call the date_range property
            'date_range_property': conf_dict.get('date_range_property', None),
            'visible_date_range_property': conf_dict.get('visible_date_range_property', None),
            'editable_date_range_property': conf_dict.get('editable_date_range_property', None),
            # Date range navigation parameters
            'navigation': conf_dict.get('navigation', False),          # Enable navigation slider
            'navigation_size': conf_dict.get('navigation_size', 10),   # Navigation slider size
            'navigation_start': conf_dict.get('navigation_start', 1),  # Start position

            # The format we use to display date labels
            'date_format': conf_dict.get('date_format', "%Y-%m-%d"),

            # The date of the column to highlight
            'highlight_date': conf_dict.get('highlight_date', 'today'),

            # Add read-only columns at the end of the matrix.
            # It needs a list of dictionnary like this:
            #    [{'label': "Productivity", 'line_property': 'productivity_index', 'position': 'left', 'hide_value': True},
            #     {'label': "Performance" , 'line_property': 'performance_index' , 'hide_tree_totals': True},
            #    ],
            'additional_columns': conf_dict.get('additional_columns', []),

            # Add read-only lines below the matrix
            'additional_line_property':  conf_dict.get('additional_line_property', None),

            # If set to true, hide the first column of the table.
            'hide_line_title': conf_dict.get('hide_line_title', False),

            # Do not allow the removal of lines
            'hide_remove_line_buttons': conf_dict.get('hide_remove_line_buttons', False),

            # Columns and row totals are optionnal
            'hide_column_totals': conf_dict.get('hide_column_totals', False),
            'hide_line_totals': conf_dict.get('hide_line_totals', False),

            # Set the threshold above which we set a column total in red. Set to None to desactivate the warning threshold.
            'column_totals_warning_threshold': conf_dict.get('column_totals_warning_threshold', None),

            # If set to True this option will hide all tree-level add-line selectors.
            'editable_tree': not conf_dict.get('non_editable_tree', False),

            # If set to True this option will hide all tree-level add-line selectors.
            'hide_tree': conf_dict.get('hide_tree', False),

            # Additional classes can be manually added
            'css_classes': conf_dict.get('css_classes', []),

            # Allow
            'custom_css': conf_dict.get('custom_css', None),
            'custom_js': conf_dict.get('custom_js', None),

            # Force the matrix in read only mode, even in editable mode
            'read_only': conf_dict.get('read_only', False),

            # Get the matrix title
            'title': conf_dict.get('title', "Lines"),

            # Get the matrix total label
            'total_label': conf_dict.get('total_label', "Total"),

            # Float rounding precision
            'precision': conf_dict.get('precision', 2),
        }

        # Check that all required parameters are there
        for p_name in ['line_property', 'line_type', 'line_inverse_property', 'tree_definition', 'cell_property', 'cell_type', 'cell_inverse_property', 'cell_value_property', 'cell_date_property']:
            if not conf.get(p_name, None):
                raise osv.except_osv('Error !', "%s parameter is missing." % p_name)

        # tree_definition list required at least one parameter
        if type(conf['tree_definition']) != type([]) or len(conf['tree_definition']) < 1:
            raise osv.except_osv('Error !', "tree_definition parameter must be a list with at least one element.")

        # Normalize parameters
        if conf['hide_tree']:
            conf['editable_tree'] = False

        # Dates should be rendered using our internal format
        if isinstance(conf['highlight_date'], datetime.date):
            conf['highlight_date'] = self._date_to_str(conf['highlight_date'])
        # TODO: convert other dates here too

        # Set consistent value ranges with sensible defaults
        default_range = [0, 0.5, 1.0]
        if not conf['increment_values']:
            conf['increment_values'] = default_range
        if not conf['cell_value_range']:
            conf['cell_value_range'] = default_range
        if not conf['cell_value_default_range']:
            # If the cell_value_range is not dynamic, its default couterpart should be the same
            if isinstance(conf['cell_value_range'], (str, unicode)):
                conf['cell_value_default_range'] = default_range
            else:
                conf['cell_value_default_range'] = conf['cell_value_range']

        return conf


    ## Utility methods

    def _date_to_str(self, date):
        return date.strftime('%Y%m%d')

    def _str_to_date(self, date):
        """ Transform string date to a proper date object
        """
        if not isinstance(date, datetime.date):
            date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        return date

    def _get_title_or_id(self, obj):
        """ Return the title of the object or a descriptive string"""
        return isinstance(obj, orm.browse_record) and getattr(obj, 'name_get')()[0][1] or obj or _("Untitled")

    def _get_translations(self, cr, conf, context):
        if conf.get('title'):
            conf['title'] = _(conf['title'])
        if conf.get('additional_columns'):
            for index, column in enumerate(conf['additional_columns']):
                conf['additional_columns'][index]['label'] = _(column['label'])
        if conf.get('total_label'):
            conf['total_label'] = _(conf['total_label'])
        return conf


    ## Native methods

    def __init__(self, *arg, **args):
        #arg = (args['line_type'], args['line_inverse_property'], "Matrix lines")
        #args.update({'type': 'one2many'})
        super(matrix, self).__init__(*arg, **args)
        # Parse and store matrix config
        self.matrix_conf = self._parse_conf(args)

    def _fnct_read(self, obj, cr, uid, ids, field_name, args, context=None):
        """ Dive into object lines and cells, and organize their info to let the matrix widget understand them
        """
        matrix_conf = deepcopy(self.matrix_conf)
        conf = self._get_translations(cr, matrix_conf, context)
        # Browse through all objects on which our matrix field is defined
        matrix_list = {}
        for base_object in obj.browse(cr, uid, ids, context):
            matrix_data = []

            # Evaluate dynamic matrix properties
            # Dynamic properties are those which value is a string instead of their native type
            # Of course this only works with properties which native type is not strings
            for flag_id in ['tree_definition', 'increment_values', 'cell_default_value', 'additional_columns', 'hide_line_title', 'hide_remove_line_buttons', 'hide_column_totals', 'hide_line_totals', 'column_totals_warning_threshold', 'editable_tree', 'hide_tree', 'css_classes', 'navigation', 'navigation_size', 'navigation_start', 'read_only', 'precision']:
                flag_value = conf[flag_id]
                if isinstance(flag_value, (str, unicode)):
                    conf[flag_id] = bool(_get_prop(base_object, flag_value))

            # Get our date ranges
            (date_range, visible_date_range, editable_date_range) = _get_date_range(base_object, conf['date_range_property'], conf['visible_date_range_property'], conf['editable_date_range_property'])

            # Get the list of all objects new rows of the matrix can be linked to
            # Keep the original order defined in matrix properties
            resource_value_list = []
            for level_def in conf['tree_definition']:
                res_def = level_def.copy()
                res_id = res_def.pop('line_property')
                res_type = res_def.pop('resource_type')
                p = base_object.pool.get(res_type)
                # Compute domain by merging its static and dynamic definition
                res_domain = res_def.pop('domain', []) + _get_prop(base_object, res_def.pop('dynamic_domain_property', None), [])
                # Build up the resource definition
                res_def.update({
                    'id': res_id,
                    'values': [(o.id, self._get_title_or_id(o)) for o in p.browse(cr, uid, p.search(cr, uid, res_domain, context=context), context)],
                    })
                resource_value_list.append(res_def)

            # Browse all lines that will compose the main part of the matrix
            lines = [(line, {'position': 'body'}) for line in _get_prop(base_object, conf['line_property'], [])]
            # Add bottom lines if provided
            if conf['additional_line_property']:
                lines += [(line, {'position': 'bottom', 'read_only': True}) for line in _get_prop(base_object, conf['additional_line_property'], [])]
            for (line, line_data) in lines:
                # Transfer some line data to the matrix widget
                line_data.update({
                    'id': line.id,
                    'name': self._get_title_or_id(line),
                    })

                # Get the type of the widget we'll use to display cell values
                line_widget = _get_prop(line, conf['line_rendering_dynamic_property'], conf['default_line_rendering'])

                # Force position of boolean widget to bottom
                if line_widget == 'boolean':
                    line_data.update({'position': 'bottom'})

                # If the line read_only flag is not already set, the default is False
                line_read_only = line_data.get('read_only', False)

                # Should we let the line be removable ?
                line_removable = True
                if line_read_only or conf['hide_remove_line_buttons']:
                    line_removable = False
                else:
                    line_removable = _get_prop(line, conf['line_removable_property'], True)

                line_data.update({
                    'widget': line_widget,
                    'read_only': line_read_only,
                    'removable': line_removable,
                    })

                # Get all resources of the line
                # Keep the order defined by matrix field's properties
                res_list = []
                for res in conf['tree_definition']:
                    res_id = res['line_property']
                    resource = _get_prop(line, res_id)
                    res_list.append({
                        'id': res_id,
                        'label': resource.id and self._get_title_or_id(resource) or line_data['name'],
                        'value': resource.id,
                        })
                line_data.update({'resources': res_list})

                # Get all cells of the line, indexed by their IDs
                cells = dict([(cell.id, cell) for cell in _get_prop(line, conf['cell_property'], [])])

                # Provide to the matrix a cell for each visible date in the range
                cells_data = {}
                for d in visible_date_range:
                    # Find a cell corresponding to the date in the date_range
                    cell = None
                    for (cell_id, cell) in cells.items():
                        cell_date = datetime.datetime.strptime(_get_prop(cell, conf['cell_date_property']), '%Y-%m-%d').date()
                        if cell_date == d:
                            break
                    # Get the current value and its allowed range
                    cell_value_range = conf['cell_value_range']
                    if isinstance(cell_value_range, (str, unicode)):
                        cell_value_range = _get_prop(cell, conf['cell_value_range'], conf['cell_value_default_range'])
                    cell_value = _get_prop(cell, conf['cell_value_property'], conf['cell_default_value'])
                    # Skip the cell to hide it if its visible property is True
                    visible_cell = _get_prop(cell, conf['cell_visible_property'], True)
                    if not visible_cell:
                        continue
                    # Pop the cell ID to mark it as consumed (this will prevent it to be automatticaly removed later)
                    if cell is not None:
                        cells.pop(cell_id)
                    # Set cell editability according its dynamic property.
                    read_only_cell = _get_prop(cell, conf['cell_readonly_property'], False)
                    if line_data.get('read_only', False):
                        # If the line is readonly then the cell is force to readonly.
                        read_only_cell = True
                    elif d not in editable_date_range:
                        # Column-level options override cells-level visibility properties
                        read_only_cell = True
                    # Pack all properties of the cell
                    cells_data[d.strftime('%Y%m%d')] = {
                        'value': cell_value,
                        'value_range': cell_value_range,
                        'read_only': read_only_cell,
                        }

                line_data.update({'cells_data': cells_data})
                # Remove all out of date, duplicate cells and inactive cells
                obj.pool.get(conf['cell_type']).unlink(cr, uid, cells.keys(), context)

                # Get data of additional columns
                for line_property in [c['line_property'] for c in conf['additional_columns'] if 'line_property' in c]:
                    if line_property in line_data['cells_data']:
                        raise osv.except_osv('Error !', "Additional line property %s conflicts with matrix column ID." % line_property)
                    v = _get_prop(line, line_property)
                    if type(v) != type(0.0):
                        v = float(v)
                    line_data['cells_data'].update({line_property: {
                        'value': v,
                        'read_only': True,
                        }})

                matrix_data.append(line_data)

            # Get default cells and their values for the template row.
            template_cells_data = {}
            for d in visible_date_range:
                # Set the editability of the cell
                read_only_cell = False
                if d not in editable_date_range:
                    read_only_cell = True
                template_cells_data[self._date_to_str(d)] = {
                    'value': conf['cell_default_value'],
                    'value_range': conf['cell_value_default_range'],
                    'read_only': read_only_cell,
                    }
            template_resources = [{
                    'id': res['line_property'],
                    'label': res['line_property'].replace('_', ' ').title(),
                    'value': 0,
                    } for res in conf['tree_definition']]
            # Add a row template at the end
            template_line_data = {
                'id': "template",
                'name': "Row template",
                'widget': conf['default_line_rendering'],
                'position': 'body',
                'read_only': False,
                'removable': not conf['hide_remove_line_buttons'],
                'cells_data': template_cells_data,
                'resources':template_resources,
                }
            matrix_data.append(template_line_data)

            # Pack all data required to render the matrix
            matrix_def = conf
            matrix_def.update({
                'matrix_data': matrix_data,
                'date_range': [self._date_to_str(d) for d in date_range], # Format our date range for our matrix # XXX Keep them as date objects ?
                'resource_value_list': resource_value_list,
                })

            matrix_list.update({base_object.id: matrix_def})
        return matrix_list



def parse_virtual_field_id(id_string):
    """ This utility method parse and validate virtual fields coming from the matrix
        Raise an exception if it tries to read a field that doesn't follow Matrix widget conventions.
        Return None for fields generated by the matrix but not usefull for data input.
        Valid matrix field names:
            * MATRIX_ID__res_XX_PROPERTY_ID
            * MATRIX_ID__res_newXX_PROPERTY_ID
            * MATRIX_ID__res_template_PROPERTY_ID  (ignored)
            * MATRIX_ID__res_dummyXX_PROPERTY_ID   (ignored)
            * MATRIX_ID__res_list_PROPERTY_ID      (ignored)
            * MATRIX_ID__line_removed
            * MATRIX_ID__line_XX
            * MATRIX_ID__line_newXX
            * MATRIX_ID__cell_XX_YYYYMMDD
            * MATRIX_ID__cell_newXX_YYYYMMDD
            * MATRIX_ID__cell_template_YYYYMMDD    (ignored)
        XXX Can we increase the readability of the validation rules embedded in this method by using reg exps ?
    """
    matrix_id = None
    # List reserved IDS that are used to separate the matrix ID prefix with the rest of the field ID
    RESERVED_SPLITBY_IDS = ['__cell_', '__res_', '__line_']
    # Separate the matrix ID and the field ID
    for reserved_id in RESERVED_SPLITBY_IDS:
        splits = id_string.split(reserved_id)
        if len(splits) < 2:
            continue
        # Two instances of a reserved ID was found,
        # or we already found a matrix ID but we can still split with another reserved ID.
        # In either case, that's bad !
        if len(splits) > 2 or matrix_id is not None:
            raise osv.except_osv('Error !', "Field %r is composed of more than one of the reserved strings %r." % (id_string, RESERVED_SPLITBY_IDS))
        matrix_id = splits[0]
    if not matrix_id:
        raise osv.except_osv('Error !', "Field %r has no matrix ID as a prefix." % id_string)
    f_id = id_string[len(matrix_id) + 2:]
    f_id_elements = f_id.split('_')

    # Check fields element lenght depending on their type
    if (f_id_elements[0] == 'cell' and len(f_id_elements) == 3) or \
       (f_id_elements[0] == 'res'  and len(f_id_elements) >= 3) or \
       (f_id_elements[0] == 'line' and len(f_id_elements) == 2):

        # Silently ignore some fields that are only used for interactivity by the matrix javascript
        if f_id.startswith('cell_template_') or \
           f_id.startswith('res_template_')  or \
           f_id.startswith('res_dummy')      or \
           f_id.startswith('res_list_'):
            return None

        # For ressource, the last parameter is the property ID of the line the resource belong to. Recompose it
        if f_id_elements[0] == 'res':
            f_id_elements = f_id_elements[:2] + ['_'.join(f_id_elements[2:])]
            # TODO: check that the PROPERTY_ID (aka f_id_elements[2]) exist as a column in the line data model

        # Check that the date is valid
        if f_id_elements[0] == 'cell':
            date_element = f_id_elements[2]
            try:
                datetime.datetime.strptime(date_element, '%Y%m%d').date()
            except ValueError:
                raise osv.except_osv('Error !', "Field %r don't have a valid %r date element." % (id_string, date_element))

        # Check that the second element is an integer. It is allowed to starts with the 'new' prefix.
        id_element = f_id_elements[1]
        if id_element.startswith('new'):
            id_element = id_element[3:]
        if (f_id_elements[0] == 'line' and id_element == 'removed') or \
           str(int(id_element)) == id_element:
            return [matrix_id] + f_id_elements

    # Requested field doesn't follow matrix convention
    raise osv.except_osv('Error !', "Field %r doesn't respect matrix widget conventions." % id_string)



def _get_matrix_fields(osv_instance):
    """ Utility method to get all matrix fields defined on the class the provided object is an instance of.
    """
    field_defs = osv_instance.__dict__['_columns']
    # The existence of a matrix_conf property indicate that the field is a matrix
    matrix_fields = dict([(f_id, f) for (f_id, f) in field_defs.items() if f.__dict__.get('matrix_conf', False)])
    if not len(matrix_fields):
        return None
    return matrix_fields



def _get_matrix_fields_conf(obj):
    return dict([(matrix_id, matrix.matrix_conf) for (matrix_id, matrix) in _get_matrix_fields(obj).items()])



def matrix_read_patch(func):
    """
    Let the matrix read the temporary fields that are not persistent in database.
    """

    @wraps(func)
    def read_matrix_virtual_fields(*arg, **kw):
        result = func(*arg, **kw)
        if len(arg) >= 5:
            (obj, cr, uid, ids, fields) = arg[:5]
        else:
            (obj, cr, uid, ids) = arg
            fields = obj._columns.keys()
        context = kw.get('context', None)
        if isinstance(ids, (int, long)):
            result = [result]
        updated_result = []
        for props in result:
            unread_fields = set(fields).difference(set(props.keys()))
            for (matrix_id, conf) in _get_matrix_fields_conf(obj).items():
                cell_pool = obj.pool.get(conf['cell_type'])
                line_pool = obj.pool.get(conf['line_type'])
                for f_id in unread_fields:
                    parsed_elements = parse_virtual_field_id(f_id)
                    if parsed_elements and parsed_elements[0] == matrix_id:
                        f_id_elements = parsed_elements[1:]
                        field_value = None
                        # Don't try to fetch current value of newly created cells and other write-only matrix-wide fields
                        WRITE_ONLY_FIELDS = [['line', 'removed']]
                        if f_id_elements not in WRITE_ONLY_FIELDS and not f_id_elements[1].startswith('new'):
                            line_id = int(f_id_elements[1])
                            if f_id_elements[0] == 'cell':
                                cell_date = datetime.datetime.strptime(f_id_elements[2], '%Y%m%d').date()
                                cell_id = cell_pool.search(cr, uid, [(conf['cell_date_property'], '=', cell_date.strftime('%Y-%m-%d')), (conf['cell_inverse_property'], '=', line_id)], limit=1, context=context)
                                if cell_id:
                                    cell = cell_pool.browse(cr, uid, cell_id, context)[0]
                                    field_value = getattr(cell, conf['cell_value_property'])
                            elif f_id_elements[0] == 'res':
                                if line_id:
                                    resource_property = f_id_elements[2]
                                    line = line_pool.browse(cr, uid, line_id, context)
                                    field_value = getattr(line, resource_property).id
                        props.update({f_id: field_value})
            updated_result.append(props)
        if isinstance(ids, (int, long)):
            updated_result = updated_result[0]
        return updated_result
    return read_matrix_virtual_fields



def matrix_write_patch(parse_only=False):
    """
        Method intended to use as a decorator on the default write() defined on
        objects having a matrix field.

        This decorator will parse and intercept virtual fields produced by a matrix
        widget, then write all values to their respective destination.

        The parse_only option let you skip all the automatic data saving performed
        there. This will provide the decorated write() method a structured
        dictionnary containing all editable matrix values and their new values, thus
        giving you the oportunity to write matrix content with your own strategy.
        This is generally useful to enhance performance.
    """

    def write_decorator(func):

        @wraps(func)
        def write_matrix_virtual_fields(*arg, **kw):
            # Extract parameters provided to the original method
            (obj, cr, uid, ids, vals) = arg[:5]
            context = kw.get('context', None)

            # We plan to update the original vals variable
            cleaned_vals = deepcopy(vals)

            # Fix common OpenERP inconsistency
            if isinstance(ids, (int, long)):
                ids = [ids]

            for report in obj.browse(cr, uid, ids, context):

                # Write one matrix at a time
                for (matrix_id, conf) in _get_matrix_fields_conf(obj).items():

                    removed_line_property_id = '_deleted_%s' % conf['line_property']
                    matrix_data = {
                        removed_line_property_id: [],
                        }

                    lines = {}
                    for (f_id, f_value) in vals.items():

                        # Ignore non-matrix fields
                        if not f_id.startswith('%s__' % matrix_id):
                            continue
                        # Remove consumed virtual matrix field
                        elif f_id in cleaned_vals:
                            del cleaned_vals[f_id]

                        # Parsing field ID will discard non-editable ones
                        parsed_elements = parse_virtual_field_id(f_id)
                        if parsed_elements and parsed_elements[0] == matrix_id:
                            f_id_elements = parsed_elements[1:]

                            # Catch removed lines field
                            if f_id_elements == ['line', 'removed']:
                                for line_id_elements in [parse_virtual_field_id(l_id.strip()) for l_id in f_value.split(',') if l_id.strip()]:
                                    if line_id_elements[0] == matrix_id and line_id_elements[1] == 'line' and not line_id_elements[2].startswith('new'):
                                        matrix_data[removed_line_property_id].append(int(line_id_elements[2]))

                            # We're reading a __cell_ or a __res_ type of field: regroup them to the line they belongs to
                            elif f_id_elements[0] in ['res', 'cell']:
                                line_id = f_id_elements[1]
                                line_data = lines.get(line_id, {})
                                line_data.update({f_id: f_value})
                                lines[line_id] = line_data

                    # No matrix data was edited on that matrix, so skip updating it
                    if not lines and not matrix_data[removed_line_property_id]:
                        continue

                    # Parse data of each line
                    for (line_id, line_data) in lines.items():
                        # Get line resources
                        line_resources = dict([(parse_virtual_field_id(f_id)[3], int(v)) for (f_id, v) in line_data.items() if f_id.startswith('%s__res_' % matrix_id)])
                        # Check all required resources are provided by the matrix
                        res_ids = set(line_resources.keys())
                        required_res_ids = set([prop['line_property'] for prop in conf['tree_definition']])
                        if res_ids != required_res_ids:
                            raise osv.except_osv('Error !', "Line %s resource mismatch: %r provided while we're expecting %r." % (line_id, res_ids, required_res_ids))
                        # Get line cells
                        line_cells = dict([(datetime.datetime.strptime(parse_virtual_field_id(f_id)[3], '%Y%m%d').date(), v) for (f_id, v) in line_data.items() if f_id.startswith('%s__cell_' % matrix_id)])
                        #
                        if line_id.startswith('new'):
                            line_id = None
                        else:
                            line_id = int(line_id)

                        # Parse and clean-up cells data
                        clean_cells = []
                        for (cell_date, cell_value) in line_cells.items():
                            # Transform the value to a float, if the user has entered nothing just use the default value
                            cell_value = ''.join([c for c in cell_value if c.isdigit() or c in ['-', '.', ',']]).replace(',', '.')
                            try:
                                cell_value = float(cell_value)
                            except ValueError:
                                cell_value = conf['cell_default_value']
                            clean_cells.append({
                                conf['cell_value_property']: cell_value,
                                conf['cell_date_property']: cell_date,
                                conf['cell_inverse_property']: line_id,
                                })

                        # Pack all cleaned matrix data in a comprehensive structure
                        line_properties = deepcopy(line_resources)
                        line_properties.update({
                            'id': line_id,
                            conf['cell_property']: clean_cells,
                            conf['line_inverse_property']: report.id,
                            })
                        matrix_data[conf['line_property']] = matrix_data.get(conf['line_property'], []) + [line_properties]

                    if parse_only:
                        # Inject a clean version of matrix data in the vals
                        matrix_widget_values = cleaned_vals.get(matrix_id, {})
                        matrix_widget_values.update({report.id: matrix_data})
                        cleaned_vals[matrix_id] = matrix_widget_values
                        # Skip the automatic content writing
                        continue

                    # Get our date ranges
                    (date_range, visible_date_range, editable_date_range) = _get_date_range(report, conf['date_range_property'], conf['visible_date_range_property'], conf['editable_date_range_property'])

                    # Write all our aggregated matrix data
                    for line_data in matrix_data.get(conf['line_property'], {}):
                        cells = line_data.pop(conf['cell_property'])
                        # Line has no idea so was created in the matrix
                        line_id = line_data.get('id', None)
                        if not line_id:
                            line_id = obj.pool.get(conf['line_type']).create(cr, uid, line_data, context)

                        # Save cells data
                        for cell_data in cells:
                            cell_data.update({'line_id': line_id})
                            cell_date = cell_data[conf['cell_date_property']]
                            # Search for an existing cell at the given date
                            cell_pool = obj.pool.get(conf['cell_type'])
                            cell_ids = cell_pool.search(cr, uid, [(conf['cell_date_property'], '=', cell_date.strftime('%Y-%m-%d')), (conf['cell_inverse_property'], '=', line_id)], context=context, limit=1)
                            # Cell doesn't exists, create it
                            if not cell_ids:
                                cell_pool.create(cr, uid, cell_data, context)
                            # Update or delete the cell
                            else:
                                cell_id = cell_ids[0]
                                # Compute the visibility state of the cell
                                cell = cell_pool.browse(cr, uid, cell_id, context)
                                visible_cell = _get_prop(cell, conf['cell_visible_property'], True)
                                if cell_date not in visible_date_range:
                                    visible_cell = False
                                # Update cell with our data or delete it if it's not visible
                                if not visible_cell:
                                    cell_pool.unlink(cr, uid, cell_id, context)
                                else:
                                    cell_pool.write(cr, uid, cell_id, cell_data, context)

                    if matrix_data[removed_line_property_id]:
                        report.pool.get(conf['line_type']).unlink(cr, uid, matrix_data[removed_line_property_id], context)

            # Replace the original vals variable by our cleaned version before passing it to the decorated write() method
            arg2 = list(arg)
            arg2[4] = cleaned_vals
            arg = tuple(arg2)

            # Call the method we decorate
            return func(*arg, **kw)

        return write_matrix_virtual_fields

    return write_decorator
