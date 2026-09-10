import type { CandidateListItem, GapAnalysisResponse, Position, SkillExtractionResponse } from "@/api/client";

export const mockCandidates: CandidateListItem[] = [
  {
    id: "c1",
    full_name: "Alice Johnson",
    email: "alice@example.com",
    current_role_title: "Senior Frontend Engineer",
    years_of_experience: 5,
    skills: [
      { id: "s1", skill_name: "React", category: "frontend", proficiency: "expert", years_used: 4 },
      { id: "s2", skill_name: "TypeScript", category: "frontend", proficiency: "advanced", years_used: 3 },
    ],
  },
  {
    id: "c2",
    full_name: "Bob Martinez",
    email: "bob@example.com",
    current_role_title: "Backend Engineer",
    years_of_experience: 3,
    skills: [
      { id: "s3", skill_name: "Python", category: "backend", proficiency: "advanced", years_used: 3 },
      { id: "s4", skill_name: "React", category: "frontend", proficiency: "intermediate", years_used: 1 },
    ],
  },
];

export const mockPositions: Position[] = [
  {
    id: "p1",
    title: "Senior React Developer",
    department: "Engineering",
    seniority: "senior",
    status: "open",
    description_raw: "We are looking for a senior React developer...",
    ai_summary: null,
    ai_seniority_suggestion: null,
    required_skills: [
      { id: "ps1", skill_name: "React", category: "frontend", is_required: true, min_proficiency: "advanced", confidence: "high", source: "ai" },
      { id: "ps2", skill_name: "TypeScript", category: "frontend", is_required: true, min_proficiency: "intermediate", confidence: "high", source: "ai" },
    ],
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "p2",
    title: "Python Backend Engineer",
    department: "Platform",
    seniority: "mid",
    status: "open",
    description_raw: "Looking for a Python backend engineer...",
    ai_summary: null,
    ai_seniority_suggestion: null,
    required_skills: [
      { id: "ps3", skill_name: "Python", category: "backend", is_required: true, min_proficiency: "intermediate", confidence: "high", source: "ai" },
    ],
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
];

export const mockGapAnalysisResult: GapAnalysisResponse = {
  candidate_id: "c1",
  candidate_name: "Alice Johnson",
  position_id: "p1",
  position_title: "Senior React Developer",
  score: 82,
  verdict: "Strong Match",
  seniority_fit: true,
  seniority_note: "Candidate's experience aligns with senior level.",
  fully_matched: [
    { skill_name: "React", min_proficiency: "advanced", is_required: true, candidate_proficiency: "expert" },
    { skill_name: "TypeScript", min_proficiency: "intermediate", is_required: true, candidate_proficiency: "advanced" },
  ],
  partial: [],
  missing: [],
  recommendations: ["Consider deepening system design knowledge for senior-level impact."],
  trace: [],
};

export const mockExtractionResult: SkillExtractionResponse = {
  skills: [
    { skill_name: "React", category: "frontend", is_required: true, min_proficiency: "advanced", confidence: "high" },
    { skill_name: "Node.js", category: "backend", is_required: false, min_proficiency: "intermediate", confidence: "medium" },
  ],
  summary: "Full-stack position requiring strong React skills and Node.js familiarity.",
  suggested_seniority: "senior",
};
