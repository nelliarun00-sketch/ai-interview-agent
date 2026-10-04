import json

questions = {
    "diagnostic": [
        {
            "id": "diag_py_01",
            "skill_id": "python",
            "question": "What is the primary difference between a list and a tuple in Python?",
            "type": "mcq",
            "difficulty": "easy",
            "options": [
                "Lists are immutable, while tuples are mutable.",
                "Lists are mutable, while tuples are immutable.",
                "Tuples can only store integers, whereas lists store any type.",
                "There is no functional difference; they are syntactic aliases."
            ],
            "correct_option": 1,
            "explanation": "In Python, lists are mutable (can be appended or modified), whereas tuples are immutable and hashable."
        },
        {
            "id": "diag_py_02",
            "skill_id": "python",
            "question": "What does the 'yield' keyword do inside a Python function?",
            "type": "mcq",
            "difficulty": "medium",
            "options": [
                "Terminates the program execution immediately.",
                "Converts the function into an asynchronous coroutine.",
                "Turns the function into a generator that yields values lazily on demand.",
                "Exports the function variable into the global namespace."
            ],
            "correct_option": 2,
            "explanation": "'yield' pauses function execution and returns a generator iterator object preserving execution state."
        },
        {
            "id": "diag_dsa_01",
            "skill_id": "dsa",
            "question": "What is the average time complexity of searching an element in a balanced Binary Search Tree (BST)?",
            "type": "mcq",
            "difficulty": "easy",
            "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
            "correct_option": 1,
            "explanation": "In a balanced BST with n nodes, height is log2(n), yielding O(log n) average search time."
        },
        {
            "id": "diag_dsa_02",
            "skill_id": "dsa",
            "question": "Which data structure is primarily used in Breadth-First Search (BFS) graph traversal?",
            "type": "mcq",
            "difficulty": "easy",
            "options": ["Stack", "Queue", "Priority Heap", "Hash Table"],
            "correct_option": 1,
            "explanation": "BFS visits vertices in level-order using a FIFO Queue."
        },
        {
            "id": "diag_oop_01",
            "skill_id": "oop",
            "question": "Which principle of OOP is demonstrated by having methods with the same name behaving differently based on the calling object?",
            "type": "mcq",
            "difficulty": "easy",
            "options": ["Encapsulation", "Polymorphism", "Abstraction", "Inheritance"],
            "correct_option": 1,
            "explanation": "Polymorphism (many forms) allows different classes to implement methods with identical signatures."
        },
        {
            "id": "diag_dbms_01",
            "skill_id": "dbms",
            "question": "Which property of ACID transactions ensures that a transaction is all-or-nothing?",
            "type": "mcq",
            "difficulty": "easy",
            "options": ["Atomicity", "Consistency", "Isolation", "Durability"],
            "correct_option": 0,
            "explanation": "Atomicity guarantees that all operations within a work unit are completed successfully or entirely rolled back."
        },
        {
            "id": "diag_os_01",
            "skill_id": "os",
            "question": "What occurs during a CPU context switch between two processes?",
            "type": "mcq",
            "difficulty": "medium",
            "options": [
                "Memory cache is deleted completely.",
                "The state (registers, program counter) of the running process is saved and the new process state is loaded.",
                "The operating system kernel reboots the scheduler thread.",
                "All process memory pages are transferred to virtual swap space."
            ],
            "correct_option": 1,
            "explanation": "A context switch stores execution state in the Process Control Block (PCB) and restores the state of the scheduled process."
        },
        {
            "id": "diag_net_01",
            "skill_id": "networks",
            "question": "At which layer of the OSI model does the TCP protocol operate?",
            "type": "mcq",
            "difficulty": "easy",
            "options": ["Application Layer", "Transport Layer", "Network Layer", "Data Link Layer"],
            "correct_option": 1,
            "explanation": "TCP and UDP operate at Layer 4 (Transport Layer) providing end-to-end communication services."
        },
        {
            "id": "diag_stat_01",
            "skill_id": "statistics",
            "question": "What does the p-value indicate in classical statistical hypothesis testing?",
            "type": "mcq",
            "difficulty": "medium",
            "options": [
                "The exact probability that the null hypothesis is true.",
                "The probability of observing results at least as extreme as the actual test data, assuming the null hypothesis is true.",
                "The statistical power of the experimental test.",
                "The probability of committing a Type II false-negative error."
            ],
            "correct_option": 1,
            "explanation": "A p-value measures evidence against the null hypothesis: lower values suggest observed data is unlikely under H0."
        },
        {
            "id": "diag_ml_01",
            "skill_id": "machine_learning",
            "question": "High training accuracy combined with significantly lower validation accuracy is a primary symptom of what?",
            "type": "mcq",
            "difficulty": "easy",
            "options": ["High Bias (Underfitting)", "High Variance (Overfitting)", "Data Leakage in Test Set", "Under-regularization of features"],
            "correct_option": 1,
            "explanation": "Overfitting occurs when a model memorizes training noise and fails to generalize to unseen validation data."
        }
    ],
    "interview_seed": {
        "python": [
            "How does memory management work in Python, and what role do reference counting and generational garbage collection play?",
            "Explain how Python decorators work under the hood and provide an example of a decorator that measures function execution time."
        ],
        "dsa": [
            "Given an array of integers, how would you find the contiguous subarray with the maximum sum in O(n) time using Kadane's Algorithm?",
            "Explain the trade-offs between QuickSort and MergeSort regarding time complexity, space complexity, and stability."
        ],
        "oop": [
            "What is the Diamond Problem in multiple inheritance, and how does Python resolve it using C3 Linearization (Method Resolution Order)?",
            "Explain the Liskov Substitution Principle (LSP) and provide an example of a class hierarchy that violates it."
        ],
        "dbms": [
            "Explain the four database transaction isolation levels (Read Uncommitted, Read Committed, Repeatable Read, Serializable) and the phenomena each prevents.",
            "What is the difference between a clustered and a non-clustered index in SQL databases?"
        ],
        "coding": [
            {
                "id": "code_01",
                "title": "Two Sum Problem",
                "difficulty": "easy",
                "problem": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target. You may assume each input has exactly one solution, and you may not use the same element twice.",
                "examples": [
                    {"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]"}
                ],
                "constraints": "2 <= nums.length <= 10^4, -10^9 <= nums[i] <= 10^9",
                "hints": ["Use a hash map to look up complements in O(1) time."]
            },
            {
                "id": "code_02",
                "title": "Longest Substring Without Repeating Characters",
                "difficulty": "medium",
                "problem": "Given a string s, find the length of the longest substring without repeating characters.",
                "examples": [
                    {"input": "s = 'abcabcbb'", "output": "3 (abc)"}
                ],
                "constraints": "0 <= s.length <= 5 * 10^4",
                "hints": ["Use a sliding window with two pointers and a character index map."]
            }
        ]
    }
}

