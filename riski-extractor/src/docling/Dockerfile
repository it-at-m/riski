FROM  quay.io/docling-project/docling-serve-cpu:latest@sha256:41c177c4c355d050e4f8e289ebbeb3bb5eaaae4c4d40914eac7c37890591fc15
# Set the working directory
WORKDIR /usr/src/app

# Copy your documentation files into the container
# COPY ./docs /usr/src/app
# Expose the port on which the app will run
EXPOSE 5001

# Command to run the Docling Serve application
CMD ["docling-serve", "run"]