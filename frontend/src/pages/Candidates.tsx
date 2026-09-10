import { candidatesApi, type CandidateListItem } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Briefcase, Plus, Search, User } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const CATEGORIES = ["", "frontend", "backend", "cloud", "devops", "database", "mobile", "testing", "architecture"];
const PROFICIENCIES = ["", "beginner", "intermediate", "advanced", "expert"];

export default function Candidates() {
  const [candidates, setCandidates] = useState<CandidateListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [skillName, setSkillName] = useState("");
  const [category, setCategory] = useState("");
  const [minProficiency, setMinProficiency] = useState("");

  const fetchCandidates = async () => {
    setLoading(true);
    try {
      const data = await candidatesApi.list({
        skill_name: skillName || undefined,
        category: category || undefined,
        min_proficiency: minProficiency || undefined,
      });
      setCandidates(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchCandidates(); }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Talent Bank</h1>
          <p className="text-muted-foreground text-sm mt-1">{candidates.length} candidates</p>
        </div>
        <Button asChild>
          <Link to="/candidates/new"><Plus className="w-4 h-4 mr-2" />Add Candidate</Link>
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by skill..."
            className="pl-8"
            value={skillName}
            onChange={(e) => setSkillName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && fetchCandidates()}
          />
        </div>
        <Select value={category} onChange={(e) => setCategory(e.target.value)} className="w-44">
          <option value="">All categories</option>
          {CATEGORIES.filter(Boolean).map((c) => <option key={c} value={c}>{c}</option>)}
        </Select>
        <Select value={minProficiency} onChange={(e) => setMinProficiency(e.target.value)} className="w-44">
          <option value="">Any proficiency</option>
          {PROFICIENCIES.filter(Boolean).map((p) => <option key={p} value={p}>{p}</option>)}
        </Select>
        <Button variant="outline" onClick={fetchCandidates}>Search</Button>
      </div>

      {/* List */}
      {loading ? (
        <p className="text-muted-foreground text-sm">Loading...</p>
      ) : candidates.length === 0 ? (
        <p className="text-muted-foreground text-sm">No candidates found.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {candidates.map((c) => (
            <Link key={c.id} to={`/candidates/${c.id}`}>
              <Card className="hover:border-primary/50 transition-colors cursor-pointer h-full">
                <CardHeader className="pb-3">
                  <div className="flex items-start gap-3">
                    <div className="rounded-full bg-primary/10 p-2">
                      <User className="w-4 h-4 text-primary" />
                    </div>
                    <div className="min-w-0">
                      <CardTitle className="text-base truncate">{c.full_name}</CardTitle>
                      <p className="text-sm text-muted-foreground truncate">{c.current_role_title}</p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-3">
                    <Briefcase className="w-3.5 h-3.5" />
                    {c.years_of_experience} years experience
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {c.skills.slice(0, 4).map((s) => (
                      <Badge key={s.id} variant="secondary" className="text-xs">{s.skill_name}</Badge>
                    ))}
                    {c.skills.length > 4 && (
                      <Badge variant="outline" className="text-xs">+{c.skills.length - 4}</Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
