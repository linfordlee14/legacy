"use client";

/**
 * Session context. The workspace shell (step 12, MVP-012) binds this to the
 * real OIDC session; until then the token is injectable, and non-production
 * environments offer a manual token field (see DevTokenGate).
 */

import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";

type Session = {
  token: string | null;
  setToken: (token: string | null) => void;
};

const SessionContext = createContext<Session>({ token: null, setToken: () => {} });

export function SessionProvider({
  children,
  initialToken = null,
}: {
  children: ReactNode;
  initialToken?: string | null;
}) {
  const [token, setTokenState] = useState<string | null>(initialToken);
  const setToken = useCallback((next: string | null) => setTokenState(next), []);
  const value = useMemo(() => ({ token, setToken }), [token, setToken]);
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): Session {
  return useContext(SessionContext);
}
