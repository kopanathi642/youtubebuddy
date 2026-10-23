import { isAxiosError } from 'axios';

/**
 * Extract a human-readable message from any thrown value.
 * Prefers the FastAPI `detail` field (string or validation-error list)
 * over axios' generic "Request failed with status code 4xx".
 */
export function getErrorMessage(error: unknown, fallback = 'Something went wrong. Please try again.'): string {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string' && detail) return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0];
      if (first && typeof first.msg === 'string') return first.msg;
    }
    if (!error.response) return 'Cannot reach the server. Check your connection and try again.';
    if (error.response.status === 413) return 'That file is too large.';
    if (error.response.status >= 500) return 'The server hit an error. Please try again shortly.';
  }
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}
