export const ISSUE_STATUSES = ['open', 'in_progress', 'completed'] as const;
export const ISSUE_PRIORITIES = ['high', 'medium', 'low'] as const;

export type IssueStatus = (typeof ISSUE_STATUSES)[number];
export type IssuePriority = (typeof ISSUE_PRIORITIES)[number];

export interface Issue {
  readonly id: string;
  readonly title: string;
  readonly description: string;
  readonly priority: IssuePriority;
  readonly status: IssueStatus;
  readonly created_by: string;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface CreateIssueRequest {
  readonly title: string;
  readonly description: string;
  readonly priority: IssuePriority;
}

export type UpdateIssueRequest = Partial<Pick<Issue, 'status' | 'priority'>>;

export interface IssueFilters {
  readonly status: IssueStatus | null;
  readonly priority: IssuePriority | null;
}

export interface IssueSummary {
  readonly total: number;
  readonly open: number;
  readonly in_progress: number;
  readonly completed: number;
}

export const EMPTY_FILTERS: IssueFilters = { status: null, priority: null };

export interface IssueStats {
  readonly total: number;
  readonly by_status: Readonly<Record<IssueStatus, number>>;
  readonly by_priority: Readonly<Record<IssuePriority, number>>;
  readonly matrix: Readonly<Record<IssueStatus, Readonly<Record<IssuePriority, number>>>>;
}
