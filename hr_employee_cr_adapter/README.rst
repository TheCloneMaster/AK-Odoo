.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Employee Costa Rica Adapter
===========================

This module includes these functionalities:
1- Automated task to update exchange rate from "Banco Central de Costa Rica" 
2- Automated task to add a vacation day every month for each employee.

This module adds the following to employees :

* hr_employee_initial_date
* hr_employee_marital_exoneration
* hr_employee_children_exoneration

This module adds the following to currency rate:

* Modify res_currency_rate_rate to a decimal presicion that works with CRC -> USD
* res_currency_rate_rate_2
* res_currency_rate_original_rate
* res_currency_rate_original_rate_2
* _cron_update()


Installation
============

To install this module, you need to:

1.  Clone the branch 11.0 of the repository https://github.com/akurey/odoo.git
2.  Add the path to this repository in your configuration (addons-path)
3.  Update the module list
4.  Go to menu *Setting -> Modules -> Local Modules*
5.  Search For *Employee Costa Rica Adapter*
6.  Install the module

Usage
=====



Bug Tracker
===========

Bugs are tracked on `GitHub Issues <hhttps://github.com/akurey/odoo/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback.


Credits
=======

Contributors
------------

* Carlos Wong <cwong@akurey.com>
* AKUREY S.A. <odoo@akurey.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by Akurey.

Akurey, is a private company whose mission is to support 
the collaborative development of Odoo features and
promote its widespread use.