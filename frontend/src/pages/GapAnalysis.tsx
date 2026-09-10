import { candidatesApi, gapAnalysisApi, positionsApi, type CandidateListItem, type GapAnalysisResponse, type Position } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { CheckCircle2, CircleDashed, XCircle } from "lucide-react";
import { useEffect, useState } from "react";

const VERDICT_STYLE: Record<string, { bg: string; text: string; border: string }> = {
  "Strong Match":   { bg: "bg-green-50",  text: "text-green-800",  border: "border-green-300" },
  "Moderate Match": { bg: "bg-blue-50",   text: "text-blue-800",   border: "border-blue-300"  },
  "Weak Match":     { bg: "bg-yellow-50", text: "text-yellow-800", border: "border-yellow-300" },
  "Not Suitable":   { bg: "bg-red-50",    text: "text-red-800",    border: "border-red-300"   },
};

export default function GapAnalysis() {
  const [candidates, setCandidates] = useState<CandidateListItem[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [candidateId, setCandidateId] = useState("");
  const [positionId, setPositionId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<GapAnalysisResponse | null>(null);

  useEffect(() => {
    candidatesApi.list().then(setCandidates).catch(() => {});
    positionsApi.list().then(setPositions).catch(() => {});
  }, []);

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!candidateId || !positionId) return;
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const data = await gapAnalysisApi.analyze(candidateId, positionId);
      setResult(data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? "Gap analysis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const verdictStyle = result ? (VERDICT_STYLE[result.verdict] ?? { bg: "bg-muted", text: "text-foreground", border: "border-border" }) : null;

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Gap Analysis</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Compare a candidate's skills against a position's requirements to identify gaps and get recommendations.
        </p>
      </div>

      {/* Selectors */}
      <form onSubmit={handleRun}>
        <Card>
          <CardContent className="pt-6">
            <div className="grid grid-cols-2 gap-4 items-end">
              <div className="space-y-1.5">
                <Label>Candidate *</Label>
                <Select value={candidateId} onChange={(e) => setCandidateId(e.target.value)} required>
                  <option value="">Select a candidate...</option>
                  {candidates.map((c) => (
                    <option key={c.id} value={c.id}>{c.full_name} — {c.current_role_title}</option>
                  ))}
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Position *</Label>
                <Select value={positionId} onChange={(e) => setPositionId(e.target.value)} required>
                  <option value="">Select a position...</option>
                  {positions.map((p) => (
                    <option key={p.id} value={p.id}>{p.title} — {p.department}</option>
                  ))}
                </Select>
              </div>
            </div>
            {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
            <div className="mt-4">
              <Button type="submit" disabled={loading || !candidateId || !positionId}>
                {loading ? "Analyzing..." : "Run Gap Analysis"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>

      {result && verdictStyle && (
        <div className="space-y-4">
          {/* Verdict banner */}
          <div className={`rounded-lg border p-5 ${verdictStyle.bg} ${verdictStyle.border}`}>
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-1">
                  {result.candidate_name} → {result.position_title}
                </p>
                <p className={`text-2xl font-bold ${verdictStyle.text}`}>{result.verdict}</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {result.seniority_fit ? "Seniority: fit" : "Seniority: mismatch"} · {result.seniority_note}
                </p>
              </div>
              <div className="text-right">
                <p className={`text-5xl font-bold ${verdictStyle.text}`}>{result.score.toFixed(0)}</p>
                <p className="text-xs text-muted-foreground">/ 100</p>
              </div>
            </div>
            <div className="mt-4 h-2.5 rounded-full bg-white/60 overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${result.score}%`,
                  backgroundColor: result.score >= 70 ? "#22c55e" : result.score >= 45 ? "#3b82f6" : result.score >= 20 ? "#eab308" : "#ef4444",
                }}
              />
            </div>
          </div>

          {/* Skill buckets */}
          <div className="grid grid-cols-3 gap-4">
            {/* Fully matched */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2 text-green-700">
                  <CheckCircle2 className="w-4 h-4" />
                  Matched ({result.fully_matched.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-1.5">
                {result.fully_matched.length === 0 ? (
                  <p className="text-xs text-muted-foreground">None</p>
                ) : result.fully_matched.map((s) => (
                  <div key={s.skill_name} className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium truncate">{s.skill_name}</span>
                    <Badge variant="success" className="text-xs shrink-0">{s.candidate_proficiency}</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Partial */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2 text-yellow-700">
                  <CircleDashed className="w-4 h-4" />
                  Partial ({result.partial.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-1.5">
                {result.partial.length === 0 ? (
                  <p className="text-xs text-muted-foreground">None</p>
                ) : result.partial.map((s) => (
                  <div key={s.skill_name} className="space-y-0.5">
                    <span className="text-sm font-medium block truncate">{s.skill_name}</span>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <span>{s.candidate_proficiency}</span>
                      <span>→ need</span>
                      <Badge variant="warning" className="text-xs">{s.min_proficiency}</Badge>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Missing */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2 text-red-700">
                  <XCircle className="w-4 h-4" />
                  Missing ({result.missing.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-1.5">
                {result.missing.length === 0 ? (
                  <p className="text-xs text-muted-foreground">None</p>
                ) : result.missing.map((s) => (
                  <div key={s.skill_name} className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium truncate">{s.skill_name}</span>
                    <Badge variant={s.is_required ? "destructive" : "outline"} className="text-xs shrink-0">
                      {s.is_required ? "required" : "preferred"}
                    </Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Recommendations */}
          {result.recommendations.length > 0 && (
            <Card>
              <CardHeader><CardTitle>Recommendations</CardTitle></CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {result.recommendations.map((rec, i) => (
                    <li key={i} className="flex gap-3 text-sm">
                      <span className="mt-0.5 shrink-0 w-5 h-5 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center">{i + 1}</span>
                      <span className="leading-relaxed">{rec}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
