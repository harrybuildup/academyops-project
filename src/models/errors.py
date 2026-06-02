class LeadError(Exception):
    pass


class LeadNotFoundError(LeadError):
    pass


class DuplicatePhoneError(LeadError):
    pass

