#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "diagrams" / "hunterflowx.drawio"


STYLE = {
    "title": "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=top;whiteSpace=wrap;fontSize=24;fontStyle=1;fontColor=#1f2937;",
    "subtitle": "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=top;whiteSpace=wrap;fontSize=12;fontColor=#4b5563;",
    "lane": "rounded=1;whiteSpace=wrap;html=1;arcSize=8;strokeColor=#d1d5db;fillColor=#f9fafb;fontColor=#111827;dashed=1;",
    "input": "rounded=1;whiteSpace=wrap;html=1;arcSize=8;strokeColor=#64748b;fillColor=#f1f5f9;fontColor=#0f172a;",
    "gate": "rhombus;whiteSpace=wrap;html=1;strokeColor=#b45309;fillColor=#fef3c7;fontColor=#78350f;",
    "process": "rounded=1;whiteSpace=wrap;html=1;arcSize=8;strokeColor=#2563eb;fillColor=#dbeafe;fontColor=#1e3a8a;",
    "event": "rounded=1;whiteSpace=wrap;html=1;arcSize=8;strokeColor=#7c3aed;fillColor=#ede9fe;fontColor=#4c1d95;",
    "data": "shape=cylinder3d;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;strokeColor=#0f766e;fillColor=#ccfbf1;fontColor=#134e4a;",
    "evidence": "rounded=1;whiteSpace=wrap;html=1;arcSize=8;strokeColor=#15803d;fillColor=#dcfce7;fontColor=#14532d;",
    "verdict": "rounded=1;whiteSpace=wrap;html=1;arcSize=8;strokeColor=#b91c1c;fillColor=#fee2e2;fontColor=#7f1d1d;",
    "dash": "rounded=1;whiteSpace=wrap;html=1;arcSize=8;strokeColor=#0891b2;fillColor=#cffafe;fontColor=#164e63;",
    "warn": "rounded=1;whiteSpace=wrap;html=1;arcSize=8;strokeColor=#dc2626;fillColor=#fee2e2;fontColor=#7f1d1d;",
    "note": "shape=note;whiteSpace=wrap;html=1;backgroundOutline=1;darkOpacity=0.05;strokeColor=#ca8a04;fillColor=#fef9c3;fontColor=#713f12;",
    "small": "rounded=1;whiteSpace=wrap;html=1;arcSize=8;strokeColor=#94a3b8;fillColor=#ffffff;fontColor=#334155;fontSize=11;",
    "edge": "endArrow=block;html=1;rounded=0;strokeWidth=2;strokeColor=#475569;fontColor=#334155;",
    "edge_dashed": "endArrow=block;html=1;rounded=0;strokeWidth=2;strokeColor=#64748b;fontColor=#334155;dashed=1;",
    "edge_green": "endArrow=block;html=1;rounded=0;strokeWidth=2;strokeColor=#16a34a;fontColor=#166534;",
    "edge_red": "endArrow=block;html=1;rounded=0;strokeWidth=2;strokeColor=#dc2626;fontColor=#7f1d1d;",
}


@dataclass
class Node:
    id: str
    label: str
    x: int
    y: int
    w: int
    h: int
    style: str


@dataclass
class Edge:
    source: str
    target: str
    label: str = ""
    style: str = "edge"


class Page:
    def __init__(self, name: str, width: int = 1800, height: int = 1100) -> None:
        self.name = name
        self.width = width
        self.height = height
        self.nodes: list[Node] = []
        self.edges: list[Edge] = []
        self._seq = 2

    def node(self, label: str, x: int, y: int, w: int, h: int, style: str = "process", ident: str | None = None) -> str:
        ident = ident or f"n{self._seq}"
        self._seq += 1
        self.nodes.append(Node(ident, label, x, y, w, h, style))
        return ident

    def edge(self, source: str, target: str, label: str = "", style: str = "edge") -> None:
        self.edges.append(Edge(source, target, label, style))


def html(value: str) -> str:
    return value.replace("\n", "<br>")


def add_cell(root: ET.Element, node: Node) -> None:
    cell = ET.SubElement(
        root,
        "mxCell",
        {
            "id": node.id,
            "value": html(node.label),
            "style": STYLE[node.style],
            "vertex": "1",
            "parent": "1",
        },
    )
    ET.SubElement(
        cell,
        "mxGeometry",
        {
            "x": str(node.x),
            "y": str(node.y),
            "width": str(node.w),
            "height": str(node.h),
            "as": "geometry",
        },
    )


