# Minimal PostgreSQL Dockerfile for notes_database container

FROM postgres:16-alpine

# Set environment variables for postgres user, db, and password (can also be set by docker-compose)
ENV POSTGRES_DB=notesdb
ENV POSTGRES_USER=notesuser
ENV POSTGRES_PASSWORD=notessecret

# Copy in the schema initialization script
COPY init.sql /docker-entrypoint-initdb.d/

# Expose default Postgres port
EXPOSE 5432
