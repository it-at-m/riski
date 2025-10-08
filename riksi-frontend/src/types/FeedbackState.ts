enum FeedbackState {
  PENDING_SEARCH, // No search has been made, no feedback is available
  CONTEXTUAL, // Feedback for a specific question
  POSITVE,
  NEGATIVE,
}

export default FeedbackState;
