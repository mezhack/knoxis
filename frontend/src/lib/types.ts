export interface User {
  id: number;
  name: string;
  email: string;
}

export interface Organization {
  id: number;
  name: string;
  slug: string;
  city?: string;
  state?: string;
}

export interface MeResponse {
  user: User;
  current_organization: Organization | null;
  role: string;
}

export interface Election {
  id: number;
  name: string;
  description?: string;
  status: ElectionStatus;
  scheduled_for?: string;
  final_rule: "manual" | "max_count";
  max_escrutinios?: number;
  positions_count?: number;
  voters_count?: number;
  current_escrutinio_number?: number;
  positions?: Position[];
  started_at?: string;
  ended_at?: string;
}

export type ElectionStatus =
  | "rascunho"
  | "pronta"
  | "em_andamento"
  | "encerrada"
  | "cancelada";

export interface Position {
  id: number;
  name: string;
  vacancies: number;
  display_order: number;
  candidates_count?: number;
}

export interface Candidate {
  id: number;
  name: string;
  display_order: number;
}

export interface Voter {
  id: number;
  name: string;
  cpf_masked: string;
}

export interface Escrutinio {
  id: number;
  number: number;
  status: "preparando" | "aberto" | "encerrado";
  is_final: boolean;
  opened_at?: string;
  closed_at?: string;
  total_voters?: number;
  voters_so_far?: number;
}

export interface EscrutinioDetail extends Escrutinio {
  positions: {
    position: { id: number; name: string };
    vacancies_remaining: number;
    candidates: { id: number; name: string }[];
  }[];
}

export interface CandidateResult {
  id: number;
  name: string;
  votes: number;
  elected: boolean;
  tie_at_cutoff: boolean;
}

export interface PositionResult {
  position: { id: number; name: string };
  vacancies: number;
  threshold: number | null;
  candidates: CandidateResult[];
  remaining_vacancies: number;
  tie_pending: boolean;
}

export interface CloseResult {
  escrutinio: { id: number; status: string; total_voters: number };
  results: PositionResult[];
  election_status: ElectionStatus;
}

export interface ParciaisData {
  etag: string;
  voters_so_far: number;
  positions: {
    position: { id: number; name: string; vacancies_remaining: number };
    candidates: { id: number; name: string; votes: number }[];
  }[];
}

export interface BallotPosition {
  id: number;
  name: string;
  vacancies: number;
  candidates: { id: number; name: string }[];
}

export interface BallotData {
  escrutinio_number: number;
  positions: BallotPosition[];
}

export interface PublicElectionData {
  election: {
    id?: number;
    name: string;
    organization_name: string;
    organization_slug?: string;
    status: ElectionStatus;
  };
  current_escrutinio: { id?: number; number: number; status: string } | null;
  message?: string;
}

export interface RelatorioData {
  election: {
    id: number;
    name: string;
    organization: { name: string; city?: string; state?: string };
  };
  escrutinio: {
    id: number;
    number: number;
    is_final: boolean;
    opened_at: string;
    closed_at: string;
  };
  totals: {
    voters: number;
    previous_voters?: number;
    abstention?: number;
  };
  positions: {
    position: { id: number; name: string };
    vacancies_in_round: number;
    threshold: number | null;
    candidates: { id: number; name: string; votes: number; elected: boolean }[];
  }[];
}
