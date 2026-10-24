class ProviderUnavailable(RuntimeError):
    status = "requires_configuration"
    def __init__(self, message, capability="unknown"):
        super().__init__(message)
        self.capability = capability

class UnsupportedCapability(ProviderUnavailable):
    status = "unavailable"
