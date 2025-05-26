FROM  quay.io/docling-project/docling-serve-cpu:latest
# Set the working directory
WORKDIR /usr/src/app

# Copy your documentation files into the container
# COPY ./docs /usr/src/app
ENV DOCLING_SERVE_MAX_SYNC_WAIT=2000
# Expose the port on which the app will run
EXPOSE 5001

# Command to run the Docling Serve application
CMD ["docling-serve", "run"]