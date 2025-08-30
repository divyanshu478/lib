from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import os



# create database object globally
db = SQLAlchemy()

def create_app() :
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
   
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL_EXTERNAL")
    app.config['SQLALCHEMY_TRACK_NOTIFICATIONS'] = False

    #connecting the database
    db.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.tasks import task_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(task_bp)


    # ✅ Scheduler setup
    from app.routes.tasks import update_due_status, send_email  
   
    scheduler = BackgroundScheduler()

    def job():
        with app.app_context():
            update_due_status()
            send_email()


    # if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    scheduler.add_job(func=job, trigger="cron", hour=8, minute=0)
    # scheduler.add_job(func=job, trigger="interval", minutes=5)
    scheduler.start()

    return app