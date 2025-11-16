import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import ProgressTracker from "../components/ProgressTracker";
import ResultsTable from "../components/ResultsTable";
import SummaryCards from "../components/SummaryCards";


export default function Dashboard() {
const { id } = useParams();
const [results, setResults] = useState([]);


const fetchResults = async () => {
const res = await fetch(`/results/${id}?limit=100`);
const data = await res.json();
setResults(data.results);
};


useEffect(() => {
const interval = setInterval(fetchResults, 3000);
return () => clearInterval(interval);
}, []);


return (
<div className="p-10">
<h1 className="text-3xl font-bold mb-4">Dashboard</h1>
<ProgressTracker uploadId={id} />
<SummaryCards results={results} />
<ResultsTable results={results} />
</div>
);
}