import { useEffect, useState } from "react";
import { getMatchHistory } from "../api/career";
import { getResumeFileUrl } from "../api/resume";
import ResumeGate from "../components/ResumeGate";
import { useResume } from "../hooks/useResume";

export default function History() {
  return (
    <ResumeGate>
      <HistoryContent />
    </ResumeGate>
  );
}

function HistoryContent() {
  const { resume } = useResume();
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!resume?.id) return;
    getMatchHistory(resume.id)
      .then((data) => setItems(data?.items || []))
      .catch((err) => setError(err.message));
  }, [resume?.id]);

  return (
    <div className="page history-page">
      <section className="page-intro">
        <span className="eyebrow">SAVED WORK</span>
        <h2>Match history</h2>
        <p>Open any previous job-match report and review its complete analysis.</p>
      </section>
      {error && <p className="form-error">{error}</p>}
      {items.length ? (
        <div className="history-report-list">
          {items.map((item) => (
            <article className="history-report" key={item.id}>
              <div className="history-report-top">
                <div>
                  <span className="eyebrow">{new Date(item.created_at).toLocaleString()}</span>
                  <h3>{Math.round(item.ats_score)}% match</h3>
                </div>
                <a
                  className="mini-button"
                  href={getResumeFileUrl(item.resume_id || resume.id)}
                  target="_blank"
                  rel="noreferrer"
                >
                  View CV
                </a>
              </div>
              <p>{(item.job_description || "Job description").slice(0, 260)}{item.job_description?.length > 260 ? "..." : ""}</p>
              <div className="badges">
                {(item.matched_skills || []).slice(0, 5).map((skill) => <span className="badge matched" key={skill}>{skill}</span>)}
              </div>
            </article>
          ))}
        </div>
      ) : <div className="form-card history-empty-state">No match history available yet. Analyze a job description to create your first report.</div>}
    </div>
  );
}
