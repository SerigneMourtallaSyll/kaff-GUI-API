"""Pagination par défaut — réponse stable que le mobile React Query peut consommer."""

from __future__ import annotations

from typing import Any

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class DefaultPageNumberPagination(PageNumberPagination):
    """
    Pagination standard avec page_size paramétrable côté client (max 100).

    Format de réponse:
        {
          "count": 142,
          "page": 2,
          "page_size": 20,
          "total_pages": 8,
          "next": "...",
          "previous": "...",
          "results": [...]
        }
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"

    def get_paginated_response(self, data: Any) -> Response:
        # paginate_queryset() est toujours appelé avant — page et request sont garantis non-null.
        assert self.page is not None, "get_paginated_response called before paginate_queryset"
        assert self.request is not None, "get_paginated_response called outside request context"
        return Response(
            {
                "count": self.page.paginator.count,
                "page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "total_pages": self.page.paginator.num_pages,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )
