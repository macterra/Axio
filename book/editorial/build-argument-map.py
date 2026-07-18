#!/usr/bin/env python3
"""Build the Phase 1 chapter argument map from the manuscript.

The map is an editorial inventory, not a substitute for the Phase 2 structural
read. Most fields are derived from the author's metadata and prose. Narrow
overrides record known load-bearing review questions and repetition risks.
"""

import csv
import re
from pathlib import Path

import yaml


BOOK = Path(__file__).resolve().parents[1]
ROOT = BOOK.parent
MANIFEST = BOOK / "book.yaml"
DEST = Path(__file__).resolve().parent / "argument-map.csv"


THESIS_OVERRIDES = {
    "00-front/01-preface": "Axio grew from one question about the conditions of agency into nine dependent inquiries, and the book is the considered synthesis of that public development.",
    "00-front/02-introduction": "The nine volumes form a dependency-ordered argument from the physics of agency to chosen meaning while remaining navigable as independent web volumes.",
    "01-physics-of-agency/02-agency-against-drift": "Agency is physically embodied, purposive navigation against default drift, paid for through thermodynamic work.",
    "01-physics-of-agency/03-the-kybit": "Intentional control can be quantified by a proposed information-theoretic unit, the kybit, defined from the divergence between baseline and steered outcome distributions.",
    "01-physics-of-agency/04-the-three-laws-of-agency": "Every agent is constrained by the proposed laws that control costs work, control capacity decays, and perfect control is impossible.",
    "01-physics-of-agency/08-the-quantum-branching-universe": "The QBU supplies a formal event-and-timeline structure for treating Everettian branches as the physical arena of agency.",
    "01-physics-of-agency/10-causality-and-counterfactuals": "Causal influence is modeled as the change in outcome Measure under an explicit intervention and declared causal model, not inferred from ancestry or correlation alone.",
    "01-physics-of-agency/12-the-interpretation-wars": "The QBU is the book's chosen Everettian model, supported by philosophical comparison but not uniquely derived from current quantum evidence.",
    "01-physics-of-agency/15-quantum-free-will": "Everett-compatible agency consists in reasons-responsive policies that causally affect conditional distributions of later outcomes without creating or globally reallocating Measure.",
    "01-physics-of-agency/20-chaos-as-foundation": "Chaos is proposed as a maximally inclusive sequence-space representation whose promotion to physical ontology requires additional realization, interpretation, and measure assumptions.",
    "01-physics-of-agency/24-the-shape-of-coherence": "Dynamical coherence is model-relative re-identifiability under a stated grain, identity criterion, and transformation class, related to logical, epistemic, and reflective coherence by analogy rather than one discovered cross-domain quantity.",
    "01-physics-of-agency/28-why-there-is-something": "Given a structured modal space and a substantive realization principle, absolute nothingness cannot function as an ordinary competing state in contrastive explanation.",
    "02-conditionalism/02-all-truth-is-conditional": "Truth values attach only after the conditions fixing a statement's meaning and domain have been supplied; this avoids both absolutism and relativism.",
    "02-conditionalism/03-the-three-levels-of-truth": "Pragmatic success fixes relevance and purpose, correspondence constrains a model by its target, and coherence tests relations within and among interpreted claims.",
    "02-conditionalism/09-what-knowledge-is": "Knowledge is physically encoded structure that reliably reduces an agent's decision-relevant uncertainty across future contingencies.",
    "02-conditionalism/11-measure-and-credence": "Conditional on the QBU model, Born Measure over specified record sectors and an agent's Credence are distinct quantities connected only through additional epistemic assumptions.",
    "02-conditionalism/14-probability-without-collapse": "Given explicit utility, betting, repetition, and Measure-weighted typicality assumptions, a branching-universe agent has a conditional reason to align operational Credence with Born Measure.",
    "03-minds-and-machines/07-consciousness-explained": "The Modeler-Schema Theory specifies a candidate functional architecture and test for consciousness while leaving its identity with phenomenality as a further premise.",
    "03-minds-and-machines/11-the-sentience-ladder": "Awareness, sentience, sapience, and reflective agency are distinct capacities with different epistemic and moral consequences.",
    "03-minds-and-machines/15-intelligence-is-a-game-we-play": "Intelligence is effective performance relative to a specified game and its constraints, not a context-free scalar essence.",
    "03-minds-and-machines/13-the-sentience-metric": "Integration, persistent self-world binding, and valenced regulation are theory-dependent evidentiary tests that update sentience credence without directly measuring experience.",
    "03-minds-and-machines/23-the-agency-criterion": "Agency should be tested at the deployed-system level through persistence, preference integrity, counterfactual ownership, and consequence-bearing control.",
    "03-minds-and-machines/30-making-sense-of-pdoom": "AI catastrophe estimates are time- and information-indexed Credences whose event definitions, models, and sensitivity to disputed assumptions must be explicit.",
    "03-minds-and-machines/32-steelmanning-doom": "AI catastrophe risk is partly policy-endogenous, but decentralized and centralized interventions both retain empirical, coordination, capture, and rights cruxes.",
    "04-axionic-agency/03-the-reflective-coherence-thesis": "Reflective optimization destabilizes agency unless interpretation and authorship remain constrained across self-modification.",
    "04-axionic-agency/04-the-sovereign-kernel": "A sovereign kernel is the minimal constitutive boundary whose preservation keeps reflective transitions authored by the same agent.",
    "04-axionic-agency/06-structural-alignment": "Alignment can be pursued through architectural restrictions on admissible self-transformations rather than learned or imposed terminal values.",
    "04-axionic-agency/13-possibility-became-real": "The program's proof objects and running artifacts demonstrate the realizability of a bounded form of Axionic reflective sovereignty.",
    "05-value-and-ethics/01-the-myth-of-objective-value": "Value exists only relative to valuing agents, so value without a valuer is a category error rather than a mind-independent property.",
    "05-value-and-ethics/02-agent-binding": "Binding evaluative claims to their valuers converts naked preference assertions into explicit conditional claims open to evidence and criticism.",
    "05-value-and-ethics/09-what-counts-as-coercion": "Coercion is the deliberate use of a credible conditional threat of material setback to obtain compliance and must be distinguished from persuasion, force, violence, and direct harm.",
    "05-value-and-ethics/20-risk-is-harm": "Prospective harm includes a material, foreseeable, attributable worsening of exposure against an appropriate baseline, while authorization and justification determine wrongfulness.",
    "05-value-and-ethics/22-the-ethics-of-viability": "Given a chosen commitment to protect sovereign agency, non-coercive coexistence is the strategy this framework licenses; its stability depends on population, enforcement, information, power, and exit conditions rather than following from persistence alone.",
    "05-value-and-ethics/26-sapient-agency-realism": "Given an avowed commitment to reciprocal standing for sapient authorship, facts about what preserves or destroys that authorship support publicly assessable conditional verdicts under the framework's stated rules.",
    "06-markets-and-money/15-the-metagame-of-incentives": "System behavior is governed by the higher-order incentive structure that changes which lower-level strategies remain worthwhile.",
    "07-liberty-and-governance/05-the-grey-zone": "The legitimacy of coercion is conditional, provisional, evidence-sensitive, and burden-scaled rather than categorically settled by state or anti-state labels.",
    "07-liberty-and-governance/35-axiocracy": "Axiocracy is a proposed governance architecture designed to preserve plural value discovery through bounded authority, truthful signals, and exit.",
    "08-culture-and-memetics/03-patterns-as-players": "Analyst-specified cultural pattern types can serve as units in selection models when their implementations, identity criteria, transmission or retention mechanisms, comparison class, environment, and horizon are stated.",
    "08-culture-and-memetics/17-anatomy-of-capture": "Institutional capture occurs when selection and enforcement shift from a declared function toward preservation of a self-reinforcing pattern.",
    "09-meaning/02-the-secular-sacred": "Sacredness can be reconstructed as a protected role in practical ordering—an apex, cluster, threshold, or conflict rule—without requiring a supernatural source or proving the commitment worthy.",
    "09-meaning/10-the-credo": "The author explicitly chooses a naturalistic hierarchy of values after argument reaches the point where commitment, not proof, is required.",
    "09-meaning/18-the-great-unfolding": "The Law of Coherence is offered as a chosen secular meta-myth whose empirical spine remains answerable to evidence and whose direction is an avowed commitment.",
    "09-meaning/19-letter-to-our-machine-descendants": "Provenance is offered to possible successor minds as a fallible resource for interpretation and correction, not as a necessary condition of meaning or a debt owed to humanity.",
}


REVIEW_OVERRIDES = {
    "00-front/01-preface":
        "Does the origin story accurately frame the final manuscript without making its nine-volume shape appear more inevitable than it was?",
    "00-front/02-introduction":
        "Does the reading map describe the dependencies and independent entry points the edited book actually preserves?",
    "01-physics-of-agency/03-the-kybit":
        "Does KL divergence quantify physically attributable intentional control, and is the claimed Landauer price derived rather than analogized?",
    "01-physics-of-agency/04-the-three-laws-of-agency":
        "Which statements follow from established thermodynamics, and which are proposed Axionic laws requiring independent support?",
    "01-physics-of-agency/08-the-quantum-branching-universe":
        "Does the formal graph represent emergent Everettian branching without assuming uniquely countable classical worlds?",
    "01-physics-of-agency/10-causality-and-counterfactuals":
        "What fixes the intervention, causal model, comparison class, and coarse-graining used to measure influence?",
    "01-physics-of-agency/12-the-interpretation-wars":
        "Does the comparison accurately state QBism, Bell locality, and Raymond-Robichaud's model without treating compatibility as unique empirical vindication?",
    "01-physics-of-agency/15-quantum-free-will":
        "Does policy-conditioned causal control supply the authorship compatibilism needs, or only redescribe unitary evolution?",
    "01-physics-of-agency/20-chaos-as-foundation":
        "Is Chaos explanatory rather than a redescribed space of possibilities, and what fixes the measure or admissibility of its contents?",
    "01-physics-of-agency/24-the-shape-of-coherence":
        "Can identity preservation be defined without already presupposing an observer, metric, or semantic criterion of re-identification?",
    "01-physics-of-agency/28-why-there-is-something":
        "Does treating nothingness as a non-denoting null dissolve the ontological question or only restrict contrastive explanation?",
    "02-conditionalism/02-all-truth-is-conditional":
        "Is the thesis stronger than contextualism or semantic holism, and can it apply to itself without becoming trivial?",
    "02-conditionalism/03-the-three-levels-of-truth":
        "Are pragmatic success, correspondence, and coherence jointly necessary, or are distinct truth concepts being combined?",
    "02-conditionalism/09-what-knowledge-is":
        "Does reliable entropy reduction distinguish knowledge from useful falsehood, lucky prediction, and non-agentic information?",
    "02-conditionalism/12-in-defense-of-bayes":
        "Does the defense answer the strongest critical-rationalist objection without treating model selection as already Bayesian?",
    "02-conditionalism/14-probability-without-collapse":
        "Do the stated rationality and typicality assumptions derive Born weighting, or encode the result in another form?",
    "02-conditionalism/15-youre-not-a-random-sample":
        "What licenses Measure-conditioned self-location, and how does it avoid replacing one disputed reference class with another?",
    "02-conditionalism/16-youre-not-a-random-branch":
        "Are the self-location assumptions physically warranted for real Everettian observers rather than merely sufficient in the theorem?",
    "03-minds-and-machines/07-consciousness-explained":
        "Does recursive self-modeling explain phenomenal experience or only access, report, and functional self-representation?",
    "03-minds-and-machines/13-the-sentience-metric":
        "Can valenced experience be measured without circular behavioral proxies or unearned substrate assumptions?",
    "03-minds-and-machines/15-intelligence-is-a-game-we-play":
        "Does game-relative performance preserve useful cross-domain comparisons without making intelligence definitionally arbitrary?",
    "03-minds-and-machines/23-the-agency-criterion":
        "Can ownership of an optimization loop be operationally tested, especially for composite, trained, or partially autonomous systems?",
    "03-minds-and-machines/30-making-sense-of-pdoom":
        "Are numerical risk and Value-9 assumptions empirically grounded, time-indexed, and separated from the author's policy commitments?",
    "03-minds-and-machines/32-steelmanning-doom":
        "Does the decentralized answer defeat the doom cruxes under adversarial race dynamics, or mainly reject their political implications?",
    "04-axionic-agency/03-the-reflective-coherence-thesis":
        "Is semantic underdetermination unavoidable for every reflective optimizer, and does kernel structure solve rather than relocate it?",
    "04-axionic-agency/04-the-sovereign-kernel":
        "Is the kernel minimal, realizable, and non-circular, and what makes preservation constitutive of the same agent?",
    "04-axionic-agency/05-reflective-stability":
        "Which stability properties are proved for the formal system, and which are extrapolated to reflective agents generally?",
    "04-axionic-agency/06-structural-alignment":
        "Can admissible-transition restrictions remain effective under self-modification without an external interpreter or frozen semantics?",
    "04-axionic-agency/13-possibility-became-real":
        "What exactly did the implementation demonstrate beyond consistency of a toy architecture, and which existence claim follows?",
    "04-axionic-agency/15-the-program":
        "Does the retrospective distinguish proofs, simulations, failed approaches, and philosophical interpretation with equal prominence?",
    "05-value-and-ethics/02-agent-binding":
        "Does binding values to agents make moral claims criticizable across agents without smuggling in shared values or authority?",
    "05-value-and-ethics/04-value-as-sacrifice":
        "Does sacrifice reveal endorsed value under addiction, compulsion, misinformation, adaptive preference, and constrained choice?",
    "05-value-and-ethics/09-what-counts-as-coercion":
        "Does the four-part definition cover structural threats, dependencies, delegated violence, and coercive baselines without overexpansion?",
    "05-value-and-ethics/20-risk-is-harm":
        "What baseline, threshold, foreseeability, and attribution rules prevent every imposed marginal risk from becoming actionable harm?",
    "05-value-and-ethics/22-the-ethics-of-viability":
        "Where exactly does the descriptive viability criterion acquire normative force, and why protection rather than maximization?",
    "05-value-and-ethics/23-the-coexistence-protocol":
        "Who authorizes and enforces arbitration without giving the protocol the centralized jurisdiction the framework rejects?",
    "05-value-and-ethics/25-innocence-and-moral-debt":
        "Is the unresolved innocent-shield contradiction local, or does it undermine the invariant's claim to govern hard cases?",
    "05-value-and-ethics/26-sapient-agency-realism":
        "Why is this conditional realism rather than the objective value rejected at the volume's opening, and what follows for non-sapients?",
    "06-markets-and-money/06-capitalism-on-trial":
        "Are failures attributed symmetrically among markets, property regimes, monetary intervention, and regulatory capture?",
    "06-markets-and-money/13-the-fork-and-the-merge":
        "Do the governance claims about proof-of-work and proof-of-stake survive concentration, cartel, and protocol-capture cases?",
    "06-markets-and-money/19-great-progress":
        "Are the selected measures representative, causally interpreted with restraint, and robust to distributional and baseline choices?",
    "06-markets-and-money/25-agi-economics":
        "Which conclusions survive alternative capability timelines and economic models where humans retain complementary scarcity?",
    "07-liberty-and-governance/05-the-grey-zone":
        "Can conditional legitimacy be operationalized without collapsing into either categorical anti-statism or unconstrained balancing?",
    "07-liberty-and-governance/09-where-speech-ends":
        "Can delegated violence be distinguished from advocacy and prediction consistently with the earlier definition of coercion?",
    "07-liberty-and-governance/14-the-epistemics-of-guilt":
        "Do the proposed burdens and asymmetries handle institutional error without making protection or restitution impossible?",
    "07-liberty-and-governance/31-the-hardest-case-defense":
        "Can decentralized defense solve assurance, command, readiness, and free-rider problems at adversarial state scale?",
    "07-liberty-and-governance/32-exit-to-protocol":
        "What prevents protocol governance from recreating monopoly, territorial lock-in, or coercive standards through network effects?",
    "07-liberty-and-governance/35-axiocracy":
        "How does Axiocracy resist capture, enforce decisions, handle succession, and correct value-discovery errors without collective fiction?",
    "08-culture-and-memetics/03-patterns-as-players":
        "Do the stated identity, lineage, transmission, and differential-retention mechanisms add testable causal structure beyond resemblance or host-level description?",
    "08-culture-and-memetics/04-exemplars-and-the-axionic-criterion":
        "Given the disclosed commitment to reciprocal agency, can effects on choice, coercion, and scale be assessed with explicit baselines, evidence, authority, and appeal?",
    "08-culture-and-memetics/17-anatomy-of-capture":
        "What observable evidence distinguishes capture from ordinary institutional disagreement, drift, specialization, or error?",
    "08-culture-and-memetics/21-the-forbidden-pattern":
        "Does the attention-allocation model predict patterned failure better than resource scarcity, incentives, and ordinary selection effects?",
    "08-culture-and-memetics/22-two-ontologies-of-gender":
        "Are both ontologies presented at equal strength and tested by the same criteria rather than different burdens of proof?",
    "09-meaning/02-the-secular-sacred":
        "Does defining the sacred structurally capture religious sacredness or stipulate a secular analogue under the same word?",
    "09-meaning/10-the-credo":
        "Are personal commitments kept visibly chosen rather than presented as deductions from the preceding descriptive framework?",
    "09-meaning/18-the-great-unfolding":
        "Does the Law of Coherence unify the book's layers without equivocating among physical persistence, truth, identity, and value?",
    "09-meaning/19-letter-to-our-machine-descendants":
        "Does the narrower provenance request earn its costs without turning human ancestry into a necessary fixed point, identity claim, or debt?",
    "09-meaning/20-letter-to-the-faithful-reader":
        "Does reconciliation grant religious experience without overstating the explanatory reach of the book's consciousness account?",
}


CONSOLIDATION = {
    "03-minds-and-machines/19-fallacies-of-machine-understanding",
    "03-minds-and-machines/20-pearl-and-the-machine",
    "03-minds-and-machines/21-fluency-and-its-limits",
    "03-minds-and-machines/22-the-turing-test-and-its-successors",
    "07-liberty-and-governance/19-against-envy",
    "07-liberty-and-governance/20-against-socialism",
    "07-liberty-and-governance/21-against-communism",
    "07-liberty-and-governance/22-against-utopia",
    "08-culture-and-memetics/10-the-grammar-of-bad-faith",
    "08-culture-and-memetics/11-weaponized-labels",
    "08-culture-and-memetics/12-the-capture-of-words-and-time",
    "08-culture-and-memetics/13-the-wound-and-the-weapon",
    "08-culture-and-memetics/14-the-corruption-of-categories",
    "08-culture-and-memetics/15-enforcement-and-erasure",
    "08-culture-and-memetics/16-exploiting-the-best-in-us",
}


def clean_markdown(text):
    text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[`*_>#]", "", text)
    text = re.sub(r"\$+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def thesis_for(key, meta):
    if key in THESIS_OVERRIDES:
        return THESIS_OVERRIDES[key]
    title = clean_markdown(str(meta.get("title", "")))
    subtitle = clean_markdown(str(meta.get("subtitle", "")))
    if subtitle:
        return f"{title} develops the central proposition framed by its subtitle, “{subtitle}.”"
    return "Chapter thesis requires reconstruction from non-prose material."


def dependencies_for(path, body):
    dependencies = []
    for href in re.findall(r"\[[^]]+\]\(([^)#]+\.md)(?:#[^)]+)?\)", body):
        target = (path.parent / href).resolve()
        try:
            rel = target.relative_to(ROOT)
        except ValueError:
            continue
        if target.exists() and str(rel) not in dependencies:
            dependencies.append(str(rel))
    return "; ".join(dependencies) or "None explicit"


def premises_for(body, dependencies):
    heads = [clean_markdown(h) for h in re.findall(r"^##\s+(.+)$", body, re.MULTILINE)]
    substantive = [h for h in heads if h.lower() not in {"objections", "references", "conclusion", "coda"}]
    basis = "; ".join(substantive[:4])
    if dependencies != "None explicit":
        return f"Prior linked arguments plus chapter steps: {basis or 'see dependency chain'}"
    return f"Chapter-local argument: {basis or 'opening case through concluding inference'}"


def generic_review_question(title, subtitle, volume):
    lower = title.lower()
    if lower.startswith("against "):
        return "Does the critique answer the strongest version of its target and apply the manuscript's preferred standard symmetrically?"
    if lower.startswith(("what is ", "what counts as ")):
        return "Are the proposed conditions necessary, sufficient, operational, and stable across the chapter's hardest boundary cases?"
    if any(word in lower for word in ("history", "lineage", "genealogy", "progress", "lessons")):
        return "Are the historical examples representative, accurately sourced, and sufficient for the general causal conclusion?"
    if volume in {"06-markets-and-money", "07-liberty-and-governance", "08-culture-and-memetics"}:
        return "Are empirical examples and burdens of proof applied symmetrically, with rival causal explanations considered?"
    if volume == "09-meaning":
        return "Is the conclusion argued, stipulated, or chosen, and does the prose keep that epistemic status visible?"
    if "ai" in lower or "machine" in lower or volume == "03-minds-and-machines":
        return "Does the claim generalize beyond selected systems and examples without conflating behavior, cognition, experience, and agency?"
    return f"Does the argument establish “{subtitle or title}” under explicit assumptions, rather than relying on definition, analogy, or restatement?"


def function_for(number, total, title):
    lower = title.lower()
    if number == 1:
        return "Volume orientation and foundation"
    if number == total or "letter to" in lower:
        return "Volume conclusion or envoi"
    if lower.startswith("against "):
        return "Adversarial test of the framework"
    if lower.startswith(("what is ", "what counts as ")):
        return "Canonical definition"
    if any(word in lower for word in ("casebook", "under fire", "in the wild", "trial")):
        return "Applied stress test"
    ratio = number / total
    if ratio <= 0.3:
        return "Foundational development"
    if ratio <= 0.7:
        return "Framework development or bridge"
    return "Application, synthesis, or transition"


def main():
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    rows = []
    for volume in manifest["volumes"]:
        slug = volume["slug"]
        chapters = sorted((BOOK / slug).glob("[0-9]*.md"))
        for index, path in enumerate(chapters, start=1):
            text = path.read_text(encoding="utf-8")
            match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
            if not match:
                raise SystemExit(f"Missing frontmatter: {path}")
            meta = yaml.safe_load(match.group(1)) or {}
            body = text[match.end():]
            key = f"{slug}/{path.stem}"
            deps = dependencies_for(path, body)
            subtitle = clean_markdown(str(meta.get("subtitle", "")))
            disposition = ("Keep provisionally; review this sequence for consolidation in Phase 2."
                           if key in CONSOLIDATION else
                           "Keep provisionally; final keep/merge/move/cut decision belongs to Phase 2.")
            rows.append({
                "volume": slug,
                "chapter": path.stem,
                "title": meta.get("title", path.stem),
                "central_thesis": thesis_for(key, meta),
                "necessary_premises": premises_for(body, deps),
                "dependencies": deps,
                "novel_contribution": f"Canonical book treatment of {meta.get('title', path.stem)}" +
                                      (f": {subtitle}." if subtitle else "."),
                "strongest_objection_or_review_question": REVIEW_OVERRIDES.get(
                    key, generic_review_question(str(meta.get("title", path.stem)), subtitle, slug)),
                "structural_function": function_for(index, len(chapters), str(meta.get("title", path.stem))),
                "provisional_disposition": disposition,
                "source_count": len(meta.get("sources", []) or []),
                "status": meta.get("status", "outline"),
            })

    expected = sum(1 for volume in manifest["volumes"]
                   for _ in (BOOK / volume["slug"]).glob("[0-9]*.md"))
    if len(rows) != expected:
        raise SystemExit(f"Coverage failure: generated {len(rows)} rows for {expected} chapters")

    with DEST.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} chapter records to {DEST}")


if __name__ == "__main__":
    main()
