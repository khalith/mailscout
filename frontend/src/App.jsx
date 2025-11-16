import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Upload from "./pages/Upload";
import Results from "./pages/Results";

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <div className="p-6 max-w-4xl mx-auto">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/results/:id" element={<Results />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
