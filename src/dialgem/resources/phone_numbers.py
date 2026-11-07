"""Phone numbers."""

from __future__ import annotations

from typing import List, Optional

from typing_extensions import Unpack

from dialgem._base_client import RequestOptions
from dialgem._resource import Resource, pid
from dialgem.types.params import (
    PhoneNumberAssignParams,
    PhoneNumberBuyParams,
    PhoneNumberCreateParams,
    PhoneNumberUpdateParams,
)
from dialgem.types.phone_number import (
    AvailablePhoneNumbers,
    InboundWebhookTestResult,
    PhoneNumber,
    PurchasedPhoneNumber,
)


class PhoneNumbers(Resource):
    """``dialgem.phone_numbers``."""

    def create(
        self, *, request_options: Optional[RequestOptions] = None, **body: Unpack[PhoneNumberCreateParams]
    ) -> PhoneNumber:
        return self._client.post("/v1/phone-numbers", body=body, cast_to=PhoneNumber, options=request_options)

    def search(
        self,
        *,
        country: Optional[str] = None,
        type: Optional[str] = None,
        area_code: Optional[str] = None,
        contains: Optional[str] = None,
        limit: Optional[int] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> AvailablePhoneNumbers:
        """Numbers that can be bought, with the monthly price.

        ``type`` is ``"local"`` (default) or ``"toll_free"``; ``area_code`` is three digits. Raises
        ``NotFoundError`` (``number_purchase_disabled``) when the deployment has not switched buying on.
        """
        query = {"country": country, "type": type, "area_code": area_code, "contains": contains, "limit": limit}
        return self._client.get(
            "/v1/phone-numbers/available", query=query, cast_to=AvailablePhoneNumbers, options=request_options
        )

    def buy(
        self, *, request_options: Optional[RequestOptions] = None, **body: Unpack[PhoneNumberBuyParams]
    ) -> PurchasedPhoneNumber:
        """Buy one of the numbers ``search`` returned. **Spends the organization's credit**: the first month is
        debited now and the rental renews monthly until the number is released. Nothing is charged if it fails."""
        return self._client.post(
            "/v1/phone-numbers/buy", body=body, cast_to=PurchasedPhoneNumber, options=request_options
        )

    def list(self, *, request_options: Optional[RequestOptions] = None) -> List[PhoneNumber]:
        return self._client.get("/v1/phone-numbers", cast_to=List[PhoneNumber], options=request_options)

    def retrieve(self, phone_number: str, /, *, request_options: Optional[RequestOptions] = None) -> PhoneNumber:
        """Look a number up by its E.164 form, e.g. ``+14155550100``."""
        return self._client.get(
            f"/v1/phone-numbers/by-number/{pid(phone_number)}", cast_to=PhoneNumber, options=request_options
        )

    def update(
        self,
        phone_number_id: str,
        /,
        *,
        request_options: Optional[RequestOptions] = None,
        **body: Unpack[PhoneNumberUpdateParams],
    ) -> PhoneNumber:
        """Change a number. ``inbound_agent_id`` is ignored unless ``set_inbound_agent=True``."""
        return self._client.patch(
            f"/v1/phone-numbers/{pid(phone_number_id)}", body=body, cast_to=PhoneNumber, options=request_options
        )

    def assign(
        self,
        phone_number_id: str,
        /,
        *,
        request_options: Optional[RequestOptions] = None,
        **body: Unpack[PhoneNumberAssignParams],
    ) -> PhoneNumber:
        return self._client.patch(
            f"/v1/phone-numbers/{pid(phone_number_id)}/assign",
            body=body,
            cast_to=PhoneNumber,
            options=request_options,
        )

    def test_inbound_webhook(
        self, phone_number_id: str, /, *, request_options: Optional[RequestOptions] = None
    ) -> InboundWebhookTestResult:
        return self._client.post(
            f"/v1/phone-numbers/{pid(phone_number_id)}/inbound-webhook/test",
            cast_to=InboundWebhookTestResult,
            options=request_options,
        )

    def rotate_inbound_webhook_secret(
        self, phone_number_id: str, /, *, request_options: Optional[RequestOptions] = None
    ) -> PhoneNumber:
        """The full new secret is in the response, once; afterwards only a hint is shown."""
        return self._client.post(
            f"/v1/phone-numbers/{pid(phone_number_id)}/inbound-webhook/rotate-secret",
            cast_to=PhoneNumber,
            options=request_options,
        )

    def delete(self, phone_number_id: str, /, *, request_options: Optional[RequestOptions] = None) -> None:
        return self._client.delete(f"/v1/phone-numbers/{pid(phone_number_id)}", options=request_options)
