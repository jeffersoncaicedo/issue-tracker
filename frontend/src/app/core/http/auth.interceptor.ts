import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';

import { AuthService } from '../auth/auth.service';
import { API_BASE_URL } from '../config/api.config';

/**
 * Adjunta el JWT SOLO a peticiones dirigidas a nuestro API, para no filtrar
 * el token a dominios de terceros.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const baseUrl = inject(API_BASE_URL);
  const token = inject(AuthService).token();

  if (!token || !req.url.startsWith(baseUrl)) {
    return next(req);
  }
  return next(req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }));
};
