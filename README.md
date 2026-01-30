# Finance AI

Finance AI is a modular platform for financial data analysis, portfolio tracking, AI-driven signal extraction, and automated reporting. It is designed for extensibility, privacy, and ease of deployment using Docker.

## Features
- **AI Analysis**: Leverage AI to analyze financial data and extract actionable signals.
- **Portfolio Tracking**: Track and analyze your investment portfolios.
- **News Fetching**: Integrate financial news for context-aware analysis.
- **Automated Email Reports**: Receive regular reports via email.
- **Web Dashboard**: Visualize analytics and portfolio performance in a modern dashboard.
- **Modular Design**: Each component (analysis, dashboard, mail, portfolio) is containerized for flexibility.

## Project Structure
```
finance-ai/
├── app/                # Core AI analysis and data fetching
├── dashboard/          # Web dashboard (Flask, JS, HTML, CSS)
├── mail/               # Email reporting service
├── portfolio/          # Portfolio tracker
├── data/               # (Ignored) Local data and database files
├── models/             # (Ignored) Downloaded models and keys
├── docker-compose.yml  # Orchestrates all services
├── Dockerfile          # Base Dockerfile for app
└── README.md           # This file
```

## Setup & Installation

### Prerequisites
- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/)
- Python 3.8+ (for local development)
- Git

### 1. Clone the Repository
```
git clone https://github.com/therundmc/finance-ai.git
cd finance-ai
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory with your credentials and API keys. Example:
```
# .env
DB_USER=your_db_user
DB_PASS=your_db_password
API_KEY=your_api_key
EMAIL_USER=your_email
EMAIL_PASS=your_email_password
```
**Never commit your `.env` file!**

### 3. Build and Start with Docker Compose
```
docker compose up --build
```
This will start all services: analysis, dashboard, mail, and portfolio tracker.

### 4. Access the Dashboard
Open your browser and go to: [http://localhost:8888](http://localhost:8888)

## Usage
- Place your data files in the `app/data/` directory (ignored by git).
- Download or place your AI models in the `models/` directory (ignored by git).
- Use the dashboard for interactive analysis and portfolio management.
- Reports will be sent automatically if email is configured.

## Development
- Each service has its own `requirements.txt`.
- To run a service locally:
  - `cd app && python ai_analysis.py`
  - `cd dashboard && python app.py`
  - `cd mail && python email_report.py`
  - `cd portfolio && python portfolio_tracker.py`
- For custom analysis, extend `app/ai_analysis.py` or add new modules.

## Security & Privacy
- Sensitive files (`.env`, `models/`, `data/`) are excluded from version control.
- Do not share your credentials or private models.

## Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License
MIT License. See LICENSE file for details.
