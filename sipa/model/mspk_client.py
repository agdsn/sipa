class MPSKClientEntry:
    mac: str
    name: str
    id: int

    def __init__(self, mac: str, name: str, id: int):
        self.mac = mac
        self.name = name
        self.id = id
