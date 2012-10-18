

class Provider(object):
    shared = False

    def __init__(self):
        self.can_adduser = not self.shared
        self.can_addpackages = not self.shared
