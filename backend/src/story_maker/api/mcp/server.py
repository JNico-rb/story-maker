"""El `ServidorMCP`: sus siete tools (`definitions.md` §12.2), montadas en `/mcp` con el mismo
`TokenDeAcceso` que `/api` y una traza `mcp:<tool>` por llamada (spec 015)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_request
from fastmcp.utilities.types import File
from mcp.types import ToolAnnotations
from sqlalchemy.orm import Session, sessionmaker
from starlette.middleware import Middleware
from starlette.routing import Route

from story_maker.agents.port import AgentPort
from story_maker.api.auth import Clock
from story_maker.api.mcp.auth import BearerAuthMiddleware
from story_maker.api.mcp.instrumentation import (
    SchemaErrorTracing,
    as_json,
    mask_union,
    traced_tool,
)
from story_maker.api.mcp.tools_read import (
    ChapterNumber,
    ChapterOut,
    download_novel_tool,
    get_chapter_tool,
    list_novels_tool,
    list_versions_tool,
    query_story_bible_tool,
)
from story_maker.api.mcp.tools_write import (
    ConfirmChangeOut,
    RequestChangeOut,
    confirm_change_tool,
    novel_for_change_request,
    request_change_tool,
)
from story_maker.api.mcp.tracing import record_call
from story_maker.api.story_bible import StoryBibleResponse
from story_maker.api.versions import VersionsListResponse
from story_maker.config import Config
from story_maker.interview.novels import NovelSummary
from story_maker.observability.mask import Mask
from story_maker.observability.port import ObservabilityPort, Trace
from story_maker.pipeline.changes.selection import Selection

READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True)
NON_DESTRUCTIVE_WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False)

Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]


def _current_user_id() -> int:
    return int(get_http_request().state.user_id)


def _call[T](
    telemetry: ObservabilityPort,
    trace: Trace,
    mask: Mask,
    tool: str,
    input_: dict[str, Any],
    fn: Callable[[], T],
) -> T:
    """Llama a `fn`, deja el span `tool:<tool>` con la entrada y la salida (o el error)
    enmascaradas, y propaga el `ToolError` tal cual (015-C16, 015-C17)."""
    try:
        result = fn()
    except ToolError as exc:
        record_call(telemetry, trace, tool, mask, input=input_, error=str(exc))
        raise
    record_call(telemetry, trace, tool, mask, input=input_, output=as_json(result))
    return result


def build_mcp_route(
    *,
    session_factory: sessionmaker[Session],
    jwt_secret: str,
    clock: Clock,
    agent_port: AgentPort,
    telemetry: ObservabilityPort,
    config: Config,
    workspace: Path,
) -> tuple[Route, Lifespan]:
    """Registra las siete tools y devuelve la ruta `/mcp` (con la autenticación como middleware
    ASGI) y el ciclo de vida que arranca y detiene su sesión (`architecture.md` §14.4)."""
    mcp = FastMCP("story-maker")
    mcp.add_middleware(SchemaErrorTracing(telemetry))

    @mcp.tool(
        run_in_thread=False,
        description="Lista las novelas del cliente con su estado y su versión vigente.",
        annotations=READ_ONLY,
    )
    def list_novels() -> list[NovelSummary]:
        user_id = _current_user_id()
        with traced_tool(
            telemetry, session_factory, "list_novels", user_id=user_id, novel_id=None
        ) as (trace, _):
            result = list_novels_tool(session_factory, user_id)
            mask = mask_union(session_factory, [n.id for n in result])
            record_call(
                telemetry,
                trace,
                "list_novels",
                mask,
                input={},
                output={"novels": [as_json(n) for n in result]},
            )
            return result

    @mcp.tool(
        run_in_thread=False,
        description="Da el historial de versiones publicadas de una novela, con sus capítulos "
        "cambiados.",
        annotations=READ_ONLY,
    )
    def list_versions(novel_id: int) -> VersionsListResponse:
        user_id = _current_user_id()
        with traced_tool(
            telemetry, session_factory, "list_versions", user_id=user_id, novel_id=novel_id
        ) as (trace, mask):
            return _call(
                telemetry,
                trace,
                mask,
                "list_versions",
                {"novel_id": novel_id},
                lambda: list_versions_tool(session_factory, user_id, novel_id),
            )

    @mcp.tool(
        run_in_thread=False,
        description="Devuelve un capítulo de una versión publicada de una novela.",
        annotations=READ_ONLY,
    )
    def get_chapter(novel_id: int, version: int, chapter: ChapterNumber) -> ChapterOut:
        user_id = _current_user_id()
        with traced_tool(
            telemetry, session_factory, "get_chapter", user_id=user_id, novel_id=novel_id
        ) as (trace, mask):
            return _call(
                telemetry,
                trace,
                mask,
                "get_chapter",
                {"novel_id": novel_id, "version": version, "chapter": chapter},
                lambda: get_chapter_tool(session_factory, user_id, novel_id, version, chapter),
            )

    @mcp.tool(
        run_in_thread=False,
        description="Devuelve la story bible (personajes, lugares, hechos y cronología) de una "
        "versión publicada.",
        annotations=READ_ONLY,
    )
    def query_story_bible(novel_id: int, version: int) -> StoryBibleResponse:
        user_id = _current_user_id()
        with traced_tool(
            telemetry, session_factory, "query_story_bible", user_id=user_id, novel_id=novel_id
        ) as (trace, mask):
            return _call(
                telemetry,
                trace,
                mask,
                "query_story_bible",
                {"novel_id": novel_id, "version": version},
                lambda: query_story_bible_tool(session_factory, user_id, novel_id, version),
            )

    @mcp.tool(
        run_in_thread=False,
        description="Descarga el PDF guardado de una versión publicada.",
        annotations=READ_ONLY,
    )
    def download_novel(novel_id: int, version: int) -> File:
        user_id = _current_user_id()
        with traced_tool(
            telemetry, session_factory, "download_novel", user_id=user_id, novel_id=novel_id
        ) as (trace, mask):
            pdf_bytes = _call(
                telemetry,
                trace,
                mask,
                "download_novel",
                {"novel_id": novel_id, "version": version},
                lambda: download_novel_tool(session_factory, user_id, novel_id, version),
            )
            return File(data=pdf_bytes, format="pdf", name=f"novela-v{version}.pdf")

    @mcp.tool(
        run_in_thread=False,
        description="Propone un cambio del lector sobre una selección (un fragmento o un hecho) "
        "de la novela; solo propone, nunca lo aplica. La confirma `confirm_change`.",
        annotations=NON_DESTRUCTIVE_WRITE,
    )
    async def request_change(novel_id: int, selection: Selection, request: str) -> RequestChangeOut:
        user_id = _current_user_id()
        with traced_tool(
            telemetry, session_factory, "request_change", user_id=user_id, novel_id=novel_id
        ) as (trace, mask):
            input_ = {"novel_id": novel_id, "selection": selection.model_dump()}
            try:
                result = await request_change_tool(
                    session_factory=session_factory,
                    agent_port=agent_port,
                    telemetry=telemetry,
                    config=config,
                    workspace=workspace,
                    clock=clock,
                    trace=trace,
                    user_id=user_id,
                    novel_id=novel_id,
                    selection=selection,
                    request=request,
                )
            except ToolError as exc:
                record_call(telemetry, trace, "request_change", mask, input=input_, error=str(exc))
                raise
            record_call(
                telemetry,
                trace,
                "request_change",
                mask,
                input=input_,
                output=result.model_dump(mode="json", exclude={"code"}),
            )
            return result

    @mcp.tool(
        run_in_thread=False,
        description="Confirma, con el código de `request_change`, una propuesta de cambio ya "
        "aceptada por la persona; encola su ejecución. Llámala solo tras esa aceptación.",
        annotations=NON_DESTRUCTIVE_WRITE,
    )
    def confirm_change(request_id: int, code: str) -> ConfirmChangeOut:
        user_id = _current_user_id()
        novel_id = novel_for_change_request(session_factory, request_id)
        with traced_tool(
            telemetry, session_factory, "confirm_change", user_id=user_id, novel_id=novel_id
        ) as (trace, mask):
            return _call(
                telemetry,
                trace,
                mask,
                "confirm_change",
                {"request_id": request_id},
                lambda: confirm_change_tool(
                    session_factory=session_factory,
                    clock=clock,
                    user_id=user_id,
                    request_id=request_id,
                    code=code,
                ),
            )

    return _splice_route(mcp, session_factory=session_factory, jwt_secret=jwt_secret, clock=clock)


def _splice_route(
    mcp: FastMCP,
    *,
    session_factory: sessionmaker[Session],
    jwt_secret: str,
    clock: Clock,
) -> tuple[Route, Lifespan]:
    """`mcp.http_app(path="/mcp")` montado con `Mount` redirige `/mcp` (sin barra) a `/mcp/`
    (307): en vez de eso, su única `Route` se traspasa tal cual al router de arriba, con la
    autenticación como su primer middleware (015-C01: la ruta exacta, sin sufijos)."""
    mcp_app = mcp.http_app(path="/mcp")
    base_route = mcp_app.routes[0]
    if not isinstance(base_route, Route):
        raise TypeError(f"fastmcp cambió su ruta de streamable-http: {type(base_route)!r}")
    methods = list(base_route.methods) if base_route.methods else None
    route = Route(
        "/mcp",
        base_route.endpoint,
        methods=methods,
        middleware=[
            Middleware(
                BearerAuthMiddleware,
                session_factory=session_factory,
                jwt_secret=jwt_secret,
                clock=clock,
            ),
            *mcp_app.user_middleware,
        ],
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with mcp_app.lifespan(app):
            yield

    return route, lifespan
