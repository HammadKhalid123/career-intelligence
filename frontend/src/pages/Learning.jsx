import { useEffect, useState } from "react";
import { getLearning, getProgress, getResources, getSavedLearning, updateProgress } from "../api/career";
import ResumeGate from "../components/ResumeGate";
import { useResume } from "../hooks/useResume";
import { exportToPdf } from "../utils/pdfExport";
import { clearGeneration, startGeneration, useGenerationTask } from "../services/generationTasks";

const types = [
  ["flashcards", "Flashcards"],
  ["quiz", "Quiz"],
  ["coding-challenge", "Coding challenge"],
  ["interview-questions", "Interview prep"],
];

function normalizeQuotes(value) {
  if (typeof value !== "string") return value;
  return value.replace(/[“”]/g, '"').replace(/[‘’]/g, "'");
}

export default function Learning() {
  return (
    <ResumeGate>
      <LearningContent />
    </ResumeGate>
  );
}

function LearningContent() {
  const { resume } = useResume();
  const [skill, setSkill] = useState(resume.parsedData?.skills?.[0] || "");
  const [type, setType] = useState("flashcards");
  const [content, setContent] = useState(null);
  const [resources, setResources] = useState(null);
  const [progress, setProgress] = useState([]);
  const [savedItems, setSavedItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const taskKey = resume?.id ? `learning:${resume.id}:${skill}:${type}` : "learning:none";
  const task = useGenerationTask(taskKey);

  useEffect(() => {
    if (!task.result && !task.error) return undefined;
    const timer = window.setTimeout(() => {
      if (task.result) {
        setContent(task.result.content);
        setResources(task.result.resources);
      }
      if (task.error) setError(task.error.message);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [task]);

  // Load progress and saved learning content on mount
  useEffect(() => {
    if (!resume?.id) return;
    getProgress(resume.id)
      .then((x) => setProgress(x.progress || []))
      .catch(() => {});

    getSavedLearning(resume.id)
      .then((res) => {
        const items = res.items || [];
        setSavedItems(items);
        if (items.length > 0) {
          // If we have saved content, auto-load the most recently updated item
          const latest = items[0];
          setSkill(latest.skill);
          setType(latest.content_type);
          setContent(latest.content);
          getResources(latest.skill).then(setResources).catch(() => {});
        }
      })
      .catch(() => {});
  }, [resume?.id]);

  // When skill changes or type changes, check if we already have it saved locally
  const handleSkillChange = (newSkill) => {
    setSkill(newSkill);
    const existing = savedItems.find((x) => x.skill === newSkill && x.content_type === type);
    if (existing) {
      setContent(existing.content);
      getResources(newSkill).then(setResources).catch(() => {});
    } else {
      setContent(null);
      setResources(null);
    }
  };

  const handleTypeChange = (newType) => {
    setType(newType);
    const existing = savedItems.find((x) => x.skill === skill && x.content_type === newType);
    if (existing) {
      setContent(existing.content);
      getResources(skill).then(setResources).catch(() => {});
    } else {
      setContent(null);
      setResources(null);
    }
  };

  const generate = async () => {
    if (!skill) return;
    setLoading(true);
    setError("");
    try {
      const { content: data, resources: links } = await startGeneration(
        taskKey,
        { skill, type },
        async () => {
          const [contentData, resourceLinks] = await Promise.all([
            getLearning(type, skill, resume.id),
            getResources(skill),
          ]);
          return { content: contentData, resources: resourceLinks };
        },
      );
      setContent(data);
      setResources(links);
      // Update saved items cache
      setSavedItems((prev) => [
        { skill, content_type: type, content: data, updated_at: new Date().toISOString() },
        ...prev.filter((x) => !(x.skill === skill && x.content_type === type)),
      ]);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const mark = async (status) => {
    try {
      const item = await updateProgress(resume.id, skill, status);
      setProgress((x) => [...x.filter((p) => p.skill !== skill), item]);
    } catch (e) {
      setError(e.message);
    }
  };

  const clearLearning = () => {
    clearGeneration(taskKey);
    setContent(null);
    setResources(null);
    setError("");
  };

  const downloadContentPdf = () => {
    if (!content) return;
    const activityName = types.find((x) => x[0] === type)?.[1] || type;
    let html = ``;

    if (type === "flashcards" && content.flashcards) {
      html += content.flashcards
        .map(
          (f, i) => `
          <div class="pdf-section">
            <div style="font-weight: 700; font-size: 15px; color: #123b35; margin-bottom: 4px;">Card ${i + 1}: ${f.question}</div>
            <p style="background: #f6faf8; padding: 10px 14px; border-radius: 8px; border-left: 3px solid #398d7b; margin: 4px 0;"><strong>Answer:</strong> ${f.answer}</p>
          </div>`
        )
        .join("");
    } else if (type === "quiz" && content.questions) {
      html += content.questions
        .map(
          (q, i) => `
          <div class="pdf-section">
            <div style="font-weight: 700; font-size: 15px; color: #123b35; margin-bottom: 6px;">Q${i + 1}: ${q.question}</div>
            <ul>
              ${q.options.map((opt, idx) => `<li>${idx === q.correct_option_index ? `<strong style="color: #287a52;">✓ ${opt} (Correct)</strong>` : opt}</li>`).join("")}
            </ul>
            <p><small><strong>Explanation:</strong> ${q.explanation}</small></p>
          </div>`
        )
        .join("");
    } else if (type === "coding-challenge" && content.challenges) {
      html += content.challenges
        .map(
          (challenge, i) => `
          <div class="pdf-section">
            <h2 style="font-size: 18px; color: #123b35;">Challenge ${i + 1}: ${challenge.title}</h2>
            <p>${challenge.description}</p>
            <pre style="background: #173b34; color: #def5eb; padding: 12px; border-radius: 8px; font-size: 12px; overflow-x: auto;"><code>${challenge.starter_code || ""}</code></pre>
            <h3>Hints</h3>
            <ul>${(challenge.hints || []).map((h) => `<li>${h}</li>`).join("")}</ul>
          </div>
        `,
        )
        .join("");
    } else if (type === "interview-questions" && content.questions) {
      html += content.questions
        .map(
          (q, i) => `
          <div class="pdf-section">
            <div style="font-weight: 700; font-size: 15px; color: #123b35; margin-bottom: 4px;">Question ${i + 1}: ${q.question}</div>
            <p><strong>Ideal Answer Key Points:</strong></p>
            <ul>
              ${(q.ideal_answer_points || []).map((p) => `<li>${p}</li>`).join("")}
            </ul>
          </div>`
        )
        .join("");
    }

    exportToPdf({
      title: `${content.skill?.toUpperCase() || skill} · ${activityName}`,
      subtitle: `Targeted Practice Material · CareerCopilot Learning Lab`,
      contentHtml: html,
    });
  };

  return (
    <div className="page narrow">
      <section className="page-intro">
        <span className="eyebrow">LEARNING LAB</span>
        <h2>Practice the skills that matter</h2>
        <p>Create targeted learning material based on the skills in your career profile.</p>
      </section>

      <section className="learning-controls">
        <label>
          Skill
          <select value={skill} onChange={(e) => handleSkillChange(e.target.value)}>
            {resume.parsedData?.skills?.map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
        <label>
          Activity
          <select value={type} onChange={(e) => handleTypeChange(e.target.value)}>
            {types.map(([v, n]) => (
              <option key={v} value={v}>
                {n}
              </option>
            ))}
          </select>
        </label>
        <button className="button" onClick={generate} disabled={loading}>
          {loading || task.status === "loading" ? "Creating..." : content ? "Regenerate activity →" : "Create activity →"}
        </button>
      </section>

      {error && <p className="form-error">{error}</p>}
      {progress.length > 0 && (
        <p className="progress-line">
          Learning progress: {progress.filter((x) => x.status === "completed").length} completed /{" "}
          {progress.length} tracked
        </p>
      )}

      {content && (
        <section className="learning-output">
          <header>
            <div>
              <span className="eyebrow">{normalizeQuotes(content.skill || skill)}</span>
              <h2>{types.find((x) => x[0] === type)?.[1]}</h2>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <button
                type="button"
                onClick={downloadContentPdf}
                className="mini-button"
                style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
              >
                📄 Download (PDF)
              </button>
              <button type="button" onClick={clearLearning} className="mini-button clear-section-button">
                Clear
              </button>
              <button onClick={() => mark("in_progress")} className="mini-button">
                In progress
              </button>
              <button onClick={() => mark("completed")} className="mini-button complete">
                Complete
              </button>
            </div>
          </header>
          <Content data={content} type={type} />
          {resources && (
            <footer>
              <b>Keep learning</b>
              {(resources.resources || [
                { title: "Documentation", url: resources.documentation_search_url },
                { title: "Video lessons", url: resources.video_search_url },
              ]).map((resource) => (
                <a key={resource.url} target="_blank" rel="noreferrer" href={resource.url}>
                  {resource.title}
                </a>
              ))}
            </footer>
          )}
        </section>
      )}
    </div>
  );
}


function Content({ data, type }) {
  const normalizedData = normalizeQuotes(data);

  if (type === "flashcards")
    return <Flashcards items={normalizedData.flashcards || []} />;
  if (type === "quiz")
    return (
      <div className="quiz">
        {normalizedData.questions?.map((x, i) => (
          <details key={i}>
            <summary>
              {i + 1}. {x.question}
            </summary>
            {x.options?.map((o, j) => (
              <p key={j} className={j === x.correct_option_index ? "correct" : ""}>
                {o}
                {j === x.correct_option_index && " (correct)"}
              </p>
            ))}
            <small>{x.explanation}</small>
          </details>
        ))}
      </div>
    );
  if (type === "coding-challenge")
    {
      const challenges = normalizedData.challenges || (normalizedData.title ? [normalizedData] : []);
      return (
        <div className="challenge-list">
          {challenges.map((challenge, i) => (
            <article className="challenge" key={`${challenge.title}-${i}`}>
              <span className="flashcard-count">Challenge {String(i + 1).padStart(2, "0")}</span>
              <h3>{challenge.title}</h3>
              <p>{challenge.description}</p>
              <pre>{challenge.starter_code}</pre>
              <b>Hints</b>
              {challenge.hints?.map((hint, j) => (
                <p key={j}>- {hint}</p>
              ))}
            </article>
          ))}
        </div>
      );
    }
  return (
    <div className="interview">
      {normalizedData.questions?.map((x, i) => (
        <details key={i}>
          <summary>{x.question}</summary>
          <ul>
            {x.ideal_answer_points?.map((p, j) => (
              <li key={j}>{p}</li>
            ))}
          </ul>
        </details>
      ))}
    </div>
  );
}

function Flashcards({ items }) {
  const [revealed, setRevealed] = useState(new Set());

  const toggleCard = (index) => {
    setRevealed((current) => {
      const next = new Set(current);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  };

  return (
    <div className="flashcards" aria-label="Flashcards">
      {items.map((item, index) => {
        const isRevealed = revealed.has(index);
        return (
          <button
            type="button"
            className={`flashcard ${isRevealed ? "is-revealed" : ""}`}
            key={`${item.question}-${index}`}
            onClick={() => toggleCard(index)}
            aria-pressed={isRevealed}
          >
            <span className="flashcard-count">Card {String(index + 1).padStart(2, "0")}</span>
            <span className="flashcard-label">{isRevealed ? "Answer" : "Question"}</span>
            <span className="flashcard-text">{isRevealed ? item.answer : item.question}</span>
            <span className="flashcard-hint">{isRevealed ? "Click to see the question" : "Click to reveal answer"}</span>
          </button>
        );
      })}
    </div>
  );
}

