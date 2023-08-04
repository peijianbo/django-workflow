from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    def __init__(self):
        super(CustomPageNumberPagination, self).__init__()
        self.page_size_query_param = 'page_size'
        self.max_page_size = 100