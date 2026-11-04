(() => {
  "use strict";
  const data = window.XDCT_DEMO;
  const changes = data.diff.changes;
  const labels = {direction: "方向 / direction", resolved_type: "类型 / resolved_type", bitstream_width: "位宽 / bitstream_width", signed: "符号 / signed", interface_type: "接口 / interface_type", modport: "modport", storage: "存储 / storage", declaration_order: "顺序 / declaration_order", kind: "端口种类 / kind"};
  const properties = Object.keys(labels);
  const list = document.getElementById("change-list");
  let filter = "all";
  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function declaration(port) {
    if (!port) return "<absent>";
    if (port.kind === "interface") return `${port.interface_type}${port.modport ? "." + port.modport : ""} ${port.name}`;
    return `${port.direction} ${port.resolved_type} ${port.name}`;
  }
  function display(value) { return value === null || value === undefined ? "—" : String(value); }
  function snapshot(port, after) {
    const node = element("div", `port-snapshot${after ? " after" : ""}`);
    node.append(element("span", "micro", after ? "AFTER / CL 123456" : "BEFORE / CL 123450"));
    node.append(element("code", `declaration${port ? "" : " absent"}`, declaration(port)));
    if (port) node.append(element("p", "port-meta", `width ${display(port.bitstream_width)} · order ${port.declaration_order} · ${port.kind === "interface" ? "interface" : `${port.storage} · ${port.signed ? "signed" : "unsigned"}`}`));
    return node;
  }
  changes.forEach(change => {
    const card = element("article", "change-card");
    card.dataset.name = change.name;
    const heading = element("div", "change-head");
    heading.append(element("span", `severity ${change.breaking ? "breaking" : "info"}`, change.breaking ? "BREAKING" : "INFO"));
    heading.append(element("h3", "change-name", change.name));
    const categories = element("div", "categories");
    change.categories.forEach(category => categories.append(element("span", "category", category)));
    heading.append(categories);
    card.append(heading);
    const pair = element("div", "port-pair");
    pair.append(snapshot(change.old, false), snapshot(change.new, true));
    card.append(pair);
    if (change.old && change.new) {
      const wrap = element("div", "delta-wrap");
      const table = element("table", "delta-table");
      table.setAttribute("aria-label", `${change.name} 变化属性`);
      const head = table.createTHead().insertRow();
      ["变化属性", "Before", "After"].forEach(text => { const th = element("th", "", text); th.scope = "col"; head.append(th); });
      const body = table.createTBody();
      properties.filter(property => change.old[property] !== change.new[property]).forEach(property => {
        const row = body.insertRow();
        [labels[property], display(change.old[property]), display(change.new[property])].forEach(text => { row.insertCell().textContent = text; });
      });
      wrap.append(table);
      card.append(wrap);
    }
    const details = element("details", "raw-details");
    details.append(element("summary", "", "查看原始端口记录"), element("pre", "", JSON.stringify({old: change.old, new: change.new}, null, 2)));
    card.append(details);
    list.append(card);
  });
  function render() {
    const query = document.getElementById("search").value.trim().toLowerCase();
    let visible = 0;
    changes.forEach((change, index) => {
      const matchesFilter = filter === "all" || filter === "breaking" && change.breaking || filter === "nonbreaking" && !change.breaking || filter === "order" && change.categories.length === 1 && change.categories[0] === "ORDER_ONLY";
      const matchesSearch = [change.name, ...change.categories, declaration(change.old), declaration(change.new)].join(" ").toLowerCase().includes(query);
      const show = matchesFilter && matchesSearch;
      list.children[index].hidden = !show;
      if (show) visible++;
    });
    document.getElementById("visible-count").textContent = `显示 ${visible} / ${changes.length} 个变化项`;
    document.getElementById("empty-state").hidden = visible > 0;
  }
  document.querySelectorAll("[data-filter]").forEach(button => button.addEventListener("click", () => {
    filter = button.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach(item => { const active = item === button; item.classList.toggle("selected", active); item.setAttribute("aria-pressed", String(active)); });
    render();
  }));
  document.getElementById("search").addEventListener("input", render);
  render();
  const outputs = {"report-code": data.report, "source-before": data.sources.before, "source-after": data.sources.after, "manifest-before": JSON.stringify(data.baseline, null, 2), "manifest-after": JSON.stringify(data.current, null, 2), "diff-code": JSON.stringify(data.diff, null, 2)};
  Object.entries(outputs).forEach(([id, content]) => { document.getElementById(id).textContent = content; });
  document.querySelectorAll("[data-evidence]").forEach(button => button.addEventListener("click", () => {
    document.querySelectorAll("[data-evidence]").forEach(item => { const active = item === button; item.classList.toggle("selected", active); item.setAttribute("aria-pressed", String(active)); });
    document.querySelectorAll(".evidence-view").forEach(view => { view.hidden = view.id !== `evidence-${button.dataset.evidence}`; });
  }));
})();
