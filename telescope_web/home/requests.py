from django.contrib import messages

def getvalue(request, name, val_type):
    """
        Converts the value of the html form element 'name' into 'val_type'
    """
    try:
        return val_type(request.GET.get(name))
    except:
        return None

def return_message(request, tag, message):
    if tag == 'success':
        messages.success(request, message)
    elif tag == 'error':
        messages.error(request, message)
    else:
        messages.info(request, message)
