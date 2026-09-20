import { useEffect, useState } from "react";
import { analyzeJob, getLatestMatch } from "../api/career";
import ResumeGate from "../components/ResumeGate";
import { useResume } from "../hooks/useResume";
import { exportToPdf } from "../utils/pdfExport";
import { startGeneration, useGenerationTask } from "../services/generationTasks";

export default function MatchReport() {
  return (
    <ResumeGate>
      <Match />
    </ResumeGate>
  );
}

function Match() {
  const { resume } = useResume();
  const taskKey = resume?.id ? `match:${resume.id}` : "match:none";
  const task = useGenerationTask(taskKey);
  const [description, setDescription] = useState(() => task.input || "");
  const [result, setResult] = useState(() => task.result || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(() => task.error?.message || "");

  useEffect(() => {
    if (!resume?.id) return;
    if (task.status !== "idle") return;
    let mounted = true;
    const wasCleared = localStorage.getItem(`careercopilot:match-cleared:${resume.id}`) === "true";
    (wasCleared ? Promise.resolve(null) : getLatestMatch(resume.id))
      .then((data) => {
        if (!mounted) return;
        if (data) {
          setResult(data);
          if (data.job_description) setDescription(data.job_description);
        }
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, [resume?.id, task.status]);

  useEffect(() => {
    const clear = () => {
      setDescription("");
      setResult(null);
      setError("");
      if (resume?.id) localStorage.setItem(`careercopilot:match-cleared:${resume.id}`, "true");
    };
    window.addEventListener("career:clear", clear);
    return () => window.removeEventListener("career:clear", clear);
  }, [resume?.id]);

  const submit = async (e) => {
    e.preventDefault();
    if (!description.trim()) return;
    setLoading(true);
    setError("");
    try {
      const nextResult = await startGeneration(taskKey, description, () => analyzeJob(resume.id, description));
      localStorage.removeItem(`careercopilot:match-cleared:${resume.id}`);
      setResult(nextResult);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadReportPdf = () => {
    if (!result) return;
    const score = Math.round(result.ats_score);
    const assessment = score >= 70 ? "Strong foundation" : "A clear path to improve";

    let html = `
      <div class="pdf-score-box">
        <div class="pdf-score-num">${score}%</div>
        <div>
          <div style="font-weight: 700; font-size: 16px; color: #123b35;">${assessment}</div>
          <div style="font-size: 13px; color: #557069;">Evidence-based ATS Fit Score</div>
        </div>
      </div>
      <p><strong>Summary:</strong> ${result.summary || "Based on technical requirements in this role."}</p>

      <div class="pdf-section">
        <h3>Skills You Match (${result.matched_skills?.length || 0})</h3>
        <div>
          ${result.matched_skills?.length ? result.matched_skills.map((s) => `<span class="badge matched">${s}</span>`).join("") : "<p>None identified</p>"}
        </div>
      </div>

      <div class="pdf-section">
        <h3>Related Experience (${result.partial_matches?.length || 0})</h3>
        <div>
          ${result.partial_matches?.length ? result.partial_matches.map((s) => `<span class="badge partial">${s}</span>`).join("") : "<p>None identified</p>"}
        </div>
      </div>

      <div class="pdf-section">
        <h3>Skills to Strengthen (${result.missing_skills?.length || 0})</h3>
        <div>
          ${result.missing_skills?.length ? result.missing_skills.map((s) => `<span class="badge missing">${s}</span>`).join("") : "<p>None</p>"}
        </div>
      </div>
    `;

    if (result.evidence?.length > 0) {
      html += `
        <div class="pdf-section">
          <h3>Why This Result (Evidence Breakdown)</h3>
          <ul>
            ${result.evidence.map((e) => `<li><strong>${e.requirement}</strong> <small style="color:#1a5b50;">[${(e.status || "").replaceAll("_", " ")}]</small>: ${e.evidence || "No supporting resume evidence found."}</li>`).join("")}
          </ul>
        </div>
      `;
    }

    if (result.eligibility_notes?.length > 0) {
      html += `
        <div class="pdf-section">
          <h3>Eligibility Notes</h3>
          <ul>
            ${result.eligibility_notes.map((n) => `<li>${n}</li>`).join("")}
          </ul>
        </div>
      `;
    }

    exportToPdf({
      title: "Job Fit & Skill-Gap Analysis Report",
      subtitle: `Candidate Resume ID: ${resume?.id || 1}`,
      contentHtml: html,
    });
  };

  return (
    <div className="page narrow">
      <section className="page-intro">
        <span className="eyebrow">JOB FIT ANALYSIS</span>
        <h2>Is this the right role for you?</h2>
        <p>Paste a job description for an evidence-based skill-gap report.</p>
      </section>

      <form onSubmit={submit} className="form-card">
        <label>
          Job description
          <textarea
            className="resize-none"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Paste the complete job description here..."
            rows="10"
          />
        </label>
        <button className="button" disabled={loading}>
          {loading || task.status === "loading" ? "Analyzing match..." : "Analyze my match →"}
        </button>
        {error && <p className="form-error">{error}</p>}
      </form>

      {result && (
        <section className="report">
          <div className="report-actions report-heading-actions">
            <span className="eyebrow" style={{ margin: 0 }}>MATCH ANALYSIS RESULT</span>
            <button
              type="button"
              onClick={downloadReportPdf}
              className="mini-button"
              style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
            >
              📄 Download Report (PDF)
            </button>
            <button type="button" className="mini-button clear-section-button" onClick={() => window.dispatchEvent(new Event("career:clear"))}>Clear match</button>
          </div>
          <div className="score">
            <div>
              <b>{Math.round(result.ats_score)}</b>
              <span>%</span>

            </div>
            <p>Evidence-based fit</p>
          </div>
          <div className="report-copy">
            <h2>
              {result.ats_score >= 70 ? "Strong foundation" : "A clear path to improve"}
            </h2>
            <p>
              {result.summary ||
                `Based on ${result.required_skills?.length || 0} technical requirements in this role.`}
            </p>
          </div>
          <SkillList title="Skills you match" type="matched" skills={result.matched_skills || []} />
          <SkillList
            title="Experience-backed requirements"
            type="partial"
            skills={getExperienceBackedSkills(result)}
          />
          <SkillList title="Skills to strengthen" type="missing" skills={result.missing_skills || []} />
          <EvidenceBreakdown evidence={result.evidence || []} />
          {result.eligibility_notes?.length > 0 && (
            <div className="eligibility-notes">
              <b>Eligibility notes</b>
              {result.eligibility_notes.map((note, i) => (
                <p key={i}>{note}</p>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}

function getExperienceBackedSkills(result) {
  return (result.evidence || [])
    .filter((item) => {
      const status = (item.status || "").toLowerCase();
      const explanation = item.evidence || "";
      return status === "partial_match" || status === "evidence_match" ||
        (status === "direct_match" && /intern|project|built|developed|performed|worked|used|experience|integrated|implemented/i.test(explanation));
    })
    .map((item) => item.requirement);
}

function EvidenceBreakdown({ evidence }) {
  const groups = [
    ["matched", "Matched requirements", "Your resume directly supports these requirements."],
    ["partial", "Related experience", "Your background is relevant, but the match is not fully direct."],
    ["missing", "Requirements to build", "These requirements were not found in the resume evidence."],
  ];
  return <div className="evidence-list"><h3>Requirement-by-requirement explanation</h3>{groups.map(([type, title, intro]) => {
    const items = evidence.filter((item) => {
      const status = (item.status || "").toLowerCase();
      if (type === "matched") return status === "direct_match";
      if (type === "partial") return status === "partial_match" || status === "evidence_match";
      return status === "missing" || status === "not_found";
    });
    return <section key={type} className={`evidence-group ${type}`}><h4>{title}<span>{items.length}</span></h4><p className="evidence-intro">{intro}</p>{items.length ? items.map((item) => <div className="evidence-card" key={item.requirement}><div><b>{item.requirement}</b><small>{(item.status || type).replaceAll("_", " ")}</small></div><p>{item.evidence || "No supporting resume evidence found."}</p></div>) : <p className="evidence-empty">No items in this category.</p>}</section>;
  })}</div>;
}

function SkillList({ title, skills, type }) {
  return (
    <div className="skill-list">
      <h3>
        {title}
        <span>{skills.length}</span>
      </h3>
      <div className="badges">
        {skills.length ? (
          skills.map((x) => (
            <span key={x} className={`badge ${type}`}>
              {x}
            </span>
          ))
        ) : (
          <p>Nothing here yet.</p>
        )}
      </div>
    </div>
  );
}

