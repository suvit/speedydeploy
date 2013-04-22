
from ..base import ObjectWithCommands

class Provider(ObjectWithCommands):
    shared = False

    namespace = 'provider'

    def __init__(self):
        self.can_adduser = not self.shared
        self.can_addpackages = not self.shared
