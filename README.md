# Hasker
Homework #6 (OTUS. Python Developer. Professional)

Web app for asking questions and getting answers

## Run dev
`docker-compose up`

## Run prod

`docker-compose -f docker-compose.prod.yml up --build`
`docker exec web python manage.py migrate --noinput`

## Run tests
`docker-compose -f docker-compose.ci.yml up`

## Hasker API
API can be found at:
 - `/api` - browsable API
 - `/api/swagger` - swagger
