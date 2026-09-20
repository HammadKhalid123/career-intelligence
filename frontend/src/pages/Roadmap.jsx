import { useEffect, useState } from "react";
import { getRoadmap, getSavedRoadmap } from "../api/career";
import ResumeGate from "../components/ResumeGate";
import { useResume } from "../hooks/useResume";
import { exportToPdf, markdownToHtml, parseMarkdownBlocks } from "../utils/pdfExport";
import { startGeneration, useGenerationTask } from "../services/generationTasks";

export default function Roadmap() {
  return (
    <ResumeGate>
      <RoadmapContent />
    </ResumeGate>
  );
}

function RoadmapContent() {
  const { resume } = useResume();
  const taskKey = resume?.id ? `roadmap:${resume.id}` : "roadmap:none";
  const task = useGenerationTask(taskKey);
  const [job, setJob] = useState(() => task.input || "");
  const [roadmap, setRoadmap] = useState(() => task.result?.roadmap || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(() => task.error?.message || "");

  useEffect(() => {
    if (!resume?.id) return;
    if (task.status !== "idle") return;
    let mounted = true;
    const wasCleared = localStorage.getItem(`careercopilot:roadmap-cleared:${resume.id}`) === "true";
    (wasCleared ? Promise.resolve(null) : getSavedRoadmap(resume.id))
      .then((data) => {
        if (!mounted) return;
        if (data?.roadmap) setRoadmap(data.roadmap);
        if (data?.job_description) setJob(data.job_description);
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, [resume?.id, task.status]);

  useEffect(() => {
    const clear = () => {
      setJob("");
      setRoadmap("");
      setError("");
      if (resume?.id) localStorage.setItem(`careercopilot:roadmap-cleared:${resume.id}`, "true");
    };
    window.addEventListener("career:clear", clear);
    return () => window.removeEventListener("career:clear", clear);
  }, [resume?.id]);

  const create = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await startGeneration(taskKey, job, () => getRoadmap(resume.id, job));
      localStorage.removeItem(`careercopilot:roadmap-cleared:${resume.id}`);
      setRoadmap(res.roadmap);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadRoadmapPdf = () => {
    if (!roadmap) return;
    const html = markdownToHtml(roadmap);
    exportToPdf({
      title: "Personalized Career Development Roadmap",
      subtitle: job ? `Target Focus: ${job.slice(0, 160)}${job.length > 160 ? "..." : ""}` : undefined,
      contentHtml: html,
    });
  };

  return (
    <div className="page narrow">
      <section className="page-intro">
        <span className="eyebrow">YOUR NEXT CHAPTER</span>
        <h2>Create your career roadmap</h2>
        <p>
          Tell Copilot which role you want, and it will build a focused
          development plan from your resume.
        </p>
      </section>

      <form className="form-card" onSubmit={create}>
        <label>
          Target job description
          <textarea
            required
            className="resize-none"
            value={job}
            onChange={(e) => setJob(e.target.value)}
            placeholder="Paste a job description or describe your target role…"
            rows="8"
          />
        </label>
        <button className="button" disabled={loading}>
          {loading || task.status === "loading" ? "Designing your roadmap…" : "Generate roadmap →"}
        </button>
        {error && <p className="form-error">{error}</p>}
      </form>

      {roadmap && (
        <article className="roadmap-output">
          <div className="report-actions">
            <span className="eyebrow" style={{ margin: 0 }}>PERSONALIZED ROADMAP</span>
            <button
              type="button"
              onClick={downloadRoadmapPdf}
              className="mini-button"
              style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
            >
              📄 Download Roadmap (PDF)
            </button>
            <button type="button" className="mini-button clear-section-button" onClick={() => window.dispatchEvent(new Event("career:clear"))}>Clear roadmap</button>
          </div>
          <RoadmapRenderer text={roadmap} />
        </article>
      )}
    </div>
  );
}

/* ----------------------------------------------------------------
   RoadmapRenderer
   Converts structured markdown blocks into styled sections.
------------------------------------------------------------------- */
function RoadmapRenderer({ text }) {
  const matchSummary = extractMatchSummary(text);
  if (matchSummary) {
    return (
      <div className="roadmap-structured">
        {matchSummary.before && <RoadmapBlocks text={matchSummary.before} />}
        <MatchSummary summary={matchSummary} />
        {matchSummary.after && <RoadmapBlocks text={matchSummary.after} />}
      </div>
    );
  }

  return <RoadmapBlocks text={text} />;
}

function RoadmapBlocks({ text }) {
  const blocks = parseMarkdownBlocks(text);

  return (
    <div className="roadmap-structured">
      {blocks.map((block, i) => {
        switch (block.type) {
          case "h1":
            return (
              <h2 key={i} className="roadmap-h1">
                {renderInline(block.content)}
              </h2>
            );
          case "h2":
            return (
              <h3 key={i} className="roadmap-h2">
                {renderInline(block.content)}
              </h3>
            );
          case "h3":
            return (
              <h4 key={i} className="roadmap-h3">
                {renderInline(block.content)}
              </h4>
            );
          case "h4":
            return (
              <h5 key={i} className="roadmap-h4">
                {renderInline(block.content)}
              </h5>
            );
          case "ul":
            return (
              <ul key={i} className="roadmap-list">
                {block.items.map((item, j) => (
                  <li key={j}>{renderInline(item)}</li>
                ))}
              </ul>
            );
          case "ol":
            return (
              <ol key={i} className="roadmap-list roadmap-list-ordered">
                {block.items.map((item, j) => (
                  <li key={j}>{renderInline(item)}</li>
                ))}
              </ol>
            );
          case "table":
            return (
              <div key={i} className="roadmap-table-wrap">
                <table className="roadmap-table">
                  <thead><tr>{block.headers.map((header, j) => <th key={j}>{renderInline(header)}</th>)}</tr></thead>
                  <tbody>{block.rows.map((row, j) => <tr key={j}>{block.headers.map((_, k) => <td key={k}>{renderInline(row[k] || "")}</td>)}</tr>)}</tbody>
                </table>
              </div>
            );
          case "p":
          default:
            return (
              <p key={i} className="roadmap-paragraph">
                {renderInline(block.content)}
              </p>
            );
        }
      })}
    </div>
  );
}

function extractMatchSummary(text) {
  const startMatch = text.match(/Match Summary\s*(?:\(([^)]+)\))?/i);
  if (!startMatch) return null;

  const start = startMatch.index;
  const missingMatch = text.slice(start).match(/What you[’']re missing\s*:/i);
  const end = missingMatch ? start + missingMatch.index : text.length;
  const summaryText = text.slice(start, end);
  const headerMatch = summaryText.match(/Requirement\s*\|\s*Status\s*\|\s*Evidence\s*\|?/i);
  if (!headerMatch) return null;

  const cells = summaryText
    .slice(headerMatch.index + headerMatch[0].length)
    .split("|")
    .map((cell) => cell.trim())
    .filter((cell) => cell && !/^[-:]+$/.test(cell));
  const rows = [];
  for (let index = 0; index + 2 < cells.length; index += 3) {
    rows.push({ requirement: cells[index], status: cells[index + 1], evidence: cells[index + 2] });
  }

  const after = missingMatch
    ? text.slice(end).replace(/What you[’']re missing\s*:/i, "What you're missing:").replace(/^\s*[-_]+\s*/m, "").trim()
    : "";
  return {
    before: text.slice(0, start).trim(),
    score: startMatch[1] || "",
    rows,
    after,
  };
}

function MatchSummary({ summary }) {
  const missingParts = summary.after.split(/\n+/).map((item) => item.replace(/^[-*•]\s*/, "").trim()).filter(Boolean);
  return (
    <section className="roadmap-match-summary">
      <div className="roadmap-summary-heading">
        <div>
          <span className="eyebrow">MATCH SUMMARY</span>
          <h3>{summary.score || "ATS score"}</h3>
        </div>
        <span className="summary-count">{summary.rows.length} requirements</span>
      </div>
      <div className="match-summary-table-wrap">
        <table className="match-summary-table">
          <thead><tr><th>Requirement</th><th>Status</th><th>Evidence</th></tr></thead>
          <tbody>
            {summary.rows.map((row, index) => (
              <tr key={`${row.requirement}-${index}`}>
                <td><strong>{renderInline(row.requirement)}</strong></td>
                <td><span className={`match-status ${row.status.includes("❌") ? "missing" : "matched"}`}>{renderInline(row.status)}</span></td>
                <td>{renderInline(row.evidence)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {missingParts.length > 0 && (
        <div className="roadmap-missing">
          <h4>What you’re missing</h4>
          <ul>{missingParts.map((item, index) => <li key={index}>{renderInline(item)}</li>)}</ul>
        </div>
      )}
    </section>
  );
}


// Handles inline **bold**, *italic*, and [text](url) links
function renderInline(text) {
  const parts = [];
  const regex = /(<br\s*\/?>)|(\*\*(.+?)\*\*)|(\*(.+?)\*)|(\[(.+?)\]\((.+?)\))|(<(https?:\/\/[^>]+)>)|(https?:\/\/[^\s)<>]+)/gi;
  let lastIndex = 0;
  let match;
  let key = 0;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    if (match[1]) {
      parts.push(<br key={key++} />);
    } else if (match[2]) {
      parts.push(<strong key={key++}>{match[3]}</strong>);
    } else if (match[4]) {
      parts.push(<em key={key++}>{match[5]}</em>);
    } else if (match[6]) {
      parts.push(
        <a key={key++} href={match[8]} target="_blank" rel="noreferrer">
          {match[7]}
        </a>
      );
    } else if (match[9]) {
      parts.push(<a key={key++} href={match[10]} target="_blank" rel="noreferrer">{match[10]}</a>);
    } else if (match[11]) {
      parts.push(<a key={key++} href={match[11]} target="_blank" rel="noreferrer">{match[11]}</a>);
    }
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  return parts;
}
