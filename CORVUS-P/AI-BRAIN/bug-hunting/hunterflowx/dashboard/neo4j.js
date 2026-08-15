let selectedEngagement = new URLSearchParams(location.search).get("engagement") || "";
let engagementList = [];
let attackGraph = null;
let selectedPathId = "";
let selectedNodeId = "";
let graphSearchTimer = null;
const visibleStages = new Set();

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function statusClass(status) {
  const value = String(status || "");
  if (value.includes("confirmed") || value.includes("incomplete") || value.includes("critical") || value.includes("rejected")) return "red";
  if (value.includes("candidate") || value.includes("high")) return "orange";
  if (value.includes("secure") || value.includes("sufficient") || value.includes("complete") || value.includes("reportable")) return "green";
  if (value.includes("partial") || value.includes("medium") || value.includes("needs") || value.includes("inconclusive") || value.includes("attempted")) return "yellow";
  if (value.includes("blocked") || value.includes("out_of_scope")) return "black";
  if (value.includes("mapped") || value.includes("running") || value.includes("queued") || value.includes("planned") || value.includes("inferred")) return "blue";
  return "black";
}

function statusPill(value) {
  return `<span class="status-pill ${statusClass(value)}">${escapeHtml(value || "-")}</span>`;
}

const STAGE_INFO = {
  js_file: {
    title: "Source / JS File",
    meaning: "Where the route or behavior was discovered from. This should point to a reviewed file, JS bundle, or source artifact.",
    risk: "If this is missing, the route may be runtime-only and source coverage is incomplete.",
    next: "Run source-verify, read the missing file one by one, then link source_flow_linked."
  },
  api_route: {
    title: "API Route",
    meaning: "The reachable endpoint or route being evaluated.",
    risk: "This is the central target surface for the path.",
    next: "Confirm method/path/base URL and map params, roles, and runtime evidence."
  },
  param: {
    title: "Parameter",
    meaning: "The request object, route parameter, query parameter, body field, or file input that can influence behavior.",
    risk: "Missing params make the angle too generic and weaken payload strategy.",
    next: "Map request fields from source, JS, OpenAPI, Burp/Caido, or browser traffic."
  },
  auth_role: {
    title: "Auth Role",
    meaning: "The account, role, tenant, session, or privilege boundary needed to test the route correctly.",
    risk: "Without role context, IDOR/BAC and ownership tests are easy to misjudge.",
    next: "Add owned account role/session context before active testing."
  },
  test_angle: {
    title: "Test Angle",
    meaning: "The concrete security angle queued or tested for this route.",
    risk: "If this is missing, the path is mapped but not operationalized into a test.",
    next: "Run angle-plan full or create a focused test card."
  },
  chaining: {
    title: "Chaining",
    meaning: "The impact path that connects this primitive to a higher-value bug or business impact.",
    risk: "A primitive without chain reasoning often becomes a weak or non-reportable finding.",
    next: "Review source/runtime pivots and add chain_candidate_added or attack_path_expanded."
  },
  evidence: {
    title: "Evidence",
    meaning: "Saved proof from request/response, browser, Burp, Caido, read-back, or evidence review.",
    risk: "Without evidence, this path is only a hypothesis.",
    next: "Execute/import evidence, then run evidence-score."
  },
  finding: {
    title: "Finding",
    meaning: "The reportability state of the path after evidence and judge review.",
    risk: "Not reportable until judge/fresh repro/proof gates are satisfied.",
    next: "Run judge and report lifecycle only after evidence is sufficient."
  }
};

