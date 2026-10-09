/** Error normalizado que consumen los componentes (independiente de HttpClient). */
export interface ApiError {
  readonly status: number;
  readonly code: string;
  readonly message: string;
}

export function isApiError(value: unknown): value is ApiError {
  return (
    typeof value === 'object' &&
    value !== null &&
    'status' in value &&
    'code' in value &&
    'message' in value
  );
}
