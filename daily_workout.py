import os
import json
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ------------------------------------------------------------------------------
# 1. Configure Logging
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ------------------------------------------------------------------------------
# 2. Load Workouts JSON
# ------------------------------------------------------------------------------


def load_workouts(json_path):
    logging.info(f"Loading workouts from {json_path}")
    try:
        with open(json_path, "r") as f:
            workout_data = json.load(f)
        days = workout_data.get("days", [])
        if not days:
            logging.error("No workouts found in the JSON file.")
            exit(1)
        logging.info(f"Loaded {len(days)} days of workouts.")
        return days
    except FileNotFoundError:
        logging.error(f"JSON file not found at {json_path}.")
        exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {e}")
        exit(1)

# ------------------------------------------------------------------------------
# 3. Build Workout HTML
# ------------------------------------------------------------------------------


def build_workout_html(day_info):
    title = day_info.get("title", "Workout")
    exercises = day_info.get("exercises", [])

    logging.info(f"Building HTML for: {title}")

    html_content = f"""\
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
            }}
            .day-title {{
                background-color: #f2f2f2;
                padding: 10px;
                border-radius: 5px;
                font-size: 20px;
                margin-bottom: 20px;
            }}
            .exercise {{
                margin-bottom: 15px;
            }}
            .exercise a {{
                text-decoration: none;
                color: #007BFF;
            }}
        </style>
    </head>
    <body>
        <div class="day-title">{title}</div>
    """

    for ex in exercises:
        name = ex.get("name", "Unknown Exercise")
        sets = ex.get("sets", "")
        rest = ex.get("rest", "")
        url = ex.get("url", "")

        if url:
            exercise_name = f'<a href="{url}" target="_blank">{name}</a>'
        else:
            exercise_name = name

        html_content += f"""
        <div class="exercise">
            <p><strong>{exercise_name}</strong></p>
            <p>Sets/Reps: {sets}</p>
            <p>Rest: {rest}</p>
        </div>
        """

    html_content += """
        <p><em>Tip:</em> Always warm up properly, focus on form, and stay hydrated!</p>
    </body>
    </html>
    """
    return html_content

# ------------------------------------------------------------------------------
# 4. Determine Today's Workout
# ------------------------------------------------------------------------------


def get_today_workout(days_list):
    today_index = datetime.utcnow().weekday()  # Monday=0, Sunday=6
    logging.info(f"Today's index (UTC): {today_index}")
    if today_index < len(days_list):
        selected_workout_title = days_list[today_index].get(
            'title', 'No Title')
        # logging.info(f"Selected workout for index {
        #              today_index}: {selected_workout_title}")
        return days_list[today_index]
    else:
        logging.error("Today's workout index is out of range.")
        exit(1)

# ------------------------------------------------------------------------------
# 5. Send Email Function
# ------------------------------------------------------------------------------


def send_email(subject, html_body, smtp_server, smtp_port, email_address, email_password, recipient_email):
    logging.info(f"Preparing to send email to {
                 recipient_email} with subject '{subject}'")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email_address
    msg["To"] = recipient_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        logging.info(f"Connecting to SMTP server: {smtp_server}:{smtp_port}")
        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.starttls()
            logging.info("Logging into SMTP server")
            server.login(email_address, email_password)
            logging.info("Sending email")
            server.sendmail(email_address, recipient_email, msg.as_string())
        logging.info(f"Email sent successfully to {recipient_email}.")
    except smtplib.SMTPException as smtp_err:
        logging.error(f"SMTP error when sending email: {smtp_err}")
    except Exception as e:
        logging.error(f"Unexpected error when sending email: {e}")

# ------------------------------------------------------------------------------
# 6. Main Execution
# ------------------------------------------------------------------------------


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(script_dir, "workouts.json")
    days_list = load_workouts(json_file_path)

    workout_today = get_today_workout(days_list)
    subject = f"{workout_today.get(
        'title', 'Your Workout')} - {datetime.utcnow().strftime('%A')}"
    html_body = build_workout_html(workout_today)

    # Fetch environment variables
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    email_address = os.getenv("EMAIL_ADDRESS")
    email_password = os.getenv("EMAIL_PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL")

    if not all([smtp_server, smtp_port, email_address, email_password, recipient_email]):
        logging.error("One or more environment variables are missing.")
        exit(1)

    send_email(subject, html_body, smtp_server, smtp_port,
               email_address, email_password, recipient_email)


if __name__ == "__main__":
    main()
