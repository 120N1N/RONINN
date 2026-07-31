let selectedEngagement = new URLSearchParams(location.search).get("engagement") || "";
let engagements = [];

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
  if (value.includes("done") || value.includes("ready") || value.includes("pass")) return "green";
  if (value.includes("queued") || value.includes("running")) return "blue";
  if (value.includes("failed") || value.includes("blocked")) return "red";
  if (value.includes("pending") || value.includes("draft")) return "yellow";
  return "black";
}

function statusPill(value) {
  return `<span class="status-pill ${statusClass(value)}">${escapeHtml(value || "-")}</span>`;
}

function api(path) {
  return `${path}?engagement=${encodeURIComponent(selectedEngagement)}`;
}

async function post(path, payload) {
  const res = await fetch(api(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function loadEngagements() {
  const res = await fetch("/api/engagements", { cache: "no-store" });
  const data = await res.json();
  engagements = data.engagements || [];
  if (!selectedEngagement) selectedEngagement = data.default_engagement || engagements[0]?.id || "";
  const select = document.getElementById("engagementSelect");
  select.innerHTML = engagements.map(item => `
    <option value="${escapeHtml(item.id)}" ${item.id === selectedEngagement ? "selected" : ""}>${escapeHtml(item.id)}</option>
  `).join("");
  document.querySelectorAll('.page-nav a[href="/"]').forEach(link => {
    link.href = selectedEngagement ? `/?engagement=${encodeURIComponent(selectedEngagement)}` : "/";
  });
  document.querySelectorAll('.page-nav a[href="/neo4j"]').forEach(link => {
    link.href = selectedEngagement ? `/neo4j?engagement=${encodeURIComponent(selectedEngagement)}` : "/neo4j";
  });
}

async function loadQueue() {
  const res = await fetch(api("/api/run-queue"), { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  renderQueue(await res.json());
}

async function loadCaido() {
  const res = await fetch(api("/api/caido/status"), { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  document.getElementById("caidoStatus").innerHTML = `
    <div class="kv"><span>Mode</span><strong>${escapeHtml(data.mode)}</strong></div>
    <div class="kv"><span>Installed</span><strong>${escapeHtml(data.installed ? "yes" : "no")}</strong></div>
    <div class="kv"><span>Binary</span><strong>${escapeHtml(data.binary || "-")}</strong></div>
    <div class="kv"><span>Proxy</span><strong>${escapeHtml(data.config?.proxy_listen || "-")}</strong></div>
    <pre>${escapeHtml((data.launch_command || []).join(" "))}</pre>
  `;
}

async function loadSafety() {
  const res = await fetch(api("/api/safety/status"), { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  document.getElementById("safetyPolicy").textContent = JSON.stringify(await res.json(), null, 2);
}

async function loadGovernance() {
  const res = await fetch(api("/api/governance/status"), { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  const summary = data.summary || {};
  const roles = Object.keys(data.config?.agent_roles || {}).length;
  document.getElementById("governanceStatus").innerHTML = `
    <div class="kv"><span>Autonomy</span><strong>${escapeHtml(Object.keys(data.config?.autonomy_levels || {}).join(", "))}</strong></div>
    <div class="kv"><span>Roles</span><strong>${escapeHtml(roles)} configured</strong></div>
    <div class="kv"><span>Allowlist</span><strong>${escapeHtml(summary.allow_hosts_count || 0)} hosts</strong></div>
    <div class="kv"><span>Active</span><strong>${escapeHtml(summary.active_tasks || 0)} tasks</strong></div>
    <div class="kv"><span>Retention</span><strong>${escapeHtml(data.config?.data_governance?.retention_days || "-")} days</strong></div>
  `;
}

async function loadReports() {
  const res = await fetch(api("/api/reports"), { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  renderReports(await res.json());
}

function renderQueue(queue) {
  const tasks = queue.tasks || [];
  document.getElementById("commandMeta").textContent = `${selectedEngagement || "-"} | ${tasks.length} queue tasks`;
  document.getElementById("queueList").innerHTML = tasks.map(task => `
    <article class="queue-card">
      <div class="queue-top">
        <div>
          <strong>${escapeHtml(task.label)}</strong>
          <span>${escapeHtml(task.stage)} | ${escapeHtml(task.id)}</span>
          <span>${escapeHtml(task.agent_role || "coordinator")} | ${escapeHtml(task.autonomy_level || (task.active ? "active_requires_approval" : "passive_auto"))}</span>
        </div>
        <div class="queue-state">
          ${statusPill(task.status)}
          ${statusPill(task.approval)}
          ${statusPill(task.validation_gate || "event_ledger")}
        </div>
      </div>
      <code>${escapeHtml((task.command || []).join(" "))}</code>
      ${task.blocked_reason ? `<div class="blocked-reason">${escapeHtml(task.blocked_reason)}</div>` : ""}
      ${task.last_output ? `<details><summary>Last output</summary><pre>${escapeHtml(task.last_output)}</pre></details>` : ""}
      <div class="queue-actions">
        ${(task.active || task.autonomy_level === "active_requires_approval") && task.approval !== "approved" ? `<button data-action="approve" data-task="${escapeHtml(task.id)}" type="button">Approve</button>` : ""}
        <button data-action="run" data-task="${escapeHtml(task.id)}" type="button">Run</button>
      </div>
    </article>
  `).join("") || `<div class="empty padded">No queue tasks yet. Seed the pipeline first.</div>`;
}

function renderReports(data) {
  const reports = data.reports || [];
  document.getElementById("reportList").innerHTML = reports.map(report => `
    <article class="report-card">
      <div>
        <strong>${escapeHtml(report.title || report.id)}</strong>
        <span>${escapeHtml(report.id)} | ${escapeHtml(report.test_id || "-")}</span>
      </div>
      ${statusPill(report.status)}
      <small>${escapeHtml(report.path || "-")}</small>
      ${(report.missing_before_submit || []).length ? `<div class="blocked-reason">${escapeHtml(report.missing_before_submit.join("; "))}</div>` : ""}
    </article>
  `).join("") || `<div class="empty padded">No report lifecycle records yet.</div>`;
}

async function reloadAll() {
  await loadEngagements();
  await Promise.all([loadQueue(), loadCaido(), loadSafety(), loadGovernance(), loadReports()]);
}

document.getElementById("engagementSelect").addEventListener("change", event => {
  selectedEngagement = event.target.value;
  const params = new URLSearchParams(location.search);
  params.set("engagement", selectedEngagement);
  history.replaceState(null, "", `/command?${params.toString()}`);
  reloadAll().catch(err => { document.getElementById("commandMeta").textContent = String(err); });
});

document.getElementById("refreshButton").addEventListener("click", () => {
  reloadAll().catch(err => { document.getElementById("commandMeta").textContent = String(err); });
});

document.getElementById("seedQueue").addEventListener("click", async () => {
  await post("/api/run-queue", { action: "seed" });
  await loadQueue();
});

document.getElementById("runNext").addEventListener("click", async () => {
  await post("/api/run-queue", { action: "run-next" });
  await reloadAll();
});

document.getElementById("queueList").addEventListener("click", async event => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  await post("/api/run-queue", { action: button.dataset.action, task_id: button.dataset.task });
  await reloadAll();
});

document.getElementById("importCaido").addEventListener("click", async () => {
  await post("/api/caido/import", {
    source: "caido",
    file_path: document.getElementById("importFile").value.trim(),
    endpoint_id: document.getElementById("importEndpoint").value.trim(),
    test_id: document.getElementById("importTest").value.trim(),
    limit: 50
  });
  await reloadAll();
});

document.getElementById("createDraft").addEventListener("click", async () => {
  await post("/api/reports", {
    action: "draft",
    test_id: document.getElementById("draftTestId").value.trim(),
    title: document.getElementById("draftTitle").value.trim()
  });
  await reloadAll();
});

reloadAll().catch(err => {
  document.getElementById("commandMeta").textContent = String(err);
});
