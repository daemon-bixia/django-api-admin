class APIAdminErrorViewMixin:
    """
    Mixin to override the exception handler dynamically for specific views.
    """

    def get_exception_handler(self):
        return self.admin_site.get_exception_handler()
