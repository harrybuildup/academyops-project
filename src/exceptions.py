class LeadError(Exception):
    pass


class LeadNotFound(LeadError):
    pass


class DuplicatePhoneError(LeadError):
    pass