rubrics = {
    "technical": {
        "scores": {
            "0-4": "Incomplete or fundamentally flawed understanding; cannot explain key definitions or operations.",
            "5-7": "Understands the core concept; communicates basic syntax or principles but misses trade-offs, internal mechanics, or edge cases.",
            "8-10": "Mastery demonstrated; explains internal implementation, architectural trade-offs, performance implications, and practical examples."
        },
        "dimensions": ["Technical Accuracy", "Depth & Mechanics", "Communication Clarity", "Practical Applications"]
    },
    "coding": {
        "scores": {
            "0-4": "Syntax errors, incorrect algorithmic approach, or fails standard sample cases.",
            "5-7": "Functional brute-force or sub-optimal approach; passes primary test cases but misses edge cases or suboptimal time/space complexity.",
            "8-10": "Optimal algorithmic complexity (e.g. O(n) instead of O(n^2)), handles null/empty/boundary inputs, clean idiomatic variable naming."
        }
    },
    "hr_behavioral": {
        "star_criteria": {
            "Situation": "Set the context, company, or technical challenge clearly.",
            "Task": "Defined personal responsibility and role in the problem.",
            "Action": "Detailed specific engineering decisions or personal initiatives taken.",
            "Result": "Quantified business impact, performance gain, or lessons learned."
        }
    }
}

with open("data/question_bank.json", "w", encoding="utf-8") as f:
    json.dump(questions, f, indent=2)

with open("data/rubrics.json", "w", encoding="utf-8") as f:
    json.dump(rubrics, f, indent=2)

print("data/question_bank.json and data/rubrics.json generated successfully")
