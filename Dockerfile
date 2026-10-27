# Sitio estático (HTML + Flutter web en /web/) servido con nginx.
FROM nginx:1.27-alpine
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY . /usr/share/nginx/html
RUN rm -rf /usr/share/nginx/html/deploy /usr/share/nginx/html/Dockerfile /usr/share/nginx/html/.htaccess
EXPOSE 80
