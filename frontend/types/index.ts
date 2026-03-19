export interface ScreeningResult {
  id?: number;
  resume_filename: string;
  similarity_score: number;
  full_name: string;
  university_name: string;
  national_or_international: string;
  email_id: string;
  github_link: string;
  phone_number: string;
  company_names: string[];
  technical_skills: string[];
  soft_skills: string[];
  total_experience: string;
  location: string;
  screening_date?: string;
  // LangGraph pipeline fields
  analysis_depth: string;
  jd_domain: string;
  jd_seniority: string;
  skill_gaps: string[];
  red_flags: string[];
  interview_questions: string[];
  overall_recommendation: string;
}

export interface ScreeningBatchResponse {
  total_resumes: number;
  results: ScreeningResult[];
  message: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}