const STATUS_INFO = {
  source_incomplete: "Source linkage is incomplete. Read and review the source artifact before trusting this path.",
  needs_context: "More context is required, usually auth role, owned account, tenant, or session details.",
  needs_chain_review: "The primitive exists, but the impact chain has not been reviewed.",
  evidence_incomplete: "Evidence is missing or not strong enough for a finding.",
  not_reportable_yet: "The path is not ready for report submission.",
  queued: "The task or angle is planned but not executed yet.",
  mapped_only: "The surface is mapped, but no testing evidence exists yet.",
  mapped_static: "The item was discovered from static/source context.",
  inferred: "The item is inferred and should be confirmed with source/runtime proof.",
  finding_candidate: "Potential finding. It still needs judge/fresh repro before final report.",
  confirmed: "Confirmed finding state, assuming evidence and judge events support it.",
  judge_reportable: "Evidence judge says this can proceed toward report.",
  tested_secure: "A negative result was recorded for the tested angle."
};

function formatMetric(value) {
  if (value === undefined || value === null) return "0";
  return String(value);
}

function graphUrl(path) {
  return selectedEngagement ? `${path}?engagement=${encodeURIComponent(selectedEngagement)}` : path;
}

async function loadEngagements() {
  const res = await fetch("/api/engagements", { cache: "no-store" });
  const data = await res.json();
  engagementList = data.engagements || [];
  if (!selectedEngagement) selectedEngagement = data.default_engagement || engagementList[0]?.id || "";
  const select = document.getElementById("engagementSelect");
  select.innerHTML = engagementList.map(item => `
    <option value="${escapeHtml(item.id)}" ${item.id === selectedEngagement ? "selected" : ""}>${escapeHtml(item.id)}</option>
  `).join("");
  select.disabled = engagementList.length === 0;
}

async function loadGraph() {
  const graphRes = await fetch(graphUrl("/api/attack-graph"), { cache: "no-store" });
  if (!graphRes.ok) throw new Error(await graphRes.text());
  attackGraph = await graphRes.json();
  if (!visibleStages.size) {
    (attackGraph.stages || []).forEach(stage => visibleStages.add(stage.key));
  }

  const cypherRes = await fetch(`${graphUrl("/api/neo4j/cypher")}`, { cache: "no-store" });
  document.getElementById("cypherPreview").value = cypherRes.ok ? await cypherRes.text() : await cypherRes.text();
  renderGraph();
}

function currentQuery() {
  return document.getElementById("graphSearch").value.trim().toLowerCase();
}

function pathNodeIds(path) {
  return new Set(Object.values(path?.nodes || {}).filter(Boolean));
}

function nodeMatches(node, query) {
  if (!query) return true;
  return JSON.stringify(node).toLowerCase().includes(query);
}

function selectedPath() {
  return (attackGraph?.paths || []).find(path => path.id === selectedPathId);
}

function nodeById(id) {
  return (attackGraph?.nodes || []).find(item => item.id === id);
}

function stageLabel(stage) {
  return STAGE_INFO[stage]?.title || (attackGraph?.stages || []).find(item => item.key === stage)?.label || stage || "Unknown";
}

function statusMeaning(status) {
  return STATUS_INFO[status] || "Review this status against the event ledger and saved evidence.";
}

function pathStageNodes(path) {
  const nodes = path?.nodes || {};
  return (attackGraph?.stages || []).map(stage => ({
    key: stage.key,
    label: stage.label,
    node: nodeById(nodes[stage.key]),
    missing: (path?.missing_stages || []).includes(stage.key)
  }));
}

function relatedPathsForNode(nodeId) {
  if (!nodeId) return [];
  return (attackGraph?.paths || []).filter(path => Object.values(path.nodes || {}).includes(nodeId));
}

function firstMissingStage(path) {
  const missing = path?.missing_stages || [];
  const preferred = ["js_file", "auth_role", "test_angle", "chaining", "evidence", "finding", "param", "api_route"];
  return preferred.find(stage => missing.includes(stage)) || missing[0] || "";
}

