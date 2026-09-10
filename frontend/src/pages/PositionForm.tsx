import { positionsApi, type Position } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

const SENIORITIES = ["junior", "mid", "senior", "lead", "principal"];
const STATUSES = ["open", "on_hold", "filled", "closed"];

export default function PositionForm() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [title, setTitle] = useState("");
  const [department, setDepartment] = useState("");
  const [seniority, setSeniority] = useState("mid");
  const [status, setStatus] = useState("open");
  const [descriptionRaw, setDescriptionRaw] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    positionsApi.get(id).then((p: Position) => {
      setTitle(p.title);
      setDepartment(p.department);
      setSeniority(p.seniority);
      setStatus(p.status);
      setDescriptionRaw(p.description_raw ?? "");
    });
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    const payload = {
      title,
      department,
      seniority,
      status,
      description_raw: descriptionRaw,
    };
    try {
      if (isEdit && id) {
        await positionsApi.update(id, payload);
        navigate(`/positions/${id}`);
      } else {
        const created = await positionsApi.create(payload);
        navigate(`/positions/${(created as Position).id}`);
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? "An error occurred. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/positions"><ArrowLeft className="w-4 h-4 mr-1" />Back</Link>
        </Button>
        <h1 className="text-xl font-bold">{isEdit ? "Edit Position" : "Add Position"}</h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader><CardTitle>Position Details</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2 space-y-1.5">
                <Label>Title *</Label>
                <Input value={title} onChange={(e) => setTitle(e.target.value)} required placeholder="e.g. Senior Frontend Engineer" />
              </div>
              <div className="space-y-1.5">
                <Label>Department *</Label>
                <Input value={department} onChange={(e) => setDepartment(e.target.value)} required placeholder="e.g. Engineering" />
              </div>
              <div className="space-y-1.5">
                <Label>Seniority *</Label>
                <Select value={seniority} onChange={(e) => setSeniority(e.target.value)}>
                  {SENIORITIES.map((s) => <option key={s} value={s}>{s}</option>)}
                </Select>
              </div>
              {isEdit && (
                <div className="space-y-1.5">
                  <Label>Status</Label>
                  <Select value={status} onChange={(e) => setStatus(e.target.value)}>
                    {STATUSES.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
                  </Select>
                </div>
              )}
            </div>
            <div className="space-y-1.5">
              <Label>Job Description</Label>
              <textarea
                className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring min-h-[200px] resize-y font-mono"
                value={descriptionRaw}
                onChange={(e) => setDescriptionRaw(e.target.value)}
                placeholder="Paste the full job description here. After saving, use 'Extract Skills' on the position detail page to run AI skill extraction."
              />
            </div>
          </CardContent>
        </Card>

        {error && <p className="text-sm text-destructive">{error}</p>}
        <div className="flex gap-3">
          <Button type="submit" disabled={saving}>
            {saving ? "Saving..." : isEdit ? "Save Changes" : "Create Position"}
          </Button>
          <Button type="button" variant="outline" onClick={() => navigate(isEdit ? `/positions/${id}` : "/positions")}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}
