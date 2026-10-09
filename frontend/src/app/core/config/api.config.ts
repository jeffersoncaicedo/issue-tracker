import { InjectionToken } from '@angular/core';

import { environment } from '../../../environments/environment';

/** URL base del API. Se inyecta como token para poder sustituirla en pruebas. */
export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL', {
  providedIn: 'root',
  factory: () => environment.apiUrl,
});
