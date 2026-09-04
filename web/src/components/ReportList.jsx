import { useEffect, useState } from "react";

const REPORTS_URL = `${import.meta.env.BASE_URL}reports/index.json`;

export default function ReportList() {
  const [reports, setReports] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(REPORTS_URL)
      .then((res) => res.json())
      .then(setReports)
      .catch(() => setError("Couldn't load the report list."));
  }, []);

  if (error) return <div className="section empty">{error}</div>;
  if (reports === null) return <div className="section empty">Loading...</div>;

  return (
    <div className="section">
      <h2>Reports</h2>
      {reports.length === 0 ? (
        <div className="empty">No digests sent yet.</div>
      ) : (
        reports.map((r) => (
          <div className="report-row" key={r.id}>
            <a href={`#/report/${r.id}`}>{r.subject}</a>
            <div className="meta">
              {new Date(r.sent_at).toLocaleString()} &middot; {r.mover_count} movers,{" "}
              {r.injury_count} injuries, {r.disagreement_count} disagreements,{" "}
              {r.news_count} news
            </div>
          </div>
        ))
      )}
    </div>
  );
}
