

# ======================================================================================================================================================



# ----------------------------

spouse = 0.0
children = 0.0
first_payment = 0.0
first_payment_tax = 0.0
monthly_salary = (brutoUSD * 2)

range_min = 799000.00
range_max = 1199000.00
first_day = payslip.env["hr.payslip"].is_month_first_day(payslip.date_from)

if not first_day:
    spouse = 2240.00
    children = 1500.00
    first_payment = float(payslip.env["hr.payslip"].get_first_payment(payslip.date_from, employee.id))
    first_payment_tax = float(payslip.env["hr.payslip"].get_first_payment_tax(payslip.date_from, employee.id))
    monthly_salary = first_payment + brutoUSD - (employee.retirement_plan / tipo_cambio)

result = monthly_salary > range_min  

# --------------------------------------------------------------

wife_amount  = 0.0
if employee.marital_exoneration and employee.marital == "married" :
    wife_amount =  spouse

children_amount=0.0
if employee.children_exoneration:
    children_amount = employee.children * children

tax_amount = 0.0

if monthly_salary > range_max:
    tax_amount = ((range_max - range_min ) * 0.1) + ((monthly_salary - range_max) * 0.15) - wife_amount - children_amount - first_payment_tax 
else:
    tax_amount = ((monthly_salary - range_min) * 0.1) - wife_amount - children_amount - first_payment_tax

if ((first_day == True) and (tax_amount > 0)):
    tax_amount = tax_amount / 2

result = tax_amount

# ======================================================================================================================================================


tipo_cambio = contract.journal_id.currency_id.rate_ids[0].rate
if payslip.date:
	index = 0
	while payslip.date < contract.journal_id.currency_id.rate_ids[index].name:
		index += 1

	tipo_cambio = contract.journal_id.currency_id.rate_ids[index].rate

result = (contract.wage - 0) / 2 / tipo_cambio


# --------------------------------------------------------------

ir_values = payslip.env['ir.values']
field_value = ir_values.get_default('base.config.settings', 'abcde')

range_max = float(payslip.env["ir.config_parameter"].get_param("rent_tax_second_value", False))
first_day = payslip.env["hr.payslip"].is_month_first_day(range_min)
