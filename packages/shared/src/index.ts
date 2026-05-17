/**
 * TypeScript mirror of Python schemas in lexguard_shared.
 * Keep field names and enum values in sync with Pydantic models.
 */

export type HealthStatus = "ok" | "degraded" | "error";

export interface HealthResponse {
  status: HealthStatus;
  service: string;
  version: string;
  timestamp: string;
}

export enum WsMessageType {
  Ping = "ping",
  Pong = "pong",
  Connected = "connected",
  Error = "error",
  Orchestrator = "orchestrator",
  Subscribe = "subscribe",
}

export interface WsEnvelope<T = Record<string, unknown>> {
  type: WsMessageType;
  payload: T;
  correlation_id?: string | null;
}

export type IngestionStatus = "pending" | "processing" | "completed" | "failed";

export interface DocumentSection {
  title: string;
  content: string;
  page: number | null;
  subsections: DocumentSection[];
}

export interface ParsedDocument {
  document_id: string;
  sections: DocumentSection[];
}

export interface IngestionJobResponse {
  document_id: string;
  status: IngestionStatus;
  message?: string | null;
}

export interface IngestionStatusResponse {
  document_id: string;
  status: IngestionStatus;
  error?: string | null;
  result?: ParsedDocument | null;
}

export type ClauseType =
  | "non_compete"
  | "arbitration"
  | "termination"
  | "confidentiality"
  | "intellectual_property"
  | "payment"
  | "liability"
  | "privacy"
  | "indemnification"
  | "other";

export interface ExtractedClause {
  clause_id: string;
  clause_type: ClauseType;
  title: string;
  text: string;
  obligations: string[];
  penalties: string[];
  rights: string[];
  durations: string[];
  financial_liabilities: string[];
  confidence: number;
}

export interface ClauseExtractionResult {
  document_id: string;
  clauses: ExtractedClause[];
}

export interface ClauseExtractionJobResponse {
  document_id: string;
  status: string;
  clause_count: number;
  message?: string | null;
}

export type RiskCategory =
  | "employment_risk"
  | "privacy_risk"
  | "financial_risk"
  | "ip_risk"
  | "arbitration_risk"
  | "compliance_risk";

export type RiskFlag =
  | "exploitative_language"
  | "vague_language"
  | "hidden_liability"
  | "one_sided_obligation"
  | "excessive_restriction";

export interface AffectedParty {
  party: string;
  role: string;
  impact: string;
  risk_level: string;
}

export interface RuleEvidence {
  rule_id: string;
  rule_name: string;
  matched_text: string;
  pattern: string;
  weight: number;
}

export interface RiskFinding {
  finding_id: string;
  clause_id: string;
  clause_title: string;
  category: RiskCategory;
  flag: RiskFlag;
  severity_score: number;
  confidence: number;
  plain_language_explanation: string;
  legal_reasoning: string;
  affected_parties: AffectedParty[];
  rule_evidence: RuleEvidence[];
  llm_enhanced: boolean;
}

export interface CategoryScore {
  category: RiskCategory;
  score: number;
  finding_count: number;
}

export interface DocumentRiskAnalysis {
  document_id: string;
  overall_severity_score: number;
  overall_confidence: number;
  summary: string;
  findings: RiskFinding[];
  category_scores: CategoryScore[];
}

export interface RiskAnalysisJobResponse {
  document_id: string;
  status: string;
  finding_count: number;
  overall_severity_score: number;
  message?: string | null;
}

export interface ConsequenceScenario {
  scenario: string;
  impact: string;
  likelihood: number;
  severity: number;
  explanation: string;
  clause_id: string;
  clause_title: string;
  finding_id?: string | null;
}

export interface ConsequenceSimulationResult {
  document_id: string;
  scenarios: ConsequenceScenario[];
  summary: string;
}

export interface ConsequenceSimulationJobResponse {
  document_id: string;
  status: string;
  scenario_count: number;
  message?: string | null;
}

export type FairnessLevel = "favorable" | "neutral" | "unfavorable";

export interface BenchmarkComparison {
  clause_id: string;
  clause_title: string;
  metric: string;
  benchmark_summary: string;
  contract_value: string;
  benchmark_range: string;
  deviation_score: number;
  fairness_assessment: FairnessLevel;
  is_outlier: boolean;
  similarity_score: number;
  comparative_explanation: string;
  negotiation_recommendation: string;
}

export interface DocumentBenchmarkResult {
  document_id: string;
  benchmark_summary: string;
  overall_deviation_score: number;
  overall_fairness: FairnessLevel;
  comparisons: BenchmarkComparison[];
  outlier_count: number;
}

export interface BenchmarkJobResponse {
  document_id: string;
  status: string;
  comparison_count: number;
  overall_deviation_score: number;
  message?: string | null;
}

export type AgentName =
  | "ingestion"
  | "extraction"
  | "risk"
  | "simulation"
  | "benchmark"
  | "negotiation";

export type AgentRunStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "skipped"
  | "retrying";

export type PipelineStatus = "pending" | "running" | "completed" | "failed" | "partial";

export interface AgentRunState {
  agent: AgentName;
  status: AgentRunStatus;
  progress: number;
  message: string;
  error?: string | null;
}

export type OrchestratorEventType =
  | "run_started"
  | "agent_started"
  | "agent_progress"
  | "agent_completed"
  | "agent_failed"
  | "agent_retrying"
  | "run_completed"
  | "run_failed";

export interface OrchestratorEvent {
  type: OrchestratorEventType;
  document_id: string;
  run_id: string;
  agent?: AgentName | null;
  message: string;
  progress: number;
  payload: Record<string, unknown>;
  timestamp: string;
}

export interface AnalysisState {
  document_id: string;
  run_id: string;
  status: PipelineStatus;
  agents: Record<string, AgentRunState>;
  parsed_document?: ParsedDocument | null;
  clauses?: ClauseExtractionResult | null;
  risk?: DocumentRiskAnalysis | null;
  consequences?: ConsequenceSimulationResult | null;
  benchmarks?: DocumentBenchmarkResult | null;
  negotiation?: NegotiationResult | null;
  overall_progress: number;
  errors: Record<string, string>;
}

export interface PipelineRunResponse {
  document_id: string;
  run_id: string;
  status: PipelineStatus;
  message?: string | null;
}

export type NegotiationPriority = "critical" | "high" | "medium" | "low";

export interface NegotiationRecommendation {
  topic: string;
  priority: NegotiationPriority;
  current_term: string;
  suggested_term: string;
  rationale: string;
  clause_id?: string | null;
}

export interface NegotiationResult {
  document_id: string;
  summary: string;
  overall_leverage: string;
  recommendations: NegotiationRecommendation[];
}
