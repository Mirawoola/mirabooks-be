"""
Supabase Database Client — using httpx directly.

The supabase-py library is incompatible with Python 3.14 (ForwardRef issue).
So we use httpx to talk to the Supabase REST API (PostgREST) directly.

This module provides a SupabaseClient class that mimics the query-builder
pattern of supabase-py, so the repositories don't need major changes.
"""

import httpx
from app.config import settings


class QueryBuilder:
    """
    Fluent query builder for the Supabase PostgREST API.

    Usage mirrors supabase-py:
        client.table("books").select("*").eq("slug", "dune").execute()
    """

    def __init__(self, base_url: str, headers: dict, table_name: str):
        self._base_url = f"{base_url}/rest/v1/{table_name}"
        self._headers = headers.copy()
        self._select_cols = "*"
        self._filters = []
        self._order_col = None
        self._order_desc = False
        self._limit_val = None
        self._offset_val = None
        self._range_start = None
        self._range_end = None
        self._is_single = False
        self._count_mode = None  # "exact", "planned", "estimated"
        self._method = "GET"
        self._body = None

    def select(self, columns: str = "*", count: str | None = None):
        self._select_cols = columns
        self._count_mode = count
        return self

    def eq(self, column: str, value):
        self._filters.append(f"{column}=eq.{value}")
        return self

    def neq(self, column: str, value):
        self._filters.append(f"{column}=neq.{value}")
        return self

    def gt(self, column: str, value):
        self._filters.append(f"{column}=gt.{value}")
        return self

    def gte(self, column: str, value):
        self._filters.append(f"{column}=gte.{value}")
        return self

    def lt(self, column: str, value):
        self._filters.append(f"{column}=lt.{value}")
        return self

    def lte(self, column: str, value):
        self._filters.append(f"{column}=lte.{value}")
        return self

    def or_(self, filters: str):
        self._filters.append(f"or=({filters})")
        return self

    def order(self, column: str, ascending: bool = True, desc: bool = False):
        self._order_col = column
        self._order_desc = desc or (not ascending)
        return self

    def limit(self, count: int):
        self._limit_val = count
        return self

    def range(self, start: int, end: int):
        self._range_start = start
        self._range_end = end
        return self

    def single(self):
        self._is_single = True
        self._headers["Accept"] = "application/vnd.pgrst.object+json"
        return self

    def maybe_single(self):
        """Like single(), but returns None if no rows are found instead of an error."""
        self._is_single = True
        self._headers["Accept"] = "application/vnd.pgrst.object+json"
        return self

    def insert(self, data):
        self._method = "POST"
        self._body = data if isinstance(data, list) else [data]
        self._headers["Prefer"] = "return=representation"
        return self

    def update(self, data):
        self._method = "PATCH"
        self._body = data
        self._headers["Prefer"] = "return=representation"
        return self

    def delete(self):
        self._method = "DELETE"
        self._headers["Prefer"] = "return=representation"
        return self

    def execute(self):
        """Execute the built query and return a response object."""
        url = self._base_url
        params = {}

        # Select
        params["select"] = self._select_cols

        # Filters
        for f in self._filters:
            key, _, value = f.partition("=")
            # Handle 'or' specially
            if key == "or":
                params["or"] = value
            else:
                params[key] = value

        # Order
        if self._order_col:
            direction = "desc" if self._order_desc else "asc"
            params["order"] = f"{self._order_col}.{direction}"

        # Limit
        if self._limit_val is not None:
            params["limit"] = str(self._limit_val)

        # Range header
        headers = self._headers.copy()
        if self._range_start is not None and self._range_end is not None:
            headers["Range"] = f"{self._range_start}-{self._range_end}"
            headers["Range-Unit"] = "items"

        # Count mode
        if self._count_mode:
            prefer = headers.get("Prefer", "")
            count_prefer = f"count={self._count_mode}"
            headers["Prefer"] = f"{prefer}, {count_prefer}".strip(", ")

        try:
            if self._method == "GET":
                resp = httpx.get(url, params=params, headers=headers, timeout=15.0)
            elif self._method == "POST":
                resp = httpx.post(url, params=params, headers=headers, json=self._body, timeout=15.0)
            elif self._method == "PATCH":
                resp = httpx.patch(url, params=params, headers=headers, json=self._body, timeout=15.0)
            elif self._method == "DELETE":
                resp = httpx.delete(url, params=params, headers=headers, timeout=15.0)
            else:
                raise ValueError(f"Unknown method: {self._method}")

            return SupabaseResponse(resp, is_single=self._is_single)
        except httpx.HTTPError as e:
            return SupabaseResponse(None, error=str(e))


class SupabaseResponse:
    """Mimics the response object from supabase-py."""

    def __init__(self, response: httpx.Response | None = None, is_single: bool = False, error: str | None = None):
        self._response = response
        self._is_single = is_single
        self._error = error

    @property
    def data(self):
        if self._error or self._response is None:
            return [] if not self._is_single else None
        if self._response.status_code >= 400:
            return [] if not self._is_single else None
        try:
            result = self._response.json()
            return result
        except Exception:
            return [] if not self._is_single else None

    @property
    def count(self):
        if self._response is None:
            return 0
        content_range = self._response.headers.get("content-range", "")
        if "/" in content_range:
            total = content_range.split("/")[-1]
            if total != "*":
                return int(total)
        return None


class SupabaseClient:
    """
    Lightweight Supabase REST API client using httpx.

    Drop-in replacement for supabase.create_client() that works on Python 3.14.
    """

    def __init__(self, url: str, key: str):
        self.url = url.rstrip("/")
        self.key = key
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    def table(self, name: str) -> QueryBuilder:
        return QueryBuilder(self.url, self.headers, name)


# Singleton instance
supabase = SupabaseClient(settings.supabase_url, settings.supabase_service_role_key)


def get_supabase() -> SupabaseClient:
    """Dependency injection helper for FastAPI routes."""
    return supabase
