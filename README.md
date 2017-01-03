Smile Matrix Widget
===================

This is a prototype of a matrix widget for OpenERP 6.0.x web client.

![Screenshot of the Smile matrix widget in action](https://github.com/kdeldycke/smile_openerp_matrix_widget/raw/master/screenshots/ascii-art-matrix.png)

This project is sponsored by [Smile](https://www.smile.fr).


Features
--------

  * Per-column and per-cell editability and visibility
  * Two types of cell widgets: float input fields and float increment buttons
  * Hierarchical grouping of lines within the matrix body
  * Lines can be added and deleted in edit mode
  * Dynamic per-column and per-line sums in edit mode
  * Date-based columns

You should also [browse the bug tracker](https://github.com/kdeldycke/smile_openerp_matrix_widget/issues): it's the best place to get an idea of which features are missing or are not implemented yet.


Requirements
------------

  * OpenERP 6.0.x
  * Chromium >= 1.5
  * Firefox >= 8.0
  * Internet Explorer >= 9.0

If you've successfully tested this widget with other or older browsers, please notify us.


Screenshots
-----------

Here are some example use of the matrix:

![](https://github.com/kdeldycke/smile_openerp_matrix_widget/raw/master/screenshots/1-level-readonly-matrix.png)

![](https://github.com/kdeldycke/smile_openerp_matrix_widget/raw/master/screenshots/1-level-editable-increment-matrix.png)

![](https://github.com/kdeldycke/smile_openerp_matrix_widget/raw/master/screenshots/2-level-readonly-additional-lines-matrix.png)

![](https://github.com/kdeldycke/smile_openerp_matrix_widget/raw/master/screenshots/2-level-editable-additional-lines-matrix.png)


FAQ
---

**Why is this module not in [Smile's canonical repository for OpenERP contibutions](https://code.launchpad.net/smile-openerp) ?**

This code started its life in Smile's internal Subversion repository and was [migrated to Git](https://kevin.deldycke.com/2011/08/how-open-source-an-internal-corporate-project-webping/) to not loose its commit history, which would have been the case if the project was to be pushed to Bazaar.


Author
------

 * [Kevin Deldycke](https://kevin.deldycke.com) - `kevin@deldycke.com`


Contributors
------------

 * [Xavier Fernandez](https://twitter.com/#!/xavierfernandez)
 * Nicolas Petit
 * Corentin Pouhet-Brunerie
 * Sylvain Bannier
 * Nicolas Clément


License
-------

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.


Changelog
---------

* **0.9.dev** (unreleased)
  * Introduce a new `today` keyword for the `highlight_date` parameter
  * Fix today's column default highlighting by recomputing dates every time a matrix is displayed
  * Auto-remove trailing zeros when adding floats
  * Do not display intermediate-level totals of empty columns
  * Strip spaces and line returns between cell's definition to fix IE9 misalignment

* **0.8** (2012-08-28)
  * Update intermediate-level totals on cell value change
  * Add a `precision` parameter to force float rounding
  * Fix initialization of matrix in tabs
  * Rename `date_range_navigation` parameter to `navigation`

* **0.7** (2012-04-25)
  * Add partial totals of hidden columns below navigation buttons
  * Update naming conventions from `*_active_*` to `*_visible_*`
  * Rename `navigation_width` parameter to `navigation_size`

* **0.6** (2012-04-17)
  * Add a `navigation_width` and `navigation_start` parameter
  * Add a start, center and end navigation buttons
  * Move the line deletion button to the far left of each line
  * Allow styling of the current date
  * Fix read-only rendering of date range navigation in multi-level matrix

* **0.5** (2012-04-03)
  * Add a new selection widget type
  * Add a new dynamic `cell_value_range` parameter for the selection widget
  * Allow additional columns to be positionned to the right or the left side of the matrix body
  * Rename widget type to line rendering mode
  * Add blank-line / spacer and a header line rendering mode

* **0.4** (2012-01-27)
  * Per-line dynamic removable property
  * Update internal field naming convention to lower the risk of collision in usual usage
  * Restrict boolean widget lines to the bottom of the matrix for now
  * Add date range column navigation
  * Allow custom CSS and Javascript to be injected in the matrix

* **0.3** (2011-12-23)
  * Only remove lines when they are explicitely deleted by the user
  * Fix JavaScript grand total and column total on line deletion

* **0.2** (2011-12-15)
  * First open-source public release

* **0.1** (2011-11-21)
  * First internal use in a customer project

* **0.0** (2011-08-05)
  * First commit
