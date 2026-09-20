function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatInlineHtml(text) {
  if (!text) return "";
  return escapeHtml(text)
    .replace(/&lt;br\s*\/??&gt;/gi, "<br>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>");
}

export function parseMarkdownBlocks(raw) {
  if (!raw) return [];
  const normalized = raw
    .replace(/\r\n/g, "\n")
    .replace(/\|\s+\|/g, "|\n|");
  const lines = normalized.split("\n");
  const blocks = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i].trim();

    if (!line) {
      i++;
      continue;
    }

    // LLM output can contain compact pipe tables or tables with a separator row.
    if (line.startsWith("|") && lines[i + 1]?.trim().startsWith("|")) {
      const next = lines[i + 1].trim();
      if (/^\|?\s*:?-{3,}/.test(next)) {
        const parseRow = (value) => value.trim().replace(/^\||\|$/g, "").split("|").map((cell) => cell.trim());
        const headers = parseRow(line);
        const rows = [];
        i += 2;
        while (i < lines.length && lines[i].trim().startsWith("|")) {
          rows.push(parseRow(lines[i]));
          i++;
        }
        blocks.push({ type: "table", headers, rows });
        continue;
      }
    }

    // Match any heading: #, ##, ###, ####, #####, ######
    // Also handles bold headings like: #### **Week 1: ...** or **#### Week 1...**
    const headingMatch = line.match(/^(\*{0,2})(#{1,6})\s*(.+?)(\*{0,2})$/);
    if (headingMatch) {
      const level = headingMatch[2].length;
      const content = headingMatch[3].trim().replace(/^[*_]+|[*_]+$/g, "");
      blocks.push({ type: `h${Math.min(level, 4)}`, content });
      i++;
      continue;
    }

    // Unordered list (-, *, •)
    if (/^[-*•]\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^[-*•]\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^[-*•]\s+/, ""));
        i++;
      }
      blocks.push({ type: "ul", items });
      continue;
    }

    // Ordered list (1. 2. 3.)
    if (/^\d+[.)]\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\d+[.)]\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^\d+[.)]\s+/, ""));
        i++;
      }
      blocks.push({ type: "ol", items });
      continue;
    }

    // Paragraph: collect consecutive plain lines together
    const paraLines = [line];
    i++;
    while (
      i < lines.length &&
      lines[i].trim() &&
      !/^(\*{0,2})#{1,6}\s/.test(lines[i].trim()) &&
      !/^[-*•]\s+/.test(lines[i].trim()) &&
      !/^\d+[.)]\s+/.test(lines[i].trim())
    ) {
      paraLines.push(lines[i].trim());
      i++;
    }
    blocks.push({ type: "p", content: paraLines.join(" ") });
  }

  return blocks;
}

export function markdownToHtml(raw) {
  const blocks = parseMarkdownBlocks(raw);
  return blocks
    .map((b) => {
      switch (b.type) {
        case "h1":
          return `<h2 class="roadmap-h1">${formatInlineHtml(b.content)}</h2>`;
        case "h2":
          return `<h3 class="roadmap-h2">${formatInlineHtml(b.content)}</h3>`;
        case "h3":
          return `<h4 class="roadmap-h3">${formatInlineHtml(b.content)}</h4>`;
        case "h4":
          return `<h5 class="roadmap-h4">${formatInlineHtml(b.content)}</h5>`;
        case "ul":
          return `<ul class="roadmap-list">${b.items
            .map((item) => `<li>${formatInlineHtml(item)}</li>`)
            .join("")}</ul>`;
        case "ol":
          return `<ol class="roadmap-list">${b.items
            .map((item) => `<li>${formatInlineHtml(item)}</li>`)
            .join("")}</ol>`;
        case "table":
          return `<div class="roadmap-table-wrap"><table class="roadmap-table"><thead><tr>${b.headers
            .map((cell) => `<th>${formatInlineHtml(cell)}</th>`)
            .join("")}</tr></thead><tbody>${b.rows
            .map((row) => `<tr>${b.headers
              .map((_, index) => `<td>${formatInlineHtml(row[index] || "")}</td>`)
              .join("")}</tr>`)
            .join("")}</tbody></table></div>`;
        case "p":
        default:
          return `<p class="roadmap-paragraph">${formatInlineHtml(b.content)}</p>`;
      }
    })
    .join("");
}

