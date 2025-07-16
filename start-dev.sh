#!/bin/bash

# Sprawdź, czy .env istnieje, jeśli nie, skopiuj z .env.example
if [ ! -f .env ]; then
  echo "Brak pliku .env, kopiuję z .env.example"
  cp .env.example .env
fi

# Uruchom docker-compose
docker-compose up --build