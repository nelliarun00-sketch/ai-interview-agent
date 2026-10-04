"""
Routes Package Initialization
-----------------------------
Exports blueprint registration helper.
"""

from flask import Flask

def register_blueprints(app: Flask):
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.progress import progress_bp
    from routes.career import career_bp
    from routes.profile import profile_bp
    from routes.onboarding import onboarding_bp
    from routes.assessment import assessment_bp
    from routes.roadmap import roadmap_bp
    from routes.resources import resources_bp
    from routes.interview import interview_bp
    from routes.resume import resume_bp
    from routes.planner import planner_bp
    from routes.performance import performance_bp
    from routes.projects_certs import projects_certs_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(career_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(assessment_bp)
    app.register_blueprint(roadmap_bp)
    app.register_blueprint(resources_bp)
    app.register_blueprint(interview_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(planner_bp)
    app.register_blueprint(performance_bp)
    app.register_blueprint(projects_certs_bp)
