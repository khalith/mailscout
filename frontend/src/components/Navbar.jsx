import React from "react";
import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="bg-white border-b p-4 flex gap-6 shadow">
      <Link to="/">Home</Link>
      <Link to="/upload">Upload</Link>
      <Link to="/dashboard">Dashboard</Link>
      <Link to="/results">Results</Link>
    </nav>
  );
}
