"""Stub module for qpt_generator to allow app to run without the actual package."""

class QPTGenerator:
    """Stub class for QPTGenerator."""
    
    def __init__(self, data, question_no):
        self.data = data
        self.question_no = question_no
    
    def generate(self):
        """Return a simple template structure."""
        # Return a basic template that won't crash the app
        return [[1] * self.question_no]
