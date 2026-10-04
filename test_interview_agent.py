"""
End-to-End Test Suite for AI-Powered Interview Preparation Agent
Verifies Flask routes, session state transitions, adaptive difficulty,
JSON evaluation handling, and the complete 5-question interview lifecycle.
"""
import unittest
from app import app, calculate_next_difficulty

class InterviewAgentTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_difficulty_adaptation_logic(self):
        """Test the DECIDE/ADAPT difficulty rules."""
        # Low score (0-4) reduces or keeps easy
        self.assertEqual(calculate_next_difficulty("hard", 3), "medium")
        self.assertEqual(calculate_next_difficulty("medium", 2), "easy")
        self.assertEqual(calculate_next_difficulty("easy", 4), "easy")

        # Medium score (5-7) maintains difficulty
        self.assertEqual(calculate_next_difficulty("easy", 6), "easy")
        self.assertEqual(calculate_next_difficulty("medium", 7), "medium")
        self.assertEqual(calculate_next_difficulty("hard", 5), "hard")

        # High score (8-10) increases difficulty
        self.assertEqual(calculate_next_difficulty("easy", 9), "medium")
        self.assertEqual(calculate_next_difficulty("medium", 8), "hard")
        self.assertEqual(calculate_next_difficulty("hard", 10), "hard")

    def test_api_status(self):
        """Test /api/status health check."""
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "online")
        self.assertIn("OBSERVE", data["architecture"])

    def test_home_page(self):
        """Test / loads the home page form."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("AI Interview Preparation Agent", html)
        self.assertIn("Student Name", html)
        self.assertIn("Target Job Role", html)
        self.assertIn("Current Technical Skills", html)
        self.assertIn("Initial Weak Areas", html)
        self.assertIn("Start AI Interview", html)

    def test_full_5_question_interview_flow(self):
        """Test complete 5-question interview and final result page."""
        # 1. Start interview
        response = self.client.post("/start-interview", data={
            "student_name": "Arun",
            "job_role": "Python Developer",
            "skills": "Python, C++, SQL",
            "weak_areas": "OOP, DSA",
            "prep_time": "2 hours per day"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Question 1 of 5", html)
        self.assertIn("Arun", html)
        self.assertIn("Python Developer", html)

        # Loop through 5 questions
        for q_num in range(1, 6):
            # Submit answer
            answer_text = f"This is my technical answer for Question {q_num}. Object Oriented Programming uses encapsulation, inheritance, polymorphism, and abstraction to organize code."
            eval_resp = self.client.post("/evaluate", data={
                "answer": answer_text
            })
            self.assertEqual(eval_resp.status_code, 200)
            eval_html = eval_resp.get_data(as_text=True)
            self.assertIn("AI Interview Evaluation", eval_html)
            self.assertIn("What You Did Well", eval_html)
            self.assertIn("What You Need to Improve", eval_html)
            self.assertIn("Weak Technical Area", eval_html)

            if q_num < 5:
                self.assertIn("Generate Next Question", eval_html)
                # Fetch next question
                next_resp = self.client.get("/next-question")
                self.assertEqual(next_resp.status_code, 200)
                next_html = next_resp.get_data(as_text=True)
                self.assertIn(f"Question {q_num + 1} of 5", next_html)
            else:
                self.assertIn("View Final Interview Summary", eval_html)

        # Final result page
        result_resp = self.client.get("/final-result")
        self.assertEqual(result_resp.status_code, 200)
        result_html = result_resp.get_data(as_text=True)
        self.assertIn("Interview Completed", result_html)
        self.assertIn("Arun", result_html)
        self.assertIn("Python Developer", result_html)
        self.assertIn("Personalized Preparation Plan", result_html)
        self.assertIn("Day 1", result_html)
        self.assertIn("Day 5", result_html)

        # Reset interview
        reset_resp = self.client.get("/reset", follow_redirects=True)
        self.assertEqual(reset_resp.status_code, 200)
        reset_html = reset_resp.get_data(as_text=True)
        self.assertIn("Start AI Interview", reset_html)

if __name__ == "__main__":
    unittest.main()
