class Protocol:
    header = ""
    payload = ""

    def __init__(self, header, payload):
        self.header = header
        self.payload = payload
