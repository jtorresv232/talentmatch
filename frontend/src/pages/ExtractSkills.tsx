import { extractionApi, positionsApi, type ExtractedSkillItem, type Position } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Sparkles } from "lucide-react";
import { useEffect, useState } from "react";

const CONFIDENCE_COLOR: Record<string, "success" | "warning" | "secondary"> = {
  high: "success",
  medium: "warning",
  low: "secondary",
};

export default function ExtractSkills() {
  const [jdText, setJdText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<{ skills: ExtractedSkillItem[]; summary: string; suggested_seniority: string } | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [selectedPosition, setSelectedPosition] = useState("");
  const [applying, setApplying] = useState(false);
  const [applySuccess, setApplySuccess] = useState(false);

  useEffect(() => {
    positionsApi.list({ status: "open" }).then(setPositions).catch(() => {});
  }, []);

  const handleExtract = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jdText.trim()) return;
    setError("");
    setResult(null);
    setApplySuccess(false);
    setLoading(true);
    try {
      const data = await extractionApi.extract(jdText.trim());
      setResult(data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? "Extraction failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async () => {
    if (!selectedPosition) return;
    setApplying(true);
    setApplySuccess(false);
    try {
      await positionsApi.extractSkills(selectedPosition, jdText.trim());
      setApplySuccess(true);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? "Failed to apply skills to position.");
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Extract Skills from Job Description</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Paste a job description and let AI extract the required skills automatically.
        </p>
      </div>

      <form onSubmit={handleExtract} className="space-y-4">
        <div className="space-y-1.5">
          <Label>Job Description *</Label>
          <textarea
            className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring min-h-[240px] resize-y font-mono"
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            placeholder="Paste the full job description here..."
            required
          />
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button type="submit" disabled={loading || !jdText.trim()}>
          <Sparkles className="w-4 h-4 mr-2" />
          {loading ? "Extracting..." : "Extract Skills"}
        </Button>
      </form>

      {result && (
        <div className="space-y-4">
          {/* Summary */}
          <Card>
            <CardHeader><CardTitle>AI Summary</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm">{result.summary}</p>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span className="font-medium">Suggested seniority:</span>
                <Badge variant="info" className="capitalize">{result.suggested_seniority}</Badge>
              </div>
            </CardContent>
          </Card>

          {/* Skills table */}
          <Card>
            <CardHeader>
              <CardTitle>Extracted Skills ({result.skills.length})</CardTitle>
            </CardHeader>
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
                    {result.skills.map((s, i) => (
                      <tr key={i} className="border-b last:border-0">
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
                        <td className="py-2">
                          <Badge variant={CONFIDENCE_COLOR[s.confidence] ?? "secondary"}>
                            {s.confidence}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Apply to position */}
          <Card>
            <CardHeader><CardTitle>Apply to Position</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Save these extracted skills directly to an open position.
              </p>
              <div className="flex gap-3 items-end">
                <div className="flex-1 space-y-1.5">
                  <Label>Select Position</Label>
                  <Select value={selectedPosition} onChange={(e) => setSelectedPosition(e.target.value)}>
                    <option value="">Choose a position...</option>
                    {positions.map((p) => (
                      <option key={p.id} value={p.id}>{p.title} — {p.department}</option>
                    ))}
                  </Select>
                </div>
                <Button
                  type="button"
                  onClick={handleApply}
                  disabled={!selectedPosition || applying}
                  variant="outline"
                >
                  {applying ? "Applying..." : "Apply Skills"}
                </Button>
              </div>
              {applySuccess && (
                <p className="text-sm text-green-600 font-medium">
                  Skills applied successfully to the selected position.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
