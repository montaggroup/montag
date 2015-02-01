def read_form_field(form, fieldname):
    val = form.vars[fieldname]
    if isinstance(val, str):
        val = val.decode('utf-8')
    return val
