import React from "react";


export default function ResultsTable({ results }) {
return (
<table className="w-full bg-white shadow rounded">
<thead>
<tr className="text-left bg-gray-100">
<th className="p-3">Email</th>
<th className="p-3">Status</th>
<th className="p-3">Score</th>
</tr>
</thead>
<tbody>
{results.map((r, i) => (
<tr key={i} className="border-b">
<td className="p-3">{r.email}</td>
<td className="p-3 capitalize">{r.status}</td>
<td className="p-3">{r.score}</td>
</tr>
))}
</tbody>
</table>
);
}