# refer UHG golden images as the base image
FROM optum-docker-auth-prod.repo1.uhc.com/chainguard/python/dev:3.12-latest-dev

# Switch to ROOT
USER root

# Install required OS packages
RUN apk update && \
apk add --no-cache \
git

# Create non-root user early, The Golden Container-base use BusyBox by default, so any groupadd or useradd commands will need to be ported to addgroup and adduser.
# --disabled-password: This option creates the user without setting a password, which is useful for non-interactive environments like Docker builds.
RUN adduser --disabled-password --home /home/advocate-assist --shell /bin/bash advocate-assist

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME

# Copy application code 
COPY --chown=advocate-assist . .
RUN pip install -r requirements.txt

# Verify the installation path of uvicorn
RUN echo "Uvicorn installation path:" && which uvicorn && \
    echo "Uvicorn version:" && uvicorn --version

# Set up user permissions
RUN mkdir -p /home/advocate-assist/.local/bin && \
    chown -R advocate-assist:advocate-assist /home/advocate-assist/.local && \
    chown -R advocate-assist:advocate-assist $APP_HOME && \
    chmod -R 755 $APP_HOME /home/advocate-assist/.local

# Ensure the non-root user has the correct PATH and explicitly ensure that the PATH includes the directories where uvicorn is installed.
ENV PATH="/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/home/advocate-assist/.local/bin:${PATH}"

# Run the web service on container startup. Here we use uvicorn
# webserver for FastAPI applications.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
EXPOSE 8080

# Use uvicorn for FastAPI with production settings
# Use ENTRYPOINT rather than CMD
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
