from django.http import HttpResponse

def root_view(request):
    http = """
    <!doctype html>
    <html>
    <head>
    <title>Meejing API</title>
    </head>
    <body>
    <h1>Welcome to the Meejing API!</h1>
    <h2>Urls:</h2><br>
    <ul>
        <li><a href="admin/">admin/</li>
        <li><a href="api/docs/">api docs</a></li>
        <li><a href="api/docs/redoc/">api docs(redoc)</a></li>
        <li><a href="api/schema/">api schema/</a></li>
    </ul>
    </body></html>
    """
    return HttpResponse(http)