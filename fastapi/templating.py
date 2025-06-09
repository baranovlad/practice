class Jinja2Templates:
    def __init__(self, directory):
        self.directory = directory
    def TemplateResponse(self, name, context, status_code=200):
        return type("TemplateResponse", (), {"status_code": status_code, "name": name, "context": context})

