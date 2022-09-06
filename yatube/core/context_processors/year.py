from datetime import datetime


def year(request):
    d = int(datetime.now().strftime("%Y"))
    return {
        'year': d,
    }
