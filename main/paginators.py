from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class ProfilePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit' # Allows client to set size: ?limit=50
    max_page_size = 50

    def get_paginated_response(self, data):
        return Response({
            'status': 'success',
            'page': self.page.number,
            'limit': self.page.paginator.per_page,
            'total': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'links': {
                'self': self.request.build_absolute_uri(),
                'prev': self.get_previous_link(),
                'next': self.get_next_link(),
            },
            'data': data
        })
        