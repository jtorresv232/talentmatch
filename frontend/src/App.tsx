import { BrowserRouter, Link, NavLink, Route, Routes } from "react-router-dom";
import { cn } from "@/lib/utils";
import Candidates from "@/pages/Candidates";
import CandidateDetail from "@/pages/CandidateDetail";
import CandidateForm from "@/pages/CandidateForm";
import Positions from "@/pages/Positions";
import PositionDetail from "@/pages/PositionDetail";
import PositionForm from "@/pages/PositionForm";
import ExtractSkills from "@/pages/ExtractSkills";
import GapAnalysis from "@/pages/GapAnalysis";
import Dashboard from "@/pages/Dashboard";

const NAV_LINKS = [
  { to: "/", label: "Dashboard" },
  { to: "/candidates", label: "Talent Bank" },
  { to: "/positions", label: "Positions" },
  { to: "/extract-skills", label: "Extract Skills" },
  { to: "/gap-analysis", label: "Gap Analysis" },
];

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b bg-white sticky top-0 z-10">
        <div className="container flex items-center gap-8 h-14">
          <Link to="/" className="font-bold text-primary text-lg tracking-tight">
            TalentMatch AI
          </Link>
          <nav className="flex items-center gap-1">
            {NAV_LINKS.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                className={({ isActive }) =>
                  cn(
                    "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent"
                  )
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="flex-1 container py-6">{children}</main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout><Dashboard /></Layout>} />
        <Route path="/candidates" element={<Layout><Candidates /></Layout>} />
        <Route path="/candidates/new" element={<Layout><CandidateForm /></Layout>} />
        <Route path="/candidates/:id" element={<Layout><CandidateDetail /></Layout>} />
        <Route path="/candidates/:id/edit" element={<Layout><CandidateForm /></Layout>} />
        <Route path="/positions" element={<Layout><Positions /></Layout>} />
        <Route path="/positions/new" element={<Layout><PositionForm /></Layout>} />
        <Route path="/positions/:id" element={<Layout><PositionDetail /></Layout>} />
        <Route path="/positions/:id/edit" element={<Layout><PositionForm /></Layout>} />
        <Route path="/extract-skills" element={<Layout><ExtractSkills /></Layout>} />
        <Route path="/gap-analysis" element={<Layout><GapAnalysis /></Layout>} />
      </Routes>
    </BrowserRouter>
  );
}
