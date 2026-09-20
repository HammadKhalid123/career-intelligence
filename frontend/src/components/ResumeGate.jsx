import { Link } from "react-router-dom";
import { useResume } from "../hooks/useResume";
export default function ResumeGate({ children }) { const { hasResume } = useResume(); return hasResume ? children : <div className="empty-state"><div className="empty-icon">↥</div><h2>Start with your resume</h2><p>Upload, parse, and index your PDF once to unlock this tool.</p><Link className="button" to="/resume">Upload resume</Link></div>; }
