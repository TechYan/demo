(() => {
  "use strict";
  const data = window.XPGGEN_DEMO;
  const frameButtons = document.getElementById("frame-buttons");
  let frameIndex = 0;
  data.frames.forEach((frame, index) => {
    const button = document.createElement("button");
    button.textContent = frame.title;
    button.addEventListener("click", () => showFrame(index));
    frameButtons.append(button);
  });
  function showFrame(index) {
    frameIndex = (index + data.frames.length) % data.frames.length;
    const frame = data.frames[frameIndex];
    const capture = document.getElementById("capture");
    capture.src = frame.src;
    capture.alt = `xpggen 真实 TUI 截图：${frame.caption}`;
    document.getElementById("full-frame").href = frame.src;
    document.getElementById("frame-caption").textContent = frame.caption;
    document.getElementById("frame-position").textContent = `${frameIndex + 1} / ${data.frames.length}`;
    [...frameButtons.children].forEach((button, i) => {
      button.classList.toggle("selected", i === frameIndex);
      button.setAttribute("aria-pressed", String(i === frameIndex));
    });
  }
  document.getElementById("previous-frame").addEventListener("click", () => showFrame(frameIndex - 1));
  document.getElementById("next-frame").addEventListener("click", () => showFrame(frameIndex + 1));
  showFrame(0);

  const descriptions = {read: "只读寄存器，不做比较。", write: "覆盖写入完整寄存器值。", rmw: "一次读改写，保留掩码之外的位。", read_check: "只比较选定字段的预期值。", poll: "每 10 μs 比较 ready，超时 1000 μs。", delay: "等待 25 μs，无寄存器目标。"};
  data.flow.steps.forEach(step => {
    const row = document.createElement("tr");
    [String(step.index), step.op].forEach(text => { const cell = row.insertCell(); cell.textContent = text; });
    const targetCell = row.insertCell();
    const target = document.createElement("span");
    target.className = "target";
    target.textContent = step.reg || "time";
    targetCell.append(target);
    const value = document.createElement("span");
    value.className = "value";
    value.textContent = step.assignments ? step.assignments.map(field => `${field.field} = ${field.value}`).join("; ") : step.op === "delay" ? `${step.delay_us} us` : step.value || "—";
    if (step.resolved && step.assignments) value.textContent += ` · mask ${step.resolved.mask}`;
    targetCell.append(value);
    row.insertCell().textContent = descriptions[step.op];
    document.getElementById("steps-body").append(row);
  });

  const names = {json: "bringup.pg.json", csv: "bringup.csv", sv: "bringup.sv", md: "bringup.md"};
  const labels = {json: "JSON", csv: "CSV", sv: "SystemVerilog", md: "Markdown"};
  let format = "json";
  function showExport(selected) {
    format = selected;
    document.getElementById("export-code").textContent = data.exports[format];
    document.getElementById("export-filename").textContent = names[format];
    const download = document.getElementById("download-export");
    download.href = `examples/${names[format]}`;
    download.textContent = `下载 ${labels[format]} ↓`;
    document.getElementById("copy-status").textContent = "";
    document.querySelectorAll("[data-format]").forEach(button => {
      const active = button.dataset.format === format;
      button.classList.toggle("selected", active);
      button.setAttribute("aria-pressed", String(active));
    });
  }
  document.querySelectorAll("[data-format]").forEach(button => button.addEventListener("click", () => showExport(button.dataset.format)));
  document.getElementById("copy-export").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(data.exports[format]);
      document.getElementById("copy-status").textContent = "已复制";
    } catch {
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(document.getElementById("export-code"));
      selection.removeAllRanges();
      selection.addRange(range);
      document.getElementById("copy-status").textContent = "已选中，可按 Ctrl+C 复制";
    }
  });
  showExport("json");
})();
