"""La costura `planning` del orquestador, montada con las piezas de 010: la candidata con el canon
del brief confirmado, el bucle de intentos del planner y la aplicación del plan aceptado
(`architecture.md` §5, §9.1; 010-C01, C17, C20, C24, C26, C27; 011-C33).

Aquí solo se traduce: el brief de 008 (JSON de `briefs.content` más los hechos extraídos
aceptados) a lo que esperan el repositorio de 009 y la ventana del planner, y la story bible de la
candidata a la vista mínima de `outline`. Las reglas siguen en sus módulos."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from sqlalchemy.orm import Session

from story_maker.agents.port import SessionRequest
from story_maker.domain.brief import AcceptedFact, BriefContent, personal_elements
from story_maker.domain.trope_catalog import TROPE_CATALOG
from story_maker.observability.port import Trace
from story_maker.pipeline.planning.brief_view import (
    BannedEntryView,
    BriefView,
    CloseOneView,
    ExtractedFactView,
    RecipientView,
    RecollectionView,
    TraitView,
)
from story_maker.pipeline.planning.candidate import start_generation_phase
from story_maker.pipeline.planning.phase import (
    InfeasibleConfig,
    ProviderFailure,
    finalize_accepted_plan,
    run_plan_phase,
)
from story_maker.pipeline.planning.resume import plan_resume_state
from story_maker.pipeline.planning.session import submit_plan_tool
from story_maker.pipeline.planning.story_bible_view import (
    EventRef,
    FactRef,
    PersonalElement,
    StoryBibleView,
)
from story_maker.pipeline.production import Production
from story_maker.pipeline.runs import get_run, naive
from story_maker.store.brief_canon import (
    BriefCloseOne,
    BriefExtractedFact,
    BriefRecipient,
    BriefRecollection,
    BriefTrait,
    ConfirmedBrief,
)
from story_maker.store.models import BannedTerm, Brief, ExtractedFact, FreeText, Novel
from story_maker.store.story_bible import StoryBible, read_story_bible


def brief_content(session: Session, novel_id: int) -> BriefContent:
    brief = session.query(Brief).filter(Brief.novel_id == novel_id).one()
    return BriefContent.model_validate(brief.content)


def accepted_facts(session: Session, novel_id: int) -> list[ExtractedFact]:
    return (
        session.query(ExtractedFact)
        .join(FreeText, ExtractedFact.free_text_id == FreeText.id)
        .filter(FreeText.novel_id == novel_id, ExtractedFact.accepted.is_(True))
        .order_by(ExtractedFact.id)
        .all()
    )


def _age(declared: int | None, birth: dt.date | None, today: dt.date) -> int:
    if declared is not None:
        return declared
    if birth is None:
        raise ValueError("el brief confirmado no tiene ni edad ni fecha de nacimiento")
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))


def confirmed_brief(session: Session, novel_id: int) -> ConfirmedBrief:
    """El brief confirmado de la novela con los ids de sus elementos personales, tal como los
    numera 008 al confirmar (`domain.brief.personal_elements`)."""
    content = brief_content(session, novel_id)
    facts = accepted_facts(session, novel_id)
    elements = personal_elements(
        content,
        [
            AcceptedFact(id=f.id, subject=f.subject, value=f.value, mandatory=f.mandatory)
            for f in facts
        ],
    )
    ids = {e.field: e.id for e in elements}
    novel = session.get_one(Novel, novel_id)
    recipient = content.recipient
    return ConfirmedBrief(
        recipient=BriefRecipient(
            name=recipient.name,
            age=_age(recipient.age, recipient.birth_date, novel.created_at.date()),
            name_element_id=ids["recipient.name"],
            traits=tuple(
                BriefTrait(t.statement, ids[f"recipient.traits[{i}]"], t.mandatory)
                for i, t in enumerate(recipient.traits)
            ),
            birth_date=recipient.birth_date,
        ),
        close_ones=tuple(
            BriefCloseOne(
                c.name,
                c.relation,
                c.species or "person",
                ids[f"close_ones[{i}]"],
                c.mandatory,
                age=c.age,
                birth_date=c.birth_date,
            )
            for i, c in enumerate(content.close_ones)
        ),
        recollections=tuple(
            BriefRecollection(
                r.statement,
                r.place,
                ids[f"recollections[{i}]"],
                r.mandatory,
                age=r.age,
                year=r.year,
                present=tuple(r.present),
                excluded=r.excluded,
            )
            for i, r in enumerate(content.recollections)
        ),
        extracted_facts=tuple(
            BriefExtractedFact(
                f.subject,
                f.attribute,
                f.value,
                accepted=True,
                mandatory=f.mandatory,
                element_id=ids[f"extracted_facts[{f.id}]"],
            )
            for f in facts
        ),
    )


def brief_view(session: Session, novel_id: int, age: int) -> BriefView:
    """Lo que el planner ve del brief: nunca el texto libre ni la cita de un hecho (010-I1)."""
    content = brief_content(session, novel_id)
    banned = session.query(BannedTerm).filter(
        BannedTerm.level == "novel", BannedTerm.novel_id == novel_id
    )
    return BriefView(
        recipient=RecipientView(
            name=content.recipient.name,
            age=age,
            traits=tuple(TraitView(t.statement, t.mandatory) for t in content.recipient.traits),
        ),
        close_ones=tuple(
            CloseOneView(c.name, c.relation, c.species or "person", c.mandatory)
            for c in content.close_ones
        ),
        recollections=tuple(
            RecollectionView(r.statement, r.place, tuple(r.present), r.excluded, r.mandatory)
            for r in content.recollections
        ),
        occasion=content.occasion or "",
        genre=content.genre or "",
        tone=content.tone or "",
        extension=content.length or "",
        dedication=content.dedication,
        banned_novel=tuple(
            BannedEntryView(b.term, b.type, tuple(b.keywords or ())) for b in banned
        ),
        plot_wishes=tuple(w.statement for w in content.plot_wishes),
        accepted_extracted_facts=tuple(
            ExtractedFactView(f.subject, f.attribute, f.value)
            for f in accepted_facts(session, novel_id)
        ),
    )


def story_bible_view(bible: StoryBible) -> StoryBibleView:
    """La story bible inicial de la candidata con los ids como texto: los de sus hechos y los
    de sus elementos personales, que son los que el outline asigna a capítulos."""
    names = {c.id: c.canonical_name for c in bible.characters}
    places = {p.id: p.canonical_name for p in bible.places}
    elements: dict[int, PersonalElement] = {}
    for fact in bible.facts:
        element = fact.personal_element_id
        if element is not None and element not in elements:
            elements[element] = PersonalElement(str(element), fact.value, fact.mandatory)
    return StoryBibleView(
        present_year=bible.present_year,
        character_names=tuple(names.values()),
        place_names=tuple(places.values()),
        fact_ids=tuple(str(f.id) for f in bible.facts),
        personal_elements=tuple(elements.values()),
        facts=tuple(
            FactRef(
                str(f.id),
                f.mandatory,
                str(f.personal_element_id) if f.personal_element_id is not None else None,
            )
            for f in bible.facts
        ),
        events=tuple(
            EventRef(
                statement=e.statement,
                moment=e.moment,
                place=places[e.place_id],
                present=tuple(names[p.character_id] for p in e.presences),
                excluded=names[e.excluded_character_id] if e.excluded_character_id else None,
            )
            for e in bible.chronology.events
            if e.origin == "brief"
        ),
    )


@dataclass(frozen=True)
class PlanningSeam:
    production: Production
    prompt: str
    prompt_version: str | None = None

    async def __call__(self, run_id: int, trace: Trace) -> None:
        """Crea la candidata si aún no la hay y abre el planner desde el intento siguiente al
        último cerrado (010-C24). Termina con el plan aplicado o con la ejecución fuera de
        `running`, que el orquestador comprueba al volver."""
        p = self.production
        now = naive(p.clock())
        with p.session_factory() as session:
            run = get_run(session, run_id)
            novel = session.get_one(Novel, run.novel_id)
            user_id, novel_id, version_id = novel.user_id, novel.id, run.candidate_version_id
            brief = confirmed_brief(session, novel_id)
        if version_id is None:
            version_id = start_generation_phase(
                p.session_factory, run_id, novel_id, brief, now=now
            ).id
        with p.session_factory() as session:
            state = plan_resume_state(session, run_id)
            view = brief_view(session, novel_id, brief.recipient.age)
            bible = story_bible_view(read_story_bible(session, version_id))

        def build_request(message: str, attempt_number: int) -> SessionRequest:
            del attempt_number  # el número va en `attempts`, no en la sesión
            return SessionRequest(
                role="planner",
                mode="plan",
                user_id=user_id,
                novel_id=novel_id,
                run_id=run_id,
                prompt=self.prompt,
                prompt_version=self.prompt_version,
                message=message,
                tools=(submit_plan_tool(),),
                trace=trace,
            )

        try:
            outcome = await run_plan_phase(
                p.port,
                p.session_factory,
                p.telemetry,
                trace,
                run_id=run_id,
                version_id=version_id,
                build_request=build_request,
                brief=view,
                story_bible=bible,
                catalog=TROPE_CATALOG,
                present_year=bible.present_year,
                max_retries=p.config.max_retries["plan"],
                now=now,
                start_attempt_number=state.next_attempt_number,
                initial_defects=state.defects,
            )
        except (ProviderFailure, InfeasibleConfig):
            return  # la ejecución ya quedó `interrupted` o `failed` (010-C26, C27)
        if outcome.verdict == "accept":
            finalize_accepted_plan(
                p.session_factory, p.telemetry, trace, run_id, version_id, outcome, now=now
            )
