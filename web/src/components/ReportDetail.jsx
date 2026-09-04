import { useEffect, useState } from "react";

export default function ReportDetail({ id }) {
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setReport(null);
    setError(null);
    fetch(`${import.meta.env.BASE_URL}reports/${id}.json`)
      .then((res) => {
        if (!res.ok) throw new Error("not found");
        return res.json();
      })
      .then(setReport)
      .catch(() => setError("Couldn't load that report."));
  }, [id]);

  if (error) return <div className="section empty">{error}</div>;
  if (!report) return <div className="section empty">Loading...</div>;

  return (
    <>
      <a className="back-link" href="#/">
        &larr; Back to all reports
      </a>

      <p className="subtitle">
        {new Date(report.sent_at).toLocaleString()} &middot; {report.scoring} scoring
      </p>

      <Section title="Ranking Movers" empty="No significant movers this pull.">
        {report.movers.map((i, idx) => (
          <div className="insight" key={idx}>
            <span className="player">{i.player_name}</span> <span className="position">{i.position}</span>
            <br />
            {i.detail}
          </div>
        ))}
      </Section>

      <Section title="Injury Watch" empty="No injury status changes.">
        {report.injuries.map((i, idx) => (
          <div className="insight" key={idx}>
            <span className="player">{i.player_name}</span>
            <br />
            {i.detail}
          </div>
        ))}
      </Section>

      <Section title="Expert Disagreement" empty="No high-disagreement players this pull.">
        {report.disagreements.map((i, idx) => (
          <div className="insight" key={idx}>
            <span className="player">{i.player_name}</span> <span className="position">{i.position}</span>
            <br />
            {i.detail}
          </div>
        ))}
      </Section>

      <Section title="Top News" empty="No new stories since the last pull.">
        {report.news.map((n) => (
          <div className="news-item" key={n.item_id}>
            <a href={n.link} target="_blank" rel="noreferrer">
              {n.title}
            </a>
          </div>
        ))}
      </Section>

      {report.narrative && (
        <div className="section">
          <h2>Summary</h2>
          <p style={{ fontSize: 14, lineHeight: 1.5 }}>{report.narrative}</p>
        </div>
      )}
    </>
  );
}

function Section({ title, empty, children }) {
  const hasContent = Array.isArray(children) ? children.length > 0 : Boolean(children);
  return (
    <div className="section">
      <h2>{title}</h2>
      {hasContent ? children : <div className="empty">{empty}</div>}
    </div>
  );
}
