import React from "react";


export default function SummaryCards({ results }) {
const valid = results.filter(r => r.status === "accept").length;
const invalid = results.filter(r => r.status === "reject").length;
const risky = results.filter(r => r.status === "greylist").length;


return (
<div className="grid grid-cols-3 gap-4 mb-6">
<div className="p-4 bg-white shadow rounded text-center">
<h2 className="text-lg font-bold">Valid</h2>
<p className="text-2xl">{valid}</p>
</div>
<div className="p-4 bg-white shadow rounded text-center">
<h2 className="text-lg font-bold">Invalid</h2>
<p className="text-2xl">{invalid}</p>
</div>
<div className="p-4 bg-white shadow rounded text-center">
<h2 className="text-lg font-bold">Risky</h2>
<p className="text-2xl">{risky}</p>
</div>
</div>
);
}