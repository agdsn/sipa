from flask_flatpages import FlatPages
#workaround found here http://stackoverflow.com/questions/11020170/using-flask-extensions-in-flask-blueprints
# because we want to use flatpages within blueprints

class CustomFlatPages(FlatPages):


    def __init__(self):
        FlatPages.__init__(self)
        self.categories = []
    
    def init_app(self, app):
        super(CustomFlatPages, self).init_app(app)
        #(TODO) PLEASE NOT SO MANY fors and if
        # that all bad karma
        # but do you know that it is only eecuted at init
        # ohh cool
        for p in self:
            print p
            found = False
            if (p.path.endswith('__init__')):
                for c in self.categories:
                    if c['link'] == p.path.split('/')[0]:
                        found = True
                if not found:
                    self.categories.append({'link': p.path.split('/')[0],'category': p})
        for p in self:
            p.meta['category_link'] = p.path.split('/')[0]
        

pages = CustomFlatPages()
