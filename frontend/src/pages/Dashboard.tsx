import { candidatesApi, positionsApi, type CandidateListItem, type Position } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Briefcase, TrendingUp, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

interface TopSkill {
  name: string;
  count: number;
}

function computeTopSkills(candidates: CandidateListItem[], top = 8): TopSkill[] {
  const freq: Record<string, number> = {};
  for (const c of candidates) {
    for (const s of c.skills) {
      freq[s.skill_name] = (freq[s.skill_name] ?? 0) + 1;
    }
  }
  return Object.entries(freq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, top)
    .map(([name, count]) => ({ name, count }));
}

export default function Dashboard() {
  const [candidates, setCandidates] = useState<CandidateListItem[]>([]);
  const [openPositions, setOpenPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      candidatesApi.list(),
      positionsApi.list({ status: "open" }),
    ]).then(([c, p]) => {
      setCandidates(c);
      setOpenPositions(p);
    }).finally(() => setLoading(false));
  }, []);

  const topSkills = computeTopSkills(candidates);
  const recent = candidates.slice(0, 6);

  if (loading) return <p className="text-muted-foreground p-8">Loading...</p>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground text-sm mt-1">TalentMatch AI — talent intelligence overview</p>
      </div>

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Users className="w-4 h-4" />
              Total Candidates
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">{candidates.length}</p>
            <Link to="/candidates" className="text-xs text-primary hover:underline mt-1 inline-block">
              View all →
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Briefcase className="w-4 h-4" />
              Open Positions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">{openPositions.length}</p>
            <Link to="/positions" className="text-xs text-primary hover:underline mt-1 inline-block">
              View all →
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Skills Tracked
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">
              {candidates.reduce((sum, c) => sum + c.skills.length, 0)}
            </p>
            <p className="text-xs text-muted-foreground mt-1">across all candidates</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Top skills */}
        <Card>
          <CardHeader><CardTitle>Top Skills in Talent Bank</CardTitle></CardHeader>
          <CardContent>
            {topSkills.length === 0 ? (
              <p className="text-sm text-muted-foreground">No skills recorded yet.</p>
            ) : (
              <div className="space-y-2">
                {topSkills.map((s) => (
                  <div key={s.name} className="flex items-center gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="text-sm font-medium truncate">{s.name}</span>
                        <span className="text-xs text-muted-foreground ml-2 shrink-0">{s.count}</span>
                      </div>
                      <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full"
                          style={{ width: `${(s.count / (topSkills[0]?.count || 1)) * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent candidates */}
        <Card>
          <CardHeader><CardTitle>Recent Candidates</CardTitle></CardHeader>
          <CardContent>
            {recent.length === 0 ? (
              <p className="text-sm text-muted-foreground">No candidates yet.</p>
            ) : (
              <div className="divide-y">
                {recent.map((c) => (
                  <Link
                    key={c.id}
                    to={`/candidates/${c.id}`}
                    className="flex items-center justify-between py-2.5 hover:bg-accent/50 -mx-2 px-2 rounded-md transition-colors"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{c.full_name}</p>
                      <p className="text-xs text-muted-foreground truncate">{c.current_role_title}</p>
                    </div>
                    <div className="flex gap-1 ml-3 shrink-0">
                      {c.skills.slice(0, 2).map((s) => (
                        <Badge key={s.id} variant="secondary" className="text-xs">{s.skill_name}</Badge>
                      ))}
                      {c.skills.length > 2 && (
                        <Badge variant="outline" className="text-xs">+{c.skills.length - 2}</Badge>
                      )}
                    </div>
                  </Link>
                ))}
              </div>
            )}
            {candidates.length > 6 && (
              <Link to="/candidates" className="text-xs text-primary hover:underline mt-3 inline-block">
                View all {candidates.length} candidates →
              </Link>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Open positions quick view */}
      {openPositions.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Open Positions</CardTitle></CardHeader>
          <CardContent>
            <div className="divide-y">
              {openPositions.slice(0, 5).map((p) => (
                <Link
                  key={p.id}
                  to={`/positions/${p.id}`}
                  className="flex items-center justify-between py-2.5 hover:bg-accent/50 -mx-2 px-2 rounded-md transition-colors"
                >
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate">{p.title}</p>
                    <p className="text-xs text-muted-foreground truncate">{p.department} · {p.seniority}</p>
                  </div>
                  <Badge variant="success" className="text-xs ml-3 shrink-0">Open</Badge>
                </Link>
              ))}
            </div>
            {openPositions.length > 5 && (
              <Link to="/positions" className="text-xs text-primary hover:underline mt-3 inline-block">
                View all {openPositions.length} open positions →
              </Link>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
