"""Reference data: voices, extraction models, flow and prompt templates."""

from __future__ import annotations

from typing import IO, Any, Dict, List, Literal, Optional, Sequence, Tuple, Union

from dialgem._base_client import RequestOptions
from dialgem._errors import DialgemError
from dialgem._resource import Resource, pid
from dialgem.types.catalog import (
    ExtractionModelList,
    FlowTemplate,
    FlowTemplateSummary,
    PromptTemplate,
    PromptTemplateSummary,
    Voice,
    VoiceDeleteResponse,
)

#: An audio clip: raw bytes, an open binary file, or ``(filename, bytes_or_file)``.
AudioFile = Union[bytes, IO[bytes], Tuple[str, Union[bytes, IO[bytes]]]]


def _clone_parts(
    name: str,
    files: Sequence[AudioFile],
    consent_confirmed: bool,
    engine: Optional[str],
    description: Optional[str],
    language: Optional[str],
    filenames: Optional[Sequence[str]],
) -> Tuple[Dict[str, str], List[Tuple[str, Any]]]:
    if consent_confirmed is not True:
        raise DialgemError(
            "consent_confirmed must be True: you are asserting that you hold the rights to this audio "
            "and have the speaker's consent to clone their voice."
        )
    if not files:
        raise DialgemError("At least one audio file is required to clone a voice.")
    data = {"name": name, "consent_confirmed": "true"}
    for key, value in (("engine", engine), ("description", description), ("language", language)):
        if value:
            data[key] = value
    parts: List[Tuple[str, Any]] = []
    for i, item in enumerate(files):
        explicit = filenames[i] if filenames and i < len(filenames) else None
        fname: Optional[str]
        if isinstance(item, tuple):
            fname, content = item
        else:
            raw_name = getattr(item, "name", None)
            fname = raw_name.replace("\\", "/").rsplit("/", 1)[-1] if isinstance(raw_name, str) else None
            content = item
        parts.append(("files", (explicit or fname or f"clip-{i + 1}.wav", content)))
    return data, parts


class Voices(Resource):
    """``dialgem.voices``."""

    def list(
        self,
        *,
        provider: Optional[str] = None,
        gender: Optional[str] = None,
        accent: Optional[str] = None,
        language: Optional[str] = None,
        search: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> List[Voice]:
        return self._client.get(
            "/v1/voices",
            query={"provider": provider, "gender": gender, "accent": accent, "language": language, "search": search},
            cast_to=List[Voice],
            options=request_options,
        )

    def clone(
        self,
        *,
        name: str,
        files: Sequence[AudioFile],
        consent_confirmed: bool,
        engine: Optional[Literal["elevenlabs", "cartesia"]] = None,
        description: Optional[str] = None,
        language: Optional[str] = None,
        filenames: Optional[Sequence[str]] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Voice:
        """Clone a voice from audio clips. ``consent_confirmed=True`` asserts you hold the rights to the
        audio and the speaker's consent. Uploads are never retried."""
        data, parts = _clone_parts(name, files, consent_confirmed, engine, description, language, filenames)
        return self._client.post_form("/v1/voices/clone", data=data, files=parts, cast_to=Voice, options=request_options)

    def delete(self, voice_id: str, /, *, request_options: Optional[RequestOptions] = None) -> VoiceDeleteResponse:
        return self._client.delete(f"/v1/voices/{pid(voice_id)}", cast_to=VoiceDeleteResponse, options=request_options)


class ExtractionModels(Resource):
    """``dialgem.extraction_models``: models usable for post-call extraction."""

    def list(self, *, request_options: Optional[RequestOptions] = None) -> ExtractionModelList:
        return self._client.get("/v1/models/extraction", cast_to=ExtractionModelList, options=request_options)


class FlowTemplates(Resource):
    """``dialgem.flow_templates``."""

    def list(
        self, *, category: Optional[str] = None, request_options: Optional[RequestOptions] = None
    ) -> List[FlowTemplateSummary]:
        return self._client.get(
            "/v1/flow-templates", query={"category": category}, cast_to=List[FlowTemplateSummary], options=request_options
        )

    def retrieve(self, template_id: str, /, *, request_options: Optional[RequestOptions] = None) -> FlowTemplate:
        return self._client.get(f"/v1/flow-templates/{pid(template_id)}", cast_to=FlowTemplate, options=request_options)


class PromptTemplates(Resource):
    """``dialgem.prompt_templates``."""

    def list(
        self, *, category: Optional[str] = None, request_options: Optional[RequestOptions] = None
    ) -> List[PromptTemplateSummary]:
        return self._client.get(
            "/v1/prompt-templates", query={"category": category}, cast_to=List[PromptTemplateSummary], options=request_options
        )

    def retrieve(self, template_id: str, /, *, request_options: Optional[RequestOptions] = None) -> PromptTemplate:
        return self._client.get(
            f"/v1/prompt-templates/{pid(template_id)}", cast_to=PromptTemplate, options=request_options
        )
