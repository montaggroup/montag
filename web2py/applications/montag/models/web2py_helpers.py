if False:
    from ide_fake import *


def read_form_field(form, fieldname):
    val = form.vars[fieldname]
    if isinstance(val, str):
        val = val.decode('utf-8')
    return val


def TOOLTIP(text):
    tip = A(IMG(_src=URL('static', 'images/clker/grey_question_mark.png')), _class="tooltip_trigger", _title=text)
    return tip


def create_error_page(message):
    response.view = 'error/error.html'
    return {'message': message}