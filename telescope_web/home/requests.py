from django.contrib import messages

def getvalue_get(request, name, val_type):
    """
        Converts the value of the html form element 'name' into 'val_type'
    """
    try:
        return val_type(request.GET.get(name))
    except:
        return None

def getvalue_post(request, name, val_type):
    """
        Converts the value of the html form element 'name' into 'val_type'
    """
    try:
        return val_type(request.POST.get(name))
    except:
        return None


def return_message(request, tag, message, extra_tags=''):
    if tag == 'success':
        messages.success(request, message, extra_tags=extra_tags)
    elif tag == 'error':
        messages.error(request, message, extra_tags=extra_tags)
    elif tag =='warning':
        messages.warning(request, message, extra_tags=extra_tags)
    else:
        messages.info(request, message, extra_tags=extra_tags)
