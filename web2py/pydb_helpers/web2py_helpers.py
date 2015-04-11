if False:
    from web2py.applications.montag.models.ide_fake import *

def read_form_field(form, fieldname):
    val = form.vars[fieldname]
    if isinstance(val, str):
        val = val.decode('utf-8')
    return val


def create_error_page(message):
    response.view = 'error/error.html'
    return {'message': message}