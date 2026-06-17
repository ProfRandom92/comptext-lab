export function LoadingState({ label = 'Loading operational telemetry…' }: { label?: string }) {
  return <div className="loading" role="status"><span className="skeleton" /> <p>{label}</p></div>;
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return <div className="error" role="alert"><h3>Telemetry unavailable</h3><p>{message}</p>{onRetry ? <button className="button" onClick={onRetry}>Retry</button> : null}</div>;
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return <div className="empty"><h3>{title}</h3><p>{description}</p></div>;
}