function nextActionForPath(path) {
  const stage = firstMissingStage(path);
  const endpoint = path?.endpoint_id || "<endpoint-id>";
  const angle = path?.angle_id || "<angle-id>";
  const test = path?.test_id || "<test-id>";
  const map = {
    js_file: {
      title: "Complete source mapping",
      command: "bbf source-verify --queue-missing",
      detail: "Read the missing source/JS file one by one, then link file -> flow -> endpoint."
    },
    auth_role: {
      title: "Add auth context",
      command: `bbf event endpoint_role_inferred --endpoint-id ${endpoint} --role owned-account-role-tbd --status needs_context`,
      detail: "Define owned account, role, tenant, or session context before active testing."
    },
    test_angle: {
      title: "Create angle plan",
      command: `bbf angle-plan full --endpoint-id ${endpoint}`,
      detail: "Turn the route into concrete multi-angle testing, not a generic idea."
    },
    chaining: {
      title: "Review chain potential",
      command: `bbf event chain_candidate_added --endpoint-id ${endpoint} --angle-id ${angle} --status needs_chain_review`,
      detail: "Connect the primitive to impact or record why it cannot chain."
    },
    evidence: {
      title: "Collect evidence",
      command: `bbf angle-exec --endpoint-id ${endpoint} --allow-active`,
      detail: "Execute through browser/Burp/Caido/http after policy and approval, or import proxy history."
    },
    finding: {
      title: "Judge reportability",
      command: test ? `bbf judge --test-id ${test}` : `bbf judge --endpoint-id ${endpoint}`,
      detail: "Run evidence judge and fresh repro before report promotion."
    }
  };
  return map[stage] || {
    title: "Review path manually",
    command: "bbf coverage",
    detail: "The path looks structurally complete or needs manual review against the event ledger."
  };
}

function propertyRows(properties) {
  const entries = Object.entries(properties || {}).filter(([, value]) => value !== "" && value !== null && value !== undefined);
  if (!entries.length) return `<div class="empty">No extra properties.</div>`;
  return entries.map(([key, value]) => `
    <div class="kv wide">
      <span>${escapeHtml(key)}</span>
      <strong>${escapeHtml(typeof value === "object" ? JSON.stringify(value) : value)}</strong>
    </div>
  `).join("");
}

function proofChecklist(path) {
  const missing = new Set(path?.missing_stages || []);
  const checks = [
    ["Source linked", !missing.has("js_file")],
    ["Route mapped", !missing.has("api_route")],
    ["Params known", !missing.has("param")],
    ["Auth context known", !missing.has("auth_role")],
    ["Angle planned/tested", !missing.has("test_angle")],
    ["Chain reviewed", !missing.has("chaining")],
    ["Evidence saved", !missing.has("evidence")],
    ["Finding judged", !missing.has("finding")]
  ];
  return checks.map(([label, ok]) => `
    <div class="proof-item ${ok ? "ok" : "missing"}">
      <span>${ok ? "OK" : "GAP"}</span>
      <strong>${escapeHtml(label)}</strong>
    </div>
  `).join("");
}

