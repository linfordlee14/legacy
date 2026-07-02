type EnvFooterProps = {
  environment?: string;
};

/**
 * DEP-06 (deployment/DEPLOYMENT.md): environment identity is visible in the
 * UI footer for non-production environments. Production renders nothing.
 * A missing value renders as "unset" so misconfiguration is visible, never silent.
 */
export function EnvFooter({
  environment = process.env.NEXT_PUBLIC_LEGACY_ENV,
}: EnvFooterProps) {
  if (environment === "production") {
    return null;
  }
  return (
    <footer data-testid="env-footer" style={{ marginTop: "auto", padding: "0.5rem 1rem" }}>
      <small>environment: {environment ?? "unset"}</small>
    </footer>
  );
}
