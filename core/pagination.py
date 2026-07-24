from rest_framework.pagination import PageNumberPagination
from core.response import ApiResponse


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return ApiResponse.success_paginated(
            results=data,
            pagination_info={
                "count": self.page.paginator.count,
                "page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "total_pages": self.page.paginator.num_pages,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
            },
            message="Liste récupérée avec succès"
        )
