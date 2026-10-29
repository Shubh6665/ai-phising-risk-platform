import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { AnalysisForm } from "../src/components/AnalysisForm";

describe("AnalysisForm Component", () => {
  it("renders form controls, labels, and accessible placeholders", () => {
    const handleSubmit = vi.fn();
    const handleReset = vi.fn();

    render(
      <AnalysisForm
        onSubmit={handleSubmit}
        isLoading={false}
        onReset={handleReset}
        hasResult={false}
      />
    );

    expect(screen.getByLabelText(/Email Subject/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email Body Content/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Analyze Email/i })).toBeInTheDocument();
  });

  it("prevents submission and displays validation error on empty or whitespace text", async () => {
    const handleSubmit = vi.fn();
    const handleReset = vi.fn();

    render(
      <AnalysisForm
        onSubmit={handleSubmit}
        isLoading={false}
        onReset={handleReset}
        hasResult={false}
      />
    );

    const submitBtn = screen.getByRole("button", { name: /Analyze Email/i });
    fireEvent.click(submitBtn);

    expect(handleSubmit).not.toHaveBeenCalled();
    expect(
      screen.getByText(/Email body text cannot be empty or whitespace only/i)
    ).toBeInTheDocument();

    // Whitespace only
    const textarea = screen.getByLabelText(/Email Body Content/i);
    await userEvent.type(textarea, "   \n  \t ");
    fireEvent.click(submitBtn);

    expect(handleSubmit).not.toHaveBeenCalled();
  });

  it("submits valid email content with optional subject", async () => {
    const handleSubmit = vi.fn().mockResolvedValue(undefined);
    const handleReset = vi.fn();

    render(
      <AnalysisForm
        onSubmit={handleSubmit}
        isLoading={false}
        onReset={handleReset}
        hasResult={false}
      />
    );

    const subjectInput = screen.getByLabelText(/Email Subject/i);
    const bodyInput = screen.getByLabelText(/Email Body Content/i);
    const submitBtn = screen.getByRole("button", { name: /Analyze Email/i });

    await userEvent.type(subjectInput, "Payroll Update Required");
    await userEvent.type(bodyInput, "Please confirm your direct deposit details immediately.");

    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(handleSubmit).toHaveBeenCalledTimes(1);
      expect(handleSubmit).toHaveBeenCalledWith({
        subject: "Payroll Update Required",
        text: "Please confirm your direct deposit details immediately.",
      });
    });
  });

  it("prevents duplicate submissions while loading is true", () => {
    const handleSubmit = vi.fn();
    const handleReset = vi.fn();

    render(
      <AnalysisForm
        onSubmit={handleSubmit}
        isLoading={true}
        onReset={handleReset}
        hasResult={false}
      />
    );

    const submitBtn = screen.getByRole("button", { name: /Analyzing Signals/i });
    expect(submitBtn).toBeDisabled();

    fireEvent.click(submitBtn);
    expect(handleSubmit).not.toHaveBeenCalled();
  });

  it("loads pre-configured phishing and legitimate sample emails", () => {
    const handleSubmit = vi.fn();
    const handleReset = vi.fn();

    render(
      <AnalysisForm
        onSubmit={handleSubmit}
        isLoading={false}
        onReset={handleReset}
        hasResult={false}
      />
    );

    const phishingBtn = screen.getByRole("button", { name: /Phishing Sample/i });
    fireEvent.click(phishingBtn);

    const subjectInput = screen.getByLabelText(/Email Subject/i);
    const bodyInput = screen.getByLabelText(/Email Body Content/i);

    expect(subjectInput).toHaveValue("URGENT: Unauthorized access detected on your corporate account");
    expect(bodyInput.getAttribute("value") || (bodyInput as HTMLTextAreaElement).value).toContain("http://192.168.1.100:8080");

    const legitBtn = screen.getByRole("button", { name: /Legitimate Sample/i });
    fireEvent.click(legitBtn);

    expect(subjectInput).toHaveValue("Q3 Engineering All-Hands Meeting Agenda and Slides");
  });

  it("clears inputs and invokes onReset when Clear button is clicked", async () => {
    const handleSubmit = vi.fn();
    const handleReset = vi.fn();

    render(
      <AnalysisForm
        onSubmit={handleSubmit}
        isLoading={false}
        onReset={handleReset}
        hasResult={true}
      />
    );

    const bodyInput = screen.getByLabelText(/Email Body Content/i);
    await userEvent.type(bodyInput, "Test email body");

    const clearBtn = screen.getByRole("button", { name: /Clear/i });
    fireEvent.click(clearBtn);

    expect(handleReset).toHaveBeenCalledTimes(1);
    expect(bodyInput).toHaveValue("");
  });
});
