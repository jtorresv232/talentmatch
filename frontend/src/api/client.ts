import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type SkillCategory =
  | "frontend" | "backend" | "cloud" | "devops" | "database"
  | "mobile" | "testing" | "architecture" | "soft_skill" | "other";

export type Proficiency = "beginner" | "intermediate" | "advanced" | "expert";
export type Seniority = "junior" | "mid" | "senior" | "lead" | "principal";
export type PositionStatus = "open" | "on_hold" | "filled" | "closed";
export type Confidence = "high" | "medium" | "low";

export interface CandidateSkill {
  id: string;
  skill_name: string;
  category: SkillCategory;
  proficiency: Proficiency;
  years_used: number | null;
}

export interface Candidate {
  id: string;
  full_name: string;
  email: string;
  years_of_experience: number;
  current_role_title: string;
  summary: string | null;
  skills: CandidateSkill[];
  created_at: string;
  updated_at: string;
}

export interface CandidateListItem extends Omit<Candidate, "summary" | "created_at" | "updated_at"> {}

export interface PositionSkill {
  id: string;
  skill_name: string;
  category: SkillCategory;
  is_required: boolean;
  min_proficiency: Proficiency;
  confidence: Confidence;
  source: string;
}

export interface Position {
  id: string;
  title: string;
  department: string;
  seniority: Seniority;
  status: PositionStatus;
  description_raw: string;
  ai_summary: string | null;
  ai_seniority_suggestion: string | null;
  required_skills: PositionSkill[];
  created_at: string;
  updated_at: string;
}

export interface ExtractedSkillItem {
  skill_name: string;
  category: SkillCategory;
  is_required: boolean;
  min_proficiency: Proficiency;
  confidence: Confidence;
}

export interface SkillExtractionResponse {
  skills: ExtractedSkillItem[];
  summary: string;
  suggested_seniority: string;
  trace: Record<string, unknown>[];
}

export interface CandidateRecommendation {
  candidate_id: string;
  candidate_name: string;
  current_role_title: string;
  years_of_experience: number;
  match_score: number;
  matched_skills: string[];
  missing_skills: string[];
  partial_skills: string[];
  rationale: string;
  suitability_verdict: string;
}

export interface PositionRecommendation {
  position_id: string;
  position_title: string;
  department: string;
  seniority: Seniority;
  match_score: number;
  matched_skills: string[];
  missing_skills: string[];
  partial_skills: string[];
  rationale: string;
  suitability_verdict: string;
}

export interface SkillGapItem {
  skill_name: string;
  min_proficiency: Proficiency;
  is_required: boolean;
  candidate_proficiency: Proficiency | null;
}

export interface GapAnalysisResponse {
  candidate_id: string;
  candidate_name: string;
  position_id: string;
  position_title: string;
  score: number;
  verdict: string;
  seniority_fit: boolean;
  seniority_note: string;
  fully_matched: SkillGapItem[];
  partial: SkillGapItem[];
  missing: SkillGapItem[];
  recommendations: string[];
  trace: Record<string, unknown>[];
}

// ---------------------------------------------------------------------------
// Candidates
// ---------------------------------------------------------------------------

export const candidatesApi = {
  list: (params?: { skill_name?: string; category?: string; min_proficiency?: string }) =>
    api.get<CandidateListItem[]>("/candidates", { params }).then((r) => r.data),
  get: (id: string) =>
    api.get<Candidate>(`/candidates/${id}`).then((r) => r.data),
  create: (data: unknown) =>
    api.post<Candidate>("/candidates", data).then((r) => r.data),
  update: (id: string, data: unknown) =>
    api.patch<Candidate>(`/candidates/${id}`, data).then((r) => r.data),
  delete: (id: string) =>
    api.delete(`/candidates/${id}`),
  recommendPositions: (id: string, top_n = 5) =>
    api.post<PositionRecommendation[]>(`/candidates/${id}/recommend-positions`, null, { params: { top_n } }).then((r) => r.data),
};

// ---------------------------------------------------------------------------
// Positions
// ---------------------------------------------------------------------------

export const positionsApi = {
  list: (params?: { status?: string; seniority?: string }) =>
    api.get<Position[]>("/positions", { params }).then((r) => r.data),
  get: (id: string) =>
    api.get<Position>(`/positions/${id}`).then((r) => r.data),
  create: (data: unknown) =>
    api.post<Position>("/positions", data).then((r) => r.data),
  update: (id: string, data: unknown) =>
    api.patch<Position>(`/positions/${id}`, data).then((r) => r.data),
  extractSkills: (id: string, jd_text: string) =>
    api.post<Position>(`/positions/${id}/extract-skills`, { jd_text }).then((r) => r.data),
  delete: (id: string) =>
    api.delete(`/positions/${id}`).then((r) => r.data),
  recommendCandidates: (id: string, top_n = 5) =>
    api.post<CandidateRecommendation[]>(`/positions/${id}/recommend-candidates`, null, { params: { top_n } }).then((r) => r.data),
};

// ---------------------------------------------------------------------------
// Extraction (standalone)
// ---------------------------------------------------------------------------

export const extractionApi = {
  extract: (jd_text: string) =>
    api.post<SkillExtractionResponse>("/extract-skills", { jd_text }).then((r) => r.data),
};

// ---------------------------------------------------------------------------
// Gap Analysis
// ---------------------------------------------------------------------------

export const gapAnalysisApi = {
  analyze: (candidate_id: string, position_id: string) =>
    api.post<GapAnalysisResponse>("/gap-analysis", { candidate_id, position_id }).then((r) => r.data),
};

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export const healthApi = {
  check: () =>
    axios.get<{ status: string }>("/health").then((r) => r.data),
};

export default api;
