class DispatchError(BaseException):
    """
    Thrown when there is a logical failure in the dispatcher
    """


class CallRequestError(BaseException):
    """
    Thrown when the input call requests are invalid
    """