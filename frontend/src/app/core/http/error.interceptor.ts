import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { AuthService } from '../auth/auth.service';
import { ApiError } from '../models/api-error.model';

const FALLBACK_MESSAGES: Record<number, string> = {
  0: 'No se pudo conectar con el servidor. Verifique su conexión e intente de nuevo.',
  401: 'Su sesión no es válida. Inicie sesión nuevamente.',
  403: 'No tiene permisos para realizar esta acción.',
  404: 'El recurso solicitado no existe.',
  503: 'El servicio no está disponible en este momento. Intente más tarde.',
};

interface BackendErrorBody {
  error?: { code?: string; message?: string };
}

/** Convierte cualquier `HttpErrorResponse` en un `ApiError` uniforme. */
export function toApiError(error: HttpErrorResponse): ApiError {
  const body = (error.error ?? {}) as BackendErrorBody;
  return {
    status: error.status,
    code: body.error?.code ?? (error.status === 0 ? 'network_error' : 'http_error'),
    message:
      body.error?.message ??
      FALLBACK_MESSAGES[error.status] ??
      'Ocurrió un error inesperado. Intente más tarde.',
  };
}

/**
 * Manejo centralizado de errores HTTP:
 *  - 401 en rutas protegidas → limpia la sesión y redirige al login.
 *  - Todo error se normaliza a `ApiError` para que la UI muestre un mensaje claro.
 */
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  return next(req).pipe(
    catchError((err: unknown) => {
      if (!(err instanceof HttpErrorResponse)) return throwError(() => err);

      const isAuthCall = req.url.endsWith('/auth/login') || req.url.endsWith('/auth/logout');
      if (err.status === 401 && !isAuthCall) {
        auth.clearSession();
        void router.navigate(['/login'], { queryParams: { reason: 'expired' } });
      }
      return throwError(() => toApiError(err));
    }),
  );
};
