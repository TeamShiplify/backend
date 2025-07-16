# Local Django + Docker Setup

## Requirements
- Docker  
- Docker Compose  
- Running scripts inside WSL (Windows Subsystem for Linux) is required for Windows users

## Getting Started
Run the startup script:
```
./start-dev.sh
```

## Important Notes
Migrations are run automatically on container start.

The source code is mounted into the container, so code changes reflect immediately.

Do NOT commit your .env file to the repository!


**If you encounter any issues, please contact the DevOps team:**
krystian@wlodek.net