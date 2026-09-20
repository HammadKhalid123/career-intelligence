import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useResume } from "../hooks/useResume";
const links = [["/", "⌂", "Overview"], ["/resume", "↥", "My Resume"], ["/match", "◎", "Job Match"], ["/roadmap", "⌁", "Career Roadmap"], ["/history", "◷", "Match History"], ["/chat", "◌", "Ask Copilot"], ["/learning", "✦", "Learning Lab"]];
export default function AppShell() {
	const { resume } = useResume();
	const location = useLocation();
	const current = links.find(([path]) => path === location.pathname)?.[2] || "CareerCopilot";
	return <div className="app-shell"><aside className="sidebar"><NavLink className="brand" to="/"><span className="brand-mark">C</span><span>Career<span>Copilot</span></span></NavLink><p className="nav-caption">WORKSPACE</p><nav>{links.map(([to, icon, name]) => <NavLink key={to} end={to === "/"} to={to} className="nav-link"><i>{icon}</i>{name}</NavLink>)}</nav><div className="resume-status"><span className="status-dot" />{resume ? <div><b>Resume ready</b><small>{resume.filename}</small></div> : <div><b>No resume yet</b><small>Upload to begin</small></div>}</div></aside><main className="main"><header className="topbar"><div><span className="eyebrow">CAREER INTELLIGENCE</span><h1>{current}</h1></div><NavLink to="/resume" className="avatar">{resume?.parsedData?.name?.slice(0, 1) || "+"}</NavLink></header><Outlet /></main></div>;
}
