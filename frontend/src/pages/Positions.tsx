import { positionsApi, type Position } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Briefcase, Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const SENIORITIES = ["", "junior", "mid", "senior", "lead", "principal"];
const STATUSES = ["", "open", "on_hold", "filled", "closed"];

const STATUS_COLOR: Record<string, string> = {
  open: "success",
  on_hold: "warning",
  filled: "secondary",
  closed: "secondary",
};

const STATUS_LABEL: Record<string, string> = {
  open: "Open",
  on_hold: "On Hold",
  filled: "Filled",
  closed: "Closed",
};

export default function Positions() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState("");
  const [seniority, setSeniority] = useState("");

  const fetchPositions = async () => {
    setLoading(true);
    try {
      const data = await positionsApi.list({
        status: status || undefined,
        seniority: seniority || undefined,
      });
      setPositions(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchPositions(); }, []);

  const grouped = positions.reduce<Record<string, Position[]>>((acc, p) => {
    (acc[p.status] ??= []).push(p);
    return acc;
  }, {});

  const groupOrder = ["open", "on_hold", "filled", "closed"];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Positions</h1>
          <p className="text-muted-foreground text-sm mt-1">{positions.length} positions</p>
        </div>
        <Button asChild>
          <Link to="/positions/new"><Plus className="w-4 h-4 mr-2" />Add Position</Link>
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-44">
          <option value="">All statuses</option>
          {STATUSES.filter(Boolean).map((s) => <option key={s} value={s}>{STATUS_LABEL[s] ?? s}</option>)}
        </Select>
        <Select value={seniority} onChange={(e) => setSeniority(e.target.value)} className="w-44">
          <option value="">All seniorities</option>
          {SENIORITIES.filter(Boolean).map((s) => <option key={s} value={s}>{s}</option>)}
        </Select>
        <Button variant="outline" onClick={fetchPositions}>Filter</Button>
      </div>

      {loading ? (
        <p className="text-muted-foreground text-sm">Loading...</p>
      ) : positions.length === 0 ? (
        <p className="text-muted-foreground text-sm">No positions found.</p>
      ) : (
        <div className="space-y-8">
          {groupOrder.filter((g) => grouped[g]?.length).map((group) => (
            <div key={group}>
              <h2 className="text-base font-semibold mb-3 flex items-center gap-2">
                <Badge variant={(STATUS_COLOR[group] as "success" | "warning" | "secondary") ?? "secondary"}>
                  {STATUS_LABEL[group]}
                </Badge>
                <span className="text-muted-foreground text-sm font-normal">{grouped[group].length} position{grouped[group].length !== 1 ? "s" : ""}</span>
              </h2>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {grouped[group].map((p) => (
                  <Link key={p.id} to={`/positions/${p.id}`}>
                    <Card className="hover:border-primary/50 transition-colors cursor-pointer h-full">
                      <CardHeader className="pb-3">
                        <div className="flex items-start gap-3">
                          <div className="rounded-full bg-primary/10 p-2">
                            <Briefcase className="w-4 h-4 text-primary" />
                          </div>
                          <div className="min-w-0">
                            <CardTitle className="text-base truncate">{p.title}</CardTitle>
                            <p className="text-sm text-muted-foreground truncate">{p.department}</p>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
                          <span className="capitalize">{p.seniority}</span>
                          <span>·</span>
                          <span>{p.required_skills.length} skills</span>
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {p.required_skills.slice(0, 4).map((s) => (
                            <Badge key={s.id} variant="secondary" className="text-xs">{s.skill_name}</Badge>
                          ))}
                          {p.required_skills.length > 4 && (
                            <Badge variant="outline" className="text-xs">+{p.required_skills.length - 4}</Badge>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
