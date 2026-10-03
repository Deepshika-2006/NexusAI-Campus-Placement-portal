# NexusAI Full-Stack Hiring Flow — V9 Audit Checklist

## 1. Student applies
- Student logs in.
- Student opens a job.
- Student applies and attaches/selects a resume.
- Application appears in Applications.
- Recruiter sees the exact resume attached to that application.

## 2. Recruiter screening
- Recruiter opens Candidates.
- Recruiter reviews profile, ATS score, match score, tests and submitted resume.
- Recruiter can move an application into Screening or Shortlisted.
- Recruiter cannot manually create Interview status from the generic status dropdown.
- Recruiter cannot mark Selected before a finalized interview with Selected decision.

## 3. Schedule interview
- Recruiter can schedule only after Shortlisted.
- Interview date/time must be in the future.
- Scheduling creates one interview and changes application status to Interview.
- Opening the same candidate again shows the existing interview instead of another Schedule Interview action.
- Repeated/rapid scheduling requests are protected by a database transaction/row lock.

## 4. Student receives interview
- Student sees the interview in Interview Center.
- Student sees the question, schedule, duration and optional meeting link.
- Before response: status is Scheduled and the page says response is pending.

## 5. Student submits response
- Student submits non-empty response.
- Response is saved to the specific interview.
- Interview becomes In Progress.
- Student is redirected back to the interview page.
- Student sees Response Submitted.
- Student cannot submit a second response.
- Refreshing the page keeps the submitted response.

## 6. Recruiter receives response
- Recruiter sees Response Received.
- Evaluation is unlocked only after a response exists.
- Recruiter cannot evaluate an unanswered interview through POST manipulation.
- Candidate's exact response is displayed.

## 7. Pending evaluation
- Recruiter can enter 0–10 scores.
- Invalid scores are rejected.
- Overall percentage is calculated from the three scores.
- Decision Pending keeps the interview In Progress.
- Application remains Interview.
- Recruiter can reopen and continue the evaluation.

## 8. Final interview decisions
### Selected
- Interview becomes Completed.
- Application becomes Selected.
- Student sees the final score and Selected result.
- Completed interview cannot be edited.

### Not Selected
- Interview becomes Completed.
- Application becomes Rejected.
- Student sees the final result.
- Completed interview cannot be edited.

### Move to Next Round
- Interview becomes Completed.
- Application remains Interview.
- Recruiter gets Schedule Next Round.
- A new round cannot be scheduled until this decision exists.
- Previous round remains visible in interview history.

## 9. Next round
- Recruiter schedules the next interview.
- The new interview is the active interview.
- Student sees the new round.
- Previous round remains Completed.
- Only the active round accepts a new response.

## 10. Cancellation/rejection safety
- Recruiter can reject a pre-finalized candidate.
- If an active interview exists and recruiter rejects the candidate, the active interview is cancelled.
- Student no longer gets a stale active interview submission flow.
- Finalized applications cannot be moved backward through the generic status control.

## 11. Resume safety
- Recruiter review uses the resume attached to the application.
- A later resume upload by the student does not replace the resume submitted for an older application.

## 12. Navigation
- Student Interview Center links open the correct interview.
- Recruiter Candidate Review links open the correct interview.
- Interview history links remain valid after completion.
