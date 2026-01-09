# HabitFlow - Personal Habit & Productivity Tracker

HabitFlow is a web application designed to help you track your daily habits (sleep, water intake, reading, etc.) and analyze how they correlate with your daily productivity and mood. By visualizing these relationships, you can optimize your routine for better performance and well-being.

**Live Demo:** [https://habitflow-demo.pythonanywhere.com](https://habitflow-demo.pythonanywhere.com) *(Placeholder)*

## Key Features
*   **Habit Tracking:** Define custom habits with targets (e.g., "Sleep 8 hours").
*   **Daily Journal:** Log your productivity (1-10) and mood (1-10) daily.
*   **Analytics Dashboard:** View correlation graphs (Scatter plots with trendlines) to see if sleeping more actually makes you more productive.
*   **Responsive UI:** Built with Tailwind CSS for a modern, mobile-friendly experience.

## Tech Stack
*   **Python 3.x**
*   **Django 4.x**
*   **Pandas & NumPy** (Data Analysis)
*   **Matplotlib** (Graph Generation)
*   **Tailwind CSS** (Frontend Styling via CDN)

## Screenshots
*(Insert Screenshots here)*
1.  **Dashboard:** Overview of habits.
2.  **Analytics:** Correlation graphs.

## How to Run Locally

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/habit_tracker.git
    cd habit_tracker
    ```

2.  **Create and activate virtual environment:**
    ```bash
    # Using uv (recommended)
    uv venv
    source .venv/bin/activate
    
    # Or standard python
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    uv pip install -r requirements.txt
    # or
    pip install -r requirements.txt
    ```

4.  **Run migrations:**
    ```bash
    python manage.py migrate
    ```

5.  **Seed initial data (optional):**
    ```bash
    python seed_data.py
    ```
    *Creates a superuser `admin`/`admin` and sample data.*

6.  **Start the server:**
    ```bash
    python manage.py runserver
    ```

7.  **Open in browser:**
    Go to [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Deployment
This project is configured for deployment on PythonAnywhere.
1.  Set `DEBUG = False` in production.
2.  Run `python manage.py collectstatic`.
3.  Configure WSGI and Virtualenv on PythonAnywhere dashboard.
