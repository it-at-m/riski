FROM  quay.io/docling-project/docling-serve-cpu:latest@sha256:fda4808f0ac3c51585ff195089109e619deb829c121416739928a87ac6e5c870
# Set the working directory
WORKDIR /usr/src/app

# Copy your documentation files into the container
# COPY ./docs /usr/src/app
# Expose the port on which the app will run
EXPOSE 5001

# Command to run the Docling Serve application
CMD ["docling-serve", "run"]