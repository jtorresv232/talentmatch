import { candidatesApi, type Candidate } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

const CATEGORIES = ["frontend", "backend", "cloud", "devops", "database", "mobile", "testing", "architecture", "soft_skill", "other"];
const PROFICIENCIES = ["beginner", "intermediate", "advanced", "expert"];

interface SkillRow {
  skill_name: string;
  category: string;
  proficiency: string;
  years_used: string;
}

const emptySkill = (): SkillRow => ({ skill_name: "", category: "frontend", proficiency: "intermediate", years_used: "" });

export default function CandidateForm() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [years, setYears] = useState("");
  const [roleTitle, setRoleTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [skills, setSkills] = useState<SkillRow[]>([emptySkill()]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    candidatesApi.get(id).then((c: Candidate) => {
      setFullName(c.full_name);
      setEmail(c.email);
      setYears(String(c.years_of_experience));
      setRoleTitle(c.current_role_title);
      setSummary(c.summary ?? "");
      setSkills(c.skills.map((s) => ({
        skill_name: s.skill_name,
        category: s.category,
        proficiency: s.proficiency,
        years_used: s.years_used != null ? String(s.years_used) : "",
      })));
    });
  }, [id]);

  const updateSkill = (index: number, field: keyof SkillRow, value: string) => {
    setSkills((prev) => prev.map((s, i) => i === index ? { ...s, [field]: value } : s));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    const payload = {
      full_name: fullName,
      email,
      years_of_experience: parseInt(years),
      current_role_title: roleTitle,
      summary: summary || null,
      skills: skills
        .filter((s) => s.skill_name.trim())
        .map((s) => ({
          skill_name: s.skill_name.trim(),
          category: s.category,
          proficiency: s.proficiency,
          years_used: s.years_used ? parseInt(s.years_used) : null,
        })),
    };
    try {
      if (isEdit && id) {
        await candidatesApi.update(id, payload);
        navigate(`/candidates/${id}`);
      } else {
        const created = await candidatesApi.create(payload);
        navigate(`/candidates/${created.id}`);
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
          <Link to="/candidates"><ArrowLeft className="w-4 h-4 mr-1" />Back</Link>
        </Button>
        <h1 className="text-xl font-bold">{isEdit ? "Edit Candidate" : "Add Candidate"}</h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader><CardTitle>Profile</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Full Name *</Label>
                <Input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
              </div>
              <div className="space-y-1.5">
                <Label>Email *</Label>
                <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
              </div>
              <div className="space-y-1.5">
                <Label>Current Role Title *</Label>
                <Input value={roleTitle} onChange={(e) => setRoleTitle(e.target.value)} required />
              </div>
              <div className="space-y-1.5">
                <Label>Years of Experience *</Label>
                <Input type="number" min={0} max={50} value={years} onChange={(e) => setYears(e.target.value)} required />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Summary</Label>
              <textarea
                className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring min-h-[80px] resize-y"
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                placeholder="Brief professional summary..."
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Skills</CardTitle>
              <Button type="button" variant="outline" size="sm" onClick={() => setSkills((p) => [...p, emptySkill()])}>
                <Plus className="w-4 h-4 mr-1" />Add Skill
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {skills.map((skill, i) => (
              <div key={i} className="grid grid-cols-[1fr_1fr_1fr_80px_36px] gap-2 items-end">
                <div className="space-y-1">
                  {i === 0 && <Label className="text-xs">Skill Name</Label>}
                  <Input
                    placeholder="e.g. React"
                    value={skill.skill_name}
                    onChange={(e) => updateSkill(i, "skill_name", e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  {i === 0 && <Label className="text-xs">Category</Label>}
                  <Select value={skill.category} onChange={(e) => updateSkill(i, "category", e.target.value)}>
                    {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
                  </Select>
                </div>
                <div className="space-y-1">
                  {i === 0 && <Label className="text-xs">Proficiency</Label>}
                  <Select value={skill.proficiency} onChange={(e) => updateSkill(i, "proficiency", e.target.value)}>
                    {PROFICIENCIES.map((p) => <option key={p} value={p}>{p}</option>)}
                  </Select>
                </div>
                <div className="space-y-1">
                  {i === 0 && <Label className="text-xs">Yrs Used</Label>}
                  <Input
                    type="number"
                    min={0}
                    max={50}
                    placeholder="—"
                    value={skill.years_used}
                    onChange={(e) => updateSkill(i, "years_used", e.target.value)}
                  />
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="text-destructive hover:text-destructive mt-auto"
                  onClick={() => setSkills((p) => p.filter((_, idx) => idx !== i))}
                  disabled={skills.length === 1}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>

        {error && <p className="text-sm text-destructive">{error}</p>}
        <div className="flex gap-3">
          <Button type="submit" disabled={saving}>{saving ? "Saving..." : isEdit ? "Save Changes" : "Create Candidate"}</Button>
          <Button type="button" variant="outline" onClick={() => navigate(isEdit ? `/candidates/${id}` : "/candidates")}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}
