const metricGroups = [
  {
    title: "Scope",
    items: [
      ["total_assets", "Assets"],
      ["total_endpoints", "Endpoints"],
      ["tested_endpoints", "Tested"],
      ["not_tested_endpoints", "Not tested"]
    ]
  },
  {
    title: "Testing",
    items: [
      ["planned_tests", "Planned tests"],
      ["planned_angles", "Planned angles"],
      ["tested_angles", "Tested angles"],
      ["creative_ideas", "Creative ideas"]
    ]
  },
  {
    title: "Evidence",
    items: [
      ["evidence_quality_avg", "Quality avg"],
      ["evidence_quality_sufficient", "Sufficient"],
      ["evidence_quality_partial", "Partial"],
      ["evidence_quality_incomplete", "Incomplete"]
    ]
  },
  {
    title: "Judge",
    items: [
      ["judge_avg_score", "Judge avg"],
      ["judge_reportable", "Reportable"],
      ["judge_candidate", "Candidate"],
      ["judge_needs_evidence", "Needs evidence"],
      ["judge_blocked", "Blocked"]
    ]
  },
  {
    title: "Source",
    items: [
      ["source_completeness_avg", "Completeness avg"],
      ["source_files_total", "Files"],
      ["source_files_complete", "Complete"],
      ["source_files_incomplete", "Incomplete"],
      ["source_reviews_missing", "Reviews missing"]
    ]
  },
  {
    title: "Risk",
    items: [
      ["risk_top_score", "Top score"],
      ["risk_avg_score", "Average score"],
      ["risk_priority_p0", "P0"],
      ["risk_priority_p1", "P1"],
      ["risk_priority_p2", "P2"],
      ["risk_priority_p3", "P3"]
    ]
  },
  {
    title: "Domain",
    items: [
      ["domain_depth_avg", "Domain avg"],
      ["domain_checks_complete", "Complete"],
      ["domain_checks_partial", "Partial"],
      ["domain_checks_missing", "Missing"],
      ["domain_wp_score", "WP score"],
      ["domain_onprem_score", "On-prem score"],
      ["domain_mobile_score", "Mobile score"]
    ]
  },
  {
    title: "Flow",
    items: [
      ["open_gaps", "Open gaps"],
      ["active_loops", "Active loops"],
      ["dead_ends_without_decision", "Dead ends no decision"],
      ["confirmed_findings", "Confirmed"],
      ["finding_candidates", "Candidates"]
    ]
  }
];

const activityLanes = [
  { key: "map", label: "Recon / Map" },
  { key: "source", label: "Source" },
  { key: "test", label: "Test / Evidence" },
  { key: "judge", label: "Judge / Domain" },
  { key: "loop", label: "Loop / Report" }
];

let selectedEngagement = new URLSearchParams(location.search).get("engagement") || "";
let engagementList = [];
let currentArtifactKind = "findings";
let currentArtifacts = [];
let searchTimer = null;
let currentAttackGraph = null;

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function metricValue(metrics, key) {
  const value = metrics?.[key];
  return value === undefined || value === null ? 0 : value;
}

function statusClass(status) {
  const value = String(status || "");
  if (value.includes("confirmed") || value.includes("incomplete") || value.includes("critical") || value.includes("rejected")) return "red";
  if (value.includes("candidate") || value.includes("high")) return "orange";
  if (value.includes("secure") || value.includes("sufficient") || value.includes("complete") || value.includes("reportable")) return "green";
  if (value.includes("partial") || value.includes("medium") || value.includes("needs_evidence") || value.includes("inconclusive") || value.includes("attempted") || value.includes("pivot")) return "yellow";
  if (value.includes("blocked") || value.includes("out_of_scope")) return "black";
  if (value.includes("mapped") || value.includes("running") || value.includes("queued") || value.includes("planned")) return "blue";
  return "black";
}

function row(cells) {
  return `<tr>${cells.map(cell => `<td>${cell ?? ""}</td>`).join("")}</tr>`;
}

function tag(value) {
  return `<span class="tag">${escapeHtml(value || "-")}</span>`;
}

function statusPill(value) {
  return `<span class="status-pill ${statusClass(value)}">${escapeHtml(value || "-")}</span>`;
}

function prettyJson(value) {
  return JSON.stringify(value, null, 2);
}

