import { useState } from "react";
const KEY = "careercopilot_resume";
export function useResume() { const [resume, setResume] = useState(() => { try { return JSON.parse(localStorage.getItem(KEY)); } catch { return null; } }); const saveResume = value => { localStorage.setItem(KEY, JSON.stringify(value)); setResume(value); }; return { resume, saveResume, hasResume: Boolean(resume?.id) }; }
