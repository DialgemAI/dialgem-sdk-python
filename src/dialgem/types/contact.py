"""Response models for this resource. Bootstrapped from the TypeScript SDK; owned by hand now."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from dialgem.types._base import DialgemModel, Number


class Contact(DialgemModel):
    id: str
    #: E.164, for example `+14155552671`. The number is the contact's identity: one contact per number.
    phone: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    #: IANA zone name, for example `America/Chicago`.
    timezone: Optional[str]
    #: Your own fields, as text.
    attributes: Dict[str, str]
    source: Any
    #: Whether the number is on your organization's do-not-call list. Read from that list
    #: each time, never stored on the contact.
    do_not_call: bool
    #: ISO 8601, no timezone suffix (UTC).
    created_at: Optional[str]
    updated_at: Optional[str]
    #: Present on `create`, `retrieve` and `update`.
    lists: Optional[List[Dict[str, Any]]] = None
    #: Present on `retrieve`: calls to or from the number.
    call_count: Optional[Number] = None
    last_call_at: Optional[str] = None


class ContactDeleteResponse(DialgemModel):
    id: str
    deleted: bool


class ContactCallSummary(DialgemModel):
    id: str
    agent_id: Optional[str]
    direction: Any
    status: str
    started_at: Optional[str]
    ended_at: Optional[str]
    duration_s: Optional[Number]
    disconnection_reason: Optional[str]
    #: The call's analysis summary, when it has one. No transcript.
    summary: Optional[str]


class ContactCallList(DialgemModel):
    total: Number
    calls: List[ContactCallSummary]


class ContactListRecord(DialgemModel):
    id: str
    name: str
    description: Optional[str]
    member_count: Number
    created_at: Optional[str]
    updated_at: Optional[str]


class ContactListDeleteResponse(DialgemModel):
    id: str
    deleted: bool


class ContactListMembersAddResponse(DialgemModel):
    id: str
    #: How many were not already in the list.
    added: Number
    member_count: Number


class ContactListMemberRemoveResponse(DialgemModel):
    id: str
    member_count: Number


ContactImportStatus = Union[Literal['queued', 'running'], str]


class ContactImport(DialgemModel):
    """A preview nobody confirmed within a day."""

    id: str
    status: ContactImportStatus
    dry_run: bool
    filename: Optional[str]
    total_rows: Number
    #: For a preview, what would be created.
    created: Number
    updated: Number
    #: Rows repeating an earlier number in the file, or existing contacts when `on_duplicate` is `skip`.
    skipped: Number
    #: Rows that could not be used. See `imports.errors`.
    errors: Number
    #: More rows were rejected than the report keeps (5,000).
    errors_truncated: bool
    failure: Optional[str]
    mapping: Optional[Dict[str, str]]
    attribute_columns: Optional[List[str]]
    default_country: Optional[str]
    on_duplicate: Optional[Union[Literal['update', 'skip'], str]]
    list_id: Optional[str]
    created_at: Optional[str]
    started_at: Optional[str]
    finished_at: Optional[str]


class ContactImportList(DialgemModel):
    imports: List[ContactImport]


class ContactCsvInspection(DialgemModel):
    headers: List[str]
    row_count: Number
    #: The guessed field-to-column mapping: `phone`, `first_name`, `last_name`, `full_name`, `email`, `timezone`.
    mapping: Dict[str, str]
    #: Columns left over, offered as your own fields.
    attribute_columns: List[str]
    sample: List[Dict[str, Optional[str]]]


class ContactImportErrorRow(DialgemModel):
    #: The line of the file, counting the header as line 1.
    row: Number
    error: str
    values: Dict[str, str]


class ContactImportErrors(DialgemModel):
    errors: List[ContactImportErrorRow]
    total: Number
    truncated: bool
