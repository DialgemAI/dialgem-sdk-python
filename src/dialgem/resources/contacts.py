"""Contacts, imports and contact lists."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from typing_extensions import Unpack

from dialgem._base_client import RequestOptions, SyncAPIClient
from dialgem._pagination import SyncPage
from dialgem._resource import Resource, pid
from dialgem.types.contact import (
    Contact,
    ContactCallList,
    ContactCsvInspection,
    ContactDeleteResponse,
    ContactImport,
    ContactImportErrors,
    ContactImportList,
    ContactListDeleteResponse,
    ContactListMemberRemoveResponse,
    ContactListMembersAddResponse,
    ContactListRecord,
)
from dialgem.types.params import (
    ContactCreateParams,
    ContactImportCreateParams,
    ContactListCreateParams,
    ContactListUpdateParams,
    ContactUpdateParams,
)


class Contacts(Resource):
    """``dialgem.contacts``."""

    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.imports = ContactImports(client)

    def create(self, *, request_options: Optional[RequestOptions] = None, **body: Unpack[ContactCreateParams]) -> Contact:
        return self._client.post("/v1/contacts", body=body, cast_to=Contact, options=request_options)

    def list(
        self,
        *,
        q: Optional[str] = None,
        list_id: Optional[str] = None,
        limit: Optional[int] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> SyncPage[Contact]:
        """Iterate the result to walk every page."""
        return self._client.paginate(
            "/v1/contacts",
            query={"q": q, "list_id": list_id, "limit": limit},
            cast_to=Contact,
            items_key="contacts",
            cursor_param="cursor",
            next_key="next_cursor",
            options=request_options,
        )

    def retrieve_by_phone(
        self,
        phone: str,
        /,
        *,
        default_country: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Contact:
        """The contact with this phone number, matched as E.164.

        ``retrieve_by_phone("(212) 220-0001", default_country="US")`` finds ``+12122200001``.
        Raises ``NotFoundError`` if you have no such contact and ``UnprocessableEntityError`` if the
        text is not a phone number.
        """
        return self._client.get(
            f"/v1/contacts/by-phone/{pid(phone)}",
            query={"default_country": default_country},
            cast_to=Contact,
            options=request_options,
        )

    def retrieve(self, contact_id: str, /, *, request_options: Optional[RequestOptions] = None) -> Contact:
        return self._client.get(f"/v1/contacts/{pid(contact_id)}", cast_to=Contact, options=request_options)

    def update(
        self, contact_id: str, /, *, request_options: Optional[RequestOptions] = None, **body: Unpack[ContactUpdateParams]
    ) -> Contact:
        return self._client.patch(
            f"/v1/contacts/{pid(contact_id)}", body=body, cast_to=Contact, options=request_options
        )

    def delete(self, contact_id: str, /, *, request_options: Optional[RequestOptions] = None) -> ContactDeleteResponse:
        return self._client.delete(
            f"/v1/contacts/{pid(contact_id)}", cast_to=ContactDeleteResponse, options=request_options
        )

    def calls(
        self,
        contact_id: str,
        /,
        *,
        limit: Optional[int] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> ContactCallList:
        return self._client.get(
            f"/v1/contacts/{pid(contact_id)}/calls",
            query={"limit": limit},
            cast_to=ContactCallList,
            options=request_options,
        )



class ContactImports(Resource):
    """``dialgem.contacts.imports``: bulk CSV imports (inspect, create, then commit)."""

    def inspect(self, csv: str, /, *, request_options: Optional[RequestOptions] = None) -> ContactCsvInspection:
        return self._client.post(
            "/v1/contacts/imports/inspect", body={"csv": csv}, cast_to=ContactCsvInspection, options=request_options
        )

    def create(
        self, *, request_options: Optional[RequestOptions] = None, **body: Unpack[ContactImportCreateParams]
    ) -> ContactImport:
        return self._client.post("/v1/contacts/imports", body=body, cast_to=ContactImport, options=request_options)

    def list(self, *, request_options: Optional[RequestOptions] = None) -> ContactImportList:
        return self._client.get("/v1/contacts/imports", cast_to=ContactImportList, options=request_options)

    def retrieve(self, import_id: str, /, *, request_options: Optional[RequestOptions] = None) -> ContactImport:
        return self._client.get(f"/v1/contacts/imports/{pid(import_id)}", cast_to=ContactImport, options=request_options)

    def errors(
        self,
        import_id: str,
        /,
        *,
        limit: Optional[int] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> ContactImportErrors:
        return self._client.get(
            f"/v1/contacts/imports/{pid(import_id)}/errors",
            query={"limit": limit},
            cast_to=ContactImportErrors,
            options=request_options,
        )

    def commit(self, import_id: str, /, *, request_options: Optional[RequestOptions] = None) -> ContactImport:
        return self._client.post(
            f"/v1/contacts/imports/{pid(import_id)}/commit", cast_to=ContactImport, options=request_options
        )

    def cancel(self, import_id: str, /, *, request_options: Optional[RequestOptions] = None) -> ContactImport:
        return self._client.delete(
            f"/v1/contacts/imports/{pid(import_id)}", cast_to=ContactImport, options=request_options
        )


class ContactLists(Resource):
    """``dialgem.contact_lists``."""

    def list(self, *, request_options: Optional[RequestOptions] = None) -> Dict[str, Any]:
        """``{"lists": [...]}``."""
        return self._client.get("/v1/contact-lists", cast_to=dict, options=request_options)

    def create(
        self, *, request_options: Optional[RequestOptions] = None, **body: Unpack[ContactListCreateParams]
    ) -> ContactListRecord:
        return self._client.post("/v1/contact-lists", body=body, cast_to=ContactListRecord, options=request_options)

    def retrieve(self, list_id: str, /, *, request_options: Optional[RequestOptions] = None) -> ContactListRecord:
        return self._client.get(f"/v1/contact-lists/{pid(list_id)}", cast_to=ContactListRecord, options=request_options)

    def update(
        self, list_id: str, /, *, request_options: Optional[RequestOptions] = None, **body: Unpack[ContactListUpdateParams]
    ) -> ContactListRecord:
        return self._client.patch(
            f"/v1/contact-lists/{pid(list_id)}", body=body, cast_to=ContactListRecord, options=request_options
        )

    def delete(self, list_id: str, /, *, request_options: Optional[RequestOptions] = None) -> ContactListDeleteResponse:
        return self._client.delete(
            f"/v1/contact-lists/{pid(list_id)}", cast_to=ContactListDeleteResponse, options=request_options
        )

    def add_contacts(
        self, list_id: str, contact_ids: List[str], /, *, request_options: Optional[RequestOptions] = None
    ) -> ContactListMembersAddResponse:
        return self._client.post(
            f"/v1/contact-lists/{pid(list_id)}/members",
            body={"contact_ids": contact_ids},
            cast_to=ContactListMembersAddResponse,
            options=request_options,
        )

    def remove_contact(
        self, list_id: str, contact_id: str, /, *, request_options: Optional[RequestOptions] = None
    ) -> ContactListMemberRemoveResponse:
        return self._client.delete(
            f"/v1/contact-lists/{pid(list_id)}/members/{pid(contact_id)}",
            cast_to=ContactListMemberRemoveResponse,
            options=request_options,
        )
