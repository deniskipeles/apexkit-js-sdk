class ApexError(Exception):
    def __init__(self, message: str, status: int = 500, code: str = None, details: any = None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.details = details

    def __str__(self):
        return f"ApexError(status={self.status}, code={self.code}, message={self.message})"
