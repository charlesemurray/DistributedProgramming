class Message:
    def __init__(self, from_channel=None, **kwargs):
        self._channel = from_channel
        if kwargs is not None:
            for key, value in kwargs.items():
                setattr(self, key, value)

    @property
    def carrier(self):
        return self._channel

    def sender(self):
        return self._channel.sender

    def receiver(self):
        return self._channel.receiver

if __name__ == "__main__":
    msg = Message(sender="A", receiver="B")
    assert msg.sender is "A"
    assert msg.receiver is "B"