function scoreBar(value) {
  const score = Math.max(0, Math.min(100, Number(value || 0)));
  const tone = score >= 85 ? "good" : score >= 45 ? "warn" : "bad";
  return `
    <div class="score">
      <div class="score-top"><span>${score}</span><span>/100</span></div>
      <div class="score-track ${tone}" style="--pct:${score}%"><span></span></div>
    </div>
  `;
}

function list(items) {
  const clean = (items || []).filter(Boolean);
  if (!clean.length) return `<span class="empty">-</span>`;
  return `<div class="subtle-list">${clean.map(item => `<div>${escapeHtml(item)}</div>`).join("")}</div>`;
}

function eventLane(type) {
  if (/source_|route_source|js_endpoint|openapi|graphql/.test(type)) return "source";
  if (/test_|payload|control_|evidence_added|endpoint_angle_tested/.test(type)) return "test";
  if (/judge|verdict|finding_|domain_/.test(type)) return "judge";
  if (/loop_|creative_|gap_|pivot|report_|operator_note/.test(type)) return "loop";
  return "map";
}

function eventTitle(type) {
  return String(type || "event").replaceAll("_", " ");
}

function eventTime(ts) {
  if (!ts) return "-";
  const date = new Date(ts);
  if (Number.isNaN(date.getTime())) return String(ts).slice(0, 19);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function eventDetail(event) {
  const parts = [
    event.endpoint_id && `endpoint ${event.endpoint_id}`,
    event.method && event.path && `${event.method} ${event.path}`,
    event.asset_id && `asset ${event.asset_id}`,
    event.source_file && `source ${event.source_file}`,
    event.test_id && `test ${event.test_id}`,
    event.angle && `angle ${event.angle}`,
    event.check_id && `check ${event.check_id}`,
    event.domain && `domain ${event.domain}`,
    event.evidence_path && `evidence ${event.evidence_path}`,
    event.review_path && `review ${event.review_path}`,
    event.reason,
    event.next_action
  ].filter(Boolean);
  return parts.slice(0, 2).join(" | ") || event.id || "-";
}

function renderOverview(metrics) {
  const data = [
    ["Endpoints", metricValue(metrics, "total_endpoints"), `${metricValue(metrics, "tested_endpoints")} tested`],
    ["Evidence", metricValue(metrics, "evidence_quality_avg"), `${metricValue(metrics, "evidence_quality_sufficient")} sufficient`],
    ["Judge", metricValue(metrics, "judge_avg_score"), `${metricValue(metrics, "judge_reportable")} reportable`],
    ["Source", metricValue(metrics, "source_completeness_avg"), `${metricValue(metrics, "source_files_incomplete")} incomplete`],
    ["Risk", metricValue(metrics, "risk_top_score"), `P0:${metricValue(metrics, "risk_priority_p0")} P1:${metricValue(metrics, "risk_priority_p1")}`],
    ["Domain", metricValue(metrics, "domain_depth_avg"), `${metricValue(metrics, "domain_checks_missing")} missing`]
  ];

  document.getElementById("overview").innerHTML = data.map(([label, value, sub]) => `
    <div class="overview-card">
      <div class="overview-label">${escapeHtml(label)}</div>
      <div class="overview-value">${escapeHtml(value)}</div>
      <div class="overview-sub">${escapeHtml(sub)}</div>
    </div>
  `).join("");
}

function renderMetrics(metrics) {
  document.getElementById("metrics").innerHTML = metricGroups.map(group => `
    <section class="panel">
      <div class="panel-header compact"><h2>${escapeHtml(group.title)}</h2></div>
      <div class="metric-list">
        ${group.items.map(([key, label]) => `
          <div class="metric-row">
            <div class="metric-label">${escapeHtml(label)}</div>
            <div class="metric-value">${escapeHtml(metricValue(metrics, key))}</div>
          </div>
        `).join("")}
      </div>
    </section>
  `).join("");
}

async function loadEvents() {
  const url = selectedEngagement
    ? `/api/events?engagement=${encodeURIComponent(selectedEngagement)}&limit=50`
    : "/api/events?limit=50";
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function loadArtifacts(kind = currentArtifactKind) {
  currentArtifactKind = kind;
  const url = `/api/artifacts?engagement=${encodeURIComponent(selectedEngagement)}&kind=${encodeURIComponent(kind)}`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  currentArtifacts = data.artifacts || [];
  renderArtifacts();
}

async function loadArtifact(path) {
  const url = `/api/artifact?engagement=${encodeURIComponent(selectedEngagement)}&path=${encodeURIComponent(path)}`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function loadAttackGraph() {
  const url = `/api/attack-graph?engagement=${encodeURIComponent(selectedEngagement)}`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  currentAttackGraph = await res.json();
  renderAttackGraph(currentAttackGraph);
}

async function searchDashboard(query) {
  const trimmed = query.trim();
  const target = document.getElementById("searchResults");
  if (!trimmed) {
    target.hidden = true;
    target.innerHTML = "";
    return;
  }
  const url = `/api/search?engagement=${encodeURIComponent(selectedEngagement)}&q=${encodeURIComponent(trimmed)}&limit=30`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  renderSearchResults(data.results || []);
}

function renderAttackGraph(graph) {
  const stages = graph.stages || [];
  const nodes = graph.nodes || [];
  const paths = graph.paths || [];
  const metrics = graph.metrics || {};
  const byStage = new Map(stages.map(stage => [stage.key, []]));
  nodes.forEach(node => {
    if (!byStage.has(node.stage)) byStage.set(node.stage, []);
    byStage.get(node.stage).push(node);
  });

  const cypherLink = document.getElementById("cypherLink");
  if (cypherLink) {
    cypherLink.href = selectedEngagement
    ? `/api/neo4j/cypher?engagement=${encodeURIComponent(selectedEngagement)}`
    : "/api/neo4j/cypher";
  }

  const openNeo4jLink = document.getElementById("openNeo4jLink");
  if (openNeo4jLink) {
    openNeo4jLink.href = selectedEngagement
      ? `/neo4j?engagement=${encodeURIComponent(selectedEngagement)}`
      : "/neo4j";
  }
  document.querySelectorAll('.page-nav a[href="/neo4j"]').forEach(link => {
    link.href = openNeo4jLink?.href || "/neo4j";
  });
  document.querySelectorAll('.page-nav a[href="/command"]').forEach(link => {
    link.href = selectedEngagement
      ? `/command?engagement=${encodeURIComponent(selectedEngagement)}`
      : "/command";
  });

  const neo = graph.neo4j || {};
  const neoText = neo.configured ? `Neo4j ready: ${neo.database || "neo4j"}` : "Neo4j optional";
  const neo4jStatus = document.getElementById("neo4jStatus");
  if (neo4jStatus) {
    neo4jStatus.textContent = neoText;
    neo4jStatus.className = `count-pill ${neo.configured ? "ready" : ""}`;
  }

  const graphSummary = document.getElementById("graphSummary");
  if (graphSummary) {
    graphSummary.innerHTML = [
      [metrics.attack_paths ?? paths.length, "Attack paths"],
      [metrics.needs_chain_review ?? 0, "Needs chain review"],
      [metrics.needs_evidence ?? 0, "Needs evidence"],
      [metrics.attack_graph_nodes ?? nodes.length, "Graph nodes"]
    ].map(([value, label]) => `
      <div class="summary-card">
        <strong>${escapeHtml(value)}</strong>
        <span>${escapeHtml(label)}</span>
      </div>
    `).join("");
  }

  const chainStrip = document.getElementById("attackChainStrip");
  if (!chainStrip) return;

  chainStrip.innerHTML = stages.map(stage => {
    const count = (byStage.get(stage.key) || []).length;
    return `
      <div class="chain-stage">
        <div class="chain-stage-title">${escapeHtml(stage.label)}</div>
        <div class="chain-stage-count">${count} nodes</div>
      </div>
    `;
  }).join("");

  const graphCanvas = document.getElementById("attackGraphCanvas");
  if (graphCanvas) {
    graphCanvas.innerHTML = `
    <div class="graph-grid">
      ${stages.map(stage => {
        const stageNodes = (byStage.get(stage.key) || []).slice(0, 8);
        return `
          <div class="graph-column">
            <div class="graph-column-title">${escapeHtml(stage.label)}</div>
            ${stageNodes.map(node => `
              <button class="graph-node ${escapeHtml(stage.key)}" type="button" data-attack-node="${escapeHtml(node.id)}">
                <div class="graph-node-title">${escapeHtml(node.label || node.id)}</div>
                <div class="graph-node-meta">${escapeHtml(node.status || "-")}</div>
              </button>
            `).join("") || `<div class="graph-node ${escapeHtml(stage.key)}"><div class="graph-node-title">No node yet</div><div class="graph-node-meta">stage missing</div></div>`}
          </div>
        `;
      }).join("")}
    </div>
  `;
  }

  const pathCount = document.getElementById("attackPathCount");
  if (pathCount) pathCount.textContent = `${paths.length} paths`;
  const pathList = document.getElementById("attackPathList");
  if (!pathList) return;
  pathList.innerHTML = paths.map(path => {
    const pct = Math.max(0, Math.min(100, Number(path.completeness || 0)));
    const missing = (path.missing_stages || []).length ? `Missing: ${(path.missing_stages || []).join(", ")}` : "Complete chain";
    return `
      <button class="attack-path-item" type="button" data-attack-path="${escapeHtml(path.id)}">
        <div class="attack-path-main">
          <span>${escapeHtml(path.endpoint_id || path.id)}</span>
          ${statusPill(path.status || "mapped_only")}
        </div>
        <div class="completion-track" style="--pct:${pct}%"><span></span></div>
        <div class="attack-path-sub">${pct}% complete | ${escapeHtml(path.angle_id || "angle pending")}</div>
        <div class="attack-path-sub">${escapeHtml(missing)}</div>
      </button>
    `;
  }).join("") || `<div class="attack-path-item"><div class="empty">No attack path generated yet.</div></div>`;
}

function renderSearchResults(results) {
  const target = document.getElementById("searchResults");
  target.hidden = false;
  if (!results.length) {
    target.innerHTML = `<div class="search-snippet">No results</div>`;
    return;
  }
  target.innerHTML = results.map((item, index) => `
    <button class="search-item" type="button" data-search-index="${index}">
      <div class="search-title">
        <span>${escapeHtml(item.title || item.id || item.path || "result")}</span>
        ${tag(item.category || item.kind || "result")}
      </div>
      <div class="search-snippet">${escapeHtml(item.path || item.id || item.status || "")}</div>
      <div class="search-snippet">${escapeHtml(item.snippet || "")}</div>
    </button>
  `).join("");
  target.dataset.results = JSON.stringify(results);
}

function renderArtifacts() {
  document.querySelectorAll("#artifactTabs button").forEach(button => {
    button.classList.toggle("active", button.dataset.kind === currentArtifactKind);
  });

  const listEl = document.getElementById("artifactList");
  if (!currentArtifacts.length) {
    listEl.innerHTML = `<div class="artifact-item"><div class="empty">No artifacts in this category</div></div>`;
    document.getElementById("artifactPreview").innerHTML = `<div class="empty">No artifact available.</div>`;
    return;
  }
  listEl.innerHTML = currentArtifacts.map((artifact, index) => `
    <button class="artifact-item" type="button" data-artifact-index="${index}">
      <div class="artifact-title">${escapeHtml(artifact.title || artifact.name || artifact.path)}</div>
      <div class="artifact-path">${escapeHtml(artifact.path)}</div>
      <div class="artifact-meta">${escapeHtml(artifact.status || artifact.kind)} | ${escapeHtml(formatBytes(artifact.size || 0))}</div>
    </button>
  `).join("");
  previewArtifact(currentArtifacts[0].path).catch(err => {
    document.getElementById("artifactPreview").innerHTML = `<div class="empty">${escapeHtml(String(err))}</div>`;
  });
}

function formatBytes(value) {
  const size = Number(value || 0);
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${Math.round(size / 1024)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

async function previewArtifact(path) {
  const data = await loadArtifact(path);
  document.querySelectorAll(".artifact-item").forEach(item => {
    const artifact = currentArtifacts[Number(item.dataset.artifactIndex || -1)];
    item.classList.toggle("active", artifact?.path === path);
  });
  document.getElementById("artifactPreview").innerHTML = `
    <h3>${escapeHtml(data.name || path)}</h3>
    <div class="preview-meta">${escapeHtml(data.path)} | ${escapeHtml(formatBytes(data.size || 0))}${data.truncated ? " | truncated preview" : ""}</div>
    <pre>${escapeHtml(data.text || "Binary or empty file preview is unavailable.")}</pre>
  `;
}

function openDrawer(title, meta, body) {
  document.getElementById("drawerTitle").textContent = title || "Detail";
  document.getElementById("drawerMeta").textContent = meta || "";
  document.getElementById("drawerBody").textContent = typeof body === "string" ? body : prettyJson(body);
  document.getElementById("drawerBackdrop").hidden = false;
  const drawer = document.getElementById("detailDrawer");
  drawer.classList.add("open");
  drawer.setAttribute("aria-hidden", "false");
}

function closeDrawer() {
  document.getElementById("drawerBackdrop").hidden = true;
  const drawer = document.getElementById("detailDrawer");
  drawer.classList.remove("open");
  drawer.setAttribute("aria-hidden", "true");
}

function renderActivity(eventsData) {
  const events = eventsData.events || [];
  window.dashboardEvents = events;
  document.getElementById("activityCount").textContent = `${eventsData.events_total || events.length} events`;

  const header = [
    `<div class="time-head">Time</div>`,
    ...activityLanes.map(lane => `<div class="lane-head">${escapeHtml(lane.label)}</div>`)
  ].join("");

  const board = events.map((event, eventIndex) => {
    const lane = eventLane(event.type);
    return [
      `<div class="time-cell">${escapeHtml(eventTime(event.ts))}<br>${escapeHtml(event.id || "")}</div>`,
      ...activityLanes.map(item => {
        if (item.key !== lane) return `<div class="activity-slot"></div>`;
        return `
          <div class="activity-slot active">
            <div class="activity-card ${item.key}" data-event-index="${eventIndex}">
              <div class="activity-title">
                <span>${escapeHtml(eventTitle(event.type))}</span>
                ${event.status ? statusPill(event.status) : ""}
              </div>
              <div class="activity-detail">${escapeHtml(eventDetail(event))}</div>
            </div>
          </div>
        `;
      })
    ].join("");
  }).join("");

  document.getElementById("activityDiagram").innerHTML = header + (board || `
    <div class="time-cell">-</div>
    <div class="activity-slot"><div class="activity-card map"><div class="activity-title">No activity</div></div></div>
    <div class="activity-slot"></div>
    <div class="activity-slot"></div>
    <div class="activity-slot"></div>
    <div class="activity-slot"></div>
  `);

  document.getElementById("activityTimeline").innerHTML = events.slice().reverse().map(event => {
    const lane = eventLane(event.type);
    const eventIndex = events.indexOf(event);
    return `
      <div class="timeline-item">
        <div class="timeline-time">${escapeHtml(eventTime(event.ts))}<br>${escapeHtml(event.id || "")}</div>
        <div class="timeline-card ${lane}" data-event-index="${eventIndex}">
          <div class="activity-title">
            <span>${escapeHtml(eventTitle(event.type))}</span>
            ${event.status ? statusPill(event.status) : ""}
          </div>
          <div class="activity-detail">${escapeHtml(eventDetail(event))}</div>
        </div>
      </div>
    `;
  }).join("") || `<div class="empty">No activity</div>`;
}

async function loadEngagements() {
  const res = await fetch("/api/engagements", { cache: "no-store" });
  const data = await res.json();
  engagementList = data.engagements || [];
  if (!selectedEngagement) {
    selectedEngagement = data.default_engagement || engagementList[0]?.id || "";
  }

  const select = document.getElementById("engagementSelect");
  select.innerHTML = engagementList.map(item => {
    const selected = item.id === selectedEngagement ? "selected" : "";
    return `<option value="${escapeHtml(item.id)}" ${selected}>${escapeHtml(item.id)}</option>`;
  }).join("");
  select.disabled = engagementList.length === 0;

  document.getElementById("engagements").innerHTML = engagementList.map(item => {
    const metrics = item.metrics || {};
    const findings = (metrics.confirmed_findings || 0) + (metrics.finding_candidates || 0);
    return row([
      `<button class="table-button" type="button" data-engagement="${escapeHtml(item.id)}">${escapeHtml(item.id)}</button>`,
      `<span>${metrics.total_endpoints || 0}</span>`,
      `<span>${metrics.tested_endpoints || 0}</span>`,
      `${metrics.source_completeness_avg || 0}% / ${metrics.source_files_incomplete || 0} missing`,
      `R:${metrics.judge_reportable || 0} C:${metrics.judge_candidate || 0} N:${metrics.judge_needs_evidence || 0}`,
      `${metrics.risk_top_score || 0} / P0:${metrics.risk_priority_p0 || 0} P1:${metrics.risk_priority_p1 || 0}`,
      `${metrics.domain_depth_avg || 0}% / ${metrics.domain_checks_missing || 0} missing`,
      `<span>${findings}</span>`,
      `<span>${metrics.open_gaps || 0}</span>`
    ]);
  }).join("") || row(["-", `<span class="empty">No initialized engagements</span>`, "-", "-", "-", "-", "-", "-", "-"]);
}

async function loadGraph() {
  const url = selectedEngagement
    ? `/api/graph?engagement=${encodeURIComponent(selectedEngagement)}`
    : "/graph_state.json";
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  const state = await res.json();
  const metrics = state.metrics || {};

  document.getElementById("meta").textContent = `${state.engagement_id} | ${state.generated_at}`;
  renderOverview(metrics);
  renderMetrics(metrics);
  await loadArtifacts(currentArtifactKind);
  await loadAttackGraph();

  try {
    renderActivity(await loadEvents());
  } catch (err) {
    document.getElementById("activityCount").textContent = "events unavailable";
    document.getElementById("activityDiagram").innerHTML = `
      <div class="time-head">Time</div>
      ${activityLanes.map(lane => `<div class="lane-head">${escapeHtml(lane.label)}</div>`).join("")}
      <div class="time-cell">-</div>
      <div class="activity-slot">
        <div class="activity-card map">
          <div class="activity-title">Activity unavailable</div>
          <div class="activity-detail">${escapeHtml(String(err))}</div>
        </div>
      </div>
      <div class="activity-slot"></div>
      <div class="activity-slot"></div>
      <div class="activity-slot"></div>
      <div class="activity-slot"></div>
    `;
    document.getElementById("activityTimeline").innerHTML = `<div class="empty">${escapeHtml(String(err))}</div>`;
  }

  document.getElementById("nodes").innerHTML = (state.nodes || []).map(node => row([
    tag(node.type),
    escapeHtml(node.id),
    escapeHtml(node.label),
    statusPill(node.status)
  ])).join("");

  renderDomainDepth(state);
  renderAngles(state);
  renderRiskPriorities(state);
  renderEvidenceJudge(state);
  renderSourceCompleteness(state);
  renderEvidenceReviews(state);
  renderGaps(state);
  renderLoops(state);
}

function renderDomainDepth(state) {
  const latestReview = (state.nodes || []).filter(node => node.type === "domain_depth_review")
    .sort((a, b) => String(a.properties?.ts || "").localeCompare(String(b.properties?.ts || "")))
    .pop();
  const checks = new Map();
  (state.nodes || []).filter(node => node.type === "domain_check")
    .sort((a, b) => String(a.properties?.ts || "").localeCompare(String(b.properties?.ts || "")))
    .forEach(node => checks.set(node.id, node));

  const domains = {};
  Array.from(checks.values()).forEach(node => {
    const domain = node.properties?.domain || "general";
    domains[domain] ||= { total: 0, complete: 0, partial: 0, missing: 0, missingLabels: [] };
    domains[domain].total += 1;
    if (node.status === "domain_complete") domains[domain].complete += 1;
    else if (node.status === "domain_partial") domains[domain].partial += 1;
    else {
      domains[domain].missing += 1;
      domains[domain].missingLabels.push(node.label);
    }
  });

  document.getElementById("domainDepth").innerHTML = Object.entries(domains).map(([domain, item]) => {
    const score = item.total ? Math.round(((item.complete * 100) + (item.partial * 50)) / item.total) : 0;
    const status = score >= 85 && item.missing === 0 ? "domain_complete" : score >= 45 ? "domain_partial" : "domain_incomplete";
    return row([
      tag(domain),
      scoreBar(score),
      statusPill(status),
      `C:${item.complete} P:${item.partial} M:${item.missing}`,
      list(item.missingLabels.slice(0, 3).length ? item.missingLabels.slice(0, 3) : [latestReview?.properties?.review_path])
    ]);
  }).join("") || row(["-", "-", statusPill("No domain depth profile"), "-", `<span class="empty">Run bbf domain-plan</span>`]);
}

function renderAngles(state) {
  document.getElementById("angles").innerHTML = (state.nodes || []).filter(node => node.type === "angle").map(node => row([
    escapeHtml(node.properties?.endpoint_id || "-"),
    escapeHtml(node.label),
    statusPill(node.status),
    escapeHtml(node.properties?.transport || "-"),
    escapeHtml(node.properties?.reason || node.properties?.evidence_path || "-")
  ])).join("") || row(["-", `<span class="empty">No endpoint angles in graph</span>`, "-", "-", "-"]);
}

function renderRiskPriorities(state) {
  const byEndpoint = new Map();
  (state.nodes || []).filter(node => node.type === "risk_priority")
    .sort((a, b) => String(a.properties?.ts || "").localeCompare(String(b.properties?.ts || "")))
    .forEach(node => byEndpoint.set(node.properties?.endpoint_id || node.id, node));

  document.getElementById("riskPriorities").innerHTML = Array.from(byEndpoint.values())
    .sort((a, b) => Number(a.properties?.rank || 9999) - Number(b.properties?.rank || 9999))
    .slice(0, 20)
    .map(node => row([
      escapeHtml(node.properties?.rank ?? "-"),
      escapeHtml(node.properties?.endpoint_id || "-"),
      scoreBar(node.properties?.risk_score ?? 0),
      statusPill(node.properties?.priority || node.status || "")
    ])).join("") || row(["-", "-", "-", statusPill("No risk priorities")]);
}

function renderEvidenceJudge(state) {
  const byTest = new Map();
  (state.nodes || []).filter(node => node.type === "evidence_judge")
    .sort((a, b) => String(a.properties?.ts || "").localeCompare(String(b.properties?.ts || "")))
    .forEach(node => byTest.set(node.properties?.test_id || node.id, node));

  document.getElementById("evidenceJudge").innerHTML = Array.from(byTest.values()).reverse().map(node => row([
    escapeHtml(node.properties?.test_id || "-"),
    scoreBar(node.properties?.score ?? 0),
    statusPill(node.status)
  ])).join("") || row(["-", "-", statusPill("No judge results")]);
}

function renderSourceCompleteness(state) {
  const byRoot = new Map();
  (state.nodes || []).filter(node => node.type === "source_completeness")
    .sort((a, b) => String(a.properties?.ts || "").localeCompare(String(b.properties?.ts || "")))
    .forEach(node => byRoot.set(node.properties?.source_root || node.id, node));

  document.getElementById("sourceCompleteness").innerHTML = Array.from(byRoot.values()).reverse().map(node => row([
    escapeHtml(node.properties?.source_root || "-"),
    scoreBar(node.properties?.score ?? 0),
    statusPill(node.status)
  ])).join("") || row(["-", "-", statusPill("No source completeness reviews")]);
}

function renderEvidenceReviews(state) {
  document.getElementById("evidenceReviews").innerHTML = (state.nodes || []).filter(node => node.type === "evidence_review").map(node => row([
    escapeHtml(node.properties?.test_id || "-"),
    scoreBar(node.properties?.score ?? 0),
    statusPill(node.status)
  ])).join("") || row(["-", "-", statusPill("No evidence reviews")]);
}

function renderGaps(state) {
  document.getElementById("gaps").innerHTML = (state.nodes || []).filter(node => node.type === "gap").map(node => row([
    escapeHtml(node.id),
    escapeHtml(node.label),
    statusPill(node.status)
  ])).join("") || row(["-", `<span class="empty">No gaps in graph</span>`, "-"]);
}

function renderLoops(state) {
  document.getElementById("loops").innerHTML = (state.nodes || []).filter(node => node.type === "loop" && !(node.status || "").startsWith("closed")).map(node => row([
    escapeHtml(node.id),
    statusPill(node.status),
    escapeHtml(node.properties?.next_action || "-")
  ])).join("") || row(["-", `<span class="empty">No active loops</span>`, "-"]);
}

async function load() {
  await loadEngagements();
  if (selectedEngagement || engagementList.length === 0) {
    await loadGraph();
  }
}

document.getElementById("engagementSelect").addEventListener("change", event => {
  selectedEngagement = event.target.value;
  const params = new URLSearchParams(location.search);
  params.set("engagement", selectedEngagement);
  history.replaceState(null, "", `/?${params.toString()}`);
  loadGraph().catch(err => {
    document.getElementById("meta").textContent = String(err);
  });
});

document.getElementById("engagements").addEventListener("click", event => {
  const button = event.target.closest("button[data-engagement]");
  if (!button) return;
  selectedEngagement = button.dataset.engagement;
  const params = new URLSearchParams(location.search);
  params.set("engagement", selectedEngagement);
  history.replaceState(null, "", `/?${params.toString()}`);
  load().catch(err => {
    document.getElementById("meta").textContent = String(err);
  });
});

document.getElementById("refreshButton").addEventListener("click", () => {
  load().catch(err => {
    document.getElementById("meta").textContent = String(err);
  });
});

document.getElementById("artifactTabs").addEventListener("click", event => {
  const button = event.target.closest("button[data-kind]");
  if (!button) return;
  loadArtifacts(button.dataset.kind).catch(err => {
    document.getElementById("artifactPreview").innerHTML = `<div class="empty">${escapeHtml(String(err))}</div>`;
  });
});

document.getElementById("artifactList").addEventListener("click", event => {
  const button = event.target.closest("button[data-artifact-index]");
  if (!button) return;
  const artifact = currentArtifacts[Number(button.dataset.artifactIndex)];
  if (!artifact) return;
  previewArtifact(artifact.path).catch(err => {
    document.getElementById("artifactPreview").innerHTML = `<div class="empty">${escapeHtml(String(err))}</div>`;
  });
});

document.getElementById("activityDiagram").addEventListener("click", event => {
  const card = event.target.closest("[data-event-index]");
  if (!card) return;
  const item = window.dashboardEvents?.[Number(card.dataset.eventIndex)];
  if (!item) return;
  openDrawer(eventTitle(item.type), `${item.id || ""} ${item.ts || ""}`.trim(), item);
});

document.getElementById("activityTimeline").addEventListener("click", event => {
  const card = event.target.closest("[data-event-index]");
  if (!card) return;
  const item = window.dashboardEvents?.[Number(card.dataset.eventIndex)];
  if (!item) return;
  openDrawer(eventTitle(item.type), `${item.id || ""} ${item.ts || ""}`.trim(), item);
});

const attackGraphCanvas = document.getElementById("attackGraphCanvas");
if (attackGraphCanvas) {
  attackGraphCanvas.addEventListener("click", event => {
    const button = event.target.closest("[data-attack-node]");
    if (!button) return;
    const node = (currentAttackGraph?.nodes || []).find(item => item.id === button.dataset.attackNode);
    if (!node) return;
    openDrawer(node.label || node.id, `${node.stage_label || node.stage || ""} ${node.status || ""}`.trim(), node);
  });
}

const attackPathList = document.getElementById("attackPathList");
if (attackPathList) {
  attackPathList.addEventListener("click", event => {
    const button = event.target.closest("[data-attack-path]");
    if (!button) return;
    const path = (currentAttackGraph?.paths || []).find(item => item.id === button.dataset.attackPath);
    if (!path) return;
    openDrawer(path.endpoint_id || path.id, `${path.completeness || 0}% complete`, path);
  });
}

document.getElementById("globalSearch").addEventListener("input", event => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    searchDashboard(event.target.value).catch(err => {
      const target = document.getElementById("searchResults");
      target.hidden = false;
      target.innerHTML = `<div class="search-snippet">${escapeHtml(String(err))}</div>`;
    });
  }, 180);
});

document.getElementById("globalSearch").addEventListener("keydown", event => {
  if (event.key === "Escape") {
    document.getElementById("searchResults").hidden = true;
    event.target.blur();
  }
});

document.getElementById("searchResults").addEventListener("click", event => {
  const button = event.target.closest("button[data-search-index]");
  if (!button) return;
  const results = JSON.parse(document.getElementById("searchResults").dataset.results || "[]");
  const item = results[Number(button.dataset.searchIndex)];
  if (!item) return;
  document.getElementById("searchResults").hidden = true;
  if (item.path) {
    previewArtifact(item.path).catch(() => openDrawer(item.title, item.path, item));
    const artifact = currentArtifacts.find(candidate => candidate.path === item.path);
    if (!artifact && item.kind) {
      loadArtifacts(item.kind).then(() => previewArtifact(item.path)).catch(() => openDrawer(item.title, item.path, item));
    }
  } else {
    openDrawer(item.title, `${item.category || ""} ${item.status || ""}`.trim(), item);
  }
});

document.addEventListener("click", event => {
  const searchShell = event.target.closest(".search-shell");
  if (!searchShell) document.getElementById("searchResults").hidden = true;
});

document.getElementById("drawerClose").addEventListener("click", closeDrawer);
document.getElementById("drawerBackdrop").addEventListener("click", closeDrawer);

load().catch(err => {
  document.getElementById("meta").textContent = String(err);
});

setInterval(load, 5000);