function renderGraph() {
  if (!attackGraph) return;
  const stages = attackGraph.stages || [];
  const nodes = attackGraph.nodes || [];
  const paths = attackGraph.paths || [];
  const metrics = attackGraph.metrics || {};
  const query = currentQuery();
  const focusPath = selectedPath();
  const focusIds = pathNodeIds(focusPath);
  const pathOnly = document.getElementById("pathOnly").checked && focusPath;

  document.getElementById("graphMeta").textContent = `${attackGraph.engagement_id || selectedEngagement} | ${attackGraph.chain}`;
  document.getElementById("cypherLink").href = graphUrl("/api/neo4j/cypher");
  document.querySelectorAll('.page-nav a[href="/"]').forEach(link => {
    link.href = selectedEngagement ? `/?engagement=${encodeURIComponent(selectedEngagement)}` : "/";
  });
  document.querySelectorAll('.page-nav a[href="/command"]').forEach(link => {
    link.href = selectedEngagement ? `/command?engagement=${encodeURIComponent(selectedEngagement)}` : "/command";
  });
  const neo = attackGraph.neo4j || {};
  const neoStatus = document.getElementById("neo4jStatus");
  neoStatus.textContent = neo.configured ? `Neo4j ready: ${neo.database || "neo4j"}` : "Neo4j optional";
  neoStatus.className = `count-pill ${neo.configured ? "ready" : ""}`;

  document.getElementById("graphMetrics").innerHTML = [
    ["Paths", metrics.attack_paths ?? paths.length],
    ["Nodes", metrics.attack_graph_nodes ?? nodes.length],
    ["Edges", metrics.attack_graph_edges ?? 0],
    ["Needs chain", metrics.needs_chain_review ?? 0],
    ["Needs evidence", metrics.needs_evidence ?? 0],
    ["Needs auth", metrics.needs_auth_context ?? 0]
  ].map(([label, value]) => `
    <div class="summary-card compact">
      <strong>${escapeHtml(formatMetric(value))}</strong>
      <span>${escapeHtml(label)}</span>
    </div>
  `).join("");

  document.getElementById("stageStrip").innerHTML = stages.map(stage => {
    const count = nodes.filter(node => node.stage === stage.key).length;
    return `<span>${escapeHtml(stage.label)} <strong>${count}</strong></span>`;
  }).join("");

  document.getElementById("stageFilters").innerHTML = stages.map(stage => `
    <label class="check-row">
      <input type="checkbox" data-stage="${escapeHtml(stage.key)}" ${visibleStages.has(stage.key) ? "checked" : ""}>
      <span>${escapeHtml(stage.label)}</span>
    </label>
  `).join("");

  const filteredPaths = paths.filter(path => !query || JSON.stringify(path).toLowerCase().includes(query));
  document.getElementById("pathCount").textContent = `${filteredPaths.length} paths`;
  document.getElementById("graphPathList").innerHTML = filteredPaths.map(path => {
    const pct = Math.max(0, Math.min(100, Number(path.completeness || 0)));
    return `
      <button class="graph-path-row ${path.id === selectedPathId ? "active" : ""}" type="button" data-path-id="${escapeHtml(path.id)}">
        <span>${escapeHtml(path.endpoint_id || path.id)}</span>
        ${statusPill(path.status || "mapped_only")}
        <small>${pct}% | ${escapeHtml(path.angle_id || "angle pending")}</small>
      </button>
    `;
  }).join("") || `<div class="empty padded">No path matches the current filter.</div>`;

  const grouped = new Map(stages.map(stage => [stage.key, []]));
  nodes.forEach(node => {
    if (!visibleStages.has(node.stage)) return;
    if (pathOnly && !focusIds.has(node.id)) return;
    if (!pathOnly && !nodeMatches(node, query)) return;
    if (!grouped.has(node.stage)) grouped.set(node.stage, []);
    grouped.get(node.stage).push(node);
  });

  document.getElementById("neo4jCanvas").innerHTML = `
    <div class="neo4j-stage-grid" style="--stage-count:${Math.max(1, stages.filter(stage => visibleStages.has(stage.key)).length)}">
      ${stages.filter(stage => visibleStages.has(stage.key)).map(stage => {
        const stageNodes = grouped.get(stage.key) || [];
        return `
          <section class="neo4j-stage-column">
            <div class="neo4j-stage-heading">
              <span>${escapeHtml(stage.label)}</span>
              <strong>${stageNodes.length}</strong>
            </div>
            <div class="neo4j-node-list">
              ${stageNodes.map(node => {
                const focus = focusIds.has(node.id) ? "focus" : "";
                const active = node.id === selectedNodeId ? "active" : "";
                return `
                  <button class="neo4j-node ${escapeHtml(node.stage)} ${focus} ${active}" type="button" data-node-id="${escapeHtml(node.id)}">
                    <span>${escapeHtml(node.label || node.id)}</span>
                    <small>${escapeHtml(node.status || "-")}</small>
                  </button>
                `;
              }).join("") || `<div class="empty stage-empty">No nodes</div>`}
            </div>
          </section>
        `;
      }).join("")}
    </div>
  `;

  renderInspector();
}

