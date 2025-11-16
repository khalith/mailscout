// frontend/src/pages/Results.jsx
import React from "react";
import { useParams } from "react-router-dom";

export default function Results() {
  const { id } = useParams();

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Results for Upload ID: {id}</h2>
      <p className="text-gray-600">
        Soon this will show results fetched from the backend API.
      </p>
    </div>
  );
}
