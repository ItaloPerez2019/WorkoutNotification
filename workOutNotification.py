# import os
# import json
# import time
# import logging
# import smtplib
# import schedule
# import datetime
# from dotenv import load_dotenv
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz  # Install with pip install pytz

logging.basicConfig(level=logging.INFO)

# ------------------------------------------------------------------------------
# 1. Configure Logging
# ------------------------------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(script_dir, "workout_scheduler.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, mode='a'),
        logging.StreamHandler()
    ]
)

logging.info("Daily Workout Scheduler script started.")

# ------------------------------------------------------------------------------
# 2. Load Environment Variables
# ------------------------------------------------------------------------------
os.environ.clear()
load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

missing_vars = []
for var_name, var_value in [
    ("SMTP_SERVER", SMTP_SERVER),
    ("SMTP_PORT", SMTP_PORT),
    ("EMAIL_ADDRESS", EMAIL_ADDRESS),
    ("EMAIL_PASSWORD", EMAIL_PASSWORD),
    ("RECIPIENT_EMAIL", RECIPIENT_EMAIL),
]:
    if not var_value:
        missing_vars.append(var_name)

if missing_vars:
    logging.error(f"Missing environment variables: {', '.join(missing_vars)}.")
    exit(1)

try:
    SMTP_PORT = int(SMTP_PORT)
except ValueError:
    logging.error(f"Invalid SMTP_PORT value: {SMTP_PORT}")
    exit(1)


# ------------------------------------------------------------------------------
# 3. Load Workouts JSON
# ------------------------------------------------------------------------------
json_file_path = os.path.join(script_dir, "workouts.json")

try:
    with open(json_file_path, "r") as f:
        workout_data = json.load(f)
except FileNotFoundError:
    logging.error(f"JSON file not found at {json_file_path}.")
    exit(1)
except json.JSONDecodeError as e:
    logging.error(f"Error decoding JSON: {e}")
    exit(1)

days_list = workout_data.get("days", [])
if not days_list:
    logging.warning("No workouts found in the JSON file.")
    days_list = []

# ------------------------------------------------------------------------------
# 4. Function to Build the Day's Workout HTML
# ------------------------------------------------------------------------------


def build_workout_html(day_info):
    title = day_info.get("title", "Workout")
    exercises = day_info.get("exercises", [])

    html_content = f"""\
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
            }}
            .day-title {{
                font-weight: bold;
                font-size: 18px;
                margin-bottom: 10px;
            }}
            .exercise {{
                margin-bottom: 10px;
            }}
            .exercise a {{
                text-decoration: none;
                color: #0066cc;
            }}
        </style>
    </head>
    <body>
        <div class="day-title">{title}</div>
    """

    for ex in exercises:
        name = ex.get("name", "")
        sets = ex.get("sets", "")
        rest = ex.get("rest", "")
        url = ex.get("url", None)

        # If there's a URL, create a hyperlink
        if url:
            html_content += f"""
            <div class="exercise">
                <p>
                    <strong>
                        <a href="{url}" target="_blank">{name}</a>
                    </strong>
                </p>
                <p>Sets/Reps: {sets}</p>
                <p>Rest: {rest}</p>
            </div>
            """
        else:
            html_content += f"""
            <div class="exercise">
                <p><strong>{name}</strong></p>
                <p>Sets/Reps: {sets}</p>
                <p>Rest: {rest}</p>
            </div>
            """

    html_content += """
        <p><em>Tip:</em> Stay hydrated and track your progress. Enjoy your workout!</p>
    </body>
    </html>
    """
    return html_content

# ------------------------------------------------------------------------------
# 5. Function to Determine Which Day's Workout to Send
# ------------------------------------------------------------------------------


def get_today_workout():
    """
    Returns the workout for the current weekday.
    Monday = 0, Tuesday = 1, ... Sunday = 6.
    We'll map that directly to the 7 days in the JSON.
    """
    today_index = datetime.datetime.now().weekday()  # 0-6
    # If you want Monday=Day 1, Tuesday=Day 2, etc.,
    # just ensure days_list[today_index] exists or wrap around with modulo.
    if today_index < len(days_list):
        return days_list[today_index]
    else:
        # If there are fewer than 7 days in the JSON,
        # fallback to day 0 or do something else
        return days_list[0] if days_list else {}

# ------------------------------------------------------------------------------
# 6. Function to Send Email
# ------------------------------------------------------------------------------


def send_daily_workout():
    """Sends the workout for today's weekday."""
    workout_for_today = get_today_workout()
    if not workout_for_today:
        logging.warning("No workout info for today.")
        return

    subject = f"{workout_for_today.get(
        'title', 'Your Workout')} - {datetime.datetime.now().strftime('%A')}"
    html_body = build_workout_html(workout_for_today)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
        logging.info(f"Workout email sent successfully to {RECIPIENT_EMAIL}.")
    except smtplib.SMTPException as smtp_err:
        logging.error(f"SMTP error when sending email: {smtp_err}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

# ------------------------------------------------------------------------------
# 7. Schedule the Job for 6 AM (local system time)
# ------------------------------------------------------------------------------


def main():
    # Schedule the send_daily_workout() function at 06: 00 every day
    schedule.every().day.at("06:00").do(send_daily_workout)

    logging.info("Scheduling daily workout at 06:00. Now entering loop...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # wait 1 minute between checks
    # #test
    # send_daily_workout()


def send_email():
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    email_address = os.getenv("EMAIL_ADDRESS")
    email_password = os.getenv("EMAIL_PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL")

    subject = "Daily Workout"
    body = "Here is your workout for the day!"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email_address
    msg["To"] = recipient_email
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.starttls()
            server.login(email_address, email_password)
            server.sendmail(email_address, recipient_email, msg.as_string())
        logging.info(f"Email sent to {recipient_email}")
    except Exception as e:
        logging.error(f"Error sending email: {e}")


if __name__ == "__main__":
    # Get current time in EST/EDT
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    logging.info(f"Current Eastern Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    send_email()
