"""Response models for ``api_key``."""

from __future__ import annotations

from typing import List, Optional

from dialgem.types._base import DialgemModel


class ApiKeyDetails(DialgemModel):
    """What an API key was granted. The secret is never returned."""

    id: str
    name: str
    #: The start of the key, to recognise it by.
    prefix: str
    #: True when the key has no scopes and can do everything.
    full_access: bool
    #: For example ``["calls:write", "agents:read"]``; ``None`` for a full-access key.
    scopes: Optional[List[str]] = None
    #: IP addresses or CIDR ranges the key may be used from; ``None`` for anywhere.
    allowed_ips: Optional[List[str]] = None
    expires_at: Optional[str] = None
    expired: bool
    last_used_at: Optional[str] = None
    created_at: Optional[str] = None
    revoked_at: Optional[str] = None


class ApiKeyInfo(DialgemModel):
    auth: str
    #: Your organization's slug.
    organization: str
    role: str
    #: The key being used; ``None`` when the request was not made with an organization API key.
    key: Optional[ApiKeyDetails] = None