export function exportToPdf({ title, subtitle, contentHtml }) {
  let iframe = document.getElementById("pdf-print-frame");
  if (!iframe) {
    iframe = document.createElement("iframe");
    iframe.id = "pdf-print-frame";
    iframe.style.position = "fixed";
    iframe.style.right = "0";
    iframe.style.bottom = "0";
    iframe.style.width = "0";
    iframe.style.height = "0";
    iframe.style.border = "none";
    document.body.appendChild(iframe);
  }

  const doc = iframe.contentWindow.document;
  doc.open();
  doc.write(`
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>${title || "Career Intelligence Report"}</title>
        <style>
          @import url("https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap");
          @page {
            size: A4;
            margin: 16mm 14mm;
          }
          * { box-sizing: border-box; }
          body {
            font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #18332e;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background: #fff;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }
          .pdf-header {
            border-bottom: 2px solid #398d7b;
            padding-bottom: 12px;
            margin-bottom: 20px;
          }
          .pdf-eyebrow {
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: #1a5b50;
            margin-bottom: 4px;
          }
          .pdf-title {
            font-family: 'Fraunces', Georgia, serif;
            font-size: 26px;
            font-weight: 700;
            color: #123b35;
            margin: 4px 0 6px;
          }
          .pdf-subtitle {
            font-size: 13.5px;
            color: #557069;
            margin: 0;
          }
          h1, h2, h3, h4, h5 {
            color: #123b35;
            page-break-after: avoid;
            break-after: avoid;
          }
          .roadmap-h1 {
            font-family: 'Fraunces', serif;
            font-size: 22px;
            font-weight: 700;
            color: #123b35;
            margin: 20px 0 8px;
            border-bottom: 1.5px solid #dcebe5;
            padding-bottom: 4px;
          }
          .roadmap-h2 {
            font-family: 'Fraunces', serif;
            font-size: 18px;
            font-weight: 700;
            color: #1a5b50;
            margin: 18px 0 7px;
            border-bottom: 1px solid #e2f0ea;
            padding-bottom: 3px;
          }
          .roadmap-h3 {
            font-size: 16px;
            font-weight: 700;
            color: #1a5b50;
            margin: 16px 0 6px;
          }
          .roadmap-h4 {
            font-size: 15px;
            font-weight: 700;
            color: #123b35;
            margin: 14px 0 6px;
            display: block;
          }
          .roadmap-paragraph, p {
            font-size: 13.5px;
            color: #2b4741;
            margin: 0 0 9px;
            line-height: 1.6;
          }
          .roadmap-list, ul, ol {
            font-size: 13.5px;
            color: #2b4741;
            margin: 5px 0 11px 18px;
            padding: 0;
            line-height: 1.6;
          }
          li { margin-bottom: 3px; }
          .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 99px;
            font-size: 11px;
            font-weight: 600;
            margin: 2px 4px 2px 0;
            background: #e9f8f2;
            color: #1a5b50;
          }
          .badge.matched { background: #d9f5e8; color: #287a52; }
          .badge.missing { background: #fff2dd; color: #bd7b22; }
          .badge.partial { background: #e4efff; color: #3f6598; }
          .pdf-score-box {
            display: inline-flex;
            align-items: center;
            gap: 15px;
            background: #f6faf8;
            border: 1px solid #dcebe5;
            border-radius: 12px;
            padding: 14px 20px;
            margin-bottom: 18px;
          }
          .pdf-score-num {
            font-family: 'Fraunces', serif;
            font-size: 32px;
            font-weight: 700;
            color: #1a5b50;
          }
          .pdf-section {
            margin-top: 18px;
            border-top: 1px solid #dcebe5;
            padding-top: 14px;
            page-break-inside: avoid;
          }
          .pdf-section h3 {
            font-size: 12px;
            letter-spacing: 1px;
            text-transform: uppercase;
            color: #71847f;
            margin: 0 0 8px;
          }
          .pdf-footer {
            margin-top: 26px;
            border-top: 1px solid #dcebe5;
            padding-top: 8px;
            font-size: 11px;
            color: #71847f;
            display: flex;
            justify-content: space-between;
          }
        </style>
      </head>
      <body>
        <div class="pdf-header">
          <div class="pdf-eyebrow">CareerCopilot AI · Official Report</div>
          <div class="pdf-title">${title}</div>
          ${subtitle ? `<div class="pdf-subtitle">${subtitle}</div>` : ""}
        </div>
        <div class="pdf-body">
          ${contentHtml}
        </div>
        <div class="pdf-footer">
          <span>Generated by CareerCopilot AI</span>
          <span>${new Date().toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}</span>
        </div>
      </body>
    </html>
  `);
  doc.close();

  setTimeout(() => {
    iframe.contentWindow.focus();
    iframe.contentWindow.print();
  }, 400);
}
