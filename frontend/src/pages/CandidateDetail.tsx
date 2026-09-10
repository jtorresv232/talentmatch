import { candidatesApi, type Candidate, type PositionRecommendation } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Briefcase, Mail, Pencil, Star, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

const PROFICIENCY_COLOR: Record<string, "success" | "info" | "warning" | "secondary"> = {
  expert: "success",
  advanced: "info",
  intermediate: "warning",
  beginner: "secondary",
};

const VERDICT_COLOR: Record<string, string> = {
  "Strong Match": "bg-green-100 text-green-800",
  "Moderate Match": "bg-blue-100 text-blue-800",
  "Weak Match": "bg-yellow-100 text-yellow-800",
  "Not Suitable": "bg-red-100 text-red-800",
};

export default function CandidateDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [recommendations, setRecommendations] = useState<PositionRecommendation[]>([]);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [showRecs, setShowRecs] = useState(false);

  useEffect(() => {
    if (id) candidatesApi.get(id).then(setCandidate);
  }, [id]);

  const handleDelete = async () => {
    if (!id || !confirm("Delete this candidate?")) return;
    await candidatesApi.delete(id);
    navigate("/candidates");
  };

  const handleFindPositions = async () => {
    if (!id) return;
    setLoadingRecs(true);
    setShowRecs(true);
    try {
      const data = await candidatesApi.recommendPositions(id, 5);
      setRecommendations(data);
    } finally {
      setLoadingRecs(false);
    }
  };

  if (!candidate) return <p className="text-muted-foreground p-8">Loading...</p>;

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/candidates"><ArrowLeft className="w-4 h-4 mr-1" />Back</Link>
        </Button>
        <div className="flex-1" />
        <Button variant="outline" size="sm" asChild>
          <Link to={`/candidates/${id}/edit`}><Pencil className="w-4 h-4 mr-1.5" />Edit</Link>
        </Button>
        <Button variant="destructive" size="sm" onClick={handleDelete}>
          <Trash2 className="w-4 h-4 mr-1.5" />Delete
        </Button>
      </div>

      {/* Profile */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-xl">{candidate.full_name}</CardTitle>
              <p className="text-muted-foreground mt-1">{candidate.current_role_title}</p>
            </div>
            <Button onClick={handleFindPositions} disabled={loadingRecs}>
              <Star className="w-4 h-4 mr-2" />
              {loadingRecs ? "Searching..." : "Find Positions"}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1.5"><Mail className="w-4 h-4" />{candidate.email}</span>
            <span className="flex items-center gap-1.5"><Briefcase className="w-4 h-4" />{candidate.years_of_experience} years experience</span>
          </div>
          {candidate.summary && <p className="text-sm">{candidate.summary}</p>}
        </CardContent>
      </Card>

      {/* Skills */}
      <Card>
        <CardHeader><CardTitle>Skills ({candidate.skills.length})</CardTitle></CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-muted-foreground">
                  <th className="text-left py-2 pr-4 font-medium">Skill</th>
                  <th className="text-left py-2 pr-4 font-medium">Category</th>
                  <th className="text-left py-2 pr-4 font-medium">Proficiency</th>
                  <th className="text-left py-2 font-medium">Years Used</th>
                </tr>
              </thead>
              <tbody>
                {candidate.skills.map((s) => (
                  <tr key={s.id} className="border-b last:border-0">
                    <td className="py-2 pr-4 font-medium">{s.skill_name}</td>
                    <td className="py-2 pr-4 text-muted-foreground">{s.category}</td>
                    <td className="py-2 pr-4">
                      <Badge variant={PROFICIENCY_COLOR[s.proficiency] ?? "secondary"}>
                        {s.proficiency}
                      </Badge>
                    </td>
                    <td className="py-2 text-muted-foreground">{s.years_used ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Recommended Positions */}
      {showRecs && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">Recommended Positions</h2>
          {loadingRecs ? (
            <p className="text-muted-foreground text-sm">Analyzing fit...</p>
          ) : recommendations.length === 0 ? (
            <p className="text-muted-foreground text-sm">No matching positions found.</p>
          ) : (
            recommendations.map((rec) => (
              <Card key={rec.position_id}>
                <CardContent className="pt-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-semibold">{rec.position_title}</p>
                      <p className="text-sm text-muted-foreground">{rec.department} · {rec.seniority}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-2xl font-bold text-primary">{rec.match_score.toFixed(0)}</p>
                      <p className="text-xs text-muted-foreground">/ 100</p>
                    </div>
                  </div>
                  <div className="mt-3">
                    <div className="h-2 rounded-full bg-secondary overflow-hidden">
                      <div className="h-full bg-primary rounded-full" style={{ width: `${rec.match_score}%` }} />
                    </div>
                  </div>
                  <span className={`mt-2 inline-block text-xs font-semibold px-2 py-0.5 rounded-full ${VERDICT_COLOR[rec.suitability_verdict] ?? ""}`}>
                    {rec.suitability_verdict}
                  </span>
                  {rec.matched_skills.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {rec.matched_skills.map((s) => <Badge key={s} variant="success" className="text-xs">{s}</Badge>)}
                      {rec.missing_skills.map((s) => <Badge key={s} variant="destructive" className="text-xs">{s}</Badge>)}
                    </div>
                  )}
                  <details className="mt-3 text-sm">
                    <summary className="cursor-pointer text-muted-foreground hover:text-foreground">Rationale</summary>
                    <p className="mt-2 text-muted-foreground leading-relaxed">{rec.rationale}</p>
                  </details>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  );
}