function renderInspector() {
  const node = (attackGraph?.nodes || []).find(item => item.id === selectedNodeId);
  const path = selectedPath();
  const body = document.getElementById("graphInspector");
  if (!node && !path) {
    body.innerHTML = `<div class="empty">Select a node or path to inspect it.</div>`;
    return;
  }
  const pathAction = nextActionForPath(path);
  const pathRows = pathStageNodes(path);
  const relatedPaths = relatedPathsForNode(node?.id);
  const nodeStage = node ? STAGE_INFO[node.stage] || {} : {};
  body.innerHTML = `
    ${path ? `
      <section class="inspector-section">
        <div class="inspector-hero">
          <div>
            <span class="inspector-kicker">Selected Path</span>
            <h3>${escapeHtml(path.endpoint_id || path.id)}</h3>
            <p>${escapeHtml(path.angle_id || "Angle not linked yet")}</p>
          </div>
          ${statusPill(path.status || "mapped_only")}
        </div>
        <div class="readiness-card">
          <div class="readiness-top">
            <strong>${escapeHtml(path.completeness || 0)}%</strong>
            <span>Path completeness</span>
          </div>
          <div class="score-track ${Number(path.completeness || 0) >= 80 ? "good" : Number(path.completeness || 0) >= 50 ? "warn" : "bad"}">
            <span style="--pct:${Math.max(0, Math.min(100, Number(path.completeness || 0)))}%"></span>
          </div>
        </div>
        <div class="next-action-card">
          <span>Recommended next action</span>
          <strong>${escapeHtml(pathAction.title)}</strong>
          <p>${escapeHtml(pathAction.detail)}</p>
          <code>${escapeHtml(pathAction.command)}</code>
        </div>
        <div class="proof-grid">
          ${proofChecklist(path)}
        </div>
        <div class="chain-detail">
          ${pathRows.map(row => `
            <div class="chain-detail-row ${row.missing ? "missing" : "ok"}">
              <div>
                <span>${escapeHtml(row.label)}</span>
                <strong>${escapeHtml(row.node?.label || `${row.label} missing`)}</strong>
                <small>${escapeHtml(row.node?.id || "no node linked")}</small>
              </div>
              ${statusPill(row.node?.status || (row.missing ? "missing" : "linked"))}
            </div>
          `).join("")}
        </div>
        <div class="inspector-actions">
          <button data-graph-action="queue_angle_plan" type="button">Queue Angle Plan</button>
          <button data-graph-action="queue_evidence_score" type="button">Queue Evidence Score</button>
          <button data-graph-action="queue_report" type="button">Queue Report Review</button>
          <button data-graph-action="mark_gap" type="button">Mark Gap</button>
        </div>
      </section>
    ` : ""}
    ${node ? `
      <section class="inspector-section">
        <div class="inspector-hero node-hero">
          <div>
            <span class="inspector-kicker">Selected Node</span>
            <h3>${escapeHtml(node.label || node.id)}</h3>
            <p>${escapeHtml(stageLabel(node.stage))}</p>
          </div>
          ${statusPill(node.status || "-")}
        </div>
        <div class="explain-card">
          <span>What this means</span>
          <p>${escapeHtml(nodeStage.meaning || "This node is part of the source-to-finding attack graph.")}</p>
        </div>
        <div class="explain-card">
          <span>Why it matters</span>
          <p>${escapeHtml(nodeStage.risk || statusMeaning(node.status))}</p>
        </div>
        <div class="explain-card">
          <span>Next step</span>
          <p>${escapeHtml(nodeStage.next || "Use the linked path and event ledger to decide the next concrete task.")}</p>
        </div>
        <div class="kv"><span>Node ID</span><strong>${escapeHtml(node.id)}</strong></div>
        <div class="kv"><span>Status note</span><strong>${escapeHtml(statusMeaning(node.status))}</strong></div>
        <div class="kv"><span>Related paths</span><strong>${escapeHtml(relatedPaths.length)}</strong></div>
        <div class="property-panel">
          <h3>Properties</h3>
          ${propertyRows(node.properties)}
        </div>
        ${relatedPaths.length ? `
          <div class="related-paths">
            <h3>Related Paths</h3>
            ${relatedPaths.slice(0, 6).map(item => `
              <button type="button" class="related-path" data-path-id="${escapeHtml(item.id)}">
                <strong>${escapeHtml(item.endpoint_id || item.id)}</strong>
                <span>${escapeHtml(item.angle_id || "angle pending")} | ${escapeHtml(item.completeness || 0)}%</span>
              </button>
            `).join("")}
          </div>
        ` : ""}
        <div class="inspector-actions">
          <button data-graph-action="queue_angle_plan" type="button">Queue From Node</button>
          <button data-graph-action="mark_gap" type="button">Mark Node Gap</button>
        </div>
        <details class="raw-details">
          <summary>Raw node data</summary>
          <pre>${escapeHtml(JSON.stringify(node, null, 2))}</pre>
        </details>
      </section>
    ` : ""}
  `;
}

