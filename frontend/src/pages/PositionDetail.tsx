import { positionsApi, type CandidateRecommendation, type Position } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Briefcase, Pencil, Sparkles, Star, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

const STATUS_COLOR: Record<string, "success" | "warning" | "secondary"> = {
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

const VERDICT_COLOR: Record<string, string> = {
  "Strong Match": "bg-green-100 text-green-800",
  "Moderate Match": "bg-blue-100 text-blue-800",
  "Weak Match": "bg-yellow-100 text-yellow-800",
  "Not Suitable": "bg-red-100 text-red-800",
};

export default function PositionDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [position, setPosition] = useState<Position | null>(null);
  const [recommendations, setRecommendations] = useState<CandidateRecommendation[]>([]);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [showRecs, setShowRecs] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [extractError, setExtractError] = useState("");

  useEffect(() => {
    if (id) positionsApi.get(id).then(setPosition);
  }, [id]);

  const handleDelete = async () => {
    if (!id || !confirm("Delete this position?")) return;
    await positionsApi.delete(id);
    navigate("/positions");
  };

  const handleReExtract = async () => {
    if (!id || !position?.description_raw) return;
    setExtracting(true);
    setExtractError("");
    try {
      const updated = await positionsApi.extractSkills(id, position.description_raw);
      setPosition(updated);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setExtractError(msg ?? "Extraction failed.");
    } finally {
      setExtracting(false);
    }
  };

  const handleFindCandidates = async () => {
    if (!id) return;
    setLoadingRecs(true);
    setShowRecs(true);
    try {
      const data = await positionsApi.recommendCandidates(id, 5);
      setRecommendations(data);
    } finally {
      setLoadingRecs(false);
    }
  };

  if (!position) return <p className="text-muted-foreground p-8">Loading...</p>;

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/positions"><ArrowLeft className="w-4 h-4 mr-1" />Back</Link>
        </Button>
        <div className="flex-1" />
        <Button variant="outline" size="sm" asChild>
          <Link to={`/positions/${id}/edit`}><Pencil className="w-4 h-4 mr-1.5" />Edit</Link>
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={handleReExtract}
          disabled={extracting || !position?.description_raw}
          title={!position?.description_raw ? "No job description to extract from" : undefined}
        >
          <Sparkles className="w-4 h-4 mr-1.5" />
          {extracting ? "Extracting..." : "Re-extract Skills"}
        </Button>
        <Button variant="destructive" size="sm" onClick={handleDelete}>
          <Trash2 className="w-4 h-4 mr-1.5" />Delete
        </Button>
      </div>

      {extractError && <p className="text-sm text-destructive">{extractError}</p>}

      {/* Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-xl">{position.title}</CardTitle>
              <p className="text-muted-foreground mt-1">{position.department}</p>
            </div>
            <Button onClick={handleFindCandidates} disabled={loadingRecs}>
              <Star className="w-4 h-4 mr-2" />
              {loadingRecs ? "Searching..." : "Find Candidates"}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <Briefcase className="w-4 h-4" />
              <span className="capitalize">{position.seniority}</span>
            </span>
            <Badge variant={STATUS_COLOR[position.status] ?? "secondary"}>
              {STATUS_LABEL[position.status] ?? position.status}
            </Badge>
          </div>
          {position.ai_summary && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">AI Summary</p>
              <p className="text-sm">{position.ai_summary}</p>
            </div>
          )}
          {position.description_raw && (
            <details>
              <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground">
                Job Description
              </summary>
              <pre className="mt-2 text-xs bg-muted rounded-md p-3 whitespace-pre-wrap font-sans leading-relaxed">
                {position.description_raw}
              </pre>
            </details>
          )}
        </CardContent>
      </Card>

      {/* Skills */}
      <Card>
        <CardHeader><CardTitle>Required Skills ({position.required_skills.length})</CardTitle></CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-muted-foreground">
                  <th className="text-left py-2 pr-4 font-medium">Skill</th>
                  <th className="text-left py-2 pr-4 font-medium">Category</th>
                  <th className="text-left py-2 pr-4 font-medium">Min Proficiency</th>
                  <th className="text-left py-2 pr-4 font-medium">Type</th>
                  <th className="text-left py-2 font-medium">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {position.required_skills.map((s) => (
                  <tr key={s.id} className="border-b last:border-0">
                    <td className="py-2 pr-4 font-medium">{s.skill_name}</td>
                    <td className="py-2 pr-4 text-muted-foreground">{s.category}</td>
                    <td className="py-2 pr-4">
                      <Badge variant="secondary">{s.min_proficiency}</Badge>
                    </td>
                    <td className="py-2 pr-4">
                      <Badge variant={s.is_required ? "info" : "outline"}>
                        {s.is_required ? "Required" : "Preferred"}
                      </Badge>
                    </td>
                    <td className="py-2 text-muted-foreground">{s.confidence}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Recommended Candidates */}
      {showRecs && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">Recommended Candidates</h2>
          {loadingRecs ? (
            <p className="text-muted-foreground text-sm">Analyzing fit...</p>
          ) : recommendations.length === 0 ? (
            <p className="text-muted-foreground text-sm">No matching candidates found.</p>
          ) : (
            recommendations.map((rec) => (
              <Card key={rec.candidate_id}>
                <CardContent className="pt-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-semibold">{rec.candidate_name}</p>
                      <p className="text-sm text-muted-foreground">{rec.current_role_title} · {rec.years_of_experience} yrs exp</p>
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
                  <div className="mt-3">
                    <Button variant="outline" size="sm" asChild>
                      <Link to={`/candidates/${rec.candidate_id}`}>View Profile</Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  );
}
