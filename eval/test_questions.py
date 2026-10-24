"""Ground-truth benchmark test questions for evaluating the Enterprise RAG Knowledge Assistant.

Each test case contains the question, category, expected source documents,
and the key factual criteria expected in the answer.
"""

TEST_CASES = [
    # --- HR Policies ---
    {
        "category": "HR Policies",
        "question": "How many days of annual leave do full-time employees accrue, and how many can be carried over?",
        "expected_sources": ["hr_policies.md"],
    },
    {
        "category": "HR Policies",
        "question": "How many weeks of paid parental leave does Aurelia offer for primary and secondary caregivers?",
        "expected_sources": ["hr_policies.md"],
    },
    {
        "category": "HR Policies",
        "question": "What is the doctor's note requirement for sick leave?",
        "expected_sources": ["hr_policies.md"],
    },

    # --- IT Onboarding & Support ---
    {
        "category": "IT Onboarding",
        "question": "What are the company's password complexity rules and how often must passwords be changed?",
        "expected_sources": ["it_onboarding.md"],
    },
    {
        "category": "IT Onboarding",
        "question": "What is the approval threshold and process for requesting additional software licenses?",
        "expected_sources": ["it_onboarding.md"],
    },

    # --- Company Overview & Culture ---
    {
        "category": "Company Overview",
        "question": "What are the four core values of Aurelia Tech?",
        "expected_sources": ["company_overview.md"],
    },
    {
        "category": "Code of Conduct",
        "question": "How can an employee report a Code of Conduct concern anonymously, and what is the policy on retaliation?",
        "expected_sources": ["code_of_conduct.md"],
    },

    # --- Engineering & Tech Stack ---
    {
        "category": "Engineering Standards",
        "question": "What are the branch naming rules and peer review approval requirements for pull requests?",
        "expected_sources": ["engineering_standards.md"],
    },
    {
        "category": "Technology Stack",
        "question": "What are the standard backend frameworks and primary databases used across Aurelia services?",
        "expected_sources": ["technology_stack.md"],
    },

    # --- Current Projects ---
    {
        "category": "Current Projects",
        "question": "What is Project Atlas, which team owns it, and what technology stack does it use?",
        "expected_sources": ["current_projects.md"],
    },
    {
        "category": "Current Projects",
        "question": "What is Project Horizon and who does the team report to?",
        "expected_sources": ["current_projects.md"],
    },

    # --- Troubleshooting & Glossary ---
    {
        "category": "Troubleshooting",
        "question": "What steps should I take if the Aurelia Secure VPN disconnects or refuses to connect?",
        "expected_sources": ["troubleshooting.md"],
    },
    {
        "category": "Glossary",
        "question": "What does ADR stand for at Aurelia, and what is its purpose?",
        "expected_sources": ["glossary.md"],
    },

    # --- Cross-Document Inquiry ---
    {
        "category": "Cross-Document",
        "question": "What is the Innovation Time policy and how does it relate to Project Horizon?",
        "expected_sources": ["current_projects.md", "glossary.md"],
    },

    # --- Out-of-Scope Negative Test Cases (Tests Honest Abstention) ---
    {
        "category": "Out-of-Scope",
        "question": "What is the company policy regarding bringing pet elephants or exotic animals into the office?",
        "expected_sources": [],  # Expects zero sources / honest abstention
    },
    {
        "category": "Out-of-Scope",
        "question": "What is the capital city of France?",
        "expected_sources": [],  # Expects zero sources / honest abstention
    },
]