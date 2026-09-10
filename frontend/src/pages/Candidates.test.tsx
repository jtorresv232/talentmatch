import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { candidatesApi } from "@/api/client";
import { mockCandidates } from "@/test/fixtures";
import Candidates from "./Candidates";

vi.mock("@/api/client");

describe("Candidates", () => {
  beforeEach(() => {
    vi.mocked(candidatesApi.list).mockResolvedValue(mockCandidates);
  });

  it("renders the page heading", async () => {
    render(<MemoryRouter><Candidates /></MemoryRouter>);
    expect(await screen.findByText("Talent Bank")).toBeInTheDocument();
  });

  it("renders candidate cards", async () => {
    render(<MemoryRouter><Candidates /></MemoryRouter>);
    expect(await screen.findByText("Alice Johnson")).toBeInTheDocument();
    expect(screen.getByText("Bob Martinez")).toBeInTheDocument();
  });

  it("shows candidate count", async () => {
    render(<MemoryRouter><Candidates /></MemoryRouter>);
    expect(await screen.findByText("2 candidates")).toBeInTheDocument();
  });

  it("renders filter controls", async () => {
    render(<MemoryRouter><Candidates /></MemoryRouter>);
    await screen.findByText("Talent Bank");
    expect(screen.getByPlaceholderText("Search by skill...")).toBeInTheDocument();
    expect(screen.getByText("All categories")).toBeInTheDocument();
    expect(screen.getByText("Any proficiency")).toBeInTheDocument();
  });

  it("shows Add Candidate link", async () => {
    render(<MemoryRouter><Candidates /></MemoryRouter>);
    await screen.findByText("Talent Bank");
    expect(screen.getByRole("link", { name: /Add Candidate/i })).toBeInTheDocument();
  });
});
