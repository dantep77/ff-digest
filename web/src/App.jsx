import { useEffect, useState } from "react";
import ReportList from "./components/ReportList.jsx";
import ReportDetail from "./components/ReportDetail.jsx";

function useHashRoute() {
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const onHashChange = () => setHash(window.location.hash);
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);
  return hash;
}

export default function App() {
  const hash = useHashRoute();
  const match = hash.match(/^#\/report\/(.+)$/);

  return (
    <div className="container">
      <h1>FF Digest Archive</h1>
      <p className="subtitle">Past fantasy football digests</p>
      {match ? <ReportDetail id={match[1]} /> : <ReportList />}
      <p className="footer">ff-digest &middot; generated automatically</p>
    </div>
  );
}