def add_edge(root: ET.Element, edge: Edge, idx: int) -> None:
    cell = ET.SubElement(
        root,
        "mxCell",
        {
            "id": f"e{idx}",
            "value": html(edge.label),
            "style": STYLE[edge.style],
            "edge": "1",
            "parent": "1",
            "source": edge.source,
            "target": edge.target,
        },
    )
    ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})


def page_to_diagram(page: Page) -> ET.Element:
    diagram = ET.Element("diagram", {"id": page.name.replace(" ", "-").lower(), "name": page.name})
    model = ET.SubElement(
        diagram,
        "mxGraphModel",
        {
            "dx": "1600",
            "dy": "900",
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": str(page.width),
            "pageHeight": str(page.height),
            "math": "0",
            "shadow": "0",
        },
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
    for node in page.nodes:
        add_cell(root, node)
    for idx, edge in enumerate(page.edges, 1):
        add_edge(root, edge, idx)
    return diagram


def add_header(page: Page, title: str, subtitle: str) -> None:
    page.node(title, 40, 24, 900, 36, "title")
    page.node(subtitle, 42, 62, 1120, 42, "subtitle")


def overview_page() -> Page:
    p = Page("00 Control Plane Overview")
    add_header(
        p,
        "Hunterflowx - Control Plane",
        "Prinsip inti: AI chat bukan truth. Event, evidence, graph, ledger, dan verdict gate adalah sumber kebenaran.",
    )
    p.node("Input Layer\nAI operator\nHuman operator\nImporter / bridge\nBrowser / Burp evidence", 60, 150, 210, 120, "input", "input")
    p.node("Scope & Safety Gate\nscope.md\nnotes/rules.md\nrate limit\nallowed accounts\nforbidden actions", 330, 140, 230, 140, "gate", "scope")
    p.node("Action Normalizer\nbbf event\nbbf import-reconfw\nbbf pentest-card\nbbf angle-plan\nbbf angle-exec\nbbf evidence-score\nbbf judge\nbbf source-verify\nbbf risk-prioritize\nbbf domain-plan\nbbf domain-verify\nbbf owasp-plan\nmanual notes -> event", 620, 140, 245, 250, "process", "norm")
    p.node("Append-only Ledger\ndata/events.jsonl\nEvery meaningful action becomes durable state", 910, 150, 230, 120, "data", "events")
    p.node("Graph Builder\nscripts/build_graph.py\nnodes, edges, metrics\nplanned vs tested", 1200, 150, 220, 120, "process", "builder")
    p.node("Live Dashboard\nhttp://127.0.0.1:5173\nmulti-engagement selector\ncoverage + gaps", 1490, 150, 220, 120, "dash", "dash")
    p.edge("input", "scope", "authorize first")
    p.edge("scope", "norm", "safe action")
    p.edge("norm", "events", "JSONL event")
    p.edge("events", "builder", "rebuild")
    p.edge("builder", "dash", "graph_state.json")

    p.node("Source Layers\nhunterweb/recon-framework\nGPTxOPUS A01-A10\nsource-grounded test cards\nbrowser/Caido/Burp evidence loop", 80, 360, 280, 240, "small", "sources")
    p.node("Bridge Rule\nExternal output is input only.\nIt cannot become confirmed until it passes final event -> evidence -> verdict.", 420, 385, 300, 160, "note", "bridge_rule")
    p.node("Workflow State\ncoverage-matrix.md\ntest-ledger.md\nnotes/loop/queue.md\nnotes/loop/log.md\npriority-testing-plan.md\ndomain-depth/", 790, 360, 270, 220, "data", "state")
    p.node("Evidence Store\nevidence/burp\nevidence/caido\nevidence/responses\nevidence/screenshots\nevidence/logs\nredacted secrets only", 1130, 360, 270, 240, "evidence", "evidence")
    p.node("Verdict Authority\nconfirmed\nfinding_candidate\ntested_secure\ninconclusive\nblocked/out_of_scope/by_design", 1470, 360, 260, 220, "verdict", "verdict")
    p.edge("sources", "bridge_rule", "methodology + raw output")
    p.edge("bridge_rule", "norm", "converted to events")
    p.edge("events", "state", "human-readable ledger")
    p.edge("state", "evidence", "test must link proof")
    p.edge("evidence", "verdict", "evidence review")
    p.edge("verdict", "events", "verdict_set", "edge_green")

    p.node("Anti-False-Positive Contract\nNo source-only confirmation\nNo scanner-only report\nNo HTTP 200 = impact\nNo dead end disappears\nNo report without evidence", 80, 700, 390, 190, "warn", "contract")
    p.node("End-of-Session Handoff\nEvents written\nEndpoints added\nTests performed\nEvidence saved\nVerdicts changed\nActive loops\nPivots created\nOpen gaps\nNext safest action", 540, 700, 390, 190, "note", "handoff")
    p.node("Recursive Hunting Loop\nrecon -> analyze -> expand -> retest -> repeat\nEndpoint, JS, fingerprint, param, and evidence can reopen loops.", 1000, 700, 390, 190, "process", "loop")
    p.node("Operator View\nDashboard shows what is mapped, planned, tested, source-incomplete, blocked, missing evidence, and still looping.", 1460, 700, 280, 190, "dash", "operator")
    p.edge("contract", "handoff", "quality bar")
    p.edge("handoff", "loop", "next action")
    p.edge("loop", "operator", "visible state")
    p.edge("operator", "input", "continue safely", "edge_dashed")
    return p


def lifecycle_page() -> Page:
    p = Page("01 Engagement Lifecycle")
    add_header(
        p,
        "Engagement Lifecycle",
        "Dari init sampai report: semua tahap harus meninggalkan event, ledger, dan evidence trail.",
    )
    x = [60, 310, 560, 810, 1060, 1310, 1560]
    ids = []
    labels = [
        "1. Init Engagement\nbbf init <program> <target>\ncreates scoped workspace",
        "2. Load Scope\nscope.md\nnotes/rules.md\nrate budget\naccounts",
        "3. Map Surface\nassets\nendpoints\nparams\nJS\nsource routes",
        "4. Plan Tests\npentest-card\npriority plan\nloop queue\ncoverage matrix",
        "5. Execute Safely\nbrowser/Burp\ncontrols\npayload attempts\nread-back",
        "6. Save Evidence\nBurp req/resp\nscreenshots\nresponses\nlogs",
        "7. Verdict/Handoff\nverdict_set\nreport draft\nnext loop\nopen gaps",
    ]
    styles = ["input", "gate", "process", "event", "process", "evidence", "verdict"]
    for i, label in enumerate(labels):
        ids.append(p.node(label, x[i], 170, 190, 130, styles[i], f"s{i}"))
        if i:
            p.edge(ids[i - 1], ids[i], "")

    p.node("Required Before Live Testing\n- scope loaded\n- out-of-scope known\n- rate limit known\n- owned test accounts known\n- forbidden actions known", 90, 420, 360, 190, "gate", "pre")
    p.node("Event Types By Stage\nscope_loaded\nasset_added\nendpoint_discovered\nparam_discovered\ntest_planned\ntest_started\npayload_attempted\ncontrol_request_sent\nevidence_added\nverdict_set", 520, 390, 360, 250, "data", "types")
    p.node("Coverage Review\ncheck_coverage.py answers:\n- total endpoints\n- tested endpoints\n- planned tests\n- evidence missing\n- open gaps\n- active loops\n- dead ends no decision", 950, 390, 360, 250, "dash", "coverage")
    p.node("Stop Condition\nIf scope/session/evidence is missing:\nwrite blocked or inconclusive.\nDo not continue as if testing was complete.", 1380, 420, 330, 190, "warn", "stop")
    p.edge("s1", "pre", "fills")
    p.edge("s3", "types", "creates")
    p.edge("s6", "coverage", "review")
    p.edge("stop", "s2", "fix missing context", "edge_dashed")
    p.edge("coverage", "stop", "gap found")

    p.node("Clean Workspace Partition\nengagements/<program>/<target>/\ndata/\nevidence/\nfindings/\nreports/\nnotes/\nleads/test-cards/\n.private/", 90, 760, 390, 190, "small", "partition")
    p.node("Rule\nThe folder is the memory.\nChat only explains the state; it does not replace the state.", 560, 780, 390, 150, "note", "folder_memory")
    p.node("Report Readiness\nA report starts only after:\n1. impact proven\n2. evidence saved\n3. verdict set\n4. duplicate/known behavior checked\n5. steps reproduce", 1030, 760, 390, 190, "verdict", "ready")
    p.edge("partition", "folder_memory", "durable")
    p.edge("folder_memory", "ready", "evidence-backed")
    return p


def recon_bridge_page() -> Page:
    p = Page("02 Recon Framework Bridge")
    add_header(
        p,
        "Recon Framework Import Bridge",
        "hunterweb/recon-framework tetap berjalan sebagai recon engine, lalu outputnya dinormalisasi menjadi event final.",
    )
    p.node("hunterweb/recon-framework\npolicy-gated recursive recon\nprogram KB validation\nsafe queues\nraw provenance", 80, 150, 300, 170, "input", "reconfw")
    p.node("Collected Inputs\nassets/hosts.jsonl\nassets/services.jsonl\nassets/urls.jsonl\nassets/endpoints.jsonl\nassets/js.jsonl\noutput/live-probes\noutput/mapping\noutput/diff\ncoverage/*.jsonl\nqueues/*.jsonl", 80, 390, 300, 300, "data", "inputs")
    p.node("bbf import-reconfw\nscripts/import_reconfw.py\nparse workspace\nmap records\nwrite events\nrebuild graph", 480, 260, 280, 190, "process", "import")
    p.node("Normalized Events\nasset_added\nendpoint_discovered\nendpoint_verified_reachable\njs_endpoint_extracted\nopenapi_endpoint_imported\ngraphql_operation_imported\nmapping_gap_found\nloop_started\nattack_path_expanded\nsource_runtime_diff_added", 860, 190, 350, 300, "event", "events")
    p.node("Graph Output\nasset nodes\nendpoint nodes\nJS/source nodes\ngap nodes\nloop nodes\nattack path nodes\nmetrics", 1310, 230, 280, 230, "dash", "graph")
    p.edge("reconfw", "inputs", "writes")
    p.edge("inputs", "import", "read")
    p.edge("import", "events", "append")
    p.edge("events", "graph", "build")

    p.node("Import Does Not Confirm\nReachable endpoint != vulnerability\nJS route != exploit\nscanner lead != finding\nall become mapped/planned/gap state only", 450, 600, 370, 180, "warn", "not_confirm")
    p.node("Why This Strengthens AI\nAI can see exactly what was extracted,\nwhat is reachable,\nwhat has gaps,\nand what should be tested next.", 900, 610, 360, 160, "note", "strength")
    p.node("Next Actions\nCreate pentest-card for priority endpoints\nOpen loop for weirdness\nRecord blocked gaps\nRun browser/Burp validation", 1340, 590, 300, 190, "process", "next")
    p.edge("events", "not_confirm", "status discipline")
    p.edge("graph", "strength", "visibility")
    p.edge("strength", "next", "prioritize")
    p.edge("next", "import", "new recon after pivot", "edge_dashed")
    return p


def pentest_bridge_page() -> Page:
    p = Page("03 Methodology Bridge")
    add_header(
        p,
        "Hunterflowx Methodology Bridge",
        "Bridge ini tidak hanya A01/IDOR. Ia memakai hunterweb recon discipline, GPTxOPUS A01-A10, source-grounded test cards, dan evidence discipline.",
    )
    p.node("Source Methodology\n../hunterweb/recon-framework\n../GPTxOPUS\nsource-grounded A01-A10\nmanual test cards\nevidence pack", 70, 150, 330, 260, "input", "pa")
    p.node("Choose Coverage Mode\nfocused bug class\nWeb/App A01-A10\nOWASP API1-API10\nboth profiles\ncreative off-checklist lead", 500, 160, 280, 220, "gate", "class")
    p.node("bbf pentest-card\nsingle card:\nidor, xss, oauth...\na01..a10\napi01..api10\n\nbbf angle-plan\ncore | deep | creative | full\n\nbbf angle-exec\nhttp | browser | burp | caido\n\nbbf evidence-score\nbaseline | mutation | negative control | read-back\n\nbbf judge\nreportability gate\n\nbbf source-verify\nsource completeness\n\nbbf risk-prioritize\nP0/P1 endpoint queue\n\nbbf owasp-plan\nsuite generation:\nweb | api | both\nruns angle-plan full by default", 880, 70, 335, 600, "process", "card")
    p.node("Generated Artifacts\nleads/test-cards/<test-id>.md\nsource-completeness.md\nmulti-angle-coverage.md\ncreative-exploration.md\nowasp-a01-a10-coverage.md\npriority-testing-plan.md\ndata/events.jsonl\ndata/graph_state.json", 1280, 145, 330, 285, "data", "artifacts")
    p.edge("pa", "class", "methodology")
    p.edge("class", "card", "selected class")
    p.edge("card", "artifacts", "writes")

    p.node("Test Card Content\nobjective\nsafe setup\ntest steps\nevidence required\nstop conditions\nnext events\nverdict gate", 80, 560, 310, 220, "small", "content")
    p.node("Queued Work Nodes\nstatus = queued\nplanned_tests from cards\nplanned_angles from angle-plan\ncreative_ideas from hypotheses\nA01-A10/API suite can create 10 or 20 cards\nfull angle-plan creates 22 angles + 10 creative seeds", 490, 520, 340, 260, "event", "queued")
    p.node("Runtime Validation\nbbf angle-exec\nbrowser/Burp/Caido/http\nbaseline request\nsafe variant\nrequest/response evidence\nmanual review before confirmed", 890, 530, 320, 250, "process", "manual")
    p.node("Evidence Quality + Judge + Verdict\nsave request/response/screenshot\nrecord evidence_added\nrun evidence-score\nrun judge\nreportable / candidate / needs evidence\nthen verdict/report gate\nconfirmed only with impact proof", 1290, 520, 360, 300, "verdict", "evverdict")
    p.edge("artifacts", "content", "review")
    p.edge("content", "queued", "visible in graph")
    p.edge("queued", "manual", "execute when ready")
    p.edge("manual", "evverdict", "proof")
    p.edge("evverdict", "pa", "A-to-B chain / next class", "edge_dashed")

    p.node("Important Boundary\nArsenal sources create plans, not findings.\nFinal workflow remains the source of truth:\nevent -> evidence -> verdict.", 570, 840, 520, 140, "note", "boundary")
    p.edge("card", "boundary", "keeps one control plane")
    return p


def recursive_loop_page() -> Page:
    p = Page("04 Recursive Hunting Loop")
    add_header(
        p,
        "Recursive Hunting Loop",
        "Setiap discovery dapat membuka attack path baru. Dead end harus pivot, block, retest, atau close dengan evidence.",
    )
    recon = p.node("Recon\nassets\nendpoints\nJS\nsource routes\nfingerprints\nruntime traffic", 170, 210, 250, 160, "process", "recon")
    analyze = p.node("Analyze\nscope fit\nbusiness impact\nrole/tenant model\nparams\nsink/source\nsibling endpoints", 620, 210, 250, 160, "process", "analyze")
    expand = p.node("Expand\nattack path\npentest-card\nnew loop\nA-to-B signal\nsource/runtime diff", 1070, 210, 250, 160, "event", "expand")
    retest = p.node("Retest\nbaseline\ncontrols\npayload mutation\nread-back\nbrowser/Burp proof", 620, 560, 250, 160, "process", "retest")
    p.edge(recon, analyze)
    p.edge(analyze, expand)
    p.edge(expand, retest)
    p.edge(retest, recon, "new discovery", "edge_dashed")

    p.node("Pivot Sources\nendpoint discovered\nparameter found\nJS hidden route\nGraphQL operation\nfingerprint\nnew feature\nweird error\npartial evidence", 80, 520, 320, 260, "small", "pivot_sources")
    p.node("Dead End Handling\npivot_decision\nstrategy_adjusted\nretest_scheduled\ngap_found\nverdict_set = tested_secure", 1030, 520, 330, 220, "note", "dead")
    p.node("Bad Closure\npayload failed, no bug\nsource looks safe\nscanner found nothing\nAI thinks done", 1430, 520, 270, 190, "warn", "bad")
    p.edge("pivot_sources", recon, "feeds")
    p.edge(retest, "dead", "if no proof")
    p.edge("dead", expand, "next safe move")
    p.edge("bad", "dead", "replace with")

    p.node("Loop State Events\nloop_started\nloop_iteration_started\nattack_path_expanded\ndead_end_recorded\npivot_decision\nretest_scheduled\nloop_closed", 520, 830, 360, 190, "data", "loop_events")
    p.node("Dashboard Signals\nactive_loops\ndead_ends_without_decision\nopen_gaps\nplanned_tests\nevidence_missing", 980, 840, 320, 170, "dash", "signals")
    p.edge("dead", "loop_events", "record")
    p.edge("loop_events", "signals", "graph metrics")
    return p


def verdict_gate_page() -> Page:
    p = Page("05 Verdict And Evidence Gate")
    add_header(
        p,
        "Verdict And Evidence Gate",
        "Tujuannya bukan menemukan banyak klaim, tapi membedakan proof, lead, gap, dan false confidence.",
    )
    p.node("Lead / Hypothesis\nscanner signal\nsource clue\nAI suspicion\npentest-card\nweird response", 70, 160, 280, 170, "input", "lead")
    p.node("Scope Accepted?", 450, 170, 180, 140, "gate", "scope")
    p.node("Runtime Test Done?", 730, 170, 180, 140, "gate", "runtime")
    p.node("Evidence Saved?", 1010, 170, 180, 140, "gate", "ev")
    p.node("Impact Proven?", 1290, 170, 180, 140, "gate", "impact")
    p.node("confirmed\nor\nfinding_candidate", 1560, 165, 180, 150, "verdict", "confirmed")
    p.edge("lead", "scope")
    p.edge("scope", "runtime", "yes")
    p.edge("runtime", "ev", "yes")
    p.edge("ev", "impact", "yes")
    p.edge("impact", "confirmed", "yes", "edge_green")

    p.node("out_of_scope\nblocked", 450, 410, 180, 110, "warn", "scope_no")
    p.node("inconclusive\nor test_planned", 730, 410, 180, 110, "note", "runtime_no")
    p.node("evidence_missing\ncannot confirm", 1010, 410, 180, 110, "warn", "ev_no")
    p.node("tested_secure\nby_design\ninconclusive", 1290, 410, 180, 130, "verdict", "impact_no")
    p.edge("scope", "scope_no", "no", "edge_red")
    p.edge("runtime", "runtime_no", "no", "edge_red")
    p.edge("ev", "ev_no", "no", "edge_red")
    p.edge("impact", "impact_no", "no", "edge_red")

    p.node("Required Evidence Types\nBurp request/response\nbrowser-visible screenshot\nowned-account before/after\nsaved response body\nlab log when authorized", 90, 680, 340, 210, "evidence", "evtypes")
    p.node("Weak Signals To Kill\nHTTP 200 alone\nmissing headers alone\nGraphQL introspection alone\nopen redirect alone\nSSRF DNS-only\nsource maps without secrets\nclient_id alone", 520, 670, 360, 230, "warn", "weak")
    p.node("Evidence Review Event\nevidence_added -> evidence_reviewed -> verdict_set\nThe verdict must reference the proof path.", 970, 700, 340, 150, "event", "evreview")
    p.node("Report Gate\nreport_draft_created only after:\njudge_reportable or accepted exception\nconfirmed/candidate\nrepro steps\nimpact statement\nredacted evidence", 1400, 680, 300, 220, "verdict", "report")
    p.edge("evtypes", "evreview", "saved proof")
    p.edge("weak", "impact_no", "stop or chain")
    p.edge("evreview", "report", "ready")
    return p


def dashboard_model_page() -> Page:
    p = Page("06 Dashboard Data Model")
    add_header(
        p,
        "Dashboard And Data Model",
        "Satu port dashboard membaca semua engagement yang sudah punya graph_state.json.",
    )
    p.node("Engagement Folder\nengagements/<program>/<target>/\ndata/events.jsonl\ndata/graph_state.json\nscope.md\nnotes/\nevidence/", 70, 160, 300, 240, "data", "eng")
    p.node("Events JSONL\nappend-only facts\nid / ts / actor / type\nasset_id / endpoint_id\ntest_id / loop_id\nstatus / evidence path", 470, 170, 300, 220, "data", "events")
    p.node("build_graph.py\nreads events\ncreates nodes\ncreates edges\ncalculates metrics", 870, 190, 260, 180, "process", "build")
    p.node("graph_state.json\nnodes\nedges\nmetrics\ngenerated_at\nengagement_id", 1220, 190, 260, 180, "data", "graph")
    p.node("serve_dashboard.py\n/api/engagements\n/api/graph?engagement=x\nstatic index.html", 1560, 180, 240, 200, "dash", "server")
    p.edge("eng", "events", "contains")
    p.edge("events", "build", "input")
    p.edge("build", "graph", "output")
    p.edge("graph", "server", "served")

    p.node("Node Types\nasset\nendpoint\nparameter\njs\nsource\nsource_completeness\nloop\ntest\nevidence\nverdict\nfinding\ngap\npivot\nattack_path", 90, 580, 260, 320, "small", "nodes")
    p.node("Core Edges\nasset_has_endpoint\nendpoint_has_param\nendpoint_has_test\ntest_has_evidence\ntest_has_verdict\nblocked_by_gap\ncreates_pivot\nloop_expands_to_path", 450, 600, 330, 260, "small", "edges")
    p.node("Metrics\nassets\nendpoints\ntested endpoints\nnot tested\nplanned tests\nsource complete/partial/incomplete\nsource reviews missing\nrisk P0/P1/top score\nevidence quality\njudge reportable/candidate/needs evidence\nconfirmed\ncandidates\ninconclusive\nevidence missing\nopen gaps\nactive loops\ndead ends no decision", 900, 560, 330, 410, "dash", "metrics")
    p.node("Operator Decisions\nWhat is mapped?\nWhat is planned?\nWhat is actually tested?\nWhat lacks evidence?\nWhat should pivot next?", 1370, 610, 320, 220, "note", "decisions")
    p.edge("graph", "nodes", "materializes")
    p.edge("graph", "edges", "relationships")
    p.edge("graph", "metrics", "summary")
    p.edge("metrics", "decisions", "guide")
    return p


def multi_engagement_page() -> Page:
    p = Page("07 Multi Engagement Operations")
    add_header(
        p,
        "Multi-Engagement Operations",
        "Banyak engagement tidak butuh banyak port. Satu dashboard membaca banyak graph_state.json.",
    )
    p.node("One Dashboard Port\nhttp://127.0.0.1:5173\nlocal only\nmulti-engagement selector", 70, 160, 310, 170, "dash", "port")
    p.node("Engagement Roots\nengagements/demo/target-app\nengagements/template/<target>\nengagements/h1/<target>\nengagements/private/<target>", 500, 140, 340, 230, "data", "roots")
    p.node("Each Engagement Owns\nscope/rules\nevents\ncoverage\ntest cards\nevidence\nfindings\nreports\nprivate notes", 960, 140, 300, 230, "data", "owns")
    p.node("Dashboard Indexer\nscan engagements/*/*/data/graph_state.json\nsort by modified time\nserve selected graph", 1380, 160, 340, 170, "process", "indexer")
    p.edge("roots", "owns", "isolated state")
    p.edge("owns", "indexer", "graph state")
    p.edge("indexer", "port", "selector")

    p.node("Recommended Command Flow\nbbf init <program> <target>\ncd engagements/<program>/<target>\nbbf import-reconfw <workspace>\nbbf pentest-card <bug-class|a01|api01>\nbbf angle-plan full\nbbf angle-exec --transport burp|caido|browser\nbbf evidence-score\nbbf judge\nbbf source-verify --source-root <path>\nbbf risk-prioritize --limit 25\nbbf owasp-plan web|api|both\nbbf build\nbbf coverage", 130, 500, 455, 435, "process", "commands")
    p.node("Engagement Separation\nNo cross-target evidence mixing\nNo token leakage between folders\nNo old engagement data in new scope\nArchive when done", 700, 570, 370, 190, "gate", "separate")
    p.node("Scale Pattern\nRun many engagements.\nKeep one dashboard.\nUse separate event ledgers.\nCompare metrics, not chats.", 1210, 570, 370, 190, "note", "scale")
    p.edge("commands", "separate", "discipline")
    p.edge("separate", "scale", "safe scale")
    p.edge("scale", "port", "single view", "edge_dashed")
    return p


def multi_angle_source_page() -> Page:
    p = Page("08 Source To Multi-Angle Chain")
    add_header(
        p,
        "Source-To-Flow, Multi-Angle Testing, And Chaining",
        "Aturan baru: source dibaca satu per satu, dihubungkan ke flow target, lalu setiap endpoint diuji dari banyak angle dan dipakai untuk chaining.",
    )
    p.node("Source Queue\nsource-file-queue.md\nJS / PHP / Python\nconfigs / templates\ncontrollers / models\nroutes / API specs", 60, 150, 280, 210, "data", "queue")
    p.node("One File Gate\nread one file fully\nwrite source-reviews/<file-id>.md\nRESTATE-OK\nno next file before artifact", 430, 150, 290, 210, "gate", "onefile")
    p.node("Flow Extraction\nentrypoints\nroutes\nhandlers\nmiddleware\nservices\nmodels/queries\nexternal calls\nfrontend API calls", 810, 150, 290, 230, "process", "flow")
    p.node("Flow Link Events\nsource_file_read\nsource_flow_linked\nattack_surface_mapped\nendpoint_angle_planned", 1190, 170, 250, 190, "event", "flowevents")
    p.node("Source Completeness + Risk\nbbf source-verify\ninventory important files\nreview artifact check\n\nbbf risk-prioritize\nrank P0/P1 endpoints\nendpoint_prioritized", 1530, 125, 280, 280, "dash", "surface")
    p.edge("queue", "onefile", "select one")
    p.edge("onefile", "flow", "extract")
    p.edge("flow", "flowevents", "record")
    p.edge("flowevents", "surface", "graph")

    p.node("Endpoint Multi-Angle Matrix\ncore 14 angles:\nauthn_session\nauthz_role\nobject_tenant_boundary\ninput_validation\nstate_transition\nbusiness_logic\ndata_exposure\nside_effect_write\nrate_limit_or_race\ncache_cors_redirect\nfile_or_url_handling\nerror_oracle\nsource_runtime_diff\nchain_potential\n\ndeep adds 8 more:\nmethod/content-type\nfield-level auth\nshadow API\nasync job/export\nidempotency/replay\nclient trust\nwebhook/callback\nsearch/filter/pagination", 60, 500, 390, 420, "small", "matrix")
    p.node("Plan Angle\nbbf angle-plan full\nendpoint_angle_planned\nstatus = queued\nplanned_angles must rise\nnot counted as tested\nkeeps untested work visible", 520, 575, 300, 215, "event", "planned")
    p.node("Test Angle\nendpoint_angle_tested\ntest_started\npayload_attempted\ncontrol_request_sent\nevidence_added", 920, 560, 300, 220, "process", "tested")
    p.node("Verdict Per Angle\ntested_secure\nfinding_candidate\nconfirmed\ninconclusive\nblocked\nout_of_scope\nby_design", 1320, 560, 300, 220, "verdict", "angleverdict")
    p.edge("surface", "matrix", "endpoint gets angles")
    p.edge("matrix", "planned", "plan relevant angles")
    p.edge("planned", "tested", "execute safely")
    p.edge("tested", "angleverdict", "evidence gate")

    p.node("Chaining Rule\nprimitive -> capability -> next input\nRecord chain_candidate_added or attack_path_expanded before reporting weak primitives.", 480, 900, 520, 120, "note", "chain")
    p.node("Hard Stop\nNo source-only confirmation.\nNo one-payload endpoint coverage.\nNo moving file-to-file without source review artifact.\nNo mapped-source claim while source-verify reports incomplete.", 1090, 890, 520, 160, "warn", "hardstop")
    p.edge("angleverdict", "chain", "strong signal")
    p.edge("hardstop", "onefile", "enforce", "edge_dashed")
    return p


def creative_lane_page() -> Page:
    p = Page("09 Creative Exploration Lane")
    add_header(
        p,
        "Creative Exploration Lane",
        "Workflow wajib diikuti, tapi AI tetap harus eksploratif: think freely, act safely, record everything.",
    )
    p.node("Trigger Signals\nweird response\nsource/runtime diff\nhidden JS route\nbusiness shortcut\nrole mismatch\nnew feature\nerror oracle\nconfig clue", 70, 160, 300, 240, "input", "signals")
    p.node("Creative Reasoning\npropose uncommon bug class\ninvent new endpoint angle\nconnect weak signals\nask chain question\nsuggest scoped recon pivot", 470, 165, 300, 230, "process", "reason")
    p.node("Safety Gate\nin scope?\nrate safe?\nowned account?\nnon-destructive?\nevidence path known?\nallowed by rules?", 870, 150, 260, 250, "gate", "safety")
    p.node("Record Idea\ncreative_hypothesis_added\ncreative_pivot_added\nchain_candidate_added\nattack_path_expanded", 1230, 180, 300, 190, "event", "record")
    p.node("Convert To Work\nendpoint_angle_planned\ntest_planned\nloop_started\ngap_found\nblocked", 1620, 185, 250, 180, "dash", "convert")
    p.edge("signals", "reason", "observe")
    p.edge("reason", "safety", "filter")
    p.edge("safety", "record", "safe hypothesis")
    p.edge("record", "convert", "make actionable")

    p.node("Allowed Creativity\n- unusual angle selection\n- targeted payload mutation\n- chaining small primitives\n- source/runtime contradiction hunting\n- business context prioritization\n- new recon path inside scope", 120, 560, 420, 230, "note", "allowed")
    p.node("Never Allowed\n- scope bypass\n- destructive proof without permission\n- source-only confirmation\n- skipping source-review artifact\n- hiding failed experiments\n- report without impact/evidence", 700, 560, 420, 230, "warn", "never")
    p.node("Loop Back\nCreative idea must become one of:\nplanned test\nendpoint angle\nchain candidate\npivot\ngap/blocker\nor closed rationale", 1280, 560, 420, 230, "process", "loopback")
    p.edge("allowed", "reason", "feeds creativity", "edge_dashed")
    p.edge("never", "safety", "guardrail", "edge_red")
    p.edge("loopback", "signals", "new discovery", "edge_dashed")
    return p


def build() -> None:
    pages = [
        overview_page(),
        lifecycle_page(),
        recon_bridge_page(),
        pentest_bridge_page(),
        recursive_loop_page(),
        verdict_gate_page(),
        dashboard_model_page(),
        multi_engagement_page(),
        multi_angle_source_page(),
        creative_lane_page(),
    ]
    mxfile = ET.Element(
        "mxfile",
        {
            "host": "app.diagrams.net",
            "modified": "2026-05-18T00:00:00.000Z",
            "agent": "Codex",
            "version": "24.7.17",
            "type": "device",
        },
    )
    for page in pages:
        mxfile.append(page_to_diagram(page))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(mxfile).write(OUT, encoding="utf-8", xml_declaration=True)
    print(OUT)
    print(f"pages={len(pages)}")
    print(f"cells={sum(2 + len(p.nodes) + len(p.edges) for p in pages)}")


if __name__ == "__main__":
    build()