async function postGraphAction(action) {
  const res = await fetch(graphUrl("/api/neo4j/action"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action,
      node_id: selectedNodeId,
      path_id: selectedPathId,
      reason: "Marked from Neo4j graph inspector"
    })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function load() {
  await loadEngagements();
  await loadGraph();
}

document.getElementById("engagementSelect").addEventListener("change", event => {
  selectedEngagement = event.target.value;
  selectedPathId = "";
  selectedNodeId = "";
  const params = new URLSearchParams(location.search);
  params.set("engagement", selectedEngagement);
  history.replaceState(null, "", `/neo4j?${params.toString()}`);
  loadGraph().catch(err => {
    document.getElementById("graphMeta").textContent = String(err);
  });
});

document.getElementById("refreshButton").addEventListener("click", () => {
  load().catch(err => {
    document.getElementById("graphMeta").textContent = String(err);
  });
});

document.getElementById("graphSearch").addEventListener("input", () => {
  clearTimeout(graphSearchTimer);
  graphSearchTimer = setTimeout(renderGraph, 120);
});

document.getElementById("pathOnly").addEventListener("change", renderGraph);

document.getElementById("stageFilters").addEventListener("change", event => {
  const input = event.target.closest("input[data-stage]");
  if (!input) return;
  if (input.checked) visibleStages.add(input.dataset.stage);
  else visibleStages.delete(input.dataset.stage);
  renderGraph();
});

document.getElementById("graphPathList").addEventListener("click", event => {
  const button = event.target.closest("button[data-path-id]");
  if (!button) return;
  selectedPathId = button.dataset.pathId;
  selectedNodeId = "";
  renderGraph();
});

document.getElementById("neo4jCanvas").addEventListener("click", event => {
  const button = event.target.closest("button[data-node-id]");
  if (!button) return;
  selectedNodeId = button.dataset.nodeId;
  renderGraph();
});

document.getElementById("graphInspector").addEventListener("click", async event => {
  const related = event.target.closest("button.related-path[data-path-id]");
  if (related) {
    selectedPathId = related.dataset.pathId;
    selectedNodeId = "";
    renderGraph();
    return;
  }
  const button = event.target.closest("button[data-graph-action]");
  if (!button) return;
  const original = button.textContent;
  button.textContent = "Queued";
  try {
    await postGraphAction(button.dataset.graphAction);
  } catch (err) {
    button.textContent = "Failed";
    setTimeout(() => { button.textContent = original; }, 1400);
    return;
  }
  setTimeout(() => { button.textContent = original; }, 1000);
});

document.getElementById("copyCypher").addEventListener("click", async event => {
  const text = document.getElementById("cypherPreview").value;
  try {
    await navigator.clipboard.writeText(text);
    event.target.textContent = "Copied";
    setTimeout(() => { event.target.textContent = "Copy"; }, 900);
  } catch {
    event.target.textContent = "Select text";
    setTimeout(() => { event.target.textContent = "Copy"; }, 1200);
  }
});

load().catch(err => {
  document.getElementById("graphMeta").textContent = String(err);
});
