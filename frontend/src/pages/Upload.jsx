import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { indexResume, parseResume, uploadResume } from "../api/resume";
import ResumeCard from "../components/ResumeCard";
import { useResume } from "../hooks/useResume";
export default function Upload() {
	const { resume, saveResume } = useResume();
	const [stage, setStage] = useState("idle");
	const [error, setError] = useState("");
	const handleFile = useCallback(async (file) => {
		setError("");
		try {
			setStage("uploading");
			const uploaded = await uploadResume(file);
			setStage("parsing");
			const parsed = await parseResume(uploaded.id);
			setStage("indexing");
			await indexResume(uploaded.id);
			saveResume({ ...uploaded, parsedData: parsed.parsed_data });
			setStage("done");
		} catch (e) {
			setError(e.message);
			setStage("error");
		}
	}, [saveResume]);
	const drop = useDropzone({ onDrop: (files) => files[0] && handleFile(files[0]), accept: { "application/pdf": [".pdf"] }, maxFiles: 1, disabled: ["uploading", "parsing", "indexing"].includes(stage) });
	const busy = stage !== "idle" && stage !== "done" && stage !== "error";
	const label = { uploading: "Uploading your PDF…", parsing: "Reading your experience and skills…", indexing: "Preparing Copilot’s knowledge base…" }[stage];
	const progress = { uploading: 33, parsing: 66, indexing: 90 }[stage] || 0;

	return (
		<div className="page narrow">
			<section className="page-intro"><span className="eyebrow">STEP 1 OF 1</span><h2>Build your career profile</h2><p>Upload a PDF resume. We’ll extract its details and prepare it for every tool.</p></section>
			<div {...drop.getRootProps()} className={`dropzone ${drop.isDragActive ? "dragging" : ""} ${busy ? "disabled" : ""}`}>
				<input {...drop.getInputProps()} />
				{busy ? <div className="upload-progress" role="status" aria-live="polite"><span className="upload-spinner" aria-hidden="true" /><h3>{label}</h3><p>This can take a moment.</p><div className="progress-track"><span style={{ width: `${progress}%` }} /></div><small>{progress}% complete</small></div> : <><div className="upload-icon">↥</div><h3>Drop your resume here</h3><p>or click to browse · PDF files only</p><button type="button" className="button secondary">Choose PDF</button></>}
			</div>
			{error && <div className="notice error"><b>Couldn’t process the resume.</b> {error}</div>}
			{resume && <><div className="result-banner" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}><div style={{ display: "flex", gap: "10px", alignItems: "center" }}><span>✓</span><div><b>{stage === "done" ? "Your resume is ready" : "Current active resume"}</b><small>{resume.filename} · indexed for Copilot</small></div></div><button type="button" className="mini-button" style={{ color: "#9b352c", borderColor: "#f7dcd8" }} onClick={() => { localStorage.removeItem("careercopilot_resume"); saveResume(null); }}>🗑️ Clear / Upload Fresh</button></div><ResumeCard data={resume.parsedData} /></>}
		</div>
	);
}

