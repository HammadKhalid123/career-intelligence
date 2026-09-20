import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import AppShell from "./components/AppShell";
import Chat from "./pages/Chat";
import Dashboard from "./pages/Dashboard";
import Learning from "./pages/Learning";
import History from "./pages/History";
import MatchReport from "./pages/MatchReport";
import Roadmap from "./pages/Roadmap";
import Upload from "./pages/Upload";

export default function App() {
  return (
    <BrowserRouter><Routes><Route element={<AppShell />}>
      <Route path="/" element={<Dashboard />} /><Route path="/resume" element={<Upload />} />
      <Route path="/match" element={<MatchReport />} /><Route path="/roadmap" element={<Roadmap />} /><Route path="/history" element={<History />} />
      <Route path="/chat" element={<Chat />} /><Route path="/learning" element={<Learning />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Route></Routes></BrowserRouter>
  );
}
