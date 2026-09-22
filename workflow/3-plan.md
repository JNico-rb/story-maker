# Process 3 — The plan (`plan.md`)

One `plan.md` per spec, in the spec's folder. One step per requirement, in implementation order, citing the ID it delivers and, when it is not T, its class: `(RF-CFG-2 · clase A)`. A step names the behaviour it delivers, not the files it touches — if it can't be phrased as a requirement of the spec, it belongs in the spec first. The one exception: a demonstration that `verification.md` §5 assigns to the spec is a step of its own, citing that row. Written → **stop**.

No step invents a figure: the ones in `architecture.md` §10.2 are read from config and fail actionably if missing.

Mark a step `[x]` only when its case goes green. If implementation proves the plan wrong, stop and change the plan with the user; every step comes from the plan.

    # NNN — <MÓD> · Plan

    - [ ] Plan approved   <- only the user marks this

    Spec: [spec.md](spec.md). Verificación: <método> (`docs/verification.md` §5).

    ### Steps
    - [ ] <requirement, as stated in the spec> (<ID> · clase <X>)

    ### Closing
    - [ ] Full suite green, type checks clean
    - [ ] Spec updated, or confirmed still true
    - [ ] Docs updated, or confirmed still true
