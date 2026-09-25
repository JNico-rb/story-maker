"""Las cinco tools de lectura: cada una llama a la misma función que su endpoint de la API, así
que devuelve lo mismo (015-I6), y ninguna modifica nada (015-I1). `definitions.md` §12.2."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, sessionmaker

from story_maker.api import story_bible as story_bible_api
from story_maker.api import versions as versions_api
from story_maker.api.mcp.errors import from_http_exception
from story_maker.api.ownership import NOT_FOUND_DETAIL, owned_or_404
from story_maker.domain.constants import CHAPTERS_PER_NOVEL
from story_maker.interview.novels import NovelSummary
from story_maker.interview.novels import list_novels as _list_novels_service
from story_maker.store.models import Novel
from story_maker.store.versions import published_version

ChapterNumber = Annotated[int, Field(ge=1, le=CHAPTERS_PER_NOVEL)]


class ChapterOut(BaseModel):
    number: int
    title: str
    text: str


def _owned_novel(session: Session, novel_id: int, user_id: int) -> Novel:
    try:
        novel: Novel = owned_or_404(session, Novel, novel_id, lambda n: n.user_id == user_id)
    except HTTPException as exc:
        from_http_exception(exc)
    return novel


def list_novels_tool(session_factory: sessionmaker[Session], user_id: int) -> list[NovelSummary]:
    with session_factory() as session:
        return _list_novels_service(session, user_id)


def list_versions_tool(
    session_factory: sessionmaker[Session], user_id: int, novel_id: int
) -> versions_api.VersionsListResponse:
    with session_factory() as session:
        try:
            return versions_api.list_versions(novel_id, user_id, session)
        except HTTPException as exc:
            from_http_exception(exc)


def get_chapter_tool(
    session_factory: sessionmaker[Session],
    user_id: int,
    novel_id: int,
    version: int,
    chapter: int,
) -> ChapterOut:
    with session_factory() as session:
        try:
            detail = versions_api.get_version(novel_id, version, user_id, session)
        except HTTPException as exc:
            from_http_exception(exc)
    for cap in detail.view.chapters:
        if cap.number == chapter:
            return ChapterOut(number=cap.number, title=cap.title, text=cap.text)
    from_http_exception(HTTPException(status_code=404, detail=NOT_FOUND_DETAIL))


def query_story_bible_tool(
    session_factory: sessionmaker[Session], user_id: int, novel_id: int, version: int
) -> story_bible_api.StoryBibleResponse:
    with session_factory() as session:
        try:
            return story_bible_api.get_story_bible(
                novel_id, user_id, session, version_number=version
            )
        except HTTPException as exc:
            from_http_exception(exc)


def download_novel_tool(
    session_factory: sessionmaker[Session], user_id: int, novel_id: int, version: int
) -> bytes:
    with session_factory() as session:
        novel = _owned_novel(session, novel_id, user_id)
        row = published_version(session, novel.id, version)
        if row is None or row.pdf_path is None or not Path(row.pdf_path).is_file():
            from_http_exception(HTTPException(status_code=404, detail=NOT_FOUND_DETAIL))
        return Path(row.pdf_path).read_bytes()
